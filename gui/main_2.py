import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Analisis Vegetasi-Iklim",
    page_icon="🌱",
    layout="wide"
)

# Data contoh untuk demo (dalam aplikasi nyata, ini akan diambil dari database/file)
KABUPATEN_KECAMATAN = {
    "Cianjur": [
        "Warungkondang", "Gekbrong", "Cugenang", "Cianjur", 
        "Campaka", "Cilaku", "Cibeber"
    ]
}

# Daftar semua kecamatan untuk fungsi yang membutuhkan
ALL_KECAMATAN = []
for kecamatan_list in KABUPATEN_KECAMATAN.values():
    ALL_KECAMATAN.extend(kecamatan_list)

VEGETASI_LIST = [
    "Padi", "Jagung", "Kentang", "Tomat", 
    "Cabai", "Kacang Tanah", "Ubi Jalar"
]

DATASET_TYPES = ["ERA-5", "CHIRTS", "MERRA-2"]

def generate_sample_data(kecamatan, vegetasi, start_date, end_date):
    """
    Fungsi untuk menghasilkan data contoh
    Dalam aplikasi nyata, ini akan mengambil data dari database
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='M')
    
    # Simulasi data pertumbuhan berdasarkan vegetasi
    base_growth = {
        "Padi": 75, "Jagung": 65, "Kentang": 55,
        "Tomat": 60, "Cabai": 70, "Kacang Tanah": 50, "Ubi Jalar": 45
    }
    
    # Tambahkan variasi random untuk simulasi
    np.random.seed(hash(kecamatan + vegetasi) % 1000)
    growth_data = []
    
    for i, tanggal in enumerate(date_range):
        # Simulasi pertumbuhan dengan tren dan variasi musiman
        base = base_growth.get(vegetasi, 60)
        seasonal = 10 * np.sin(2 * np.pi * i / 12)  # Variasi musiman
        noise = np.random.normal(0, 5)  # Noise random
        growth = max(0, base + seasonal + noise)
        
        growth_data.append({
            'Tanggal': tanggal,
            'Pertumbuhan (%)': round(growth, 1),
            'Curah_Hujan': round(np.random.normal(150, 50), 1),
            'Suhu_Rata': round(np.random.normal(26, 3), 1),
            'Kelembaban': round(np.random.normal(75, 10), 1)
        })
    
    return pd.DataFrame(growth_data)

def get_climate_factors(vegetasi):
    """
    Mengembalikan faktor cuaca yang paling berpengaruh dan kondisi optimal
    """
    climate_data = {
        "Padi": {
            "faktor_utama": "Curah Hujan dan Suhu",
            "curah_hujan": "1200-1800 mm/tahun",
            "suhu": "22-30°C",
            "kelembaban": "70-85%",
            "catatan": "Membutuhkan air yang cukup selama fase pertumbuhan"
        },
        "Jagung": {
            "faktor_utama": "Suhu dan Sinar Matahari", 
            "curah_hujan": "400-800 mm/tahun",
            "suhu": "21-27°C",
            "kelembaban": "60-70%",
            "catatan": "Toleran kekeringan, membutuhkan sinar matahari penuh"
        },
        "Kentang": {
            "faktor_utama": "Suhu Dingin dan Kelembaban",
            "curah_hujan": "500-700 mm/tahun", 
            "suhu": "15-20°C",
            "kelembaban": "80-85%",
            "catatan": "Cocok di dataran tinggi dengan suhu sejuk"
        }
    }
    
    # Default untuk vegetasi lain
    default = {
        "faktor_utama": "Suhu dan Curah Hujan",
        "curah_hujan": "600-1000 mm/tahun",
        "suhu": "20-28°C", 
        "kelembaban": "65-75%",
        "catatan": "Kondisi iklim tropis pada umumnya"
    }
    
    return climate_data.get(vegetasi, default)

def create_download_data(kecamatan, dataset_type, start_date, end_date):
    """
    Membuat data CSV untuk diunduh
    Dalam aplikasi nyata, ini akan mengambil dari server
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Simulasi data cuaca berdasarkan dataset type
    weather_data = []
    np.random.seed(hash(kecamatan + dataset_type) % 1000)
    
    for tanggal in date_range:
        data_row = {
            'Tanggal': tanggal.strftime('%Y-%m-%d'),
            'Kabupaten': kecamatan.split(', ')[1] if ', ' in kecamatan else 'Cianjur',
            'Kecamatan': kecamatan.split(', ')[0] if ', ' in kecamatan else kecamatan,
            'Dataset': dataset_type,
            'Suhu_Min': round(np.random.normal(20, 3), 1),
            'Suhu_Max': round(np.random.normal(30, 4), 1),
            'Curah_Hujan': round(max(0, np.random.exponential(5)), 1),
            'Kelembaban': round(np.random.normal(75, 15), 1),
            'Kecepatan_Angin': round(np.random.normal(8, 3), 1)
        }
        weather_data.append(data_row)
    
    return pd.DataFrame(weather_data)

# ========================
# TAMPILAN UTAMA APLIKASI
# ========================

st.title("🌱 Analisis Keterkaitan Vegetasi dengan Iklim")
st.markdown("---")

# Sidebar untuk input utama
st.sidebar.header("⚙️ Pengaturan Analisis")

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

# Validasi tanggal
if start_date >= end_date:
    st.sidebar.error("Tanggal mulai harus lebih awal dari tanggal akhir!")
    st.stop()

# ========================
# DASHBOARD UTAMA
# ========================

