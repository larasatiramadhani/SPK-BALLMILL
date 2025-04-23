import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta, date
import locale
import threading
import time as tm 
# URL dari Google Apps Script Web App
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz8XodRWGaQLjdRTKPNdJOi-OvchLtbZ5liGJCne3VNX-IeMGHM0YGZmq9x8cLHBbdz/exec"

# Atur locale ke bahasa Indonesia
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
except locale.Error:
    print("Locale 'id_ID.UTF-8' tidak tersedia, menggunakan locale default.")

# Function to get all data from Google Sheets
def get_all_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return []

# Function to get options
def get_options():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=20)
        response.raise_for_status()
        options = response.json()
        for key in options:
            options[key].insert(0, "")  # Add empty option as default
        return options
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil opsi: {e}")
        return {}

# Function to update data
def update_data(updated_row):
    try:
        updated_row["Tanggal"] = updated_row["Tanggal"].strftime("%A, %d %B %Y")
        updated_row["Waktu Mulai"] = updated_row["Waktu Mulai"].strftime("%H:%M")
        updated_row["Waktu Selesai"] = updated_row["Waktu Selesai"].strftime("%H:%M")

        payload = {
            "action": "update_data",
            "updated_row": updated_row,
        }
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan: {e}")
        return {"status": "error", "error": str(e)}
    
