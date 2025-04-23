import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta
import time as tm
import threading
from datetime import date
import re

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwc7KdXG4t8x-4aO-8xKXPmni7JV65KRKtWe9F0oesOcSdtNaBE7xTUK5S2L639e6We/exec"


# Fungsi untuk mendapatkan semua data dari Google Sheets
def overview():
    @st.cache_data
    def get_all_data():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return []

    def filter_dataframe(df):
        """
        Adds a UI on top of a dataframe to let viewers filter columns.

        Args:
            df (pd.DataFrame): Original dataframe

        Returns:
            pd.DataFrame: Filtered dataframe
        """
        modify = st.checkbox("Tambah Filter")

        if not modify:
            return df

        df_filtered = df.copy()  # Salin dataframe agar tidak mengubah aslinya

        # Konversi tipe data untuk filter

        # Filter UI
        with st.container():
            to_filter_columns = st.multiselect("Pilih kolom untuk filter", df_filtered.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")

                if column == "Tanggal":  # Slider untuk tanggal
                    # Ubah format tanggalnya dulu agar bisa di sort
                    bulan_indo_to_eng = {
                        "Januari": "January", "Februari": "February", "Maret": "March", "April": "April",
                        "Mei": "May", "Juni": "June", "Juli": "July", "Agustus": "August",
                        "September": "September", "Oktober": "October", "November": "November", "Desember": "December"
                    }
                    # Hilangkan nama hari dan ubah nama bulan ke bahasa Inggris
                    df_filtered[column] = df_filtered[column].apply(lambda x: re.sub(r"^\w+, ", "", x))  # Hapus nama hari
                    df_filtered[column] = df_filtered[column].replace(bulan_indo_to_eng, regex=True)  # Ubah nama bulan

                    # Parsing ke datetime
                    df_filtered[column] = pd.to_datetime(df_filtered[column], format="%d %B %Y")

                    min_date, max_date = df_filtered[column].min().date(), df_filtered[column].max().date()

                    # Ambil input tanggal dari pengguna
                    date_range = right.date_input(
                        f"Filter {column}",
                        min_value=min_date,
                        max_value=max_date,
                        value=(min_date, max_date),  # Default ke rentang min-max
                    )

                    # Pastikan date_range selalu dalam bentuk yang benar
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_date, end_date = date_range
                    else:
                        start_date = end_date = date_range[0]  # Ambil elemen pertama kalau masih tuple

                    # Filter data dengan hanya membandingkan tanggal (tanpa waktu)
                    df_filtered = df_filtered[
                        (df_filtered[column].dt.date >= start_date) & 
                        (df_filtered[column].dt.date <= end_date)
                    ]

                    # Ubah format ke "Hari, Tanggal Bulan Tahun"
                    # Kamus Nama Hari Inggris → Indonesia
                    hari_eng_to_indo = {
                        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis",
                        "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
                    }
                        # **Tambahkan Nama Hari dan Format ke "Hari, Tanggal Bulan Tahun"**
                    df_filtered["Hari"] = df_filtered[column].dt.strftime('%A').map(hari_eng_to_indo)  # Konversi nama hari
                    df_filtered[column] = df_filtered[column].dt.strftime('%d %B %Y')  # Format tanggal biasa
                    df_filtered[column] = df_filtered["Hari"] + ", " + df_filtered[column]  # Gabungkan Nama Hari
                    df_filtered.drop(columns=["Hari"], inplace=True)  # Hapus kolom tambahan

                elif column in ["Waktu Mulai", "Waktu Selesai"]:

                    df_filtered[column] = pd.to_datetime(df_filtered[column], errors='coerce').dt.time
                    # Pastikan kolom tidak kosong
                    if df_filtered[column].dropna().empty:
                        st.warning(f"Tidak ada data untuk {column}.")
                        continue  # Lewati filter ini jika tidak ada data

                    min_time, max_time = df_filtered[column].dropna().min(), df_filtered[column].dropna().max()
                    # Tambahkan validasi jika min_time == max_time
                    if min_time == max_time:
                        min_time = (datetime.combine(datetime.today(), min_time) - timedelta(minutes=30)).time()
                        max_time = (datetime.combine(datetime.today(), max_time) + timedelta(minutes=30)).time()
                    start_time, end_time = right.slider(
                        f"Filter {column}",
                        min_value=min_time,
                        max_value=max_time,
                        value=(min_time, max_time),
                        format="HH:mm"
                    )

                    df_filtered = df_filtered[
                        (df_filtered[column] >= start_time) &
                        (df_filtered[column] <= end_time)
                    ]
                    df_filtered[column] = df_filtered[column].apply(lambda x: x.strftime("%H:%M") if pd.notnull(x) else "")

                elif column in ["Nomor SPK", "Operator", "Line", "Item" ,"Speed(kg/jam)",
                                "Siklus(kg)","Filler","Bt","SPK","Keterangan","Kendala"]:  # Filter kategori
                    unique_values = df_filtered[column].unique()
                    selected_values = right.multiselect(
                        f"Filter {column}",
                        options=unique_values,
                        default=[],
                    )
                    if selected_values:
                        df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
        return df_filtered
    def overview():
        st.title("Data Overview")
        data = get_all_data()
        columns = [
            "Nomor SPK", "Tanggal", "Waktu Mulai", "Waktu Selesai", "Operator", "Line", 
            "Item", "Speed(kg/jam)","Siklus(kg)","Filler","Bt","SPK","Keterangan","Kendala"
        ]
        
        df = pd.DataFrame(data[1:], columns=columns) if data else pd.DataFrame(columns=columns)

        if data:
            # Balik urutan baris → data terbaru di atas
            df = df.iloc[::-1].reset_index(drop=True)

        if st.button("Muat Ulang Data"):
            st.cache_data.clear()
            st.rerun()

        st.dataframe(filter_dataframe(df))

    overview()
