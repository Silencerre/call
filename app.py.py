import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. КРАСИВАЯ ОБОЛОЧКА ---
st.set_page_config(page_title="Car Calc Premium", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 40px; color: #00FFCC; }
    .stNumberInput, .stSelectbox { border-radius: 10px; }
    .main-box { background: #1E1E1E; padding: 25px; border-radius: 15px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОДКЛЮЧЕНИЕ (Убедись, что JSON ключи в Secrets!) ---
def get_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    # Открываем твою таблицу
    return client.open_by_key("1SY-3dXz5trcG_t9vX1BWKtSAtVmBLHtwYz9bOEQNMso").sheet1

try:
    ws = get_sheet()
except Exception as e:
    st.error("Настрой Service Account в Secrets!")
    st.stop()

# --- 3. ИНТЕРФЕЙС КАК В ТАБЛИЦЕ ---
st.title("💎 CAR CALCULATOR INTERFACE")

with st.container():
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        bid = st.number_input("💵 СТАВКА ($)", value=1000, step=100)
        auction = st.selectbox("🏗️ АУКЦИОН", ["IAAI", "COPART"])
    with c2:
        loc = st.text_input("📍 ЛОКАЦИЯ", "ACE - Carson (CA)")
        model = st.text_input("🚗 МОДЕЛЬ", "2023")
    with c3:
        dest = st.selectbox("🚢 ПОРТ", ["Odesa", "Constanta", "Klaipeda"])
        fuel = st.selectbox("⛽ ТОПЛИВО", ["GAS", "EV", "HYB", "DIESEL"])
    with c4:
        body = st.selectbox("📦 КУЗОВ", ["SUV", "Седан"])
        vin = st.text_input("🔢 VIN (последние 4)", "0001")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. КНОПКА РАСЧЕТА ---
if st.button("🔄 ПОСЧИТАТЬ В ТАБЛИЦЕ"):
    with st.spinner('Записываю данные в Google Sheets...'):
        # ПИШЕМ ДАННЫЕ В ТВОИ ЯЧЕЙКИ (На основе твоего скрина)
        # B5 - Ставка, B4 - Локация, D4 - Порт, E4 - Кузов, F4 - Топливо
        updates = [
            {'range': 'B5', 'values': [[bid]]},
            {'range': 'B4', 'values': [[loc]]},
            {'range': 'D4', 'values': [[dest]]},
            {'range': 'E4', 'values': [[body]]},
            {'range': 'F4', 'values': [[fuel]]}
        ]
        ws.batch_update(updates)
        
        # ЧИТАЕМ ГОТОВЫЕ РЕЗУЛЬТАТЫ (Которые твоя таблица уже посчитала)
        # Допустим: E3 - ALL IN (Итог), B6 - Сбор, B12 - Транспорт, B15 - Мыто
        all_in = ws.acell('E3').value
        transport = ws.acell('B12').value
        customs = ws.acell('B15').value

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("ТРАНСПОРТ", transport)
    res2.metric("ТАМОЖНЯ", customs)
    res3.metric("ALL IN (ИТОГО)", all_in)
    
    st.balloons()
