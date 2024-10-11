from datetime import datetime
from src.core import UserProfile
import pandas as pd
import src.utils as h
import streamlit as st


profile = UserProfile()

hr_data_df   = profile.get_all_hr_zones()
max_hr       = profile.get_max_hr()
rest_hr      = profile.get_resting_hr()

st.title("Heart Rate Zones Manager")
st.info(f"Current Max HR: {max_hr} BPM")

# Initialize heart rate zone percentages
zone_pcts = {f"zone.{i}": 0 for i in range(1, 6)}
if not hr_data_df.empty:
    latest_hr_data = hr_data_df.iloc[-1]
    for zone in range(1, 6):
        zone_key = f"zone.{zone}"
        zone_pcts[zone_key] = latest_hr_data[f"{zone_key}.pct"]

if max_hr > 0:
    timestamp = datetime.now().isoformat()
    hr_data = {"timestamp": timestamp}

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Heart Rate Zones")
        st.write("Expressed as a % of Max HR")
        zone_1 = st.number_input("ZONE 1 | RECOVERY",   min_value=0,          max_value=200, step=1, value=zone_pcts["zone.1"])
        zone_2 = st.number_input("ZONE 2 | ENDURANCE",  min_value=zone_1 + 1, max_value=200, step=1, value=zone_pcts["zone.2"])
        zone_3 = st.number_input("ZONE 3 | TEMPO",      min_value=zone_2 + 1, max_value=200, step=1, value=zone_pcts["zone.3"])
        zone_4 = st.number_input("ZONE 4 | THRESHOLD",  min_value=zone_3 + 1, max_value=200, step=1, value=zone_pcts["zone.4"])
        zone_5 = st.number_input("ZONE 5 | VO2 MAX",    min_value=zone_4 + 1, max_value=200, step=1, value=zone_pcts["zone.5"])


    with col2:
        hr_data["zone.1"] = {"pct": zone_1,      "low_hr": int(rest_hr * 1.75),               "max_hr": int(max_hr * (zone_1 / 100))}
        hr_data["zone.2"] = {"pct": zone_2,      "low_hr": hr_data["zone.1"]["max_hr"] + 1,   "max_hr": int(max_hr * (zone_2 / 100))}
        hr_data["zone.3"] = {"pct": zone_3,      "low_hr": hr_data["zone.2"]["max_hr"] + 1,   "max_hr": int(max_hr * (zone_3 / 100))}
        hr_data["zone.4"] = {"pct": zone_4,      "low_hr": hr_data["zone.3"]["max_hr"] + 1,   "max_hr": int(max_hr * (zone_4 / 100))}
        hr_data["zone.5"] = {"pct": zone_5,      "low_hr": hr_data["zone.4"]["max_hr"] + 1,   "max_hr": int(max_hr * 1.05)}

        st.subheader("Heart Rate Bands (BPM)")
        st.divider()
        # Zone 1 / Warm Up
        st.success(f"**Zone 1**: {hr_data['zone.1']['low_hr']} - {hr_data['zone.1']['max_hr']} ({hr_data['zone.1']['max_hr']} BPM)")
        # Zone 2 / Easy
        st.success(f"**Zone 2**: {hr_data['zone.2']['low_hr']} - {hr_data['zone.2']['max_hr']} ({hr_data['zone.2']['max_hr'] - hr_data['zone.2']['low_hr']} BPM)")
        # Zone 3 / Aerobic
        st.info(f"**Zone 3**:    {hr_data['zone.3']['low_hr']} - {hr_data['zone.3']['max_hr']} ({hr_data['zone.3']['max_hr'] - hr_data['zone.3']['low_hr']} BPM)")
        # Zone 4 / Threshold
        st.warning(f"**Zone 4**: {hr_data['zone.4']['low_hr']} - {hr_data['zone.4']['max_hr']} ({hr_data['zone.4']['max_hr'] - hr_data['zone.4']['low_hr']} BPM)")
        # Zone 5 / Maximum
        st.error(f"**Zone 5**:   {hr_data['zone.5']['low_hr']} - {hr_data['zone.5']['max_hr']} BPM")

    if st.button("Save Heart Rate Zones"):
        if hr_data:
            hr_data_json = {"timestamp": hr_data["timestamp"]}

            for zone in ["zone.1", "zone.2", "zone.3", "zone.4", "zone.5"]:
                hr_data_json[f"{zone}.pct"]      = hr_data[zone]["pct"]
                hr_data_json[f"{zone}.low_hr"]   = hr_data[zone]["low_hr"]
                hr_data_json[f"{zone}.max_hr"]   = hr_data[zone]["max_hr"]
            
            hr_data_new_df = pd.DataFrame(hr_data_json, index=[0])
            combined_df = pd.concat([hr_data_df, hr_data_new_df], ignore_index=True)
            h.save_data(combined_df.to_dict(orient='records'), profile.HR_FILE)
            st.success("Heart rate zones saved successfully!")
        else:
            st.warning("No heart rate data to save.")

    st.subheader("Saved Heart Rate Zones")
    if not hr_data_df.empty:
        display_df = profile.get_all_hr_zones()[['timestamp', 'zone.1.max_hr', 'zone.2.max_hr', 'zone.3.max_hr', 'zone.4.max_hr', 'zone.5.max_hr']]
        st.dataframe(display_df)
else:
    st.warning("No Max HR value found. Please set your Max HR in the basic profile.")
