import streamlit as st
import requests
import random
st.title("🌱 SmartCrop Advisory App")
st.subheader("For Small & Marginal Farmers")

# Sidebar inputs
st.sidebar.header("Enter Your Details")
farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name", value="")
location = st.sidebar.text_input("📍 Location (City/Village)", value="")
soil_type = st.sidebar.selectbox("🌍 Soil Type",
                                 ["Alluvial", "Black", "Red", "Laterite", "Sandy", "Clay"])
crop_stage = st.sidebar.selectbox("🌾 Crop Stage",
                                  ["Sowing", "Vegetative", "Flowering", "Harvesting"])

def get_weather(city):
    api_key = "YOUR_OPENWEATHERMAP_API_KEY"   # <-- replace with your real API key
    if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        return None
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if resp.status_code != 200:
            return None
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"]
        }
    except Exception:
        return None

def crop_advisory(soil, weather, stage):
    advice_list = []

    # Soil-based suggestions
    if soil == "Black":
        advice_list.append("Best crops: Cotton, Soybean, Maize.")
    elif soil == "Alluvial":
        advice_list.append("Best crops: Wheat, Sugarcane, Rice, Pulses.")
    elif soil == "Sandy":
        advice_list.append("Best crops: Bajra, Groundnut, Watermelon.")

    # Weather-based suggestions
    if weather:
        t = weather.get("temperature")
        h = weather.get("humidity")
        if t is not None and t > 35:
            advice_list.append("⚠️ High temperature: Irrigate crops frequently.")
        if t is not None and t < 15:
            advice_list.append("⚠️ Low temperature: Use crop covers to retain heat.")
        if h is not None and h > 70:
            advice_list.append("⚠️ High humidity: Watch for fungal diseases.")

    # Stage-based fertilizer suggestion
    if stage == "Sowing":
        advice_list.append("Use nitrogen-rich fertilizers for better germination.")
    elif stage == "Vegetative":
        advice_list.append("Apply urea/DAP for strong growth.")
    elif stage == "Flowering":
        advice_list.append("Use potash and micronutrients.")
    elif stage == "Harvesting":
        advice_list.append("Reduce irrigation; focus on pest control.")

    return advice_list

# Display
if location:
    st.header(f"📍 Advisory for {farmer_name or 'Farmer'} in {location}")
    weather = get_weather(location)

    if weather:
        st.write(f"*🌡️ Temperature:* {weather['temperature']} °C")
        st.write(f"*💧 Humidity:* {weather['humidity']} %")
        st.write(f"*☁️ Condition:* {weather['condition']}")
    else:
        st.warning("⚠️ Weather data not available. Check your location spelling or API key.")

    st.subheader("✅ Personalized Crop Advisory")
    for tip in crop_advisory(soil_type, weather, crop_stage):
        st.write("- " + tip)

    schemes = [
        "PM-KISAN: Direct cash transfer to farmers.",
        "Soil Health Card Scheme: Helps manage soil nutrients.",
        "PMFBY: Crop insurance for farmers."
    ]
    st.info("📢 Govt. Scheme: " + random.choice(schemes))
else:
    st.info("Enter a Location in the sidebar to get advisory.")
