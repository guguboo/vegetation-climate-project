import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import datetime, date
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Clim-Veg App",
    page_icon="🌱",
    layout="wide"
)

# Data kabupaten dan kecamatan
KABUPATEN_KECAMATAN = {
    "Cianjur": [
        "Warungkondang", "Gekbrong", "Cugenang", "Cianjur",
        "Campaka", "Cilaku", "Cibeber"
    ]
}

ALL_KECAMATAN = []
for kecamatan_list in KABUPATEN_KECAMATAN.values():
    ALL_KECAMATAN.extend(kecamatan_list)

VEGETASI_LIST = [
    "Padi Pandanwangi"
]

DATASET_TYPES = ["ERA-5", "CHIRTS", "MERRA-2"]

# Parameter cuaca berdasarkan dataset dengan deskripsi yang lebih lengkap
WEATHER_PARAMETERS = {
    "ERA-5": {
        'temperature_2m': 'Air Temperature (°C)',
        'temperature_2m_min': 'Daily Min Air Temperature (°C)',
        'temperature_2m_max': 'Daily Max Air Temperature (°C)',
        'soil_temperature_level_1': 'Topsoil Temperature 0-7cm (°C)',
        'soil_temperature_level_2': 'Soil Temperature 7-28cm (°C)',
        'volumetric_soil_water_layer_1': 'Topsoil Moisture (%)',
        'volumetric_soil_water_layer_2': 'Soil Moisture 7-28cm (%)',
        'volumetric_soil_water_layer_3': 'Soil Moisture 28-100cm (%)',
        'total_precipitation_sum': 'Total Precipitation (mm)',
        'dewpoint_temperature_2m': 'Dewpoint Temperature (°C)',
        'surface_solar_radiation_downwards_sum': 'Solar Radiation (W/m²)',
        'surface_net_solar_radiation_sum': 'Net Solar Radiation (W/m²)',
        'total_evaporation_sum': 'Total Evaporation (mm)',
        'u_component_of_wind_10m': 'East-West Wind (m/s)',
        'v_component_of_wind_10m': 'North-South Wind (m/s)'
    },
    "CHIRTS": {
        'heat_index': 'Heat Index (°C)',
        'maximum_temperature': 'Maximum Temperature (°C)',
        'minimum_temperature': 'Minimum Temperature (°C)',
        'relative_humidity': 'Relative Humidity (%)',
        'saturation_vapor_pressure': 'Saturation Vapor Pressure (kPa)',
        'vapor_pressure_deficit': 'Vapor Pressure Deficit (kPa)'
    },
    "MERRA-2": {
        'T2M': 'Temperature at 2m (°C)',
        'T2MDEW': 'Dew/Frost Point at 2m (°C)',
        'T2MWET': 'Wet Bulb Temperature at 2m (°C)',
        'TS': 'Earth Skin Temperature (°C)',
        'T2M_RANGE': 'Temperature Range at 2m (°C)',
        'T2M_MAX': 'Temperature Maximum at 2m (°C)',
        'T2M_MIN': 'Temperature Minimum at 2m (°C)',
        'PS': 'Surface Pressure (kPa)',
        'WS2M': 'Wind Speed at 2m (m/s)',
        'WS2M_MAX': 'Wind Speed Maximum at 2m (m/s)',
        'WS2M_MIN': 'Wind Speed Minimum at 2m (m/s)',
        'GWETTOP': 'Surface Soil Wetness',
        'GWETROOT': 'Root Zone Soil Wetness'
    }
}