# Function to delete data
def delete_data(unique_key):
    try:
        response = requests.post(APPS_SCRIPT_URL, json={"action": "delete_data", "unique_key": unique_key}, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

def parse_time(time_str):
    """Convert a time string into a datetime.time object."""
    if isinstance(time_str, str):
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return time(0, 0)
    elif isinstance(time_str, time):
        return time_str
    else:
        return time(0, 0)

# Fungsi Ping Otomatis (Keep Alive)
def keep_alive():
    while True:
        try:
            response = requests.get(APPS_SCRIPT_URL, timeout=30)
            print(f"Keep Alive Status: {response.status_code}")
        except Exception as e:
            print(f"Keep Alive Error: {e}")
        tm.sleep(600)  # Ping setiap 10 menit

# Menjalankan fungsi keep_alive di thread terpisah agar tidak mengganggu UI
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()

# Get options for select box
all_data = get_all_data()
options = get_options()
data_clean = [row for row in options.get("Dropdown List", []) if isinstance(row, list) and len(row) > 2]  # Pastikan ada minimal 3 kolom (BU, Line, Produk)

# Extract Line unik (dulu BU)
def extract_unique_line(data):
    try:
        return sorted(set(row[0] for row in data if row[0]))
    except Exception as e:
        st.error(f"Error saat mengekstrak Line: {e}")
        return []

# operator 
def operator_list(data, column_index=10):  
    try:
        return sorted(set(row[column_index] for row in data if row[column_index]))
    except Exception as e:
        st.error(f"Error saat mengekstrak Operator: {e}")
        return []

# Filter Item berdasarkan Line
def filter_by_line(data, selected_line, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == selected_line and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter Item: {e}")
        return []

# Filter Speed berdasarkan Line dan Item
def filter_by_speed(data, line, item, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == line and row[3] == item and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter Speed: {e}")
        return []

# Filter Siklus
def filter_by_siklus(data, line, item, speed, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == line and row[3] == item and row[4] == speed and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter Siklus: {e}")
        return []

# Filter Filler
def filter_by_filler(data, line, item, speed, siklus, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == line and row[3] == item and row[4] == speed and row[5] == siklus and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter Filler: {e}")
        return []

# Filter Bt
def filter_by_bt(data, line, item, speed, siklus, filler, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == line and row[3] == item and row[4] == speed and row[5] == siklus and row[6] == filler and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter Bt: {e}")
        return []

# Filter SPK
def filter_by_spk(data, line, item, speed, siklus, filler, bt, column_index):
    try:
        return sorted(set(row[column_index] for row in data if row[0] == line and row[3] == item and row[4] == speed and row[5] == siklus and row[6] == filler and row[7] == bt and row[column_index]))
    except Exception as e:
        st.error(f"Error saat memfilter SPK: {e}")
        return []
    
bu_options = extract_unique_line(data_clean)
# Get data from Google Sheets

st.title("📄 Surat Perintah Kerja")

# Pastikan session_state untuk halaman ada
if "page" not in st.session_state:
    st.session_state["page"] = 0

if isinstance(all_data, list) and all_data:
    df = pd.DataFrame(all_data, columns=[
        "Nomor SPK", "Tanggal", "Waktu Mulai", "Waktu Selesai", "Operator", "Line", "Item", "Speed (kg/jam)",
        "Siklus (kg)", "Filler", "Bt", "SPK", "Keterangan", "Kendala"
    ])
    # Urutkan data agar yang terbaru (yang masuk terakhir) muncul duluan
    df = df.iloc[::-1].reset_index(drop=True)

    st.subheader("📊 Data Keseluruhan")
    items_per_page = 10
    total_pages = (len(df) // items_per_page) + (1 if len(df) % items_per_page != 0 else 0)

    start_idx = st.session_state["page"] * items_per_page
    end_idx = start_idx + items_per_page
    displayed_rows = df.iloc[start_idx:end_idx]

    for index, row in displayed_rows.iterrows():
        unique_key = row["Nomor SPK"]
        with st.expander(f"📄 {unique_key}"):
            st.write(f"📅 Tanggal: {row['Tanggal']}")
            st.write(f"⏱ Waktu Mulai: {row['Waktu Mulai']}")
            st.write(f"⏳ Waktu Selesai: {row['Waktu Selesai']}")
            st.write(f"👤 Operator: {row['Operator']}")
            st.write(f"🏭 Line Produksi: {row['Line']}")
            st.write(f"📦 Item: {row['Item']}")
            st.write(f"⚡ Speed (kg/jam): {row['Speed (kg/jam)']}")
            st.write(f"🔁 Siklus (kg): {row['Siklus (kg)']}")
            st.write(f"🥄 Filler: {row['Filler']}")
            st.write(f"🧪 Bt: {row['Bt']}")
            st.write(f"📑 SPK: {row['SPK']}")
            st.write(f"📝 Keterangan: {row['Keterangan']}")
            st.write(f"⚠️ Kendala: {row['Kendala']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑 Hapus {unique_key}", key=f"delete_{unique_key}"):
                    st.session_state.confirm_delete = unique_key

            with col2:
                # if row['SM'] == "Approved":
                #     st.warning("🚫 Data ini sudah Approved oleh Manager.")

                if st.button(f"✏ Edit {unique_key}", key=f"edit_{unique_key}"):
                    st.session_state["edit_data"] = row
                    st.session_state["editing"] = True

    # Navigasi halaman
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state["page"] > 0:
            if st.button("⬅ Previous"):
                st.session_state["page"] -= 1
                st.rerun()
    with col2:
        if st.session_state["page"] < total_pages - 1:
            if st.button("Next ➡"):
                st.session_state["page"] += 1
                st.rerun()


# Konfirmasi penghapusan
if "confirm_delete" in st.session_state and st.session_state.confirm_delete:
    unique_key = st.session_state.confirm_delete
    st.error("Apakah Anda yakin ingin menghapus data ini?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Hapus"):
            delete_data(unique_key)
            st.success(f"Data {unique_key} berhasil dihapus.")
            st.session_state.confirm_delete = None  # Reset konfirmasi
            tm.sleep(2)
            st.rerun()  # Refresh UI setelah penghapusan
    with col2:
        if st.button("Batal"):
            st.session_state.confirm_delete = None  # Reset konfirmasi
            st.toast("Penghapusan dibatalkan.",icon="↩")
            tm.sleep(2)
            st.rerun()

if st.session_state.get("editing", False):
    st.subheader("✏ Edit Data")
    row = st.session_state["edit_data"]

    # Konversi Tanggal
    if isinstance(row["Tanggal"], str):
        try:
            tanggal_date = datetime.strptime(row["Tanggal"], "%A, %d %B %Y").date()
        except ValueError:
            tanggal_date = datetime.now().date()
    else:
        tanggal_date = row["Tanggal"]

    nomor_spk = row["Nomor SPK"]
    selected_row = df[df["Nomor SPK"] == nomor_spk].iloc[0]
    
    # Atur session state awal
    # st.session_state.operator = selected_row.get("Operator", "")
    st.session_state.line = selected_row.get("Line", "")
    st.session_state.item = selected_row.get("Item", "")
    st.session_state.speed = selected_row.get("Speed", "")
    st.session_state.siklus = selected_row.get("Siklus (kg)", "")
    st.session_state.filler = selected_row.get("Filler", "")
    st.session_state.bt = selected_row.get("Bt", "")
    st.session_state.spk_value = selected_row.get("SPK", "")

    # Input Nomor SPK dan Tanggal
    st.text_input("🔢 Nomor SPK", value=nomor_spk, disabled=True)
    tanggal = st.date_input("📅 Tanggal", value=tanggal_date)

    start_time = st.time_input("⏰ Jam Mulai", value=parse_time(row["Waktu Mulai"]))
    stop_time = st.time_input("⏳ Jam Selesai", value=parse_time(row["Waktu Selesai"]))

    operator_options = operator_list(data_clean[1:])
    if "operator" not in st.session_state:
        st.session_state.operator = selected_row.get("Operator", "")

    operator = st.selectbox("👷 Operator", operator_options, index=operator_options.index(st.session_state.operator) if st.session_state.operator in operator_options else 0)

    if operator != st.session_state.operator:
        st.session_state.operator = operator

    # LINE
    line_options = extract_unique_line(data_clean[1:])
    line = st.selectbox("🏭 Line", line_options, index=line_options.index(st.session_state.line) if st.session_state.line in line_options else 0)
    if line != st.session_state.line:
        st.session_state.line = line
        st.session_state.item = ""
        st.session_state.speed = ""
        st.session_state.siklus = ""
        st.session_state.filler = ""
        st.session_state.bt = ""
        st.session_state.spk_value = ""

    # ITEM
    item_options = filter_by_line(data_clean, st.session_state.line, 3)
    item = st.selectbox("🏷 Item", item_options, index=item_options.index(st.session_state.item) if st.session_state.item in item_options else 0)
    if item != st.session_state.item:
        st.session_state.item = item
        st.session_state.speed = ""
        st.session_state.siklus = ""
        st.session_state.filler = ""
        st.session_state.bt = ""
        st.session_state.spk_value = ""

    # SPEED
    speed_options = filter_by_speed(data_clean, st.session_state.line, st.session_state.item, 4)
    speed = st.selectbox("🚀 Speed", speed_options, index=speed_options.index(st.session_state.speed) if st.session_state.speed in speed_options else 0)
    if speed != st.session_state.speed:
        st.session_state.speed = speed
        st.session_state.siklus = ""
        st.session_state.filler = ""
        st.session_state.bt = ""
        st.session_state.spk_value = ""

    # SIKLUS
    siklus_options = filter_by_siklus(data_clean, st.session_state.line, st.session_state.item, st.session_state.speed, 5)
    siklus = st.selectbox("🔁 Siklus", siklus_options, index=siklus_options.index(st.session_state.siklus) if st.session_state.siklus in siklus_options else 0)
    if siklus != st.session_state.siklus:
        st.session_state.siklus = siklus
        st.session_state.filler = ""
        st.session_state.bt = ""
        st.session_state.spk_value = ""

    # FILLER
    filler_options = filter_by_filler(data_clean, st.session_state.line, st.session_state.item, st.session_state.speed, st.session_state.siklus, 6)
    filler = st.selectbox("🧪 Filler", filler_options, index=filler_options.index(st.session_state.filler) if st.session_state.filler in filler_options else 0)
    if filler != st.session_state.filler:
        st.session_state.filler = filler
        st.session_state.bt = ""
        st.session_state.spk_value = ""

    # BT
    bt_options = filter_by_bt(data_clean, st.session_state.line, st.session_state.item, st.session_state.speed, st.session_state.siklus, st.session_state.filler, 7)
    bt = st.selectbox("⚙ Bt", bt_options, index=bt_options.index(st.session_state.bt) if st.session_state.bt in bt_options else 0)
    if bt != st.session_state.bt:
        st.session_state.bt = bt
        st.session_state.spk_value = ""

    # SPK
    spk_options = filter_by_spk(data_clean, st.session_state.line, st.session_state.item, st.session_state.speed, st.session_state.siklus, st.session_state.filler, st.session_state.bt, 8)
    spk = st.selectbox("📄 SPK", spk_options, index=spk_options.index(st.session_state.spk_value) if st.session_state.spk_value in spk_options else 0)
    if spk != st.session_state.spk_value:
        st.session_state.spk_value = spk
    
    # Keterangan 
    ket = st.text_area("📝 Keterangan", value=row.get("Keterangan", ""), height=100)

    # Kendala
    kendala = st.text_area("🚧 Kendala", value=row.get("Kendala", ""), height=100)

    # Final row setelah edit
    updated_row = {
        "Nomor SPK": nomor_spk,
        "Tanggal": tanggal,
        "Waktu Mulai": start_time,
        "Waktu Selesai": stop_time,
        "Operator": st.session_state.operator, 
        "Line": st.session_state.line,
        "Item": st.session_state.item,
        "Speed (kg/jam)": st.session_state.speed,
        "Siklus (kg)": st.session_state.siklus,
        "Filler": st.session_state.filler,
        "Bt": st.session_state.bt,
        "SPK": st.session_state.spk_value,
        'Keterangan': ket,
        'Kendala': kendala
    }

    # Checkbox untuk konfirmasi update
    confirm_update = st.checkbox("Saya yakin ingin memperbarui data.")

    # Tombol update hanya aktif jika checkbox dicentang
    if st.button("💾 Simpan Perubahan", disabled=not confirm_update):
        result = update_data(updated_row)
        if result.get("status") == "success":
            st.toast("Data berhasil diperbarui!", icon="✅")
            tm.sleep(2)
            st.session_state["editing"] = False
            st.rerun()
        else:
            st.error("Gagal memperbarui data. Silakan coba lagi.")