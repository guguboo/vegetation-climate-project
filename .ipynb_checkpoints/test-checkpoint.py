import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import ccf
import warnings
warnings.filterwarnings('ignore')

# Set consistent plotting style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)

# Configuration
start_year = 2013
end_year = 2016
climate_dir = "climate_timeseries/cleaned/"
vegetation_dir = "pandanwangi_timeseries/"
evi = True
kecamatan_names = ['warungkondang']
available_climate_datasets = ['chirts_warungkondang.csv']
available_vegetation_datasets = ['warungkondang.csv']

if evi:
    available_vegetation_datasets = ['evi_' + dataset for dataset in available_vegetation_datasets]

extract_statistics = ['mean', 'min', 'max', 'std']
statistic_corr = ['mean', 'min', 'max', 'std', 'smoothed_mean']

# Features from CHIRTS dataset
chirts_features = [
    'heat_index',
    'maximum_temperature',
    'minimum_temperature',
    'relative_humidity',
    'saturation_vapor_pressure',
    'vapor_pressure_deficit',
]

# Load climate data
def load_climate_data(climate_dir, datasets, kecamatan_names):
    climate_df = {}
    for i, dataset in enumerate(datasets):
        try:
            curr = pd.read_csv(f"{climate_dir}/{dataset}")
            kec = kecamatan_names[min(i, len(kecamatan_names)-1)]
            climate_df[kec] = curr
        except Exception as e:
            print(f"File kecamatan {kec} tidak dapat dimuat: {e}")
    return climate_df

# Load vegetation data
def load_vegetation_data(vegetation_dir, datasets, kecamatan_names):
    vegetation_df = {}
    for i, dataset in enumerate(datasets):
        try:
            curr = pd.read_csv(f"{vegetation_dir}/{dataset}")
            kec = kecamatan_names[min(i, len(kecamatan_names)-1)]
            vegetation_df[kec] = curr
        except Exception as e:
            print(f"File vegetasi {kec} tidak dapat dimuat: {e}")
    return vegetation_df

# Process climate data
def climate_df_processing(df):
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d')
    df.set_index('datetime', inplace=True)
    # Ensure all features are numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Filter by year range
    return df[(df.index.year >= start_year) & (df.index.year <= end_year)]

# Process vegetation data
def vegetation_preprocessing(df):
    df = df.iloc[:, 1:]
    df = df[df.label == 'pandanwangi']
    df = df.set_index('cluster_id')
    df = df.describe()
    df = df.T
    df = df[extract_statistics]
    
    # Convert index to datetime
    indexes = df.index
    new_indexes = []
    for i in indexes:
        date = pd.to_datetime(i, format='%Y%m%d')
        new_indexes.append(date)
    
    df['datetime'] = new_indexes
    df = df.set_index('datetime')
    df = df.asfreq('5D', method='nearest')

    # Filter by year range
    return df[(df.index.year >= start_year) & (df.index.year <= end_year)]

# Apply Savitzky-Golay filter for smoothing
def smoothing_sg(df, window_length=21, polyorder=3):
    for col in ['mean', 'min', 'max']:
        if col in df.columns:
            filtered = savgol_filter(df[col], window_length=window_length, polyorder=polyorder)
            df[f'smoothed_{col}'] = filtered
    return df

# Calculate rolling statistics
def add_rolling_stats(df, window=30):
    for col in df.columns:
        df[f'{col}_rolling_mean'] = df[col].rolling(window=window).mean()
        df[f'{col}_rolling_std'] = df[col].rolling(window=window).std()
    return df

# First difference for stationarity
def difference_df(df):
    return df.diff().dropna()

# Perform stationarity test (Augmented Dickey-Fuller)
def test_stationarity(df):
    results = {}
    for col in df.columns:
        adf_result = sm.tsa.stattools.adfuller(df[col].dropna())
        results[col] = {
            'ADF Statistic': adf_result[0],
            'p-value': adf_result[1],
            'Stationary': adf_result[1] < 0.05
        }
    return pd.DataFrame(results).T

