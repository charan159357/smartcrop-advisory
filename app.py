import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

# ------------------- CONFIG -------------------
st.set_page_config(page_title="SmartCrop Advisory", layout="wide")
DATA_FILE = "smartcrop_data.csv"

# ------------------- Crop & Fertilizer Knowledge Base -------------------
CROP_RECOMMENDATIONS = {
    "Alluvial": ["Wheat", "Sugarcane", "Rice", "Pulses"],
    "Black": ["Cotton", "Soybean", "Millets"],
    "Red": ["Groundnut", "Millets", "Pulses"],
    "Laterite": ["Cashew", "Coconut", "Pineapple"],
    "Sandy": ["Pulses", "Groundnut", "Watermelon"],
    "Clay": ["Rice", "Sugarcane", "Jute"]
}

FERTILIZER_RECOMMENDATIONS = {
    "Wheat": ["Urea", "DAP", "MOP"],
    "Rice": ["Urea", "Superphosphate", "Potash"],
    "Sugarcane": ["Nitrogen-rich fertilizers", "Phosphorus fertilizers"],
    "Cotton": ["NPK (Nitrogen, Phosphorus, Potassium)"],
    "Soybean": ["Potash", "Phosphate fertilizers"],
    "Groundnut": ["Gypsum", "Phosphate fertilizers"],
    "Pulses": ["Biofertilizers", "DAP"],
    "Millets": ["Farmyard manure", "Urea"],
    "Cashew": ["Organic compost", "Potash fertilizers"],
    "Coconut": ["NPK fertilizers", "Farmyard manure"],
    "Pineapple": ["Nitrogen fertilizers", "Potash"],
    "Watermelon": ["Urea", "Superphosphate"],
    "Jute": ["Urea", "Potash", "Zinc sulphate"]
}

# ------------------- HELPER FUNCTIONS -------------------
def get_weather(city):
    api_key = st.secrets["OPENWEATHER_API_KEY"] if "OPENWEATHER_API_KEY" in st.secrets else None
    if not api_key:
        return None, "⚠️ No API key found"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"]
            }, None
        else:
            return None, f"⚠️ Error fetching weather: {response.status_code}"
    except Exception as e:
        return None, f"⚠️ Exception: {str(e)}"

def simple_yield_estimate(soil, stage):
    if soil in ["Alluvial", "Black", "Clay"]:
        return {"text": "High fertility soil, expect ~2.5 - 3 tons/acre"}
    elif soil in ["Red", "Laterite"]:
        return {"text": "Medium fertility soil, expect ~1.5 - 2 tons/acre"}
    else:
        return {"text": "Low fertility soil, expect ~1 - 1.5 tons/acre"}

def get_dummy_mandi_prices(state):
    data = {
        "Karnataka": [("Wheat", 2200, "Bengaluru APMC"), ("Rice", 1800, "Mandya APMC")],
        "Maharashtra": [("Cotton", 6000, "Nagpur APMC"), ("Soybean", 4500, "Pune APMC")],
        "Punjab": [("Wheat", 2000, "Ludhiana APMC"), ("Rice", 1900, "Amritsar APMC")]
    }
    return pd.DataFrame(data.get(state, []), columns=["Commodity", "Price (₹/quintal)", "Market"])

# ------------------- SIDEBAR INPUTS -------------------
st.sidebar.header("👨‍🌾 Farmer Details")
farmer_name = st.sidebar.text_input("👤 Farmer Name", value="")
location = st.sidebar.text_input("📍 Location (City/Village)", value="")
soil_type = st.sidebar.selectbox("🌱 Soil Type", list(CROP_RECOMMENDATIONS.keys()))
crop_stage = st.sidebar.selectbox("🌾 Crop Stage", ["Sowing", "Vegetative", "Flowering", "Harvesting"])
state = st.sidebar.selectbox("🛒 State for Mandi Prices", ["Karnataka", "Maharashtra", "Punjab"])

# ------------------- MAIN APP -------------------
st.title("🌾 SmartCrop Advisory")
st.subheader("For Small & Marginal Farmers")

# Weather
if location:
    weather, error = get_weather(location)
    if weather:
        st.success(f"🌡 Temp: {weather['temp']}°C | 💧 Humidity: {weather['humidity']}% | ☁ {weather['condition']}")
    else:
        st.warning(error)

# Crop Advisory
st.subheader(f"📌 Advisory for {farmer_name or 'Farmer'} in {location or 'your area'}")

if soil_type in CROP_RECOMMENDATIONS:
    crops = CROP_RECOMMENDATIONS[soil_type]
    st.write(f"**Best crops for {soil_type} soil:** {', '.join(crops)}")

    for crop in crops:
        if crop in FERTILIZER_RECOMMENDATIONS:
            st.write(f"- 🌱 **{crop}** → Recommended fertilizers: {', '.join(FERTILIZER_RECOMMENDATIONS[crop])}")

# Yield Estimate
st.subheader("📊 Yield Estimate")
estimate = simple_yield_estimate(soil_type, crop_stage)
st.info(estimate["text"])

# Mandi Prices
st.subheader("📉 Mandi Prices (Sample)")
df_mandi = get_dummy_mandi_prices(state)
st.table(df_mandi)
