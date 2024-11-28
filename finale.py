# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Mon Sep 30 17:25:01 2024

# @author: MSI
# """

#%% program ini nantinya untuk memprediksi peta yg asli

import rasterio
import os
import sys
import pandas as pd
import geopandas as gpd
from rasterio.mask import mask
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(script_dir)
import addFeature as af
import training_pixel as train
#%%
bands_src = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

band_path = parent_dir + '/Data/satelit/21082024/'

for i in range(1, 13):
    if i != 9 and i != 10:
        curr_band = rasterio.open(band_path + "B" + str(i) + ".jp2")
        bands_src[i] = curr_band

bands_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

for i in range(1, 13):
    if i != 9 and i != 10:
        bands_list[i] = bands_src[i].read(1)

print("Successfully Read Bands Raster")
#%% CLIPPING

# print(test_geojson[0]["coordinates"][0])
# polygon_gdf = gpd.read_file(geojson_path + file) 
# polygon_gdf = gpd.GeoDataFrame(geometry=[Polygon(my_geojson[0]["coordinates"])])

DTA_Cisangkuy = gpd.read_file(script_dir + "/dta_cisangkuy.geojson")

src = bands_src[1]
polygon_gdf = DTA_Cisangkuy
polygon_gdf.crs = "EPSG:4326"
polygon_gdf_reprojected = polygon_gdf.to_crs(bands_src[1].crs)

clipped_bands = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

for i in range(1, 13):
    if i != 9 and i != 10:
        clipped, transformed = mask(bands_src[i], polygon_gdf_reprojected.geometry, crop=True)
        clipped_bands[i] = clipped[0]

#%% pembuatan dataset clipping yang belum dilabel (menghiraukan 0)

output_arr = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
done_xy = False

# print(clipped_bands)
for i in range(1, 13):
    if i != 9 and i != 10:
        print("clipping band ke-" + str(i))
        clip = clipped_bands[i]
        for row_idx in range(0,len(clip)):
            clip_row = clip[row_idx]
            for col_idx in range(0, len(clip_row)):
                item = clip_row[col_idx]
                if item != 0:                
                    output_arr[i].append(item)
                    if not done_xy:
                        output_arr[13].append(row_idx)
                        output_arr[14].append(col_idx)
                    
        done_xy = True

print("Done clipping bands")
#%% output ke excel (JIKA SUDAH ADA TIDAK PERLU)
filename = "dta_cisangkuy.xlsx"


if os.path.exists(parent_dir + "/Data/(to predict)/" + filename):
    print("File exists.")
else:
    output_filename = filename
    out_df = pd.DataFrame({'B1': output_arr[1],
                           'B2': output_arr[2], 
                           'B3': output_arr[3], 
                           'B4': output_arr[4], 
                           'B5': output_arr[5], 
                           'B6': output_arr[6], 
                           'B7': output_arr[7], 
                           'B8': output_arr[8], 
                           'B11': output_arr[11],
                           'B12': output_arr[12],
                           'x': output_arr[13],
                           'y': output_arr[14]})
    
    out_df['NDVI'] = af.addNDVI(out_df['B4'], out_df['B8'])
    out_df['EVI'] = af.addEVI(out_df['B2'], out_df['B4'], out_df['B8'])
    out_df['NDWI'] = af.addNDWI(out_df['B3'], out_df['B8'])
    
    start_time = time.time()
    out_df.to_excel(parent_dir + '/Data/(to predict)/' + output_filename, index=False)
    end_time = time.time()
    
    print(f"Time taken to export: {end_time - start_time:.2f} seconds")

#%% REMAP the classification to 2D map

normalized_b2 = clipped_bands[2] / clipped_bands[2].max() * 800
normalized_b3 = clipped_bands[3] / clipped_bands[3].max() * 800
normalized_b4 = clipped_bands[4] / clipped_bands[4].max() * 800


