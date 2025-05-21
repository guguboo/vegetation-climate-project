import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import json

start_year = 2013
end_year = 2016

climate_dir = "climate_timeseries/cleaned/"
vegetation_dir = "pandanwangi_timeseries/"
evi = True

# kecamatan_names = ['warungkondang', 'cibeber', 'campaka']
kecamatan_names = ['warungkondang']
# available_climate_datasets = ['POWER_warungkondang.csv', 'POWER_cibeber.csv']
# available_climate_datasets = ['era5_warungkondang.csv', 'era5_cibeber.csv', 'era5_campaka.csv']
# available_vegetation_datasets = ['warungkondang.csv', 'cibeber3.csv', 'campaka']
available_climate_datasets = ['chirts_warungkondang.csv']
available_vegetation_datasets = ['warungkondang.csv']

if evi:
    for i in range(len(available_vegetation_datasets)):
        available_vegetation_datasets[i] = 'evi_' + str(available_vegetation_datasets[i])
        
extract_statistics = ['mean', 'min', 'max', 'std']
statistic_corr = ['mean', 'min', 'max', 'std', 'smoothed_mean']

era5_features = [
        # Temperature variables
        'temperature_2m',                       # Air temperature
        'temperature_2m_min',                   # Daily minimum air temperature
        'temperature_2m_max',                   # Daily maximum air temperature
        'soil_temperature_level_1',             # Topsoil temperature (0-7 cm)
        'soil_temperature_level_2',             # Soil temperature (7-28 cm)
        
        # Moisture variables
        'volumetric_soil_water_layer_1',        # Topsoil moisture content
        'volumetric_soil_water_layer_2',        # Soil moisture (7-28 cm)
        'volumetric_soil_water_layer_3',        # Soil moisture (28-100 cm)
        'total_precipitation_sum',              # Total rainfall and snow
        'dewpoint_temperature_2m',              # Air humidity indicator
        
        # Radiation and energy variables
        'surface_solar_radiation_downwards_sum', # Solar radiation at surface
        'surface_net_solar_radiation_sum',       # Net solar radiation at surface
        
        # Evaporation and water cycle
        'total_evaporation_sum',                 # Actual evaporation
        
        # Wind variables
        'u_component_of_wind_10m',               # East-west wind component
        'v_component_of_wind_10m'                # North-south wind component
    ]

openweather_features = [
        'temp',         # Current temperature (C or K depending on units)
        'feels_like',   # Perceived temperature considering humidity and wind (C or K)
        'temp_min',     # Minimum temperature at the moment (C or K)
        'temp_max',     # Maximum temperature at the moment (C or K)
        'pressure',     # Atmospheric pressure at sea level (hPa)
        'humidity',     # Humidity percentage (%)
        'wind_speed',   # Wind speed (meter/sec)
        'wind_deg',     # Wind direction in degrees (0–360)
        'rain_1h',      # Rain volume for the last 1 hour (mm)
        'rain_3h',      # Rain volume for the last 3 hours (mm)
        'clouds_all'    # Cloudiness percentage (%)
    ]

chirts_features = [
        'heat_index',
        'maximum_temperature',
        'minimum_temperature',
        'relative_humidity',
        'saturation_vapor_pressure',
        'vapor_pressure_deficit',
    ]

power_features = [
        'T2M',           # MERRA-2 Temperature at 2 Meters (C)
        'T2MDEW',        # MERRA-2 Dew/Frost Point at 2 Meters (C)
        'T2MWET',        # MERRA-2 Wet Bulb Temperature at 2 Meters (C)
        'TS',            # MERRA-2 Earth Skin Temperature (C)
        'T2M_RANGE',     # MERRA-2 Temperature at 2 Meters Range (C)
        'T2M_MAX',       # MERRA-2 Temperature at 2 Meters Maximum (C)
        'T2M_MIN',       # MERRA-2 Temperature at 2 Meters Minimum (C)
        'PS',            # MERRA-2 Surface Pressure (kPa)
        'WS2M',          # MERRA-2 Wind Speed at 2 Meters (m/s)
        'WS2M_MAX',      # MERRA-2 Wind Speed at 2 Meters Maximum (m/s)
        'WS2M_MIN',      # MERRA-2 Wind Speed at 2 Meters Minimum (m/s)
        'GWETTOP',       # MERRA-2 Surface Soil Wetness (1)
        'GWETROOT'      # MERRA-2 Root Zone Soil Wetness (1)
    ]