def get_location_specific_climate_factors():
    """
    Mengembalikan faktor cuaca yang spesifik untuk setiap kombinasi vegetasi dan kecamatan
    """
    climate_factors = {
        ("Padi Pandanwangi", "Warungkondang"): {
            "faktor_utama": "Titik pengembunan,Angin(Barat-Timur),Suhu udara minimum,Volume air tanah,Temperatur tanah,Temperatur udara,Temperatur maksimum,Kelembapan udara",
            "titik_pengembunan": '19.23 - 20.61 °C',
            "angin_barat_timur": '-0.37 hingga -0.07 m/s',
            "volume_air_tanah": f"45 - 49% (siklus pertama tahunan) dan 25 - 27% (siklus kedua tahunan)",
            "temperatur_tanah": f"23.76 - 24.32 °C",
            "temperatur_udara": f"21.70 - 22.50 °C",
            "kelembapan_udara": f"87.80 - 91.81 %",
            "catatan": "",
            "faktor_dominan": "Temperatur tanah dan Volume air tanah"
        },
        ("Padi Pandanwangi", "Gekbrong"): {
            "faktor_utama": "Titik pengembunan,Angin(Barat-Timur),Suhu udara minimum,Volume air tanah,Temperatur tanah,Temperatur maksimum,Kelembapan udara",
            "titik_pengembunan": '19.13 - 20.69 °C',
            "angin_barat_timur": '-0.28 hingga -0.1 m/s',
            "volume_air_tanah": f"43 - 49% (siklus pertama tahunan) dan 25 - 27% (siklus kedua tahunan)",
            "temperatur_tanah": f"23.73 - 24.25 °C",
            "temperatur_udara": f"21.58 - 22.71 °C",
            "kelembapan_udara": f"89.88 - 93.97 %",
            "catatan": "",
            "faktor_dominan": "Temperatur tanah dan Volume air tanah"
        },
        ("Padi Pandanwangi", "Cugenang"): {
            "faktor_utama": "Titik pengembunan,Angin(Barat-Timur),Volume air tanah,Temperatur tanah,Rentang temperatur",
            "titik_pengembunan": '18.52 - 19.77 °C',
            "angin_barat_timur": '-0.41 hingga -0.04 m/s',
            "volume_air_tanah": f"38 - 43% (siklus pertama tahunan) dan 17 - 18% (siklus kedua tahunan)",
            "temperatur_tanah": f"22.92 - 23.68 °C",
            "rentang_temperatur": f"6.04 - 7.47 °C",
            "catatan": "",
            "faktor_dominan": "Volume air tanah"
        },
        ("Padi Pandanwangi", "Cianjur"): {
            "faktor_utama": "Titik pengembunan,Volume air tanah,Temperatur tanah,Rentang temperatur",
            "titik_pengembunan": '19.81 - 21.15 °C',
            "volume_air_tanah": f"33 - 35% (siklus pertama tahunan) dan 19 - 21% (siklus kedua tahunan)",
            "temperatur_tanah": f"24.16 - 24.47 °C",
            "rentang_temperatur": f"6.14 - 6.49 °C",
            "catatan": "",
            "faktor_dominan": "Volume air tanah"
        },
        ("Padi Pandanwangi", "Campaka"): {
            "faktor_utama": "Radiasi Matahari,Volume air tanah,Temperatur tanah,Temperatur udara, Temperatur udara maksimum",
            "radiasi_matahari": f"0 - 0.11 J/m^2",
            "temperatur_udara": f"21.71 - 22.38 °C",
            "temperatur_tanah": f"22.99 - 23.18 °C",
            "volume_air_tanah": f"47.85 – 51.16 %",
            "catatan": "",
            "faktor_dominan": "Volume air tanah"
        },
        ("Padi Pandanwangi", "Cilaku"): {
            "faktor_utama": "Volume air tanah,Temperatur tanah,Temperatur udara,Rentang temperatur,Angin(Barat-Timur)",
            "temperatur_udara": f"24.81 - 25.15 °C",
            "temperatur_tanah": f"23.05 - 24.11 °C",
            "rentang_temperatur": f"6.08 - 7.70 °C",
            "angin_barat_timur": '-0.45 hingga -0.09 m/s',
            "volume_air_tanah": f"49 - 50% (siklus pertama tahunan) dan 28 - 29% (siklus kedua tahunan)",
            "catatan": "",
            "faktor_dominan": "Volume air tanah dan Temperatur tanah"
        },
        ("Padi Pandanwangi", "Cibeber"): {
            "faktor_utama": "Volume air tanah,Temperatur tanah,Temperatur udara",
            "temperatur_udara": f"23.35 - 24.16 °C",
            "temperatur_tanah": f"24.61 - 24.98 °C",
            "volume_air_tanah": f"28.26 - 29.40 %",
            "catatan": "",
            "faktor_dominan": "Volume air tanah dan Temperatur tanah"
        },
    }

    return climate_factors

