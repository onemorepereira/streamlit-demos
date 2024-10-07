import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os

POWER_FILE = "power_profile.json"
PROFILE_FILE = "basic_profile.json"

def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
            if data:
                return pd.json_normalize(data)
            else:
                st.error("The profile file is empty.")
                return pd.DataFrame()
    else:
        st.error(f"File {file_path} not found.")
        return pd.DataFrame()

def save_data(data, file_name):
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

def get_latest_ftp():
    df = load_data(PROFILE_FILE)
    if not df.empty and "ftp" in df.columns:
        ftp = df["ftp"].iloc[-1]
        if pd.notna(ftp):
            return int(ftp)
        else:
            st.warning("No valid FTP value found in the profile. Please update your profile.")
            return 0
    else:
        st.warning("FTP value not found in profile data.")
        return 0

power_df = load_data(POWER_FILE)
ftp = get_latest_ftp()

st.title("Power Zones Manager")
st.write(f"Current FTP: {ftp} Watts")

# Preload pct values if they exist
zone_pcts = {f"zone.{i}": 0 for i in range(1, 8)}  # Initialize default zone percentages
if not power_df.empty:
    latest_power_data = power_df.iloc[-1]  # Get the latest saved data
    for zone in range(1, 8):
        zone_key = f"zone.{zone}"
        zone_pcts[zone_key] = latest_power_data[f"{zone_key}.pct"]

if ftp > 0:
    timestamp = datetime.now().isoformat()
    power_data = {"timestamp": timestamp}  # Change this to a dictionary for better structure

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Power Zones (%)")
        zone_1 = st.number_input("Zone 1 (Recovery)",   min_value=0,            max_value=200, step=1, value=zone_pcts["zone.1"])
        zone_2 = st.number_input("Zone 2 (Endurance)",  min_value=zone_1 + 1,   max_value=200, step=1, value=zone_pcts["zone.2"])
        zone_3 = st.number_input("Zone 3 (Tempo)",      min_value=zone_2 + 1,   max_value=200, step=1, value=zone_pcts["zone.3"])
        zone_4 = st.number_input("Zone 4 (Threshold)",  min_value=zone_3 + 1,   max_value=200, step=1, value=zone_pcts["zone.4"])
        zone_5 = st.number_input("Zone 5 (VO2 Max)",    min_value=zone_4 + 1,   max_value=200, step=1, value=zone_pcts["zone.5"])
        zone_6 = st.number_input("Zone 6 (Anaerobic)",  min_value=zone_5 + 1,   max_value=200, step=1, value=zone_pcts["zone.6"])

    with col2:
        power_data["zone.1"] = {"pct": zone_1,      "low_pwr": 0,                                   "max_pwr": int(ftp * (zone_1 / 100))}
        power_data["zone.2"] = {"pct": zone_2,      "low_pwr": power_data["zone.1"]["max_pwr"] + 1, "max_pwr": int(ftp * (zone_2 / 100))}
        power_data["zone.3"] = {"pct": zone_3,      "low_pwr": power_data["zone.2"]["max_pwr"] + 1, "max_pwr": int(ftp * (zone_3 / 100))}
        power_data["zone.4"] = {"pct": zone_4,      "low_pwr": power_data["zone.3"]["max_pwr"] + 1, "max_pwr": int(ftp * (zone_4 / 100))}
        power_data["zone.5"] = {"pct": zone_5,      "low_pwr": power_data["zone.4"]["max_pwr"] + 1, "max_pwr": int(ftp * (zone_5 / 100))}
        power_data["zone.6"] = {"pct": zone_6,      "low_pwr": power_data["zone.5"]["max_pwr"] + 1, "max_pwr": int(ftp * (zone_6 / 100))}
        power_data["zone.7"] = {"pct": zone_6 + 1,  "low_pwr": power_data["zone.6"]["max_pwr"] + 1, "max_pwr": 9999}

        st.subheader("Power Bands (Watts)")
        st.divider()
        st.write(f"**Zone 1**: 0 - {int(ftp * (zone_1 / 100))} Watts")
        st.write(f"**Zone 2**: {power_data['zone.2']['low_pwr']} - {int(ftp * (zone_2 / 100))} Watts")
        st.write(f"**Zone 3**: {power_data['zone.3']['low_pwr']} - {int(ftp * (zone_3 / 100))} Watts")
        st.write(f"**Zone 4**: {power_data['zone.4']['low_pwr']} - {int(ftp * (zone_4 / 100))} Watts")
        st.write(f"**Zone 5**: {power_data['zone.5']['low_pwr']} - {int(ftp * (zone_5 / 100))} Watts")
        st.write(f"**Zone 6**: {power_data['zone.6']['low_pwr']} - {int(ftp * (zone_6 / 100))} Watts")
        st.write(f"**Zone 7**: {power_data['zone.7']['low_pwr']} - Unlimited Watts")
        st.divider()

    if st.button("Save Power Zones"):
        if power_data:
            last_record = power_data
            flat_power_data = {"timestamp": last_record["timestamp"]}

            for zone in ["zone.1", "zone.2", "zone.3", "zone.4", "zone.5", "zone.6", "zone.7"]:
                flat_power_data[f"{zone}.pct"]      = last_record[zone]["pct"]
                flat_power_data[f"{zone}.low_pwr"]  = last_record[zone]["low_pwr"]
                flat_power_data[f"{zone}.max_pwr"]  = last_record[zone]["max_pwr"]

            new_power_data_df = pd.DataFrame([flat_power_data])

            if not power_df.empty:
                power_df = pd.concat([power_df, new_power_data_df], ignore_index=True)
            else:
                power_df = new_power_data_df

            save_data(power_df.to_dict(orient="records"), POWER_FILE)
            st.success("Power zones saved successfully!")
        else:
            st.warning("No power data to save.")
            
    st.subheader("Saved Power Zones")
    if not power_df.empty:
        flattened_df = pd.json_normalize(power_df.to_dict(orient='records'))
        display_df = flattened_df[['zone.1.max_pwr','zone.2.max_pwr','zone.3.max_pwr','zone.4.max_pwr','zone.5.max_pwr','zone.6.max_pwr',]]
        st.dataframe(display_df)
else:
    st.warning("No FTP value found. Please set your FTP in the basic profile.")
