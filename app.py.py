import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Настройка страницы
st.set_page_config(page_title="Car Calc Live", layout="wide")
st.title("📊 КАЛЬКУЛЯТОР (LIVE ИЗ GOOGLE TABLES)")

# Ссылка на твою таблицу
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

# Создаем подключение
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)  # Данные обновляются раз в минуту
def load_live_data():
    # Читаем лист TOW (логистика по США)
    df_t = conn.read(spreadsheet=spreadsheet_url, worksheet="TOW")
    # Читаем лист Freight1 (море)
    df_f = conn.read(spreadsheet=spreadsheet_url, worksheet="Freight1", header=None)
    return df_t, df_f

df_tow, df_freight = load_live_data()

# --- ИНТЕРФЕЙС (БОКОВАЯ ПАНЕЛЬ) ---
with st.sidebar:
    st.header("📥 ВВОД ДАННЫХ")
    bid = st.number_input("СТАВКА ($)", value=10000)
    car_year = st.number_input("ГОД ВЫПУСКА", 2010, 2026, 2022)
    engine = st.number_input("ОБЪЕМ (см³)", 0, 6000, 2000)
    
    if not df_tow.empty:
        # Убираем пустые значения из списка городов
        loc_list = sorted([x for x in df_tow['Loaction'].unique() if pd.notna(x)])
        loc = st.selectbox("ЛОКАЦИЯ АУКЦИОНА", loc_list)
    
    body = st.radio("ТИП КУЗОВА", ["Легковая (Седан)", "SUV / Кроссовер"])
    fuel = st.selectbox("ТОПЛИВО", ["GAS", "EV", "HYB", "DIESEL"])
    dest = st.selectbox("ПОРТ НАЗНАЧЕНИЯ", ["Odesa", "Constanta", "Klaipeda"])

# --- ЛОГИКА РАСЧЕТА ---
inland, us_port = 0, "NJ"
if not df_tow.empty and loc:
    row = df_tow[df_tow['Loaction'] == loc].iloc[0]
    ports = {'NJ': 'NJ', 'GA': 'GA', 'TX': 'TX', 'CA': 'CA', 'WA': 'WA'}
    valid_costs = {}
    for p_code, p_name in ports.items():
        try:
            val = row[p_code]
            if pd.notna(val) and str(val).lower() != 'error':
                valid_costs[p_code] = float(str(val).replace('$', '').replace(',', ''))
        except: continue
    if valid_costs:
        us_port = min(valid_costs, key=valid_costs.get)
        inland = valid_costs[us_port]

# Поиск моря (учитываем формулы из таблицы)
ocean = 0
try:
    # Находим строку порта (напр. Odesa)
    start_idx = df_freight[df_freight[0].str.contains(dest, case=False, na=False)].index[0]
    header = df_freight.iloc[start_idx].tolist()
    
    c_idx = -1
    for i, h in enumerate(header):
        if str(h).strip().upper() == us_port:
            c_idx = i; break
            
    if c_idx != -1:
        target_fuel = fuel if "Легковая" in body else f"{fuel} SUV"
        for k in range(start_idx + 1, start_idx + 25):
            if target_fuel in str(df_freight.iloc[k, 0]).upper():
                val = df_freight.iloc[k, c_idx]
                if pd.notna(val) and str(val).strip() != '':
                    ocean = float(str(val).replace('$', '').replace(',', ''))
                    break
except: pass

# --- ВЫВОД ---
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("ГОД", car_year)
c2.metric("ДВИГАТЕЛЬ", f"{engine} см³")
c3.metric("ПОРТ США", us_port)
c4.metric("СУША (Inland)", f"${inland}")

if ocean > 0:
    st.success(f"### МОРЕ ДО {dest.upper()}: ${ocean}")
else:
    st.warning(f"### МОРЕ: ДАННЫЕ В ТАБЛИЦЕ НЕ НАЙДЕНЫ ({us_port} -> {dest})")

st.divider()
st.header(f"💰 ИТОГО ДОСТАВКА: ${inland + ocean:,.0f}")

if st.button("🔄 Обновить данные из таблицы сейчас"):
    st.cache_data.clear()
    st.rerun()