def get_climate_factors(vegetasi, kecamatan):
    """
    Mendapatkan faktor cuaca spesifik untuk kombinasi vegetasi dan kecamatan
    Jika tidak ada data spesifik, return data default berdasarkan vegetasi
    """
    specific_factors = get_location_specific_climate_factors()

    # Cek apakah ada data spesifik untuk kombinasi ini
    key = (vegetasi, kecamatan)
    if key in specific_factors:
        return specific_factors[key]

    default_factors = {
        "Padi": {
            "faktor_utama": "Curah Hujan dan Suhu",
            "curah_hujan": "1200-1800 mm/tahun",
            "suhu": "22-30°C",
            "kelembaban": "70-85%",
            "catatan": "Membutuhkan air yang cukup selama fase pertumbuhan",
            "faktor_dominan": "Curah Hujan"
        },
        "Jagung": {
            "faktor_utama": "Suhu dan Sinar Matahari",
            "curah_hujan": "400-800 mm/tahun",
            "suhu": "21-27°C",
            "kelembaban": "60-70%",
            "catatan": "Toleran kekeringan, membutuhkan sinar matahari penuh",
            "faktor_dominan": "Sinar Matahari"
        },
        "Kentang": {
            "faktor_utama": "Suhu Dingin dan Kelembaban",
            "curah_hujan": "500-700 mm/tahun",
            "suhu": "15-20°C",
            "kelembaban": "80-85%",
            "catatan": "Cocok di dataran tinggi dengan suhu sejuk",
            "faktor_dominan": "Suhu Dingin"
        }
    }

    # Default untuk vegetasi lain
    default = {
        "faktor_utama": "Suhu dan Curah Hujan",
        "curah_hujan": "600-1000 mm/tahun",
        "suhu": "20-28°C",
        "kelembaban": "65-75%",
        "catatan": "Kondisi iklim tropis pada umumnya",
        "faktor_dominan": "Suhu"
    }

    return default_factors.get(vegetasi.split(' ')[0], default) # Use only the first word for default

@st.cache_data
def load_climate_data(dataset_type, kecamatan):
    """Loads climate data from CSV based on dataset type and kecamatan."""
    df_climate = pd.DataFrame()
    if dataset_type == "MERRA-2":
        df_climate = pd.read_csv(f"../climate_timeseries/cleaned/POWER_all.csv")
    else:
        if dataset_type == 'ERA-5':
            dataset_type = 'era5'
        file_name = f"../climate_timeseries/cleaned/{dataset_type.lower()}_{kecamatan.lower()}.csv"
        df_climate = pd.read_csv(file_name)

    df_climate['Tanggal'] = pd.to_datetime(df_climate['datetime'])
    df_climate = df_climate.drop(columns=['datetime']) 
    return df_climate

@st.cache_data
def load_vegetation_data(kecamatan):
    """Loads vegetation data from CSV based on kecamatan."""
    df_veg = pd.DataFrame()
    file_name = f"../veg_df/veg_{kecamatan.lower()}.csv"
    df_veg = pd.read_csv(file_name)
    df_veg['Tanggal'] = pd.to_datetime(df_veg['datetime'])
    df_veg = df_veg.drop(columns=['datetime'])
    df_veg = df_veg[['Tanggal','growth']]
    if 'growth' in df_veg.columns:
        df_veg = df_veg.rename(columns={'growth': 'Pertumbuhan (%)'})
    return df_veg


