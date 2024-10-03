
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
            st.subheader("Heart Rate")
            st.metric(label='Avg BPM ❤️',   value=summary['Avg BPM ❤️'])
            st.metric(label='Max BPM ❤️',   value=summary['Max BPM ❤️'])
            st.divider()
            
            st.subheader("Temps")
            st.metric(label='Avg ℃ 🌡️',    value=summary['Avg ℃ 🌡️'])
            st.metric(label='Max ℃ 🌡️',    value=summary['Max ℃ 🌡️'])
            
        with col2:
            st.subheader("Power")
            st.metric(label='Avg W ⚡',     value=summary['Avg W ⚡'])
            st.metric(label='Max W ⚡',     value=summary['Max W ⚡'])
            st.divider()
            
            st.subheader("Intensity")
            st.metric(label='NP® W ⚡',     value=summary['NP® W ⚡'])
            st.metric(label='IF®',          value=summary['IF®'])
            st.metric(label='TSS®',         value=summary['TSS®'])
        
        with col3:
            st.subheader("Power Avgs")
            st.metric(label='Max W 30s ⚡', value=summary['Max W 30s ⚡'])
            st.metric(label='Max W 5m ⚡',  value=summary['Max W 5m ⚡'])
            # st.metric(label='Max W 10m ⚡', value=summary['Max W 10m ⚡'])
            st.metric(label='Max W 20m ⚡', value=summary['Max W 20m ⚡'])
            st.metric(label='Max W 60m ⚡', value=summary['Max W 60m ⚡'])
            st.divider()
            
            st.subheader("Speed")
            st.metric(label='Avg kmh 🚴',   value=summary['Avg kmh 🚴'])
            st.metric(label='Max kmh 🚴',   value=summary['Max kmh 🚴'])
            st.metric(label='Dist km 📏',   value=summary['Dist km 📏'])
            
        with col4:
            st.subheader("Cadence")
            st.metric(label='Avg RPM 🌪️',   value=summary['Avg RPM 🌪️'])
            st.metric(label='Max RPM 🌪️',   value=summary['Max RPM 🌪️'])
            st.divider()
            
            st.subheader("Time")
            st.metric(label='Coasting',     value=summary['Coasting'].iloc[0])
            st.metric(label='Stopped',      value=summary['Stopped'].iloc[0])
            st.metric(label='Working',      value=summary['Working'].iloc[0])
            st.metric(label='Total',        value=summary['Total'].iloc[0])
            
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
