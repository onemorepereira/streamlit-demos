
from streamlit_folium import st_folium
import streamlit as st
import helper as h
import os


PROFILE_FILE        = "basic_profile.json"
HR_FILE             = 'hr_profile.json'
FTP                 = h.get_latest_ftp(PROFILE_FILE)
MAX_HR              = h.get_latest_maxhr(PROFILE_FILE)
RESTING_HR          = h.get_latest_restinghr(PROFILE_FILE)
HR_ZONES            = h.load_data(HR_FILE)
LATEST_HR_ZONES     = h.get_latest_hr_zones(HR_ZONES)

st.set_page_config(
    page_title="FIT/GPX File Browser",
    layout="wide",
    page_icon="🗺️"
)

st.title("FIT/GPX File Browser")

display_activity_df = st.checkbox("Display data tables", value=None)

col1, col2, col3 = st.columns([1,1,1])
with col1:
    try:
        st.success(f"FTP Setting: {FTP}W")
    except Exception as e:
        st.error(f"Could not find a valid FTP value: {e}")
with col2:
    try:
        st.success(f"Max Heart Rate Setting: {MAX_HR}bpm")
    except Exception as e:
        st.error(f"Could not find a valid Max HR value: {e}")
with col3:
    try:
        st.success(f"Resting Heart Rate Setting: {RESTING_HR}bpm")
    except Exception as e:
        st.error(f"Could not find a valid Resting HR value: {e}")
    
# Directory selection
directory = st.text_input("Specify the directory containing FIT/GPX files:", './samples')

# List files in the directory and allow user to select one
if directory:
    try:
        files = [f for f in sorted(os.listdir(directory)) if f.endswith(('.fit', '.gpx'))]
        if files:
            selected_file = st.selectbox("Choose a FIT/GPX file:", files)
            
            if selected_file:
                file_path = os.path.join(directory, selected_file)
                
                try:
                    if selected_file.endswith(".fit"):
                        with open(file_path, "rb") as uploaded_file:
                            parsed_fit      = h.parse_fit_file(uploaded_file)
                            activity        = parsed_fit[0]
                            event_data      = parsed_fit[1]
                            event_time      = parsed_fit[1]['timestamp'].iloc[0] if parsed_fit[1]['timestamp'].iloc[0] else None
                            sport           = parsed_fit[2]['sport'].iloc[-1]
                            summary         = h.get_summary(activity, FTP, format="fit")
                            hr_zone_time    = h.calculate_hr_zone_time(activity, LATEST_HR_ZONES)
                            activity_te     = h.calculate_training_effect(hr_zone_time, float(summary['intensity_factor'].iloc[0]))
                    
                    elif selected_file.endswith(".gpx"):
                        with open(file_path, "rb") as uploaded_file:
                            activity = h.gpx_to_dataframe(uploaded_file)
                            summary  = h.get_summary(activity, FTP, format="gpx")
                    
                except Exception as e:
                    st.error(f"An error occurred while processing the file: {e}")
        else:
            st.warning("No FIT or GPX files found in the specified directory.")
    except Exception as e:
        st.error(f"An error occurred while accessing the directory: {e}")

    col1, col2 = st.columns([1,1])
    with col1:
        st.info(f"**Activity: {str.title(sport)}**")
    with col2:
        st.info(f"**Date: {h.format_nice_date(event_time)}**")
        
    try:
        col1, col2, col3, col4, col5 = st.columns([1,1,1,1,4], vertical_alignment='top', gap='small')
        with col1:
            st.subheader("Time")
            st.metric(label='Coasting 🕰️',  value=summary['time_coasting_string'].iloc[0])
            st.metric(label='Stopped 🕰️',   value=summary['time_stopped_string'].iloc[0])
            st.metric(label='Working 🕰️',   value=summary['time_working_string'].iloc[0])
            st.metric(label='Total 🕰️',     value=summary['time_total_string'].iloc[0])
            
            if summary['temp_avg'].iloc[0] != 0:
                st.divider()
                st.subheader("Temps")
                st.metric(label='Avg ℃ 🌡️', value=summary['temp_avg'])
                st.metric(label='Max ℃ 🌡️', value=summary['temp_max'])
            
        with col2:
            st.subheader("Power")
            st.metric(label='Avg W ⚡', value=summary['power_avg'])
            st.metric(label='Max W ⚡', value=summary['power_max'])
            st.divider()
            
            st.subheader("Intensity")
            st.metric(label='NP® W ⚡', value=summary['power_normalized'])
            st.metric(label='IF®',      value=summary['intensity_factor'])
            st.metric(label='TSS®',     value=summary['tss'])
        
        with col3:
            st.subheader("Power Avgs")
            st.metric(label='Max W 30s ⚡', value=summary['power_max_avg_30s'])
            st.metric(label='Max W 5m ⚡',  value=summary['power_max_avg_5m'])
            if summary['power_max_avg_10m'].iloc[0] != 0:
                st.metric(label='Max W 10m ⚡', value=summary['power_max_avg_10m'])
            if summary['power_max_avg_20m'].iloc[0] != 0:
                st.metric(label='Max W 20m ⚡', value=summary['power_max_avg_20m'])
            if summary['power_max_avg_60m'].iloc[0] != 0:
                st.metric(label='Max W 60m ⚡', value=summary['power_max_avg_60m'])
            st.divider()
            
            st.subheader("Speed")
            st.metric(label='Avg kmh 🚴',   value=summary['speed_avg'])
            st.metric(label='Max kmh 🚴',   value=summary['speed_max'])
            st.metric(label='Dist km 📏',   value=summary['distance_total'])
            
        with col4:
            st.subheader("Cadence")
            st.metric(label='Avg RPM 🌪️',   value=summary['cadence_avg'])
            st.metric(label='Max RPM 🌪️',   value=summary['cadence_max'])
            st.divider()
            
            st.subheader("Heart Rate")
            st.metric(label='Avg BPM ❤️',   value=summary['hr_avg'])
            st.metric(label='Max BPM ❤️',   value=summary['hr_max'])
            st.divider()

            st.subheader("Training Effect")
            st.metric(label='Aerobic TE',    value=activity_te[0])
            st.metric(label='Anaerobic TE',  value=activity_te[1])
            

            
        with col5:
            st.subheader("Map")
            route_map = h.plot_map(activity)
            if route_map:
                st_folium(route_map, use_container_width=True, key="map", returned_objects=[])
            else:
                st.write("No latitude/longitude data available in this FIT file.")
        
    except Exception as e:
        st.error(e)

    if display_activity_df:
        st.dataframe(activity)
        st.dataframe(summary)
        st.dataframe(hr_zone_time)
else:
    st.info("Please upload a FIT or GPX file to inspect.")
