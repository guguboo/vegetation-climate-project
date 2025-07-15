import pandas as pd
import numpy as np
from datetime import datetime

filename = "ee-chart.csv"

def read_vegetation_data(file_path):
    """Read and clean vegetation data from CSV"""
    df = pd.read_csv(file_path, parse_dates=['system:time_start'])
    df = df.dropna(subset=['evi', 'ndvi'], how='all')
    print(df['evi'])
    df['evi'] = df['evi'].astype(str).str.replace(',', '', regex=False).astype(float)
    df['ndvi'] = df['ndvi'].astype(str).str.replace(',', '', regex=False).astype(float)
    df['date'] = pd.to_datetime(df['system:time_start'])
    df = df.sort_values('date')
    return df


def decimal_month(date):
    """Convert datetime to decimal month for smooth plotting"""
    month = date.month
    day = date.day
    # Approximate position within month (0-1)
    month_position = (day - 1) / 31  # Simple approximation
    return month + month_position

def generate_tikz_code(df, scale=0.85, width="0.80"):
    """Generate TikZ code for the plot"""
    # Create decimal month values for data points
    df['decimal_month'] = df['date'].apply(decimal_month)
    
    # Format EVI coordinates
    evi_coords = ' '.join([f"({float(row['decimal_month']):.2f},{float(row['evi']):.3f})" for _, row in df.iterrows() if pd.notna(row['evi'])])
    
    # Format NDVI coordinates
    ndvi_coords = ' '.join([f"({float(row['decimal_month']):.2f},{float(row['ndvi']):.3f})" for _, row in df.iterrows() if pd.notna(row['ndvi'])])
        
    # Create TikZ code
    tikz_code = f"""% Time series graph of EVI and NDVI values
\\begin{{minipage}}[c]{{{width}\\textwidth}}
	\\begin{{figure}}[H]
		\\centering
		\\begin{{tikzpicture}}[scale={scale}]
		\\begin{{axis}}[
			ymin=-0.2,
			ymax=1.0,
			xlabel={{}},
			ylabel={{Nilai Indeks}},
			xticklabel style={{rotate=45,anchor=east,font=\\small}},
			xtick={{1,2,3,4,5,6,7,8,9,10,11,12}},
			xticklabels={{Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec}},
			ymajorgrids=true,
			grid style=dashed,
			legend pos=north west,
			legend style={{font=\\small}}
		]
		% EVI data
		\\addplot+[smooth,mark=none,thick,color=green!70!black] coordinates {{
			{evi_coords}
		}};
		% NDVI data
		\\addplot+[smooth,mark=none,thick,color=blue] coordinates {{
			{ndvi_coords}
		}};

		\\legend{{EVI, NDVI}}
		\\end{{axis}}
		\\end{{tikzpicture}}
		\\caption{{}}
	\\end{{figure}}
\\end{{minipage}}
"""
    return tikz_code


def main():
    # File path - update this to the location of your CSV file
    file_path = './' + filename
    
    # Read and process data
    df = read_vegetation_data(file_path)
    print(df['evi'])
    print(df['ndvi'])
        
    # Generate TikZ code
    tikz_code = generate_tikz_code(df)
    

    
    # Also write just the TikZ code for inclusion in existing documents
    with open('vegetation_indices_tikz_snippet.tex', 'w') as f:
        f.write(tikz_code)
    
    print("TikZ code generated and saved to 'vegetation_indices_tikz.tex'")
    print("TikZ snippet saved to 'vegetation_indices_tikz_snippet.tex'")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(df[['evi', 'ndvi']].describe())

if __name__ == "__main__":
    main()