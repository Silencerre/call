import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Calc", layout="wide")
st.title("🚗 ИНТЕРФЕЙС КАЛЬКУЛЯТОР (ДАННЫЕ ИЗ GOOGLE)")

# Ссылка на твою таблицу
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

@st.cache_data(ttl=5)
def load_sheets(url):
    base = url.split('/edit')[0]
    # Читаем листы как есть, со всеми результатами формул
    df_tow = pd.read_csv(f"{base}/gviz/tq?tqx=out:csv&sheet=TOW")
    df_freight = pd.read_csv(f"{base}/gviz/tq?tqx=out:csv&sheet=Freight1", header=None)
    return df_tow, df_freight

try:
    df_t, df_f = load_sheets(GSHEET_URL)
except:
    st.error("Ошибка связи. Проверь интернет и доступ к таблице.")
    st.stop()

# --- ТВОЙ ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("📥 ВВОД")
    # Локация из колонки Loaction
    loc_list = sorted([str(x).strip() for x in df_t['Loaction'].unique() if pd.notna(x)])
    u_loc = st.selectbox("ЛОКАЦИЯ", loc_list)
    
    u_body = st.radio("КУЗОВ", ["Легковая", "SUV"])
    u_fuel = st.selectbox("ТОПЛИВО", ["GAS", "EV", "HYB", "DIESEL"])
    u_dest = st.selectbox("ПОРТ ПРИБЫТИЯ", ["Odesa", "Constanta", "Klaipeda"])

# --- ПРОСТОЙ ПОИСК ЦИФРЫ В ТАБЛИЦЕ ---
inland_price = 0
port_usa = "NJ"
ocean_price = 0

# 1. Тянем сушу из TOW
row_t = df_t[df_t['Loaction'].str.strip() == u_loc].iloc[0]
possible_ports = ['NJ','GA','TX','CA','WA']
vals = {}
for p in possible_ports:
    raw = str(row_t.get(p, '0')).replace('$','').replace(',','').strip()
    if raw.replace('.','',1).isdigit():
        vals[p] = float(raw)

if vals:
    port_usa = min(vals, key=vals.get) # Самый дешевый порт
    inland_price = vals[port_usa]

# 2. Тянем море из Freight1 (строго по координатам)
try:
    # Чистим Freight от мусора для поиска
    f_clean = df_f.fillna('').astype(str).apply(lambda x: x.str.strip().str.upper())
    
    # Ищем строку порта (ODESA / CONSTANTA)
    s_idx = f_clean[f_clean[0] == u_dest.upper()].index[0]
    
    # Ищем колонку порта США (NJ / CA / TX) в этой же строке
    header = f_clean.iloc[s_idx].tolist()
    c_idx = header.index(port_usa.upper())
    
    # Ищем строку топлива под портом
    target = u_fuel.upper() if u_body == "Легковая" else f"{u_fuel.upper()} SUV"
    for k in range(s_idx + 1, s_idx + 30):
        if f_clean.iloc[k, 0] == target:
            res = df_f.iloc[k, c_idx]
            ocean_price = float(str(res).replace('$','').replace(',','').strip())
            break
except:
    ocean_price = 0

# --- ВЫВОД НА ЭКРАН ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric("СУША (TOW)", f"${inland_price:,.0f}")
    st.caption(f"Маршрут: {u_loc} -> {port_usa}")

with col2:
    if ocean_price > 0:
        st.metric("МОРЕ (FREIGHT)", f"${ocean_price:,.0f}")
    else:
        st.error("МОРЕ: Нет данных")

st.divider()
st.header(f"💰 ИТОГО: ${inland_price + ocean_price:,.0f}")

if st.button("🔄 ОБНОВИТЬ ИЗ GOOGLE"):
    st.cache_data.clear()
    st.rerun()
