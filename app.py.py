import streamlit as st
import pandas as pd

# 1. Загрузка данных с учетом твоих названий на GitHub
@st.cache_data
def load_all_data():
    try:
        # Пытаемся прочитать файлы с двойным расширением, как на твоем скрине
        df_tow = pd.read_csv('TOW.csv.csv')
        df_freight = pd.read_csv('Freight1.csv.csv', header=None)
        return df_tow, df_freight
    except:
        try:
            # Если переименуешь обратно, этот блок сработает для обычных названий
            df_tow = pd.read_csv('TOW.csv')
            df_freight = pd.read_csv('Freight1.csv', header=None)
            return df_tow, df_freight
        except Exception as e:
            st.error(f"Файлы не найдены! Проверь названия на GitHub. Ошибка: {e}")
            return pd.DataFrame(), pd.DataFrame()

df_tow, df_freight = load_all_data()

# 2. Улучшенная логика поиска моря
def get_ocean_fee(dest, us_port, fuel, is_suv, df):
    try:
        # Находим строку с портом (Odesa, Constanta и т.д.)
        start_idx = df[df[0].str.contains(dest, case=False, na=False)].index[0]
        header_row = df.iloc[start_idx].tolist()
        
        # Ищем колонку порта США
        col_idx = -1
        for i, val in enumerate(header_row):
            if str(val).strip().upper() == us_port.strip().upper():
                col_idx = i
                break
        
        if col_idx == -1: return None

        # Формируем ключ для поиска (GAS, GAS SUV, EV и т.д.)
        search_term = fuel.strip().upper()
        if is_suv:
            search_term = f"{search_term} SUV"

        # Ищем значение в строках ниже порта
        for k in range(start_idx + 1, start_idx + 20):
            row_label = str(df.iloc[k, 0]).strip().upper()
            if search_term == row_label or (not is_suv and search_term in row_label):
                price = df.iloc[k, col_idx]
                if pd.isna(price) or str(price).strip() == '' or 'ERROR' in str(price).upper():
                    continue # Ищем дальше, если пустая ячейка
                return float(str(price).replace('$', '').replace(',', ''))
    except:
        return None
    return None

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="USA Car Calc", layout="wide")
st.title("🏎️ Калькулятор доставки из США")

with st.sidebar:
    st.header("Настройки")
    bid = st.number_input("Ставка на аукционе $", value=5000)
    
    # Выбор кузова (Легковая или Кроссовер)
    car_body = st.radio("Тип кузова", ["Легковая (Седан/Хэтч)", "Кроссовер (SUV/Внедорожник)"])
    is_suv = True if "Кроссовер" in car_body else False
    
    if not df_tow.empty:
        loc = st.selectbox("Локация (Город)", sorted(df_tow['Loaction'].unique()))
    
    dest = st.selectbox("Порт назначения", ["Odesa", "Constanta", "Klaipeda"])
    fuel = st.selectbox("Топливо", ["GAS", "EV", "HYB", "DIESEL"])

# РАСЧЕТЫ
inland = 0
us_port = "NJ"
if not df_tow.empty and loc:
    row = df_tow[df_tow['Loaction'] == loc].iloc[0]
    prices = {'NJ': row['NJ'], 'GA': row['GA'], 'TX': row['TX'], 'CA': row['CA'], 'WA': row['WA']}
    valid = {k: float(v) for k, v in prices.items() if str(v).replace('.','',1).isdigit()}
    if valid:
        us_port = min(valid, key=valid.get)
        inland = valid[us_port]

ocean = get_ocean_fee(dest, us_port, fuel, is_suv, df_freight)

# ВЫВОД РЕЗУЛЬТАТОВ
st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Суша (Inland)", f"${inland}")
    st.caption(f"Через порт: {us_port}")

with c2:
    if ocean:
        st.metric("Море (Ocean)", f"${ocean}")
    else:
        st.error("Море: Данные не найдены")
        st.caption("Проверь Freight1.csv")

with c3:
    # Примерная сумма (можешь добавить свои сборы)
    total = bid + inland + (ocean if ocean else 0)
    st.metric("ИТОГО (без растаможки)", f"${total:,.0f}")

# ОТЛАДКА (только если нужно проверить, что видит программа)
if st.checkbox("Показать таблицу Freight для проверки"):
    st.write(df_freight)