if selected_kabupaten and selected_kecamatan and selected_vegetasi:
    st.header(f"📊 Dashboard: {selected_vegetasi} di {selected_kecamatan}, {selected_kabupaten}")
    
    # Ambil data iklim untuk vegetasi yang dipilih
    climate_info = get_climate_factors(selected_vegetasi)
    
    # Layout dengan 2 kolom
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌡️ Faktor Cuaca Paling Berpengaruh")
        st.info(f"**{climate_info['faktor_utama']}**")
        st.write(f"📌 {climate_info['catatan']}")
    
    with col2:
        st.subheader("🎯 Kondisi Cuaca Optimal")
        st.success(f"""
        **Curah Hujan:** {climate_info['curah_hujan']}  
        **Suhu:** {climate_info['suhu']}  
        **Kelembaban:** {climate_info['kelembaban']}
        """)
    
    st.markdown("---")
    
    # Ambil data untuk chart
    chart_data = generate_sample_data(selected_kecamatan, selected_vegetasi, start_date, end_date)
    
    # Chart Time Series
    st.subheader("📈 Grafik Pertumbuhan dan Data Cuaca")
    
    # Pilihan tampilan chart
    chart_type = st.radio(
        "Pilih data yang ingin ditampilkan:",
        ["Pertumbuhan Vegetasi", "Data Cuaca", "Gabungan"],
        horizontal=True
    )
    
    if chart_type == "Pertumbuhan Vegetasi":
        fig = px.line(
            chart_data, 
            x='Tanggal', 
            y='Pertumbuhan (%)',
            title=f'Pertumbuhan {selected_vegetasi} di {selected_kecamatan}, {selected_kabupaten}',
            color_discrete_sequence=['#2E8B57']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Data Cuaca":
        # Chart untuk data cuaca (multiple lines)
        fig = go.Figure()
        
        # Tambahkan line untuk setiap parameter cuaca
        fig.add_trace(go.Scatter(
            x=chart_data['Tanggal'], 
            y=chart_data['Curah_Hujan'],
            mode='lines', 
            name='Curah Hujan (mm)',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=chart_data['Tanggal'], 
            y=chart_data['Suhu_Rata'],
            mode='lines', 
            name='Suhu Rata-rata (°C)',
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=chart_data['Tanggal'], 
            y=chart_data['Kelembaban'],
            mode='lines', 
            name='Kelembaban (%)',
            yaxis='y3'
        ))
        
        # Layout dengan multiple y-axes
        fig.update_layout(
            title=f'Data Cuaca di {selected_kecamatan}, {selected_kabupaten}',
            xaxis_title='Tanggal',
            yaxis=dict(title='Curah Hujan (mm)', side='left'),
            yaxis2=dict(title='Suhu (°C)', side='right', overlaying='y'),
            yaxis3=dict(title='Kelembaban (%)', side='right', overlaying='y', position=0.95),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:  # Gabungan
        # Subplot dengan 2 chart
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=[f'Pertumbuhan {selected_vegetasi}', 'Data Cuaca'],
            vertical_spacing=0.1
        )
        
        # Chart pertumbuhan
        fig.add_trace(
            go.Scatter(x=chart_data['Tanggal'], y=chart_data['Pertumbuhan (%)'],
                      mode='lines', name='Pertumbuhan (%)', line=dict(color='#2E8B57')),
            row=1, col=1
        )
        
        # Chart cuaca
        fig.add_trace(
            go.Scatter(x=chart_data['Tanggal'], y=chart_data['Curah_Hujan'], 
                      mode='lines', name='Curah Hujan (mm)', line=dict(color='#4169E1')),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=chart_data['Tanggal'], y=chart_data['Suhu_Rata'], 
                      mode='lines', name='Suhu (°C)', line=dict(color='#FF6347')),
            row=2, col=1
        )
        
        fig.update_layout(height=600, title_text=f"Analisis Gabungan - {selected_kecamatan}, {selected_kabupaten}")
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabel data (sampel)
    with st.expander("📋 Lihat Data Detail"):
        st.dataframe(chart_data, use_container_width=True)

# ========================
# FITUR UNDUH DATASET
# ========================

st.markdown("---")
st.header("📥 Unduh Dataset Cuaca")

col1, col2, col3 = st.columns(3)

with col1:
    download_kabupaten = st.selectbox(
        "Kabupaten untuk Dataset:",
        list(KABUPATEN_KECAMATAN.keys()),
        key="download_kabupaten"
    )
    
    # Dropdown kecamatan berdasarkan kabupaten yang dipilih untuk download
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
st.subheader("📅 Rentang Waktu Dataset")
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
            # Simulasi delay
            import time
            time.sleep(2)
            
            # Buat data untuk diunduh
            download_data = create_download_data(
                f"{download_kecamatan}, {download_kabupaten}", dataset_type, download_start, download_end
            )
            
            # Konversi ke CSV
            csv_data = download_data.to_csv(index=False)
            
            # Nama file
            filename = f"{dataset_type}_{download_kabupaten}_{download_kecamatan}_{download_start}_{download_end}.csv"
            
            st.success(f"✅ Dataset siap! ({len(download_data)} baris data)")
            
            # Tombol download
            st.download_button(
                label="📥 Unduh Dataset CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                type="secondary"
            )
            
            # Pratinjau data
            with st.expander("👀 Pratinjau Dataset"):
                st.dataframe(download_data.head(10), use_container_width=True)

# ========================
# FOOTER
# ========================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🌱 Aplikasi Analisis Vegetasi-Iklim | Dibuat dengan Streamlit</p>
    <p>💡 <em>Catatan: Data yang ditampilkan adalah simulasi untuk demo</em></p>
</div>
""", unsafe_allow_html=True)