rgb_image = np.dstack((normalized_b4, normalized_b3, normalized_b2)).astype(np.uint8)
rgb_raw = np.dstack((clipped_bands[2],clipped_bands[3],clipped_bands[4]))

plt.figure(figsize=(20, 12))  
plt.imshow(rgb_image)


#%% predict data

with open(script_dir + '/filename.txt', 'r') as file:
    content = file.read().strip()

filename = content
dta = "dta_cisangkuy.xlsx"
start_time = time.time()
hasil = train.predict_real_data(filename, dta)
end_time = time.time()

print(f"Time taken to Predict: {end_time - start_time:.2f} seconds")

#%%
lahan = hasil['land_cover']
x_all = hasil['x']
y_all = hasil['y']

hasil_b2 = clipped_bands[2].copy()
hasil_b3 = clipped_bands[3].copy()
hasil_b4 = clipped_bands[4].copy()


pixel_count = hasil.shape[0]
for i in range(0, pixel_count):
    j = x_all[i]
    k = y_all[i]
    if lahan[i] == 'crop':
        hasil_b2[j][k] = 255  # Bright Yellow
        hasil_b3[j][k] = 255
        hasil_b4[j][k] = 0
    elif lahan[i] == 'agriculture':
        hasil_b2[j][k] = 255  # Light Orange
        hasil_b3[j][k] = 165
        hasil_b4[j][k] = 0
    elif lahan[i] == 'grassland':
        hasil_b2[j][k] = 50   # Light Green
        hasil_b3[j][k] = 205
        hasil_b4[j][k] = 50
    elif lahan[i] == 'settlement':
        hasil_b2[j][k] = 255  # Light Gray
        hasil_b3[j][k] = 0
        hasil_b4[j][k] = 0
    elif lahan[i] == 'road_n_railway':
        hasil_b2[j][k] = 101  # Dark Brown
        hasil_b3[j][k] = 67
        hasil_b4[j][k] = 33
    elif lahan[i] == 'forest':
        hasil_b2[j][k] = 34   # Dark Green
        hasil_b3[j][k] = 139
        hasil_b4[j][k] = 34
    elif lahan[i] == 'land_without_scrub':
        hasil_b2[j][k] = 210  # Sandy Brown
        hasil_b3[j][k] = 180
        hasil_b4[j][k] = 140
    elif lahan[i] == 'river':
        hasil_b2[j][k] = 0    # Bright Blue
        hasil_b3[j][k] = 0
        hasil_b4[j][k] = 255
    elif lahan[i] == 'tank':
        hasil_b2[j][k] = 0  # Purple
        hasil_b3[j][k] = 100
        hasil_b4[j][k] = 255
        
legend_patches = [
    mpatches.Patch(color=[255/255, 255/255, 0], label='Crop'),            # Bright Yellow
    mpatches.Patch(color=[255/255, 165/255, 0], label='Agriculture'),      # Light Orange
    mpatches.Patch(color=[50/255, 205/255, 50/255], label='Grassland'),    # Light Green
    mpatches.Patch(color=[255/255, 0/255, 0/255], label='Settlement'), # Light Gray
    mpatches.Patch(color=[101/255, 67/255, 33/255], label='Road/Railway'), # Dark Brown
    mpatches.Patch(color=[34/255, 139/255, 34/255], label='Forest'),       # Dark Green
    mpatches.Patch(color=[210/255, 180/255, 140/255], label='Land Without Scrub'), # Sandy Brown
    mpatches.Patch(color=[0/255, 0/255, 255/255], label='River'),          # Bright Blue
    mpatches.Patch(color=[0/255, 100/255, 255/255], label='Tank'),       # Purple
]

rgb_image = np.dstack((hasil_b2, hasil_b3, hasil_b4)).astype(np.uint8)
plt.figure(figsize=(20, 12))  # Set width to 10 inches, height to 6 inches
plt.imshow(rgb_image)
plt.legend(handles=legend_patches, loc='upper left', fontsize='medium')

plt.show()

# Define legend patches for each land cover type
