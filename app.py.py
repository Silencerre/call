import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Calc Live", layout="wide")
st.title("🚗 ВАШ КАЛЬКУЛЯТОР (LIVE ИЗ ТАБЛИЦЫ)")

# Ссылка на твою таблицу
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

@st.cache_data(ttl=5)
def load_full_data(url):
    base = url.split('/edit')[0]
    # Загружаем листы целиком
    tow_url = f"{base}/gviz/tq?tqx=out:csv&sheet=TOW"
    freight_url = f"{base}/gviz/tq?tqx=out:csv&sheet=Freight1"
    return pd.read_csv(tow_url), pd.read_csv(freight_url, header=None)

try:
    df_t, df_f = load_full_data(GSHEET_URL)
    st.success("✅ Соединение с таблицей установлено. Считаю по вашим формулам.")
except:
    st.error("❌ Ошибка доступа к Google Sheets")
    st.stop()

# --- ИНТЕРФЕЙС (ТОЛЬКО ВВОД) ---
with st.sidebar:
    st.header("📥 ВВОД ДАННЫХ")
    
    # 1. Выбор локации (берем из TOW)
    loc_list = sorted([str(x).strip() for x in df_t['Loaction'].unique() if pd.notna(x)])
    user_loc = st.selectbox("Локация аукциона", loc_list)
    
    # 2. Параметры для фильтрации
    user_body = st.radio("Тип кузова", ["Легковая", "SUV"])
    user_fuel = st.selectbox("Топливо", ["GAS", "EV", "HYB", "DIESEL"])
    user_dest = st.selectbox("Порт назначения", ["Odesa", "Constanta", "Klaipeda"])

# --- ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ (БЕРЕМ ТОЛЬКО ГОТОВЫЕ ЦИФРЫ) ---

# Вычисляем, какой порт США выбрала твоя таблица (самый дешевый)
row_t = df_t[df_t['Loaction'].str.strip() == user_loc].iloc[0]
costs = {}
for p in ['NJ','GA','TX','CA','WA']:
    v = str(row_t.get(p, '')).replace('$','').replace(',','').strip()
    if v.replace('.','',1).isdigit(): costs[p] = float(v)

selected_port = min(costs, key=costs.get) if costs else "NJ"
inland_val = costs[selected_port] if costs else 0

# Ищем итоговую ячейку МОРЯ на листе Freight1
ocean_val = 0
try:
    f_df = df_f.fillna('').astype(str)
    # Находим строку с портом (Odesa и т.д.)
    s_idx = f_df[f_df[0].str.strip().str.upper() == user_dest.upper()].index[0]
    # Находим колонку порта США в этой же строке
    header_row = f_df.iloc[s_idx].str.strip().str.upper().tolist()
    c_idx = header_row.index(selected_port.upper())
    
    # Ищем строку с нужным топливом ниже
    target_text = user_fuel.upper() if user_body == "Легковая" else f"{user_fuel.upper()} SUV"
    for k in range(s_idx + 1, s_idx + 30):
        if f_df.iloc[k, 0].strip().upper() == target_text:
            raw_price = f_df.iloc[k, c_idx].replace('$','').replace(',','').strip()
            if raw_price.replace('.','',1).isdigit():
                ocean_val = float(raw_price)
            break
except:
    pass

# --- ФИНАЛЬНЫЙ ЭКРАН ---
st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📍 МАРШРУТ")
    st.info(f"{user_loc} ➔ {selected_port}")

with c2:
    st.subheader("🚛 СУША")
    st.metric(label="Цена из TOW", value=f"${inland_val:,.0f}")

with c3:
    st.subheader("🚢 МОРЕ")
    if ocean_val > 0:
        st.metric(label=f"До {user_dest}", value=f"${ocean_val:,.0f}")
    else:
        st.error("Нет цены в таблице")

st.divider()
st.success(f"### 💰 ИТОГО ДОСТАВКА (РЕЗУЛЬТАТ ТАБЛИЦЫ): ${inland_val + ocean_val:,.0f}")

if st.button("🔄 ОБНОВИТЬ ЦЕНЫ ИЗ ГУГЛ ТАБЛИЦЫ"):
    st.cache_data.clear()
    st.rerun()
