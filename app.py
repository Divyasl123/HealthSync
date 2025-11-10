# app.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import os
import time

# optional TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="HealthSync+ | AI Health", page_icon="💖", layout="wide")

# ---------- STYLES ----------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #fce4ec, #e3f2fd);
}
.container {
    background-color: white;
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    max-width: 1100px;
    margin: 18px auto;
}
h1 {text-align:center; color:#d81b60; font-weight:800;}
.stButton>button {
  background:linear-gradient(90deg,#d81b60,#42a5f5);
  color:white; border:none; border-radius:10px; padding:10px 18px; font-weight:600;
}
.stButton>button:hover {
  background:linear-gradient(90deg,#42a5f5,#d81b60);
}
footer, header, #MainMenu {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "users" not in st.session_state: st.session_state.users = {}
if "otp" not in st.session_state: st.session_state.otp = None
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = None

HISTORY_FILE = "health_data.csv"

# ---------- Helper: speech ----------
def speak_text(text):
    if not TTS_AVAILABLE:
        st.warning("Voice not available (pyttsx3 not installed). Install pyttsx3 to enable voice.")
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error("TTS Error: " + str(e))

# ---------- Main layout ----------
st.title("💖 HealthSync+ Smart AI Health Assistant")

with st.container():
    st.markdown('<div class="container">', unsafe_allow_html=True)

    # LOGIN / REGISTER (if not logged in)
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["🔐 Login", "🆕 Register"])

        with tab1:
            st.header("Login")
            login_id = st.text_input("Username or Email")
            login_pw = st.text_input("Password", type="password")
            if st.button("Login"):
                if login_id in st.session_state.users and st.session_state.users[login_id]["password"] == login_pw:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_id
                    st.success(f"Welcome back, {login_id} ✅")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please check username/password.")

        with tab2:
            st.header("Register")
            full_name = st.text_input("Full Name", key="reg_name")
            reg_email = st.text_input("Email ID", key="reg_email")
            reg_phone = st.text_input("Phone Number", key="reg_phone")
            reg_pw = st.text_input("Create Password", type="password", key="reg_pw")

            if st.button("Send OTP"):
                if reg_email and reg_phone:
                    st.session_state.otp = str(random.randint(100000, 999999))
                    with st.spinner("Sending OTP (demo)..."):
                        time.sleep(1.2)
                    st.success(f"Demo OTP (sent to email): {st.session_state.otp}")
                else:
                    st.warning("Please provide email and phone.")

            otp_input = st.text_input("Enter OTP", key="reg_otp")
            if st.button("Register Account"):
                if otp_input and otp_input == st.session_state.otp:
                    username_key = full_name if full_name else reg_email
                    st.session_state.users[username_key] = {"email": reg_email, "phone": reg_phone, "password": reg_pw}
                    st.success("Account created successfully! You can now login.")
                    st.session_state.otp = None
                else:
                    st.error("Invalid or missing OTP.")
    else:
        # ---------- DASHBOARD ----------
        st.subheader(f"👋 Welcome, {st.session_state.current_user}!")
        st.markdown("Your AI assistant will analyze readings and suggest actions — voice included.")

        # two-column inputs + AI card
        left, right = st.columns([2, 1])
        with left:
            st.markdown("### 🩺 Enter Health Parameters")
            input_name = st.text_input("Display name", value=st.session_state.current_user)
            age = st.number_input("Age (years)", min_value=1, max_value=120, value=20)
            temp = st.number_input("Body Temperature (°F)", min_value=90.0, max_value=110.0, value=98.6, step=0.1)
            heart = st.number_input("Heart Rate (BPM)", min_value=30, max_value=220, value=75)
            sugar = st.number_input("Blood Sugar (mg/dL)", min_value=40, max_value=400, value=100)
            bp_sys = st.number_input("BP — Systolic (mmHg)", min_value=70, max_value=240, value=120)
            bp_dia = st.number_input("BP — Diastolic (mmHg)", min_value=40, max_value=160, value=80)
            notes = st.text_area("Notes / Symptoms (optional)")

        with right:
            st.markdown("### 🤖 AI Assistant")
            st.image("https://cdn-icons-png.flaticon.com/512/4406/4406231.png", width=140)
            st.info("AI provides advice, voice output, and saves history for trend analysis.")

        # ---------- SAFE REFERENCE VALUES ----------
        safe_refs = {
            "Temperature": 99.0,
            "Heart Rate": 100,
            "Blood Sugar": 140,
            "BP Sys": 130,
            "BP Dia": 85
        }

        def evaluate_status(val, param):
            if param == "Temperature":
                if val > 100.4: return "high"
                elif val > 99.0: return "slightly_high"
                else: return "normal"
            if param == "Heart Rate":
                if val > 120 or val < 50: return "high"
                elif val > 100: return "slightly_high"
                else: return "normal"
            if param == "Blood Sugar":
                if val >= 200: return "high"
                elif val > 140: return "slightly_high"
                else: return "normal"
            if param == "BP Sys":
                if val >= 180: return "high"
                elif val > 140: return "slightly_high"
                else: return "normal"
            if param == "BP Dia":
                if val >= 120: return "high"
                elif val > 90: return "slightly_high"
                else: return "normal"
            return "normal"

        # ---------- ANALYZE FUNCTION ----------
        def analyze_all(temp, heart, sugar, bp_sys, bp_dia):
            metrics = {
                "Temperature": temp,
                "Heart Rate": heart,
                "Blood Sugar": sugar,
                "BP Sys": bp_sys,
                "BP Dia": bp_dia
            }
            statuses = {k: evaluate_status(metrics[k], k) for k in metrics}
            severity_score = sum(3 if s == "high" else 1 if s == "slightly_high" else 0 for s in statuses.values())

            if severity_score == 0:
                overall = "✅ All clear — readings are within normal ranges."
                ai_text = "All readings look good. Keep a healthy routine with balanced food and rest."
            elif severity_score <= 3:
                overall = "⚠️ Slight irregularities found."
                ai_text = "Some readings are a little high. Drink water, rest, and recheck later."
            else:
                overall = "🚨 Critical — please consult a doctor soon."
                ai_text = "Several readings are beyond safe limits. Seek medical advice urgently."
            return overall, ai_text, statuses

        # ---------- ON CLICK ----------
        if st.button("Analyze My Health 💖"):
            overall, ai_text, statuses = analyze_all(temp, heart, sugar, bp_sys, bp_dia)
            color = "#2e7d32" if "✅" in overall else "#ef6c00" if "⚠️" in overall else "#c62828"
            st.markdown(f"<h3 style='color:{color}'>{overall}</h3>", unsafe_allow_html=True)
            st.info(ai_text)

            # Voice
            if TTS_AVAILABLE:
                speak_text(overall + " " + ai_text)

        # ---------- BAR GRAPH ----------
        st.write("---")
        st.subheader("📊 Health Overview (Bar Graph Style)")
        data = {
            "Parameter": ["Temperature", "Heart Rate", "Blood Sugar", "BP Sys", "BP Dia"],
            "Value": [temp, heart, sugar, bp_sys, bp_dia],
            "SafeValue": [safe_refs["Temperature"], safe_refs["Heart Rate"], safe_refs["Blood Sugar"], safe_refs["BP Sys"], safe_refs["BP Dia"]]
        }
        df = pd.DataFrame(data)
        df["Status"] = df.apply(lambda x: evaluate_status(x["Value"], x["Parameter"]), axis=1)
        color_map = {"normal": "#ec407a", "slightly_high": "#ffb74d", "high": "#f44336"}

        bars = alt.Chart(df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Parameter:N"),
            y=alt.Y("Value:Q"),
            color=alt.Color("Status:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None)
        )

        line = alt.Chart(df).mark_rule(color="green", strokeDash=[6, 4]).encode(y="SafeValue:Q")
        text = alt.Chart(df).mark_text(dy=-10, color="black").encode(x="Parameter:N", y="Value:Q", text=alt.Text("Value:Q", format=".1f"))
        chart = (bars + line + text).properties(height=350)
        st.altair_chart(chart, use_container_width=True)

        # ---------- AI SECTION BELOW ----------
        st.write("---")
        st.subheader("💬 AI Assistant — Health Tips")
        st.markdown("""
        - ✅ *Normal*: Maintain your current lifestyle.  
        - ⚠️ *Slightly high*: Hydrate, rest, and recheck after a few hours.  
        - 🚨 *High*: Consult a doctor immediately.  
        """)

        # ---------- LOGOUT ----------
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.success("You are logged out.")
            time.sleep(0.7)
            st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#ad1457;'>💖 Built by Divya & Soumya | Innovation Ignite 2025 | AI Health Dashboard 💙</div>", unsafe_allow_html=True)
