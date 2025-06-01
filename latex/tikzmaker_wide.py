import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import matplotlib as mpl

# Set larger font sizes for better readability in plots
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['axes.labelsize'] = 12
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 10

variables = ['evi']

filename = "ee-chart.csv"

def read_vegetation_data(file_path):
    """Read and clean vegetation data from CSV"""
    df = pd.read_csv(file_path, parse_dates=['datetime'])
    df = df.dropna(subset=variables, how='all')
    
    # Handle numeric conversions safely
    for col in variables:
        if df[col].dtype == object:  # Check if it's string/object type
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).astype(float)
    
    df['date'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('date')
    return df

def decimal_year_month(date):
    """Convert datetime to decimal year.month for smooth plotting"""
    year = date.year
    month = date.month
    day = date.day
    # Approximate position within month (0-1)
    month_position = (day - 1) / 31  # Simple approximation
    return year + (month - 1 + month_position) / 12

def generate_yearly_tikz_code(df, scale=0.8, width="\\textwidth"):
    """Generate TikZ code for the plot showing multiple years"""
    # Create decimal year values for data points
    df['decimal_year'] = df['date'].apply(decimal_year_month)
    
    # Get min and max years for axis setup
    min_year = df['date'].dt.year.min()
    max_year = df['date'].dt.year.max()
    
    # Format EVI coordinates
    evi_coords = ' '.join([f"({float(row['decimal_year']):.3f},{float(row['evi']):.3f})" 
                           for _, row in df.iterrows() if pd.notna(row['evi'])])
    
    # Format NDVI coordinates
    # ndvi_coords = ' '.join([f"({float(row['decimal_year']):.3f},{float(row['ndvi']):.3f})" 
    #                         for _, row in df.iterrows() if pd.notna(row['ndvi'])])
    
    # Create evenly spaced tick marks for years (including half-year marks if span > 1 year)
    year_span = max_year - min_year
    if year_span > 1:
        # Create half-year ticks
        year_ticks = []
        year_labels = []
        for year in range(min_year, max_year + 1):
            year_ticks.extend([year, year + 0.5])
            year_labels.extend([str(year), ""])
        # Remove last half-year tick if it exceeds the max year
        if max_year + 0.5 > df['decimal_year'].max():
            year_ticks = year_ticks[:-1]
            year_labels = year_labels[:-1]
    else:
        # For shorter periods, use quarterly ticks
        year_ticks = []
        year_labels = []
        for year in range(min_year, max_year + 1):
            year_ticks.extend([year, year + 0.25, year + 0.5, year + 0.75])
            year_labels.extend([str(year), f"Q2", f"Q3", f"Q4"])
    
    # Format tick positions and labels
    tick_positions = ','.join([f"{tick}" for tick in year_ticks])
    tick_labels = ','.join([f"{label}" for label in year_labels])
    
    # Set appropriate width (make wider)
    # Create TikZ code with wider aspect ratio and better x-axis spread
    tikz_code = f"""% Time series graph of EVI and NDVI values over multiple years
\\begin{{minipage}}[c]{{{width}}}
	\\begin{{figure}}[H]
		\\centering
		\\begin{{tikzpicture}}[scale={scale}]
		\\begin{{axis}}[
			ymin=0,
			ymax=1.0,
			width=15cm, % Wider plot
			height=8cm, % Control height for good aspect ratio
			xlabel={{Year}},
			ylabel={{Index Value}},
			xticklabel style={{rotate=45,anchor=east,font=\\small}},
			xtick={{{tick_positions}}},
			xticklabels={{{tick_labels}}},
			ymajorgrids=true,
			xmajorgrids=true,
			grid style=dashed,
			legend pos=north west,
			legend style={{font=\\small}}
		]
		% EVI data
		\\addplot+[smooth,mark=none,mark size=1pt,thick,color=green!70!black] coordinates {{
			{evi_coords}
		}};
		
		\\legend{{EVI, NDVI}}
		\\end{{axis}}
		\\end{{tikzpicture}}
		\\caption{{isi sendiri}}
	\\end{{figure}}
\\end{{minipage}}
"""
    return tikz_code

# % NDVI data
# 		\\addplot+[smooth,mark=none,mark size=1pt,thick,color=blue] coordinates {{
# 			{ndvi_coords}
# 		}};

def main():
    # File path - update this to the location of your CSV file
    file_path = './' + filename
    
    # Read and process data
    df = read_vegetation_data(file_path)
    
    # Generate continuous time series TikZ code
    tikz_code = generate_yearly_tikz_code(df)
    
    # Save the TikZ code
    with open('vegetation_indices_yearly_tikz.tex', 'w') as f:
        f.write(tikz_code)
    
    print("TikZ code generated and saved to 'vegetation_indices_yearly_tikz.tex'")

if __name__ == "__main__":
    main()