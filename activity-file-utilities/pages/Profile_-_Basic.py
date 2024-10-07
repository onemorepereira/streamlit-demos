from datetime import datetime
import helper as h
import streamlit as st


DATA_FILE = "basic_profile.json"

st.title("Profile Manager")

profiles_df     = h.load_data(DATA_FILE)
latest_profile  = profiles_df.iloc[-1] if not profiles_df.empty else None
unit_system     = st.radio("Choose unit system:", ("Imperial (lbs, inches)", "Metric (kg, cm)"))

col1, col2 = st.columns(2)
with col1:
    dob     = st.date_input("Date of Birth", value=datetime.strptime(latest_profile['dob'], '%Y-%m-%d')                         if latest_profile is not None else None)
    sex     = st.selectbox("Sex", ["Male", "Female"], index=["Male", "Female"].index(latest_profile['sex'])   if latest_profile is not None else 0)
    ftp     = st.number_input("FTP (Functional Threshold Power)",   min_value=0, step=1, value=int(latest_profile['ftp'])       if latest_profile is not None else 0)
    max_hr  = st.number_input("Maximum Heart Rate (BPM)",           min_value=0, step=1, value=int(latest_profile['max_hr'])    if latest_profile is not None else 0)

with col2:
    if unit_system == "Imperial (lbs, inches)":
        weight_lbs  = st.number_input("Weight (lbs)",    min_value=0.0, step=1.0,   value=float(latest_profile['weight_lbs']) if latest_profile is not None else 0.0)
        height_ft   = st.number_input("Height (feet)",   min_value=0,   step=1,     value=int(latest_profile['height_ft'])    if latest_profile is not None else 0)
        height_in   = st.number_input("Height (inches)", min_value=0,   step=1,     value=int(latest_profile['height_in'])    if latest_profile is not None else 0)
        weight_kg   = weight_lbs * 0.453592
        height_cm   = (height_ft * 12 + height_in) * 2.54

    else:
        weight_kg    = st.number_input("Weight (kg)", min_value=0.0, step=1.0, value=float(latest_profile['weight_kg']) if latest_profile is not None else 0.0)
        height_cm    = st.number_input("Height (cm)", min_value=0.0, step=1.0, value=float(latest_profile['height_cm']) if latest_profile is not None else 0.0)
        weight_lbs   = weight_kg / 0.453592
        total_inches = height_cm / 2.54
        height_ft    = int(total_inches // 12)
        height_in    = int(total_inches % 12)

    st.write(f"Converted Weight: {weight_lbs:.2f} lbs / {weight_kg:.2f} kg")
    st.write(f"Converted Height: {height_ft} ft {height_in} in / {height_cm:.2f} cm")

# Timestamp for data entry
timestamp = datetime.now().isoformat()

# Manage the form submission
if st.button("Save Entry"):
    entry = {
        "dob":          str(dob),
        "sex":          sex,
        "ftp":          int(ftp),
        "max_hr":       int(max_hr),
        "weight_lbs":   weight_lbs,
        "weight_kg":    weight_kg,
        "height_ft":    int(height_ft),
        "height_in":    int(height_in),
        "height_cm":    round(float(height_cm),2),
        "timestamp":    timestamp
    }

    data = h.load_data(DATA_FILE).to_dict(orient="records")
    data.append(entry)
    h.save_data(data, DATA_FILE)
    st.success("Profile saved successfully!")

st.header("Saved Profiles")
data = h.load_data(DATA_FILE)
if not data.empty:
    st.dataframe(data)
else:
    st.write("No profiles found.")
