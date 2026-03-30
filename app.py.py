import streamlit as st
import pandas as pd

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="Car Calc Live", layout="wide")
st.title("🚗 КАЛЬКУЛЯТОР ДОСТАВКИ (LIVE GOOGLE SHEETS)")

# Твоя ссылка на таблицу
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso/edit?usp=sharing"

# 2. ФУНКЦИЯ ЗАГРУЗКИ (ТОЛЬКО ИЗ GOOGLE)
@st.cache_data(ttl=60)
def load_from_google(url):
    # Превращаем ссылку в формат для экспорта конкретных листов в CSV
    base_url = url.split('/edit')[0]
    tow_link = f"{base_url}/gviz/tq?tqx=out:csv&sheet=TOW"
    freight_link = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Freight1"
    
    # Читаем данные. Если в ячейках ошибки формул (#VALUE!), pandas воспримет их как пустоту
    df_t = pd.read_csv(tow_link)
    df_f = pd.read_csv(freight_link, header=None)
    return df_t, df_f

try:
    df_tow, df_freight = load_from_google(GSHEET_URL)
    st.success("✅ Данные синхронизированы с Google Таблицей")
except Exception as e:
    st.error(f"❌ Ошибка подключения. Проверь доступ к таблице. Техническая инфо: {e}")
    st.stop()

# 3. БОКОВАЯ ПАНЕЛЬ (ВВОД)
with st.sidebar:
    st.header("📋 ПАРАМЕТРЫ")
    bid = st.number_input("Ставка на аукционе ($)", value=5000, step=500)
    
    # Список городов из колонки 'Loaction' (лист TOW)
    if 'Loaction' in df_tow.columns:
        locations = sorted([str(x) for x in df_tow['Loaction'].unique() if pd.notna(x) and str(x).strip() != ''])
        loc = st.selectbox("Локация (Город)", locations)
    else:
        st.error("В таблице TOW не найдена колонка 'Loaction'")
        st.stop()
        
    body = st.radio("Тип кузова", ["Легковая (Седан/Хэтч)", "Кроссовер (SUV/Внедорожник)"])
    fuel = st.selectbox("Топливо", ["GAS", "EV", "HYB", "DIESEL"])
    dest = st.selectbox("Порт назначения", ["Odesa", "Constanta", "Klaipeda"])

# 4. ЛОГИКА РАСЧЕТА
inland, ocean, us_port = 0.0, 0.0, "NJ"

# А. Считаем СУШУ (TOW)
try:
    row = df_tow[df_tow['Loaction'] == loc].iloc[0]
    # Ищем самый дешевый порт среди NJ, GA, TX, CA, WA
    port_costs = {}
    for p in ['NJ', 'GA', 'TX', 'CA', 'WA']:
        val = str(row.get(p, '')).replace('$', '').replace(',', '').strip()
        # Если в ячейке число, берем его
        if val and val.replace('.', '', 1).isdigit():
            port_costs[p] = float(val)
    
    if port_costs:
        us_port = min(port_costs, key=port_costs.get)
        inland = port_costs[us_port]
except:
    st.warning(f"Не удалось рассчитать сушу для {loc}")

# Б. Считаем МОРЕ (Freight1)
try:
    # Ищем строку с названием порта назначения
    target_dest = dest.strip().upper()
    s_idx = df_freight[df_freight[0].astype(str).str.upper().str.contains(target_dest, na=False)].index[0]
    
    # Ищем колонку с портом отправки в этой строке
    header_row = df_freight.iloc[s_idx].tolist()
    c_idx = -1
    for i, h in enumerate(header_row):
        if str(h).strip().upper() == us_port.upper():
            c_idx = i
            break
            
    if c_idx != -1:
        # Определяем тип топлива для поиска
        search_fuel = fuel.upper() if "Легковая" in body else f"{fuel.upper()} SUV"
        
        # Проверяем 20 строк ниже заголовка порта
        for k in range(s_idx + 1, s_idx + 21):
            label = str(df_freight.iloc[k, 0]).strip().upper()
            if search_fuel in label:
                price_raw = str(df_freight.iloc[k, c_idx]).replace('$', '').replace(',', '').strip()
                if price_raw and price_raw.replace('.', '', 1).isdigit():
                    ocean = float(price_raw)
                break
except:
    ocean = 0.0

# 5. ВЫВОД РЕЗУЛЬТАТОВ
st.divider()
col1, col2, col3 = st.columns(3)

col1.metric("ПОРТ ОТПРАВКИ", us_port)
col2.metric("СУША (Inland)", f"${inland:,.0f}")
if ocean > 0:
    col3.metric("МОРЕ (Ocean)", f"${ocean:,.0f}")
else:
    col3.error("МОРЕ: Данные не найдены")

st.divider()
total_delivery = inland + ocean
st.header(f"💰 ИТОГО ДОСТАВКА: ${total_delivery:,.0f}")
st.info(f"Маршрут: {loc} ➔ {us_port} ➔ {dest}")

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
    st.cache_data.clear()
    st.rerun()
