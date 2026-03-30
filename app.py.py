import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Calc Live", layout="wide")
st.title("🚗 КАЛЬКУЛЯТОР ДОСТАВКИ (Odesa Edition)")

GSHEET_URL = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

@st.cache_data(ttl=10) # Сократил время кэша до 10 сек для тестов
def load_data(url):
    base = url.split('/edit')[0]
    t_url = f"{base}/gviz/tq?tqx=out:csv&sheet=TOW"
    f_url = f"{base}/gviz/tq?tqx=out:csv&sheet=Freight1"
    return pd.read_csv(t_url), pd.read_csv(f_url, header=None)

try:
    df_t, df_f = load_data(GSHEET_URL)
    st.success("✅ Данные загружены")
except:
    st.error("❌ Ошибка связи с Google Sheets")
    st.stop()

with st.sidebar:
    st.header("📋 ПАРАМЕТРЫ")
    bid = st.number_input("Ставка ($)", value=1000)
    
    # Города из TOW
    locs = sorted([str(x).strip() for x in df_t['Loaction'].unique() if pd.notna(x)])
    loc = st.selectbox("Локация аукциона", locs)
    
    body = st.radio("Кузов", ["Легковая", "SUV"])
    fuel = st.selectbox("Топливо", ["GAS", "EV", "HYB", "DIESEL"])
    # ТУТ ТЕПЕРЬ СТРОГО Odesa
    dest = st.selectbox("Порт назначения", ["Odesa", "Constanta", "Klaipeda"])

# --- РАСЧЕТ СУШИ ---
inland, us_port = 0.0, "NJ"
row = df_t[df_t['Loaction'].str.strip() == loc].iloc[0]
costs = {}
for p in ['NJ','GA','TX','CA','WA']:
    v = str(row.get(p, '')).replace('$','').replace(',','').strip()
    if v.replace('.','',1).isdigit(): 
        costs[p] = float(v)

if costs:
    us_port = min(costs, key=costs.get)
    inland = costs[us_port]

# --- РАСЧЕТ МОРЯ (СТРОГАЯ ЛОГИКА) ---
ocean = 0.0
try:
    # 1. Очищаем таблицу от пробелов для поиска
    f_df = df_f.fillna('').astype(str)
    
    # 2. Ищем СТРОКУ, где написано Odesa (или что выбрано)
    # Ищем точное совпадение в первой колонке
    s_idx = -1
    for i, val in enumerate(f_df[0]):
        if val.strip().upper() == dest.strip().upper():
            s_idx = i
            break
            
    if s_idx != -1:
        # 3. Ищем КОЛОНКУ порта (NJ, CA и т.д.) в найденной строке
        header_row = f_df.iloc[s_idx].str.strip().str.upper().tolist()
        c_idx = -1
        if us_port.upper() in header_row:
            c_idx = header_row.index(us_port.upper())
            
        if c_idx != -1:
            # 4. Ищем ТИП ТОПЛИВА ниже по строкам
            target = fuel.upper() if body == "Легковая" else f"{fuel.upper()} SUV"
            
            for k in range(s_idx + 1, s_idx + 25):
                row_label = f_df.iloc[k, 0].strip().upper()
                if target == row_label: # Строгое сравнение
                    price_raw = f_df.iloc[k, c_idx].replace('$','').replace(',','').strip()
                    if price_raw.replace('.','',1).isdigit():
                        ocean = float(price_raw)
                    break
except Exception as e:
    st.write(f"Ошибка поиска: {e}")

# --- ВЫВОД ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("ПОРТ США", us_port)
c2.metric("СУША (TOW)", f"${inland:,.0f}")
c3.metric("МОРЕ (FREIGHT)", f"${ocean:,.0f}" if ocean > 0 else "НЕТ ДАННЫХ")

st.divider()
st.header(f"💰 ИТОГО ДОСТАВКА: ${inland + ocean:,.0f}")

if st.button("🔄 ОБНОВИТЬ ИЗ ТАБЛИЦЫ"):
    st.cache_data.clear()
    st.rerun()
