import streamlit as st
import pandas as pd

# Настройка страницы
st.set_page_config(page_title="Car Calc Live", layout="wide")
st.title("📊 КАЛЬКУЛЯТОР (LIVE)")

# Твоя ссылка
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

# Функция для прямого чтения (если gsheets_connection тупит)
@st.cache_data(ttl=60)
def load_data_direct(url):
    # Превращаем обычную ссылку в прямую ссылку на скачивание CSV для каждого листа
    tow_url = url.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=TOW')
    freight_url = url.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv&sheet=Freight1')
    
    df_t = pd.read_csv(tow_url)
    df_f = pd.read_csv(freight_url, header=None)
    return df_t, df_f

try:
    df_tow, df_freight = load_data_direct(GSHEET_URL)
    st.success("✅ Соединение установлено!")
except Exception as e:
    st.error(f"❌ Ошибка доступа! Убедись, что доступ 'Все, у кого есть ссылка'. Текст ошибки: {e}")
    st.stop()

# --- ВВОД ДАННЫХ ---
with st.sidebar:
    st.header("📥 ПАРАМЕТРЫ")
    bid = st.number_input("СТАВКА ($)", value=10000)
    loc_list = sorted([str(x) for x in df_tow['Loaction'].unique() if pd.notna(x)])
    loc = st.selectbox("ЛОКАЦИЯ", loc_list)
    body = st.radio("КУЗОВ", ["Легковая", "SUV / Кроссовер"])
    fuel = st.selectbox("ТОПЛИВО", ["GAS", "EV", "HYB", "DIESEL"])
    dest = st.selectbox("ПОРТ", ["Odesa", "Constanta", "Klaipeda"])

# --- ЛОГИКА ---
# Ищем цену суши
row = df_tow[df_tow['Loaction'] == loc].iloc[0]
valid_ports = {p: float(str(row[p]).replace('$','').replace(',','')) for p in ['NJ','GA','TX','CA','WA'] if pd.notna(row[p]) and str(row[p]).replace('.','').isdigit()}

if valid_ports:
    us_port = min(valid_ports, key=valid_ports.get)
    inland = valid_ports[us_port]
    
    # Ищем море
    ocean = 0
    try:
        s_idx = df_freight[df_freight[0].str.contains(dest, case=False, na=False)].index[0]
        target = fuel if "Легковая" in body else f"{fuel} SUV"
        # Ищем колонку порта
        header = df_freight.iloc[s_idx].tolist()
        c_idx = -1
        for i, h in enumerate(header):
            if str(h).strip().upper() == us_port:
                c_idx = i; break
        
        if c_idx != -1:
            for k in range(s_idx + 1, s_idx + 20):
                if target in str(df_freight.iloc[k, 0]).upper():
                    ocean = float(str(df_freight.iloc[k, c_idx]).replace('$','').replace(',',''))
                    break
    except: pass

    # --- ВЫВОД ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("ПОРТ США", us_port)
    c2.metric("СУША", f"${inland}")
    c3.metric("МОРЕ", f"${ocean}")
    
    st.header(f"💰 ИТОГО ДОСТАВКА: ${inland + ocean}")
else:
    st.warning("Нет цен для этой локации")

if st.button("🔄 ОБНОВИТЬ"):
    st.cache_data.clear()
    st.rerun()
