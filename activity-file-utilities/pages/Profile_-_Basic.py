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
    dob         = st.date_input("Date of Birth", value=datetime.strptime(latest_profile['dob'], '%Y-%m-%d') if latest_profile is not None else None)
    sex         = st.selectbox("Sex", ["Male", "Female"], index=["Male", "Female"].index(latest_profile['sex']) if latest_profile is not None else 0)
    ftp         = st.number_input("FTP (Functional Threshold Power)", min_value=0, step=1, value=int(latest_profile['ftp']) if latest_profile is not None else 0)
    max_hr      = st.number_input("Maximum Heart Rate (BPM)", min_value=0, step=1, value=int(latest_profile['max_hr']) if latest_profile is not None else 0)
    resting_hr  = st.number_input("Resting Heart Rate (BPM)", min_value=0, step=1, value=int(latest_profile['resting_hr']) if latest_profile is not None else 0)

with col2:
    if unit_system == "Imperial (lbs, inches)":
        weight_lbs  = st.number_input("Weight (lbs)", min_value=0.0, step=1.0, value=round(float(latest_profile['weight_lbs']), 2) if latest_profile is not None else 0.0)
        height_ft   = st.number_input("Height (feet)", min_value=0, step=1, value=int(latest_profile['height_ft']) if latest_profile is not None else 0)
        height_in   = st.number_input("Height (inches)", min_value=0, step=1, value=int(latest_profile['height_in']) if latest_profile is not None else 0)
        weight_kg   = round(weight_lbs * 0.453592, 2)
        height_cm   = round((height_ft * 12 + height_in) * 2.54, 2)

    else:
        weight_kg    = st.number_input("Weight (kg)", min_value=0.0, step=1.0, value=round(float(latest_profile['weight_kg']), 2) if latest_profile is not None else 0.0)
        height_cm    = st.number_input("Height (cm)", min_value=0.0, step=1.0, value=round(float(latest_profile['height_cm']), 2) if latest_profile is not None else 0.0)
        weight_lbs   = round(weight_kg / 0.453592, 2)
        total_inches = height_cm / 2.54
        height_ft    = int(total_inches // 12)
        height_in    = int(total_inches % 12)

    st.success(f"Converted Weight: {round(weight_lbs, 2) if weight_lbs % 1 else int(weight_lbs)} lbs / {round(weight_kg, 2) if weight_kg % 1 else int(weight_kg)} kg")
    st.success(f"Converted Height: {height_ft} ft {height_in} in / {round(height_cm, 2) if height_cm % 1 else int(height_cm)} cm")

# Timestamp for data entry
timestamp = datetime.now().isoformat()

# Manage the form submission
if st.button("Save Entry"):
    entry = {
        "dob":          str(dob),
        "sex":          sex,
        "ftp":          int(ftp),
        "max_hr":       int(max_hr),
        "resting_hr":   int(resting_hr),
        "weight_lbs":   round(weight_lbs, 2) if weight_lbs % 1 else int(weight_lbs),
        "weight_kg":    round(weight_kg, 2) if weight_kg % 1 else int(weight_kg),
        "height_ft":    int(height_ft),
        "height_in":    int(height_in),
        "height_cm":    round(float(height_cm), 2) if height_cm % 1 else int(height_cm),
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
