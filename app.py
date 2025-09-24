import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import io
from gtts import gTTS
from pathlib import Path

st.set_page_config(page_title="SmartCrop Advisory App", layout="wide")

# ---------- Helpers ----------
def get_api_key():
    return st.secrets.get("general", {}).get("OPENWEATHERMAP_API_KEY", None)

def get_current_weather(city):
    api_key = get_api_key()
    if not api_key:
        return None
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        return {
            "temperature": d["main"]["temp"],
            "humidity": d["main"]["humidity"],
            "condition": d["weather"][0]["description"],
        }
    except Exception:
        return None

def get_forecast(city, days=3):
    api_key = get_api_key()
    if not api_key:
        return None
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)
        daily = {}
        for item in data.get("list", []):
            dt = datetime.utcfromtimestamp(item["dt"])
            if dt > end_date:
                continue
            date_key = dt.date().isoformat()
            temps = daily.setdefault(date_key, {"temps": [], "hums": [], "conds": []})
            temps["temps"].append(item["main"]["temp"])
            temps["hums"].append(item["main"]["humidity"])
            temps["conds"].append(item["weather"][0]["description"])
        result = []
        for d, v in sorted(daily.items())[:days]:
            avg_t = sum(v["temps"]) / len(v["temps"])
            avg_h = sum(v["hums"]) / len(v["hums"])
            cond = max(set(v["conds"]), key=v["conds"].count)
            result.append(
                {"date": d, "avg_temp": round(avg_t, 1), "avg_humidity": round(avg_h, 1), "condition": cond}
            )
        return result
    except Exception:
        return None

def crop_advisory(soil, weather, stage):
    advice_list = []
    if soil == "Black":
        advice_list.append("Best crops: Cotton, Soybean, Maize.")
    elif soil == "Alluvial":
        advice_list.append("Best crops: Wheat, Sugarcane, Rice, Pulses.")
    elif soil == "Sandy":
        advice_list.append("Best crops: Bajra, Groundnut, Watermelon.")
    else:
        advice_list.append("Consider crop rotation and soil testing for best results.")

    if weather:
        t = weather.get("temperature")
        h = weather.get("humidity")
        if t is not None and t > 35:
            advice_list.append("High temperature: Irrigate frequently and use mulches.")
        if t is not None and t < 15:
            advice_list.append("Low temperature: Use crop covers to retain heat.")
        if h is not None and h > 70:
            advice_list.append("High humidity: Watch for fungal diseases.")

    if stage == "Sowing":
        advice_list.append("Use nitrogen-rich fertilizers for better germination.")
    elif stage == "Vegetative":
        advice_list.append("Apply urea/DAP for strong growth; monitor leaf color for deficiency.")
    elif stage == "Flowering":
        advice_list.append("Use potash and micronutrients to improve fruit/seed formation.")
    elif stage == "Harvesting":
        advice_list.append("Reduce irrigation; focus on pest control and timely harvesting.")

    return advice_list

def simple_yield_estimate(soil, forecast, stage):
    base = 0.6
    if soil == "Alluvial": base += 0.15
    if soil == "Black": base += 0.1
    if stage == "Vegetative": base += 0.05
    if stage == "Flowering": base += 0.02
    if forecast and len(forecast) > 0:
        t = forecast[0]["avg_temp"]
        h = forecast[0]["avg_humidity"]
        if t > 35:
            base -= 0.08
        if h > 80:
            base -= 0.06
    base = max(0.2, min(0.98, base))
    percent = int(base * 100)
    return {"factor": base, "text": f"Estimated relative yield: {percent}% (rule-based approx)."}

def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp.read()

def get_dummy_mandi_prices(state="Karnataka"):
    data = [
        {"commodity": "Wheat", "unit": "kg", "price": 2200, "market": "Bengaluru APMC"},
        {"commodity": "Rice", "unit": "kg", "price": 1800, "market": "Mandya APMC"},
        {"commodity": "Maize", "unit": "kg", "price": 1500, "market": "Bengaluru APMC"},
        {"commodity": "Cotton", "unit": "quintal", "price": 5200, "market": "Gulbarga APMC"},
    ]
    return pd.DataFrame(data)

# ---------- UI ----------
st.title("🌱 SmartCrop Advisory App")
st.subheader("For Small & Marginal Farmers")

# Debug API Key
API_KEY = get_api_key()
if API_KEY:
    st.success("✅ OpenWeatherMap API key loaded successfully.")
else:
    st.warning("⚠️ No OpenWeatherMap API key found in Streamlit Secrets. Please add it in App → Settings → Secrets.")

with st.sidebar:
    st.header("Farmer Details")
    farmer_name = st.text_input("👨‍🌾 Farmer Name", value="")
    location = st.text_input("📍 Location (City/Village)", value="Bengaluru")
    soil_type = st.selectbox("🌍 Soil Type", ["Alluvial", "Black", "Red", "Laterite", "Sandy", "Clay"])
    crop_stage = st.selectbox("🌾 Crop Stage", ["Sowing", "Vegetative", "Flowering", "Harvesting"])
    lang = st.selectbox("🗣️ Voice language", ["en", "hi"], index=0)

if not location:
    st.info("Enter a Location in the sidebar to get advisory, forecast, and charts.")
    st.stop()

current = get_current_weather(location)
forecast = get_forecast(location, days=4)

col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📍 Advisory for {farmer_name or 'Farmer'} in {location}")

    if current:
        st.subheader("Current Weather")
        st.write(f"🌡️ Temperature: **{current['temperature']} °C**")
        st.write(f"💧 Humidity: **{current['humidity']}%**")
        st.write(f"☁️ Condition: **{current['condition']}**")
    else:
        st.warning("⚠️ Current weather data not available.")

    if forecast:
        st.subheader("Forecast (next days)")
        st.table(pd.DataFrame(forecast))
    else:
        st.info("Forecast not available.")

    st.subheader("✅ Personalized Crop Advisory")
    advice_text = "\n".join(crop_advisory(soil_type, current or (forecast[0] if forecast else None), crop_stage))
    for tip in advice_text.split("\n"):
        st.write("- " + tip)

    st.subheader("📈 Yield Estimate")
    estimate = simple_yield_estimate(soil_type, forecast, crop_stage)
    st.info(estimate["text"])

    st.subheader("🔊 Voice Advisory")
    if st.button("Play Advisory"):
        try:
            mp3_bytes = text_to_speech(advice_text, lang=lang)
            st.audio(mp3_bytes, format="audio/mp3")
        except Exception as e:
            st.error("Voice output failed: " + str(e))

with col2:
    st.header("📊 Mandi Prices (Sample)")
    state = st.selectbox("State", ["Karnataka", "Maharashtra", "Punjab"], index=0)
    df_mandi = get_dummy_mandi_prices(state=state)
    st.table(df_mandi)
