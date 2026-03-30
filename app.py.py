import streamlit as st
import pandas as pd

# Попытка импорта с проверкой
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

st.set_page_config(page_title="Car Calc Live", layout="wide")

if not HAS_GSHEETS:
    st.error("⏳ Библиотека еще устанавливается на сервере. Подожди 1-2 минуты и обнови страницу.")
    st.info("Убедись, что в requirements.txt написано: st-gsheets-connection")
    st.stop()

# --- ОСНОВНОЙ КОД ---
st.title("📊 КАЛЬКУЛЯТОР (LIVE GOOGLE SHEETS)")

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_live_data():
    # Читаем листы
    df_t = conn.read(spreadsheet=spreadsheet_url, worksheet="TOW")
    df_f = conn.read(spreadsheet=spreadsheet_url, worksheet="Freight1", header=None)
    return df_t, df_f

try:
    df_tow, df_freight = load_live_data()
    st.success("✅ Данные из Google Таблицы успешно загружены!")
except Exception as e:
    st.error(f"❌ Не удалось подключиться к таблице. Проверь, что доступ открыт 'Всем, у кого есть ссылка'.")
    st.stop()

# --- ДАЛЬШЕ ИДЕТ ТВОЙ ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("📥 ВВОД ДАННЫХ")
    bid = st.number_input("СТАВКА ($)", value=10000)
    car_year = st.number_input("ГОД ВЫПУСКА", 2010, 2026, 2022)
    
    # Очистка списка локаций от пустых строк
    loc_list = sorted([str(x) for x in df_tow['Loaction'].unique() if pd.notna(x) and str(x).strip() != ''])
    loc = st.selectbox("ЛОКАЦИЯ АУКЦИОНА", loc_list)
    
    body = st.radio("ТИП КУЗОВА", ["Легковая (Седан)", "SUV / Кроссовер"])
    fuel = st.selectbox("ТОПЛИВО", ["GAS", "EV", "HYB", "DIESEL"])
    dest = st.selectbox("ПОРТ НАЗНАЧЕНИЯ", ["Odesa", "Constanta", "Klaipeda"])

# Расчет логики (Суша и Море)
# ... (тот же код расчета, что был выше) ...

# ВЫВОД РЕЗУЛЬТАТОВ
st.divider()
total_delivery = 0 # Тут будет сумма inland + ocean
# (Блок отображения метрик)

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ ИЗ ТАБЛИЦЫ"):
    st.cache_data.clear()
    st.rerun()
