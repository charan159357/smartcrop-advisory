import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from gtts import gTTS
import io

# ----------------- CONFIG -----------------
st.set_page_config(page_title="SmartCrop Advisory", layout="wide")

# ----------------- WEATHER -----------------
def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10).json()
        if response.get("cod") != 200:
            return None
        return {
            "temp": response["main"]["temp"],
            "humidity": response["main"]["humidity"],
            "condition": response["weather"][0]["description"],
        }
    except:
        return None

# ----------------- YIELD ESTIMATION -----------------
def simple_yield_estimate(soil, stage):
    if soil == "Alluvial":
        return {"text": "High fertility soil, expect ~2.5 - 3 tons/acre"}
    elif soil == "Black":
        return {"text": "Good for cotton & soybean, yields ~2 tons/acre"}
    else:
        return {"text": "Average yield ~1.5 tons/acre"}

# ----------------- VOICE ADVISORY -----------------
def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp.read()

# ----------------- MANDI PRICES (Agmarknet API) -----------------
def get_mandi_prices(state, api_key):
    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[state]": state,
            "limit": 50
        }
        response = requests.get(url, params=params, timeout=10).json()
        if "records" in response:
            df = pd.DataFrame(response["records"])
            return df[["state", "district", "market", "commodity", "variety", "min_price", "max_price", "modal_price"]]
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

# ----------------- UI -----------------
st.title("🌾 SmartCrop Advisory for Farmers")

# Farmer inputs
col1, col2 = st.columns(2)

with col1:
    farmer_name = st.text_input("👨‍🌾 Farmer Name", "")
    location = st.text_input("📍 Location (City/Village)", "Bangalore")
    soil_type = st.selectbox("🧱 Soil Type", ["Alluvial", "Black", "Red", "Laterite"])
    crop_stage = st.selectbox("🌱 Crop Stage", ["Sowing", "Vegetative", "Flowering", "Harvest"])
    voice_lang = st.selectbox("🗣️ Voice language", ["en", "hi", "ta", "kn"])

with col2:
    st.subheader("📊 Mandi Prices (Live)")
    states = [
        "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Delhi","Goa",
        "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
        "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
        "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
        "Uttar Pradesh","Uttarakhand","West Bengal"
    ]
    state = st.selectbox("Select State", states)

# ----------------- WEATHER DISPLAY -----------------
st.subheader(f"📌 Advisory for {farmer_name or 'Farmer'} in {location}")

OWM_KEY = st.secrets.get("OWM_API_KEY", None)
if not OWM_KEY:
    st.error("⚠️ Please add your OpenWeatherMap API key in Streamlit Secrets.")
else:
    weather = get_weather(location, OWM_KEY)
    if weather:
        st.success(f"🌡 Temp: {weather['temp']}°C | 💧 Humidity: {weather['humidity']}% | ☁ {weather['condition']}")
    else:
        st.warning("⚠️ Weather data not available (check city spelling or API key).")

# ----------------- ADVISORY -----------------
st.subheader("✅ Personalized Crop Advisory")
advice_text = (
    f"For {soil_type} soil in {crop_stage} stage: \n"
    "- Ensure proper irrigation. \n"
    "- Apply fertilizers based on soil health card. \n"
    "- Monitor for pests and diseases."
)
st.write(advice_text)

# Yield estimate
st.subheader("📈 Yield Estimate")
estimate = simple_yield_estimate(soil_type, crop_stage)
st.info(estimate["text"])

# Voice output
if st.button("🔊 Play Advisory"):
    try:
        mp3_bytes = text_to_speech(advice_text, lang=voice_lang)
        st.audio(mp3_bytes, format="audio/mp3")
    except Exception as e:
        st.error("Voice output failed: " + str(e))

# ----------------- SHOW MANDI DATA -----------------
MANDI_KEY = st.secrets.get("MANDI_API_KEY", None)
if not MANDI_KEY:
    st.error("⚠️ Please add your Agmarknet API key in Streamlit Secrets.")
else:
    df_mandi = get_mandi_prices(state, MANDI_KEY)
    if not df_mandi.empty:
        st.dataframe(df_mandi.head(20))
    else:
        st.warning("⚠️ No mandi data available for this state right now.")