def generate_sample_data(kecamatan, vegetasi, start_date, end_date, dataset_type="ERA-5"):
    """
    Loads and combines actual climate and vegetation data.
    """
    # Load vegetation data
    df_veg = load_vegetation_data(kecamatan)
    # print(df_veg.head())
    # print(df_veg.tail())


    # Load climate data
    df_climate = load_climate_data(dataset_type, kecamatan)
    if df_climate.empty:
        return pd.DataFrame() # Return empty if no climate data


    df_veg['Tanggal'] = df_veg['Tanggal'].dt.normalize()
    df_climate['Tanggal'] = df_climate['Tanggal'].dt.normalize()

    df_veg = df_veg[(df_veg['Tanggal'] >= pd.to_datetime(start_date)) & (df_veg['Tanggal'] <= pd.to_datetime(end_date))]
    df_climate = df_climate[(df_climate['Tanggal'] >= pd.to_datetime(start_date)) & (df_climate['Tanggal'] <= pd.to_datetime(end_date))]

    combined_df = pd.merge(df_veg, df_climate, on='Tanggal', how='inner')
    combined_df = combined_df.sort_values(by='Tanggal').reset_index(drop=True)

    return combined_df

def create_download_data(kecamatan, dataset_type, start_date, end_date):
    """
    Loads actual climate data for download.
    """
    df_climate = load_climate_data(dataset_type, kecamatan)
    if df_climate.empty:
        return pd.DataFrame()

    df_climate = df_climate[(df_climate['Tanggal'] >= pd.to_datetime(start_date)) & (df_climate['Tanggal'] <= pd.to_datetime(end_date))]

    df_climate['Kabupaten'] = 'Cianjur'
    df_climate['Kecamatan'] = kecamatan
    df_climate['Dataset'] = dataset_type

    common_weather_cols = ['Tanggal', 'Kabupaten', 'Kecamatan', 'Dataset']

    for param_key in WEATHER_PARAMETERS.get(dataset_type, {}).keys():
        if param_key in df_climate.columns:
            common_weather_cols.append(param_key)

    cols_to_include = [col for col in common_weather_cols if col in df_climate.columns]
    return df_climate[cols_to_include]


# ========================
# TAMPILAN UTAMA APLIKASI
# ========================

st.title("🌱 Analisis Iklim-Vegetasi")
st.markdown("---")

# Sidebar untuk input utama
st.sidebar.header("Pengaturan")

# Dropdown pemilihan kabupaten
selected_kabupaten = st.sidebar.selectbox(
    "Pilih Kabupaten:",
    list(KABUPATEN_KECAMATAN.keys()),
    help="Pilih kabupaten terlebih dahulu"
)

# Dropdown pemilihan kecamatan berdasarkan kabupaten
if selected_kabupaten:
    available_kecamatan = KABUPATEN_KECAMATAN[selected_kabupaten]
    selected_kecamatan = st.sidebar.selectbox(
        "Pilih Kecamatan:",
        available_kecamatan,
        help=f"Pilih kecamatan di {selected_kabupaten}"
    )
else:
    selected_kecamatan = None
    st.sidebar.warning("Silakan pilih kabupaten terlebih dahulu")

selected_vegetasi = st.sidebar.selectbox(
    "Pilih Jenis Vegetasi:",
    VEGETASI_LIST,
    help="Pilih jenis tanaman yang ingin dianalisis"
)

# Pemilihan rentang waktu untuk analisis
st.sidebar.subheader("📅 Rentang Waktu Analisis")
start_date = st.sidebar.date_input(
    "Tanggal Mulai:",
    value=date(2023, 1, 1),
    max_value=date.today()
)

end_date = st.sidebar.date_input(
    "Tanggal Akhir:",
    value=date(2024, 12, 31),
    max_value=date.today()
)

# Pemilihan dataset type untuk analisis cuaca
st.sidebar.subheader("🌦️ Dataset Cuaca")
selected_dataset = st.sidebar.selectbox(
    "Pilih Dataset:",
    DATASET_TYPES,
    help="Pilih jenis dataset untuk parameter cuaca"
)

