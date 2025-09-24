import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from gtts import gTTS

# ----------------- CONFIG -----------------
st.set_page_config(page_title="SmartCrop Advisory", layout="wide")

DATA_FILE = "smartcrop_data.csv"

# ----------------- WEATHER -----------------
def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return None
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
        }
    except:
        return None

# ----------------- YIELD ESTIMATION -----------------
def simple_yield_estimate(soil, stage):
    if soil == "Alluvial":
        return {"text": "High fertility soil, expect 2.5 - 3 tons/acre"}
    elif soil == "Black":
        return {"text": "Good for cotton, yields ~2 tons/acre"}
    else:
        return {"text": "Average yield ~1.5 tons/acre"}

# ----------------- VOICE ADVISORY -----------------
def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save("advice.mp3")
    return "advice.mp3"

# ----------------- MANDI PRICES (Agmarknet API) -----------------
def get_mandi_prices(state, api_key):
    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[state]": state,
            "limit": 50   # fetch first 50 rows
        }
        response = requests.get(url, params=params)
        data = response.json()
        if "records" in data:
            df = pd.DataFrame(data["records"])
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
    voice_lang = st.selectbox("🗣️ Voice language", ["en", "hi", "kn", "ta"])

with col2:
    st.subheader("📊 Mandi Prices (Live from Agmarknet)")
    states = [
        "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Delhi","Goa",
        "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
        "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
        "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
        "Uttar Pradesh","Uttarakhand","West Bengal"
    ]
    state = st.selectbox("Select State", states)

# ----------------- WEATHER DISPLAY -----------------
st.subheader(f"📌 Advisory for {farmer_name} in {location}")

OWM_KEY = st.secrets.get("OWM_API_KEY", None)
if not OWM_KEY:
    st.error("⚠️ No OpenWeatherMap API key found in Streamlit secrets.")
else:
    weather = get_weather(location, OWM_KEY)
    if weather:
        st.success(f"🌡 Temp: {weather['temp']}°C | 💧 Humidity: {weather['humidity']}% | ☁ {weather['condition']}")
    else:
        st.warning("⚠️ Current weather data not available.")

# ----------------- ADVISORY -----------------
st.subheader("✅ Personalized Crop Advisory")
advice_text = (
    "Best crops: Wheat, Sugarcane, Rice, Pulses.\n"
    "Use nitrogen-rich fertilizers for better germination."
)
st.write(advice_text)

# Yield estimate
st.subheader("📈 Yield Estimate")
estimate = simple_yield_estimate(soil_type, crop_stage)
st.info(estimate["text"])

# Voice output
if st.button("🔊 Play Advisory"):
    mp3_file = text_to_speech(advice_text, voice_lang)
    audio_file = open(mp3_file, "rb")
    st.audio(audio_file.read(), format="audio/mp3")

# ----------------- SHOW MANDI DATA -----------------
MANDI_KEY = st.secrets.get("MANDI_API_KEY", None)
if not MANDI_KEY:
    st.error("⚠️ No Agmarknet API key found in Streamlit secrets.")
else:
    df_mandi = get_mandi_prices(state, MANDI_KEY)
    if not df_mandi.empty:
        st.dataframe(df_mandi.head(20))
    else:
        st.warning("⚠️ No mandi data available for this state at the moment.")