# Calculate cross-correlation with different lags
def calculate_lagged_correlation(climate_df, vegetation_df, max_lag=30):
    vegetation_stats = statistic_corr
    
    lag_correlation = {
        'kec': [],
        'statistic': [],
        'climate_feature': [],
        'lag': [],
        'correlation': [],
        'p_value': []
    }
    
    for stat in vegetation_stats:
        if stat in vegetation_df.columns:
            veg_series = vegetation_df[stat]
            
            for feature in climate_df.columns:
                climate_series = climate_df[feature]
                
                # Ensure both series have the same frequency and are aligned
                common_idx = veg_series.index.intersection(climate_series.index)
                veg_aligned = veg_series.loc[common_idx]
                climate_aligned = climate_series.loc[common_idx]
                
                # Calculate cross-correlation for different lags
                for lag in range(-max_lag, max_lag + 1):
                    if lag < 0:
                        # Negative lag: climate leads vegetation
                        x = climate_aligned.iloc[:lag].values if lag != 0 else climate_aligned.values
                        y = veg_aligned.iloc[-lag:].values if lag != 0 else veg_aligned.values
                    else:
                        # Positive lag: vegetation leads climate
                        x = climate_aligned.iloc[lag:].values if lag != 0 else climate_aligned.values
                        y = veg_aligned.iloc[:-lag].values if lag != 0 else veg_aligned.values
                    
                    if len(x) > 10 and len(y) == len(x):  # Ensure enough samples
                        # Calculate correlation and p-value
                        corr, p_value = stats.pearsonr(x, y)
                        
                        lag_correlation['kec'].append('warungkondang')
                        lag_correlation['statistic'].append(stat)
                        lag_correlation['climate_feature'].append(feature)
                        lag_correlation['lag'].append(lag)
                        lag_correlation['correlation'].append(corr)
                        lag_correlation['p_value'].append(p_value)
    
    return pd.DataFrame(lag_correlation)

# Calculate Granger causality
def granger_causality_test(climate_df, vegetation_df, max_lag=10):
    from statsmodels.tsa.stattools import grangercausalitytests
    
    results = {
        'climate_feature': [],
        'vegetation_stat': [],
        'max_lag': [],
        'min_p_value': [],
        'causality_direction': []
    }
    
    for climate_feature in climate_df.columns:
        for veg_stat in vegetation_df.columns:
            if veg_stat in statistic_corr:
                # Get aligned series
                common_idx = climate_df.index.intersection(vegetation_df.index)
                if len(common_idx) < max_lag + 2:
                    continue
                    
                climate_series = climate_df[climate_feature].loc[common_idx]
                veg_series = vegetation_df[veg_stat].loc[common_idx]
                
                # Prepare data for Granger test
                data = pd.DataFrame({
                    'climate': climate_series,
                    'vegetation': veg_series
                })
                
                # Test if climate Granger-causes vegetation
                try:
                    climate_to_veg = grangercausalitytests(data[['vegetation', 'climate']], 
                                                          maxlag=max_lag, verbose=False)
                    
                    # Extract minimum p-value across all lags
                    min_p_climate_to_veg = min([climate_to_veg[lag][0]['ssr_chi2test'][1] 
                                             for lag in range(1, max_lag+1)])
                    
                    # Test if vegetation Granger-causes climate
                    veg_to_climate = grangercausalitytests(data[['climate', 'vegetation']], 
                                                          maxlag=max_lag, verbose=False)
                    
                    min_p_veg_to_climate = min([veg_to_climate[lag][0]['ssr_chi2test'][1] 
                                             for lag in range(1, max_lag+1)])
                    
                    # Determine causality direction
                    if min_p_climate_to_veg < 0.05 and min_p_veg_to_climate >= 0.05:
                        direction = 'climate->vegetation'
                        min_p = min_p_climate_to_veg
                    elif min_p_climate_to_veg >= 0.05 and min_p_veg_to_climate < 0.05:
                        direction = 'vegetation->climate'
                        min_p = min_p_veg_to_climate
                    elif min_p_climate_to_veg < 0.05 and min_p_veg_to_climate < 0.05:
                        direction = 'bidirectional'
                        min_p = min(min_p_climate_to_veg, min_p_veg_to_climate)
                    else:
                        direction = 'none'
                        min_p = min(min_p_climate_to_veg, min_p_veg_to_climate)
                    
                    results['climate_feature'].append(climate_feature)
                    results['vegetation_stat'].append(veg_stat)
                    results['max_lag'].append(max_lag)
                    results['min_p_value'].append(min_p)
                    results['causality_direction'].append(direction)
                
                except Exception as e:
                    print(f"Error in Granger test: {e}")
    
    return pd.DataFrame(results)