# Validasi tanggal
if start_date >= end_date:
    st.sidebar.error("Tanggal mulai harus lebih awal dari tanggal akhir!")
    st.stop()

# ========================
# DASHBOARD UTAMA
# ========================

if selected_kabupaten and selected_kecamatan and selected_vegetasi:
    st.header(f"Dashboard Vegetasi {selected_vegetasi} \nKec. {selected_kecamatan}, Kab. {selected_kabupaten}")

    # Ambil data iklim untuk vegetasi dan kecamatan yang dipilih
    climate_info = get_climate_factors(selected_vegetasi, selected_kecamatan)

    # Layout dengan 2 kolom
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Variabel Cuaca Paling Berkaitan")
        faktor_utama_list = climate_info['faktor_utama'].split(',')
        faktor_utama_txt = "**Faktor Utama:** \n\n" + "  \n".join(faktor_utama_list)
        st.info(faktor_utama_txt)

        # Tambahkan informasi faktor dominan
        st.success(f"**Faktor Dominan:** {climate_info.get('faktor_dominan', 'Tidak ditentukan')}")

    with col2:
        st.subheader("🎯 Faktor Iklim Berkaitan dengan Suhu")

        # Daftar faktor suhu yang akan dicek
        faktor_suhu_keys = [
            ("Titik pengembunan", "titik_pengembunan"),
            ("Angin (Barat–Timur)", "angin_barat_timur"),
            ("Volume air tanah", "volume_air_tanah"),
            ("Temperatur tanah", "temperatur_tanah"),
            ("Temperatur udara", "temperatur_udara"),
            ("Kelembapan udara", "kelembapan_udara"),
            ("Rentang temperatur", "rentang_temperatur"),
            ("Radiasi matahari", "radiasi_matahari")
        ]

        # Siapkan list untuk menyimpan baris yang tersedia
        faktor_suhu_lines = []

        for label, key in faktor_suhu_keys:
            if key in climate_info and climate_info[key]:
                faktor_suhu_lines.append(f"**{label}:**")
                faktor_suhu_lines.append(f"{climate_info[key]}")
                faktor_suhu_lines.append(f"\n")

        # Gabungkan dan tampilkan jika ada
        if faktor_suhu_lines:
            faktor_suhu_text = "  \n".join(faktor_suhu_lines)
            st.success(faktor_suhu_text)
        else:
            st.info("Tidak ada data faktor suhu yang tersedia.")

    st.markdown("---")

    # Filter rentang tanggal untuk grafik
    st.subheader("Visualisasi Grafik")
    col1, col2 = st.columns(2)

    with col1:
        chart_start_date = st.date_input(
            "Tanggal Mulai Grafik:",
            value=start_date,
            min_value=start_date,
            max_value=end_date,
            key="chart_start"
        )

    with col2:
        chart_end_date = st.date_input(
            "Tanggal Akhir Grafik:",
            value=end_date,
            min_value=start_date,
            max_value=end_date,
            key="chart_end"
        )

    # Validasi rentang tanggal grafik
    if chart_start_date >= chart_end_date:
        st.error("Tanggal mulai grafik harus lebih awal dari tanggal akhir!")
        st.stop()

    # Ambil data untuk chart dengan filter tanggal
    chart_data = generate_sample_data(selected_kecamatan, selected_vegetasi, chart_start_date, chart_end_date, selected_dataset)

    if chart_data.empty:
        st.warning("No data available for the selected parameters and date range.")
    else:
        # Pilihan tampilan chart
        chart_type = st.radio(
            "Pilih data yang ingin ditampilkan:",
            ["Pertumbuhan Vegetasi", "Data Cuaca", "Gabungan"],
            horizontal=True
        )

        if chart_type == "Pertumbuhan Vegetasi":
            print(chart_data.head())
            if 'Pertumbuhan (%)' in chart_data.columns:
                fig = px.line(
                    chart_data,
                    x='Tanggal',
                    y='Pertumbuhan (%)',
                    title=f'Pertumbuhan {selected_vegetasi} di {selected_kecamatan}, {selected_kabupaten}<br><sub>Dataset: {selected_dataset} | Periode: {chart_start_date} - {chart_end_date}</sub>',
                    color_discrete_sequence=['#2E8B57']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Kolom 'Pertumbuhan (%)' tidak ditemukan di data vegetasi yang dimuat.")

        elif chart_type == "Data Cuaca":
            # Parameter selection untuk data cuaca
            st.subheader("🌦️ Pilih Parameter Cuaca")
            available_params = WEATHER_PARAMETERS.get(selected_dataset, {})

            filtered_available_params = {k: v for k, v in available_params.items() if k in chart_data.columns}


            selected_params = st.multiselect(
                f"Pilih parameter cuaca dari dataset {selected_dataset}:",
                options=list(filtered_available_params.keys()),
                default=list(filtered_available_params.keys())[:3] if len(filtered_available_params) > 3 else list(filtered_available_params.keys()),
                format_func=lambda x: available_params.get(x, x)
            )

            if not selected_params:
                st.warning("Silakan pilih minimal satu parameter cuaca!")
            else:
                fig = go.Figure()

                colors = ['#4169E1', '#FF6347', '#32CD32', '#FF69B4', '#20B2AA', '#FFA500', '#9370DB', '#DC143C']

                for i, param in enumerate(selected_params):
                    if param in chart_data.columns:
                        fig.add_trace(go.Scatter(
                            x=chart_data['Tanggal'],
                            y=chart_data[param],
                            mode='lines',
                            name=available_params.get(param, param),
                            line=dict(color=colors[i % len(colors)])
                        ))

                fig.update_layout(
                    title=f'Data Cuaca di {selected_kecamatan}, {selected_kabupaten}<br><sub>Dataset: {selected_dataset} | Periode: {chart_start_date} - {chart_end_date}</sub>',
                    xaxis_title='Tanggal',
                    yaxis_title='Nilai Parameter',
                    height=500,
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Info parameter yang dipilih
                with st.expander("Info Parameter yang Dipilih"):
                    for param in selected_params:
                        if param in available_params:
                            st.write(f"**{param}**: {available_params[param]}")

        else:
            # Parameter selection untuk gabungan
            st.subheader("🌦️ Pilih Parameter Cuaca untuk Grafik Gabungan")
            available_params = WEATHER_PARAMETERS.get(selected_dataset, {})
            # Filter available_params to only include columns present in chart_data
            filtered_available_params = {k: v for k, v in available_params.items() if k in chart_data.columns}

            selected_params_combined = st.multiselect(
                f"Pilih parameter cuaca dari dataset {selected_dataset}:",
                options=list(filtered_available_params.keys()),
                default=list(filtered_available_params.keys())[:2] if len(filtered_available_params) > 2 else list(filtered_available_params.keys()),
                format_func=lambda x: available_params.get(x, x),
                key="combined_params"
            )

            if not selected_params_combined:
                st.warning("Silakan pilih minimal satu parameter cuaca untuk grafik gabungan!")
            elif 'Pertumbuhan (%)' not in chart_data.columns:
                st.warning("Kolom 'Pertumbuhan (%)' tidak ditemukan di data vegetasi yang dimuat. Tidak dapat membuat grafik gabungan.")
            else:
                # Create subplot dengan 2 y-axis
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Pertumbuhan Vegetasi (%)', 'Parameter Cuaca Terpilih'),
                    vertical_spacing=0.1,
                    shared_xaxes=True
                )

                # Grafik pertumbuhan vegetasi
                fig.add_trace(
                    go.Scatter(
                        x=chart_data['Tanggal'],
                        y=chart_data['Pertumbuhan (%)'],
                        mode='lines+markers',
                        name='Pertumbuhan Vegetasi (%)',
                        line=dict(color='#2E8B57', width=3),
                        marker=dict(size=6)
                    ),
                    row=1, col=1
                )

                # Grafik parameter cuaca
                colors = ['#4169E1', '#FF6347', '#32CD32', '#FF69B4', '#20B2AA', '#FFA500', '#9370DB', '#DC143C']

                for i, param in enumerate(selected_params_combined):
                    if param in chart_data.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=chart_data['Tanggal'],
                                y=chart_data[param],
                                mode='lines',
                                name=available_params.get(param, param),
                                line=dict(color=colors[i % len(colors)], width=2)
                            ),
                            row=2, col=1
                        )

                fig.update_layout(
                    title=f'Grafik Gabungan: {selected_vegetasi} di {selected_kecamatan}, {selected_kabupaten}<br><sub>Dataset: {selected_dataset} | Periode: {chart_start_date} - {chart_end_date}</sub>',
                    height=600,
                    showlegend=True,
                    hovermode='x unified'
                )

                fig.update_xaxes(title_text="Tanggal", row=2, col=1)
                fig.update_yaxes(title_text="Pertumbuhan (%)", row=1, col=1)
                fig.update_yaxes(title_text="Nilai Parameter", row=2, col=1)

                st.plotly_chart(fig, use_container_width=True)


