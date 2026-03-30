import streamlit as st
import pandas as pd
import datetime

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="USA Car Calc", page_icon="🚢", layout="wide")

@st.cache_data
def load_all_data():
    try:
        df_tow = pd.read_csv('TOW.csv')
        # Читаем Freight как текст, чтобы проще искать блоки (Constanta, Odesa...)
        with open('Freight1.csv', 'r', encoding='utf-8') as f:
            freight_lines = [line.strip().split(',') for line in f.readlines()]
        return df_tow, freight_lines
    except Exception as e:
        st.error(f"Ошибка загрузки файлов: {e}")
        return pd.DataFrame(), []

df_tow, freight_raw = load_all_data()

# --- ФУНКЦИЯ ПОИСКА МОРЯ (FREIGHT) ---
def get_ocean_cost(dest_port, us_port, fuel_type, raw_data):
    # Упрощенный поиск по строкам файла Freight1.csv
    try:
        start_row = -1
        # Ищем начало блока порта (напр. "Odesa")
        for i, line in enumerate(raw_data):
            if dest_port.lower() in line[0].lower():
                start_row = i
                break
        
        if start_row == -1: return 0
        
        # Определяем индекс колонки порта США (NJ, GA, TX...)
        header = raw_data[start_row]
        col_idx = -1
        for j, h in enumerate(header):
            if us_port.upper() in h.upper():
                col_idx = j
                break
        
        if col_idx == -1: return 0

        # Ищем строку с типом топлива ниже заголовка
        for k in range(start_row + 1, start_row + 15):
            if fuel_type.upper() in raw_data[k][0].upper():
                val = raw_data[k][col_idx]
                return float(val) if val and val != 'Error' else 0
    except:
        return 0
    return 0

# --- ИНТЕРФЕЙС ---
st.title("🚗 Калькулятор авто из США (Full Data Sync)")

with st.sidebar:
    st.header("📋 Параметры")
    bid = st.number_input("Ставка ($)", value=8000, step=500)
    
    if not df_tow.empty:
        loc = st.selectbox("Локация аукциона", sorted(df_tow['Loaction'].unique()))
    else:
        loc = st.text_input("Локация")
        
    dest = st.selectbox("Порт назначения", ["Constanta", "Odesa", "Klaipeda"])
    
    # Сопоставляем типы топлива с названиями в твоем Freight1.csv
    fuel_map = {"Бензин": "GAS", "Дизель": "DIESEL", "Электро": "EV", "Гибрид": "HYB"}
    fuel_ui = st.selectbox("Тип топлива", list(fuel_map.keys()))
    fuel_code = fuel_map[fuel_ui]
    
    car_year = st.number_input("Год", 2010, 2025, 2020)
    engine = st.number_input("Объем (см³)", 500, 6000, 2000)

# --- РАСЧЕТ ---
# 1. Суша и выбор порта США
inland_cost = 0
best_us_port = "NJ" # По умолчанию
if not df_tow.empty and loc:
    row = df_tow[df_tow['Loaction'] == loc].iloc[0]
    prices = {'NJ': row['NJ'], 'GA': row['GA'], 'TX': row['TX'], 'CA': row['CA'], 'WA': row['WA']}
    valid = {k: float(v) for k, v in prices.items() if str(v).replace('.','',1).isdigit()}
    if valid:
        best_us_port = min(valid, key=valid.get)
        inland_cost = valid[best_us_port]

# 2. Море из Freight1.csv
ocean_cost = get_ocean_cost(dest, best_us_port, fuel_code, freight_raw)

# 3. Налоги и сборы (из BASE.csv логики)
auction_fee = bid * 0.12 # Усредненный сбор
swift = 381
broker_exp = 850
customs = (bid * 0.1) + (engine/1000 * 50 * (2025-car_year)) + (bid * 0.2) # Примерная формула

total = bid + auction_fee + inland_cost + ocean_cost + swift + broker_exp + customs

# --- ОТОБРАЖЕНИЕ ---
c1, c2, c3 = st.columns(3)
c1.metric("ИТОГО (All In)", f"${total:,.0f}")
c2.metric("Доставка (Суша + Море)", f"${(inland_cost + ocean_cost):,.0f}")
c3.metric("Растаможка", f"${customs:,.0f}")

st.divider()
st.subheader("🔍 Детализация маршрута")
st.write(f"**Аукцион:** {loc} ➔ **Порт США:** {best_us_port} ➔ **Назначение:** {dest}")

with st.expander("Посмотреть все расходы"):
    df_res = pd.DataFrame({
        "Статья": ["Авто", "Аукцион", "Суша (TOW)", "Море (Freight)", "Растаможка", "Прочее"],
        "Сумма": [bid, auction_fee, inland_cost, ocean_cost, customs, swift + broker_exp]
    })
    st.table(df_res)