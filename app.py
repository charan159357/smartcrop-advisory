import streamlit as st
import requests
from gtts import gTTS

# ----------------- CONFIG -----------------
st.set_page_config(page_title="SmartCrop Advisory", layout="wide")

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
        return "High fertility soil, expect 2.5 - 3 tons/acre"
    elif soil == "Black":
        return "Good for cotton, yields ~2 tons/acre"
    else:
        return "Average yield ~1.5 tons/acre"

# ----------------- VOICE ADVISORY -----------------
def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save("advice.mp3")
    return "advice.mp3"

# ----------------- UI -----------------
st.title("🌾 SmartCrop Advisory for Farmers")

# Farmer inputs
farmer_name = st.text_input("👨‍🌾 Farmer Name", "")
location = st.text_input("📍 Location (City/Village)", "Bangalore")
soil_type = st.selectbox("🧱 Soil Type", ["Alluvial", "Black", "Red", "Laterite"])
crop_stage = st.selectbox("🌱 Crop Stage", ["Sowing", "Vegetative", "Flowering", "Harvest"])
voice_lang = st.selectbox("🗣️ Voice language", ["en", "hi", "kn", "ta"])

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
    f"For soil type {soil_type}, suitable crops include Wheat, Sugarcane, Rice, Pulses.\n"
    f"At the {crop_stage} stage, use recommended fertilizers and irrigation practices."
)

st.write(advice_text)

# Yield estimate
st.subheader("📈 Yield Estimate")
estimate = simple_yield_estimate(soil_type, crop_stage)
st.info(estimate)

# Voice output
if st.button("🔊 Play Advisory"):
    mp3_file = text_to_speech(advice_text, voice_lang)
    audio_file = open(mp3_file, "rb")
    st.audio(audio_file.read(), format="audio/mp3")