# ========================
# FITUR UNDUH DATASET
# ========================

st.markdown("---")
st.header("Unduh Dataset Cuaca")

col1, col2, col3 = st.columns(3)

with col1:
    download_kabupaten = st.selectbox(
        "Kabupaten untuk Dataset:",
        list(KABUPATEN_KECAMATAN.keys()),
        key="download_kabupaten"
    )

    if download_kabupaten:
        available_download_kecamatan = KABUPATEN_KECAMATAN[download_kabupaten]
        download_kecamatan = st.selectbox(
            "Kecamatan untuk Dataset:",
            available_download_kecamatan,
            key="download_kecamatan"
        )
    else:
        download_kecamatan = None

with col2:
    dataset_type = st.selectbox(
        "Jenis Dataset:",
        DATASET_TYPES,
        help="ERA-5: Reanalysis, CHIRTS: Temperature, MERRA-2: Meteorological"
    )

with col3:
    st.write("📄 Info Dataset:")
    dataset_info = {
        "ERA-5": "Dataset reanalisis cuaca global",
        "CHIRTS": "Data suhu dan presipitasi harian",
        "MERRA-2": "Data meteorologi modern"
    }
    st.info(dataset_info[dataset_type])

# Rentang waktu untuk download
st.subheader("Atur Rentang Waktu")
col1, col2 = st.columns(2)