# Visualize time series data
def plot_time_series(climate_df, vegetation_df, feature, stat):
    fig, ax1 = plt.subplots(figsize=(14, 6))
    
    # Plot climate data
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel(feature, color=color)
    climate_series = climate_df[feature]
    ax1.plot(climate_series.index, climate_series.values, color=color, label=feature)
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Create second y-axis for vegetation data
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel(f'Vegetation {stat}', color=color)
    veg_series = vegetation_df[stat]
    ax2.plot(veg_series.index, veg_series.values, color=color, label=f'Vegetation {stat}')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Add title and legend
    plt.title(f'Time Series: {feature} vs Vegetation {stat}')
    fig.tight_layout()
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.savefig(f'time_series_{feature}_{stat}.png')
    plt.close()

# Visualize lag correlation
def plot_lag_correlation(lag_corr_df, vegetation_stat, climate_feature):
    subset = lag_corr_df[(lag_corr_df['statistic'] == vegetation_stat) & 
                         (lag_corr_df['climate_feature'] == climate_feature)]
    
    plt.figure(figsize=(10, 5))
    plt.plot(subset['lag'], subset['correlation'], marker='o')
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    
    # Add significance threshold lines (assuming p<0.05)
    significant = subset[subset['p_value'] < 0.05]
    plt.scatter(significant['lag'], significant['correlation'], color='red', 
                s=80, label='p < 0.05', zorder=3)
    
    plt.title(f'Lag Correlation: {climate_feature} vs Vegetation {vegetation_stat}')
    plt.xlabel('Lag (Negative: Climate leads, Positive: Vegetation leads)')
    plt.ylabel('Correlation Coefficient')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'lag_correlation_{climate_feature}_{vegetation_stat}.png')
    plt.close()

# Visualize correlation heatmap
def plot_correlation_heatmap(lag_corr_df, lag=0):
    # Filter for specific lag
    lag_subset = lag_corr_df[lag_corr_df['lag'] == lag]
    
    # Prepare data for heatmap
    pivot_data = lag_subset.pivot_table(
        index='climate_feature', 
        columns='statistic', 
        values='correlation'
    )
    
    plt.figure(figsize=(12, 8))
    
    # Create heatmap
    sns.heatmap(pivot_data, annot=True, cmap='coolwarm', center=0, 
                vmin=-1, vmax=1, fmt='.2f')
    
    plt.title(f'Correlation Heatmap (Lag = {lag})')
    plt.tight_layout()
    plt.savefig(f'correlation_heatmap_lag_{lag}.png')
    plt.close()
    
    # Also create p-value heatmap
    p_value_pivot = lag_subset.pivot_table(
        index='climate_feature', 
        columns='statistic', 
        values='p_value'
    )
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(p_value_pivot < 0.05, annot=p_value_pivot, cmap='viridis', 
                fmt='.3f', cbar_kws={'label': 'p-value'})
    
    plt.title(f'P-values Heatmap (Lag = {lag})')
    plt.tight_layout()
    plt.savefig(f'pvalue_heatmap_lag_{lag}.png')
    plt.close()

