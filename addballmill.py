import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta
import time as tm
import threading
from datetime import date

def run():
    # URL dari Google Apps Script Web App
    APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwc7KdXG4t8x-4aO-8xKXPmni7JV65KRKtWe9F0oesOcSdtNaBE7xTUK5S2L639e6We/exec"

    # Fungsi untuk mendapatkan semua data dari Google Sheets
    def get_all_data():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return []

    # Fungsi untuk mendapatkan opsi dari Google Sheets
    def get_options():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=10)
            response.raise_for_status()
            options = response.json()
            return options
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return {}

    # Fungsi untuk mengirim data ke Google Sheets
    def add_data(form_data):
        try:
            response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}


    # Fungsi Ping Otomatis (Keep Alive)
    # def keep_alive():
    #     while True:
    #         try:
    #             response = requests.get(APPS_SCRIPT_URL, timeout=10)
    #             print(f"Keep Alive Status: {response.status_code}")
    #         except Exception as e:
    #             print(f"Keep Alive Error: {e}")
    #         tm.sleep(600)  # Ping setiap 10 menit

    # # Menjalankan fungsi keep_alive di thread terpisah agar tidak mengganggu UI
    # thread = threading.Thread(target=keep_alive, daemon=True)
    # thread.start()


    # Fungsi untuk mendapatkan nomor SPK otomatis
    def generate_spk_number(selected_date):
        bulan_romawi = {
            1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
            7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
        }
        all_data = get_all_data()
        selected_month = selected_date.month
        selected_year = selected_date.year
        selected_month_romawi = bulan_romawi[selected_month]  # Konversi bulan ke Romawi

        # Ambil semua nomor SPK untuk bulan dan tahun ini
        spk_numbers = [
            row[0] for row in all_data
            if len(row) > 0 and f"/{selected_month_romawi}/{selected_year}" in row[0]
        ]

        if spk_numbers:
            # Ambil nomor terakhir dan tambahkan 1
            last_spk = max(spk_numbers)  # Ambil nomor terbesar
            last_number = int(last_spk.split("/")[0])  # Ambil angka sebelum "/PR/"
            new_number = last_number + 1
        else:
    # Jika belum ada SPK bulan ini, mulai dari 1
            new_number = 1

        # Format nomor SPK baru
        return f"{str(new_number).zfill(2)}/PR/{selected_month_romawi}/{selected_year}"

    # Ambil data dari Google Sheets
    st.session_state.setdefault("form_tanggal", date.today())
    all_data = get_all_data()

    # Ambil data untuk select box
    options = get_options()
    defaults = {
        "form_nomorSPK": generate_spk_number(st.session_state["form_tanggal"]), 
        "form_tanggal": st.session_state["form_tanggal"], 
        "form_start": datetime.now().time(), 
        "form_stop": datetime.now().time(), 
        "form_operator" : "",
        "form_line" : "",
        "form_item" : "",
        "form_speed": "",
        "form_siklus": 0,
        "form_filler" : 0,
        "form_bt" : 0,
        "form_spk" : 0,
        "form_keterangan" : "",
        "form_kendala" : "",
    }

    # Pastikan semua nilai default ada di session state tanpa overwrite jika sudah ada
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    # Pastikan form_add_reset ada di session_state
    st.session_state.setdefault("form_add_reset", False)

    # Reset nilai form jika form_add_reset bernilai True
    if st.session_state.form_add_reset:
        st.session_state.update(defaults)
        st.session_state.form_add_reset = False  # Kembalikan ke False setelah reset

    st.title("📄 Surat Perintah Kerja Ballmill")  
    import overview
    overview.overview()
    
    # Divider
    st.markdown("---")
    
    ## NO SPK & TANGGAL ##
    st.markdown("## 🗂️ Informasi SPK Ballmill ")
    st.markdown("---")
    col1, col2 = st.columns(2)  
    with col1:
        tanggal = st.date_input("Tanggal", value=st.session_state.get("form_tanggal"), key="form_tanggal")
    with col2:
        if "form_tanggal" not in st.session_state or tanggal != st.session_state["form_tanggal"]:
            st.session_state["form_tanggal"] = tanggal
        
        nomor_spk = st.text_input("Nomor SPK", value=generate_spk_number(st.session_state["form_tanggal"]), key="form_nomorSPK", disabled=True)
    
    ## START & STOP ##
    st.subheader("⏳ Waktu Produksi")  
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("Jam Start", value=st.session_state.get("form_start"), key="form_start")
    with col2:
        stop_time = st.time_input("Jam Stop", value=st.session_state.get("form_stop"), key="form_stop")
    # Divider
    st.markdown("---")

    st.subheader("🎯 Detail Ballmill")

    # Pastikan kita hanya mengambil data yang valid
    data_clean = [row for row in options.get("Dropdown List", []) if isinstance(row, list) and len(row) > 2]  # Pastikan ada minimal 3 kolom (, Line, Produk)

    # Fungsi untuk mendapatkan daftar unik BU
    def extract_unique_line(data):
        try:
            return sorted(set(row[0] for row in data if row[0]))  # Pastikan nilai Line tidak kosong
        except Exception as e:
            st.error(f"Error saat mengekstrak Line: {e}")
            return []
        
    def extract_unique_operator(data):
        try:
            return sorted(set(row[10] for row in data if row[10]))  # Pastikan nilai operator tidak kosong
        except Exception as e:
            st.error(f"Error saat mengekstrak Line: {e}")
            return []
        
    # Fungsi untuk memfilter Item berdasarkan Line yang dipilih
    def filter_by_line(data, selected_line, column_index):
        try:
            return sorted(set(row[column_index] for row in data if row[0] == selected_line and row[column_index]))
        except Exception as e:
            st.error(f"Error saat memfilter berdasarkan Line: {e}")
            return []

    # Fungsi untuk memfilter Speed, Siklus, Filter, Bt dan SPK berdasarkan Item yang dipilih
    def filter_by_item(data, selected_item, column_index):
        try:
            return sorted(set(row[column_index] for row in data if row[3] == selected_item and row[column_index]))
        except Exception as e:
            st.error(f"Error saat memfilter berdasarkan Item: {e}")
            return []
        

    operator_options = extract_unique_operator(data_clean)  # Ambil Line dari options

    if "form_operator" in st.session_state and st.session_state["form_operator"] not in operator_options:
        st.session_state["form_operator"] =  st.session_state.get("form_operator", "")

    # Dropdown untuk Line
    operator = st.selectbox("Operator", [""] + operator_options, key="form_operator")
        
    # Ambil daftar unik Line dari dataset
    line_options = extract_unique_line(data_clean)  # Ambil Line dari options

    if "form_line" in st.session_state and st.session_state["form_line"] not in line_options:
        st.session_state["form_line"] =  st.session_state.get("form_line", "")

    # Dropdown untuk Line
    line = st.selectbox("Line", [""] + line_options, key="form_line")

    # Ambil daftar Item berdasarkan Line yang dipilih
    list_item = filter_by_line(data_clean, line, 1) if line else []

    if "form_item" in st.session_state and st.session_state["form_item"] not in list_item:
        st.session_state["form_item"] =  st.session_state.get("form_item", "")

    # Dropdown untuk Item
    item = st.selectbox("Item", [""] + list_item, key="form_item")

    # Ambil daftar Speed berdasarkan Item yang dipilih
    list_speed = filter_by_item(data_clean, item, 4) if item else []

    if "form_speed" in st.session_state and st.session_state["form_speed"] not in list_speed:
        st.session_state["form_speed"] = st.session_state.get("form_speed", "")

    # Dropdown untuk Speed
    speed = st.selectbox("Pilih Speed", [""] + list_speed, key="form_speed") 
    # Ambil baris data yang sesuai speed

    if item and speed:
        try:
            selected_row = next(
                row for row in data_clean
                if row[3] == item and str(row[4]) == str(speed)
            )

            # Simpan ke session_state agar bisa dipakai di form
            st.session_state["form_siklus"] = selected_row[5]
            st.session_state["form_filler"] = selected_row[6]
            st.session_state["form_bt"] = selected_row[7]
            st.session_state["form_spk"] = selected_row[8]

        except StopIteration:
            st.warning("Data tidak ditemukan untuk kombinasi Item dan Speed yang dipilih.")
        except Exception as e:
            st.error(f"Terjadi error saat mengambil data: {e}")

    siklus = st.number_input("Siklus(Kg)", value=st.session_state["form_siklus"], disabled=True)
    filler = st.number_input("Filler", value=st.session_state["form_filler"], disabled=True)
    bt = st.number_input("BT", value=st.session_state["form_bt"], disabled=True)
    spk = st.text_input("SPK", value=st.session_state["form_spk"], disabled=True)
    
    st.markdown("### 📝 Keterangan Tambahan")
    # KETERANGAN
    keterangan = st.text_area("Keterangan",key="form_keterangan")
     
    #KENDALA
    kendala = st.text_area("Kendala", key = "form_kendala")

    if not line or not item or not speed :
        st.error("⚠ Pilih Line, Item dan Speed")

    # # Divider
    # st.markdown("---")

    # Tombol Simpan
    st.markdown("---")

    form_completed = all(st.session_state.get(key) for key in [
        "form_tanggal", "form_start", "form_stop", "form_operator", "form_line", "form_item", "form_speed"
    ])


    submit_button = st.button("💾 Simpan Data", use_container_width=True,disabled=not form_completed)


    # Jika tombol "Simpan Data" ditekan
    if submit_button:
        try:
            formatted_tanggal = tanggal.strftime("%Y-%m-%d")  

            # Data yang akan dikirim ke Apps Script
            data = {
                "action": "add_data",
                "NomorSPK": nomor_spk,
                "Tanggal": formatted_tanggal,
                "Start" : start_time.strftime("%H:%M"),
                "Stop" : stop_time.strftime("%H:%M"),
                "Operator" : operator,
                "Line": line, 
                "Item" : item,
                "Speed": speed,
                "SiklusKG" : siklus,
                "Filler" : filler,
                "Bt" : bt,
                "SPK" : spk,
                "Keterangan" : keterangan,
                "Kendala" : kendala
                
            }

            # Kirim data ke Apps Script menggunakan POST request
            response = requests.post(APPS_SCRIPT_URL, json=data)
            result = response.json()

            if result.get("status") == "success":
                st.success("Data berhasil ditambahkan!")
                st.session_state.form_add_reset = True
                st.rerun() 

            else:
                st.error(f"Terjadi kesalahan: {result.get('error')}")

        except Exception as e:
            st.error(f"Error: {str(e)}")
if __name__ == "__main__":
    run()