with col1:
    download_start = st.date_input(
        "Tanggal Mulai Dataset:",
        value=date(2024, 1, 1),
        key="download_start"
    )

with col2:
    download_end = st.date_input(
        "Tanggal Akhir Dataset:",
        value=date(2024, 3, 31),
        key="download_end"
    )

# Tombol unduh
if st.button("🔄 Siapkan Dataset untuk Diunduh", type="primary"):
    if not download_kabupaten or not download_kecamatan:
        st.error("Silakan pilih kabupaten dan kecamatan terlebih dahulu!")
    elif download_start >= download_end:
        st.error("Tanggal mulai harus lebih awal dari tanggal akhir!")
    else:
        with st.spinner("Menyiapkan dataset..."):
            import time
            time.sleep(2)

            download_data = create_download_data(
                download_kecamatan, dataset_type, download_start, download_end
            )

            if not download_data.empty:
                csv_data = download_data.to_csv(index=False)
                filename = f"{dataset_type}_{download_kabupaten}_{download_kecamatan}_{download_start}_{download_end}.csv"

                st.success(f"Dataset siap. ({len(download_data)} baris data)")

                st.download_button(
                    label="Unduh Dataset CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="secondary"
                )

                with st.expander("Pratinjau Dataset"):
                    st.dataframe(download_data.head(10), use_container_width=True)
            else:
                st.warning("No data found for the selected download criteria.")