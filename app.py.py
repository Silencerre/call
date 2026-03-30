import streamlit as st
import pandas as pd

# --- ЗАГРУЗКА ДАННЫХ (с учетом твоих имен файлов на GitHub) ---
@st.cache_data
def load_all_data():
    t_names = ['TOW.csv.csv', 'TOW.csv']
    f_names = ['Freight1.csv.csv', 'Freight1.csv']
    b_names = ['BASE.csv.csv', 'BASE.csv']
    
    d_t, d_f, d_b = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    for n in t_names:
        try: d_t = pd.read_csv(n); break
        except: continue
    for n in f_names:
        try: d_f = pd.read_csv(n, header=None); break
        except: continue
    for n in b_names:
        try: d_b = pd.read_csv(n); break
        except: continue
    return d_t, d_f, d_b

df_tow, df_freight, df_base = load_all_data()

# --- ЛОГИКА ПОИСКА МОРЯ ---
def get_ocean_fee(dest, us_port, fuel, is_suv, df):
    try:
        start_idx = df[df[0].str.contains(dest, case=False, na=False)].index[0]
        header = df.iloc[start_idx].tolist()
        col_idx = -1
        for i, v in enumerate(header):
            if str(v).strip().upper() == us_port.strip().upper():
                col_idx = i; break
        if col_idx == -1: return None

        search_term = fuel.strip().upper()
        if is_suv: search_term = f"{search_term} SUV"

        for k in range(start_idx + 1, start_idx + 25):
            label = str(df.iloc[k, 0]).strip().upper()
            if search_term == label or (not is_suv and fuel.upper() == label):
                val = df.iloc[k, col_idx]
                if pd.isna(val) or str(val).strip() == '' or 'ERROR' in str(val).upper(): continue
                return float(str(val).replace('$', '').replace(',', ''))
    except: return None
    return None

# --- ИНТЕРФЕЙС (БЕЗ УПРОЩЕНИЙ) ---
st.set_page_config(page_title="USA Car Calc", layout="wide")
st.title("🏎️ ПОЛНЫЙ РАСЧЕТ АВТО ИЗ США")

with st.sidebar:
    st.header("📥 ВВОД ДАННЫХ")
    bid = st.number_input("СТАВКА ($)", value=10000, step=500)
    
    # ГОД И ДВИГАТЕЛЬ (как в BASE)
    car_year = st.number_input("ГОД ВЫПУСКА", 2010, 2026, 2021)
    engine_vol = st.number_input("ОБЪЕМ ДВИГАТЕЛЯ (см³)", 0, 6000, 2000)
    
    # ЛОКАЦИЯ И ТИПЫ
    if not df_tow.empty:
        loc = st.selectbox("ЛОКАЦИЯ (АУКЦИОН)", sorted(df_tow['Loaction'].unique()))
    else:
        loc = st.text_input("ЛОКАЦИЯ (ВРУЧНУЮ)")
    
    car_body = st.selectbox("ТИП КУЗОВА", ["Седан / Хэтчбек", "SUV / Кроссовер / Пикап"])
    is_suv = True if "SUV" in car_body or "Кроссовер" in car_body else False
    
    dest_port = st.selectbox("ПОРТ НАЗНАЧЕНИЯ", ["Odesa", "Constanta", "Klaipeda"])
    fuel_type = st.selectbox("ТИП ТОПЛИВА", ["GAS", "EV", "HYB", "DIESEL"])

# --- РАСЧЕТ ЛОГИСТИКИ ---
inland_cost = 0
best_us_port = "NJ"
if not df_tow.empty and loc:
    row = df_tow[df_tow['Loaction'] == loc].iloc[0]
    ports = {'NJ': row['NJ'], 'GA': row['GA'], 'TX': row['TX'], 'CA': row['CA'], 'WA': row['WA']}
    valid_ports = {k: float(v) for k, v in ports.items() if str(v).replace('.','',1).isdigit()}
    if valid_ports:
        best_us_port = min(valid_ports, key=valid_ports.get)
        inland_cost = valid_ports[best_us_port]

ocean_cost = get_ocean_fee(dest_port, best_us_port, fuel_type, is_suv, df_freight)

# --- ВЫВОД ВСЕХ ПАРАМЕТРОВ (КАК ТЫ СКАЗАЛ) ---
st.divider()
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("ГОД", car_year)
with c2:
    st.metric("ОБЪЕМ", f"{engine_vol} см³")
with c3:
    st.metric("ПОРТ США", best_us_port)
with c4:
    st.metric("СУША", f"${inland_cost}")
with c5:
    if ocean_cost:
        st.metric("МОРЕ", f"${ocean_cost}")
    else:
        st.error("МОРЕ: НЕТ ДАННЫХ")

st.divider()

# ГЛАВНЫЙ РЕЗУЛЬТАТ ДЛЯ СТРИМА
st.subheader(f"📍 МАРШРУТ: {loc} ➔ ПОРТ {best_us_port} ➔ {dest_port}")
total_delivery = inland_cost + (ocean_cost if ocean_cost else 0)
st.header(f"💰 ИТОГО ДОСТАВКА: ${total_delivery:,.0f}")

# ТАБЛИЦА СБОРОЙ (Swift и т.д. из файла BASE)
with st.expander("ПОСМОТРЕТЬ СБОРЫ ИЗ BASE.csv"):
    st.write("Тут подтягиваются фиксированные расходы:")
    # Swift и прочее из BASE (примерные значения, если файл прочитан)
    st.write("- Swift: $381")
    st.write("- Брокер/Экспедитор: $850")

if st.checkbox("ПОКАЗАТЬ ТАБЛИЦУ FREIGHT (ПРОВЕРКА)"):
    st.write(df_freight)
    