# Main execution flow
def main():
    # Load data
    climate_df = load_climate_data(climate_dir, available_climate_datasets, kecamatan_names)
    vegetation_df = load_vegetation_data(vegetation_dir, available_vegetation_datasets, kecamatan_names)
    
    # Process data
    preprocessed_climate = {}
    preprocessed_vegetation = {}
    
    for kec in kecamatan_names:
        preprocessed_climate[kec] = climate_df_processing(climate_df[kec])
        preprocessed_vegetation[kec] = vegetation_preprocessing(vegetation_df[kec])
        preprocessed_vegetation[kec] = smoothing_sg(preprocessed_vegetation[kec])
    
    # Test for stationarity
    for kec in kecamatan_names:
        print(f"\nStationarity Test for Climate Data ({kec}):")
        climate_stationarity = test_stationarity(preprocessed_climate[kec])
        print(climate_stationarity)
        
        print(f"\nStationarity Test for Vegetation Data ({kec}):")
        vegetation_stationarity = test_stationarity(preprocessed_vegetation[kec])
        print(vegetation_stationarity)
    
    # Apply differencing if needed
    differenced_climate = {}
    differenced_vegetation = {}
    
    for kec in kecamatan_names:
        # Check if we need differencing
        climate_stationary = test_stationarity(preprocessed_climate[kec])
        veg_stationary = test_stationarity(preprocessed_vegetation[kec])
        
        if not climate_stationary['Stationary'].all():
            differenced_climate[kec] = difference_df(preprocessed_climate[kec])
            print(f"Applied differencing to climate data for {kec}")
        else:
            differenced_climate[kec] = preprocessed_climate[kec]
            
        if not veg_stationary['Stationary'].all():
            differenced_vegetation[kec] = difference_df(preprocessed_vegetation[kec])
            print(f"Applied differencing to vegetation data for {kec}")
        else:
            differenced_vegetation[kec] = preprocessed_vegetation[kec]
    
    # Align time series
    aligned_data = {}
    for kec in kecamatan_names:
        common_indices = differenced_climate[kec].index.intersection(differenced_vegetation[kec].index)
        aligned_data[kec] = {
            'climate': differenced_climate[kec].loc[common_indices],
            'vegetation': differenced_vegetation[kec].loc[common_indices]
        }
    
    # Calculate lagged correlations
    results = {}
    for kec in kecamatan_names:
        print(f"\nAnalyzing lagged correlations for {kec}...")
        lag_corr_df = calculate_lagged_correlation(
            aligned_data[kec]['climate'], 
            aligned_data[kec]['vegetation'], 
            max_lag=30
        )
        results[kec] = lag_corr_df
    
    # Identify strongest correlations
    for kec in kecamatan_names:
        lag_corr = results[kec]
        # Filter for significant correlations
        significant = lag_corr[lag_corr['p_value'] < 0.05]
        
        # Sort by absolute correlation values
        strongest = significant.loc[significant['correlation'].abs().sort_values(ascending=False).index]
        
        print(f"\nTop 10 strongest correlations for {kec}:")
        print(strongest.head(10))
    
    # Granger causality test
    for kec in kecamatan_names:
        print(f"\nGranger causality test for {kec}...")
        granger_results = granger_causality_test(
            aligned_data[kec]['climate'],
            aligned_data[kec]['vegetation']
        )
        
        # Filter for significant causal relationships
        significant_causality = granger_results[granger_results['min_p_value'] < 0.05]
        
        print(f"\nSignificant causal relationships for {kec}:")
        print(significant_causality)
    
    # Visualizations
    selected_kec = kecamatan_names[0]  # Use first kecamatan for examples
    
    # 1. Time series plots for top correlations
    if len(significant) > 0:
        top_correlation = strongest.iloc[0]
        feature = top_correlation['climate_feature']
        stat = top_correlation['statistic']
        
        plot_time_series(
            aligned_data[selected_kec]['climate'],
            aligned_data[selected_kec]['vegetation'],
            feature, stat
        )
    
    # 2. Lag correlation plots
    for feature in chirts_features[:3]:  # Plot first 3 features for example
        for stat in ['mean', 'smoothed_mean']:
            plot_lag_correlation(results[selected_kec], stat, feature)
    
    # 3. Correlation heatmaps at different lags
    for lag in [-10, -5, 0, 5, 10]:
        plot_correlation_heatmap(results[selected_kec], lag)
    
    print("\nAnalysis complete! Visualization files have been saved.")

if __name__ == "__main__":
    main()