def difference_df(df):
    df = df.diff()
    return df

# df_OpenWeather = pd.read_csv(f"{data_dir}/OpenWeather_pandanwangi.csv")
climate_df = {}
curr_kec = 0

try:
    for dataset in available_climate_datasets:
        curr = pd.read_csv(f"{climate_dir}/{dataset}")
        climate_df[kecamatan_names[curr_kec]] = curr
except:
    print(f"file kecamatan {kecamatan_names[curr_kec]} belum ada")

preprocessed_climate = {}

def climate_df_processing(df):
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
    df.set_index('datetime', inplace=True)
    return df[(df.index.year >= start_year) & (df.index.year <= end_year)]


for kec in kecamatan_names:
    preprocessed_climate[kec] = climate_df_processing(climate_df[kec])

vegetation_df = {}

try:
    for i, dataset in enumerate(available_vegetation_datasets):
        curr = pd.read_csv(f"{vegetation_dir}/{dataset}")
        vegetation_df[kecamatan_names[i]] = curr
except:
    ""
    
preprocessed_vegetation = {}

def vegetation_preprocessing(df):
    df = df.iloc[:, 1:]
    df = df[df.label == 'pandanwangi']
    df = df.set_index('cluster_id')
    df = df.describe()
    df = df.T
    df = df[extract_statistics]
    indexes = df.index
    new_indexes = []
    for i in indexes:
        date = pd.to_datetime(i, format='%Y%m%d')
        new_indexes.append(date)
    df['datetime'] = new_indexes
    df = df.set_index('datetime')
    df = df.asfreq('5D', method='nearest')

    return df[(df.index.year >= start_year) & (df.index.year <= end_year)]

for kec in kecamatan_names:
    preprocessed_vegetation[kec] = vegetation_preprocessing(vegetation_df[kec])

def smoothing_sg(df):
    filtered = savgol_filter(df['mean'], window_length=20, polyorder=3)
    df['smoothed_mean'] = filtered
    return df
    
for kec in kecamatan_names:
    smoothing_sg(preprocessed_vegetation[kec])

differenced_climate = {}
differenced_vegetation = {}

intersecting_indices = preprocessed_climate['warungkondang'].index.intersection(preprocessed_vegetation['warungkondang'].index)

for kec in kecamatan_names:
    differenced_climate[kec] = difference_df(preprocessed_climate[kec].loc[intersecting_indices]).iloc[1:, :]
    differenced_vegetation[kec] = difference_df(preprocessed_vegetation[kec]).loc[intersecting_indices].iloc[1:, :]

# dataframe extract
correlation_indexes = {
    'kec': [],
    'statistic': [],
    'cuaca': [],
    'pearson': [],
    'spearman': []
}

for kec in kecamatan_names:
    kec_vegetation = differenced_vegetation[kec]
    kec_climate = differenced_climate[kec]
    stat_dict = {}
    for statistic in statistic_corr:
        curr_stat = kec_vegetation[statistic]
        cuaca_dict = {}
        for faktor_cuaca in chirts_features:
            pearson = curr_stat.corr(kec_climate[faktor_cuaca], method='pearson')
            spearman = curr_stat.corr(kec_climate[faktor_cuaca], method='spearman')
            correlation_indexes['pearson'].append(pearson)
            correlation_indexes['spearman'].append(spearman)
            correlation_indexes['cuaca'].append(faktor_cuaca)
            correlation_indexes['statistic'].append(statistic)
            correlation_indexes['kec'].append(kec)

correlation_df = pd.DataFrame(correlation_indexes)

selected_kec = 'warungkondang'
kec_corr = correlation_df[correlation_df['kec'] == selected_kec]



