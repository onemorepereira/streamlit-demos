
from streamlit_folium import st_folium
import streamlit as st
import helper as h


st.set_page_config(
    page_title="FIT/GPX File Utilities",
    layout="wide",
    page_icon="🗺️"
)

st.title("FIT/GPX File Utilities")
ftp           = st.number_input("Functional Threshold Power (FTP): ", 200)
uploaded_file = st.file_uploader("Choose a FIT/GPX file", type=["fit", "gpx"])

if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/fits":
            activity = h.parse_fit_file(uploaded_file)
            summary  = h.get_summary(activity, ftp, format="fit")
        elif uploaded_file.type == "application/gpx+xml":
            activity = h.gpx_to_dataframe(uploaded_file)
            summary  = h.get_summary(activity, ftp, format="gpx")
        
    except Exception as e:
        st.error(e)

    try:
        col1, col2, col3, col4, col5 = st.columns([1,1,1,1,4], vertical_alignment='top', gap='small')
        with col1:
            st.subheader("Time")
            st.metric(label='Coasting 🕰️',  value=summary['time_coasting'].iloc[0])
            st.metric(label='Stopped 🕰️',   value=summary['time_stopped'].iloc[0])
            st.metric(label='Working 🕰️',   value=summary['time_working'].iloc[0])
            st.metric(label='Total 🕰️',     value=summary['time_total'].iloc[0])
            
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
            
        with col5:
            st.subheader("Map")
            route_map = h.plot_map(activity)
            if route_map:
                st_folium(route_map, use_container_width=True, key="map", returned_objects=[])
            else:
                st.write("No latitude/longitude data available in this FIT file.")
    except Exception as e:
        st.error(e)

else:
    st.info("Please upload a FIT or GPX file to inspect.")
