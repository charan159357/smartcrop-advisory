import streamlit as st
import requests
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import json

st.set_page_config(page_title="SmartCrop Advisory", layout="wide")

DATA_FILE = "smartcrop_data.csv"

# ---------- HELPERS ----------
def get_current_weather(city):
    try:
        if "api_keys" in st.secrets and "openweather" in st.secrets["api_keys"]:
            api_key = st.secrets["api_keys"]["openweather"]
        else:
            st.warning("⚠️ No OpenWeatherMap API key found in Streamlit secrets.")
            return None

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        return {"temperature": d["main"]["temp"],
                "humidity": d["main"]["humidity"],
                "condition": d["weather"][0]["description"]}
    except Exception as e:
        st.error(f"Error fetching weather: {e}")
        return None

def get_forecast(city, days=3):
    try:
        if "api_keys" in st.secrets and "openweather" in st.secrets["api_keys"]:
            api_key = st.secrets["api_keys"]["openweather"]
        else:
            return None

        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
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
            avg_t = sum(v["temps"])/len(v["temps"])
            avg_h = sum(v["hums"])/len(v["hums"])
            cond = max(set(v["conds"]), key=v["conds"].count)
            result.append({"date": d, "avg_temp": round(avg_t,1), "avg_humidity": round(avg_h,1), "condition": cond})
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
            advice_list.append("⚠️ High temperature: Irrigate crops frequently and use mulches.")
        if t is not None and t < 15:
            advice_list.append("⚠️ Low temperature: Use crop covers to retain heat.")
        if h is not None and h > 70:
            advice_list.append("⚠️ High humidity: Watch for fungal diseases; consider preventive fungicide if recommended.")

    if stage == "Sowing":
        advice_list.append("Use nitrogen-rich fertilizers for better germination.")
    elif stage == "Vegetative":
        advice_list.append("Apply urea/DAP for strong growth; monitor leaf color for deficiency.")
    elif stage == "Flowering":
        advice_list.append("Use potash and micronutrients to improve fruit/seed formation.")
    elif stage == "Harvesting":
        advice_list.append("Reduce irrigation; focus on pest control and timely harvesting.")

    return advice_list

def pest_disease_alerts(forecast):
    alerts = []
    if not forecast:
        return alerts
    for day in forecast:
        if day["avg_humidity"] > 75 and day["avg_temp"]>20:
            alerts.append(f"{day['date']}: High risk of fungal diseases (humidity {day['avg_humidity']}%).")
        if day["avg_temp"] > 38:
            alerts.append(f"{day['date']}: Heat stress risk (temp {day['avg_temp']}°C).")
    return alerts

def simple_yield_estimate(soil, forecast, stage):
    base = 0.6
    if soil == "Alluvial": base += 0.15
    if soil == "Black": base += 0.1
    if stage == "Vegetative": base += 0.05
    if stage == "Flowering": base += 0.02
    if forecast and len(forecast)>0:
        t = forecast[0]["avg_temp"]
        h = forecast[0]["avg_humidity"]
        if t>35:
            base -= 0.08
        if h>80:
            base -= 0.06
    base = max(0.2, min(0.98, base))
    percent = int(base*100)
    return {"factor": base, "text": f"Estimated relative yield: {percent}% (rule-based approx)."}

def save_entry(data):
    df_row = pd.DataFrame([data])
    if not os.path.exists(DATA_FILE):
        df_row.to_csv(DATA_FILE, index=False)
    else:
        df_row.to_csv(DATA_FILE, mode='a', header=False, index=False)

# ---------- UI ----------
st.title("🌱 SmartCrop Advisory App")
st.subheader("For Small & Marginal Farmers (Enhanced)")

with st.sidebar:
    st.header("Farmer Details")
    farmer_name = st.text_input("👨‍🌾 Farmer Name", value="")
    location = st.text_input("📍 Location (City/Village)", value="")
    soil_type = st.selectbox("🌍 Soil Type", ["Alluvial", "Black", "Red", "Laterite", "Sandy", "Clay"])
    crop_stage = st.selectbox("🌾 Crop Stage", ["Sowing", "Vegetative", "Flowering", "Harvesting"])
    save_local = st.checkbox("Save this advisory locally (CSV)", value=True)
    st.markdown("---")
    st.markdown("**Quick actions**")
    if st.button("Show saved data file"):
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            st.dataframe(df.tail(10))
        else:
            st.info("No saved data yet.")

if not location:
    st.info("Enter a Location in the sidebar to get advisory, forecast, and charts.")
    st.stop()

current = get_current_weather(location)
forecast = get_forecast(location, days=4)

col1, col2 = st.columns([2,1])

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
        df_fore = pd.DataFrame(forecast)
        st.table(df_fore)

        dates = [d['date'] for d in forecast]
        temps = [d['avg_temp'] for d in forecast]
        hums = [d['avg_humidity'] for d in forecast]

        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(dates, temps, marker='o')
        ax.set_title("Avg Temperature (next days)")
        ax.set_ylabel("°C")
        ax.grid(True)
        st.pyplot(fig)

        fig2, ax2 = plt.subplots(figsize=(6,3))
        ax2.plot(dates, hums, marker='o')
        ax2.set_title("Avg Humidity (next days)")
        ax2.set_ylabel("%")
        ax2.grid(True)
        st.pyplot(fig2)
    else:
        st.info("Forecast not available.")

    st.subheader("✅ Personalized Crop Advisory")
    for tip in crop_advisory(soil_type, current or (forecast[0] if forecast else None), crop_stage):
        st.write("- " + tip)

    st.subheader("📈 Yield Estimate")
    estimate = simple_yield_estimate(soil_type, forecast, crop_stage)
    st.info(estimate["text"])

    st.subheader("⚠️ Pest & Disease Alerts")
    alerts = pest_disease_alerts(forecast)
    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.write("No immediate high-risk alerts predicted.")

    st.subheader("📢 Relevant Govt. Schemes")
    schemes = [
        {"name":"PM-KISAN", "desc":"Income support scheme for farmers."},
        {"name":"Soil Health Card Scheme", "desc":"Provides soil nutrient recommendations."},
        {"name":"PMFBY", "desc":"Crop insurance (Pradhan Mantri Fasal Bima Yojana)."},
        {"name":"e-NAM", "desc":"National Agriculture Market platform."}
    ]
    for s in schemes:
        st.write(f"**{s['name']}** — {s['desc']}")

with col2:
    st.header("Actions & Save Data")
    record = {
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "farmer": farmer_name,
        "location": location,
        "soil": soil_type,
        "stage": crop_stage,
        "current_temp": current['temperature'] if current else None,
        "current_humidity": current['humidity'] if current else None,
        "forecast": json.dumps(forecast) if forecast else None,
        "advisory": "; ".join(crop_advisory(soil_type, current or (forecast[0] if forecast else None), crop_stage))
    }

    if save_local and st.button("Save advisory to CSV"):
        save_entry(record)
        st.success("Saved locally to " + DATA_FILE)

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            st.download_button("📥 Download saved CSV", f, file_name=DATA_FILE)
