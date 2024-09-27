import streamlit as st
import helper as h


st.set_page_config(
    page_title="GPX Comparison",
    layout="wide",
    page_icon="🗺️"
)

st.title("GPX File Comparison Tool")

# Upload GPX files
uploaded_file1 = st.file_uploader("Choose the first GPX file", type="gpx")
uploaded_file2 = st.file_uploader("Choose the second GPX file", type="gpx")

display_median = st.checkbox('Display median charts, too')

# Check if both files are uploaded
if uploaded_file1 is not None and uploaded_file2 is not None:
    # Convert the uploaded GPX files to DataFrames
    gpx_df1 = h.gpx_to_dataframe(uploaded_file1)
    gpx_df2 = h.gpx_to_dataframe(uploaded_file2)
    
    # Aggregate data
    agg_df1 = h.aggregate_gpx_data(gpx_df1)
    agg_df2 = h.aggregate_gpx_data(gpx_df2)

    st.subheader("Comparison Charts")
    # Speed Comparison
    if not agg_df1['mean_speed'].isnull().all() and not agg_df2['mean_speed'].isnull().all():
        combined_speed_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_speed', 'Speed Comparison', 'Speed (mph)')
        st.altair_chart(combined_speed_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_speed'].isnull().all() and not agg_df2['median_speed'].isnull().all():
            combined_speed_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_speed', 'Speed Comparison', 'Speed (mph)')
            st.altair_chart(combined_speed_chart, use_container_width=True)

    # Power Comparison
    if not agg_df1['mean_power'].isnull().all() and not agg_df2['mean_power'].isnull().all():
        combined_power_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_power', 'Power Comparison', 'Power (W)')
        st.altair_chart(combined_power_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_power'].isnull().all() and not agg_df2['median_power'].isnull().all():
            combined_power_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_power', 'Power Comparison', 'Power (W)')
            st.altair_chart(combined_power_chart, use_container_width=True)
        
    # Heart Rate Comparison
    if not agg_df1['mean_heart_rate'].isnull().all() and not agg_df2['mean_heart_rate'].isnull().all():
        combined_hr_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_heart_rate', 'Heart Rate Comparison', 'Heart Rate (bpm)')
        st.altair_chart(combined_hr_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_heart_rate'].isnull().all() and not agg_df2['median_heart_rate'].isnull().all():
            combined_hr_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_heart_rate', 'Heart Rate Comparison', 'Heart Rate (bpm)')
            st.altair_chart(combined_hr_chart, use_container_width=True)
        
    # Temperature Comparison
    if not agg_df1['mean_temperature'].isnull().all() and not agg_df2['mean_temperature'].isnull().all():
        combined_temp_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_temperature', 'Temperature Comparison', 'Temperature (℉)')
        st.altair_chart(combined_temp_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_temperature'].isnull().all() and not agg_df2['median_temperature'].isnull().all():
            combined_temp_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_temperature', 'Temperature Comparison', 'Temperature (℉)')
            st.altair_chart(combined_temp_chart, use_container_width=True)
        
    # Elevation Comparison
    if not agg_df1['mean_elevation'].isnull().all() and not agg_df2['mean_elevation'].isnull().all():
        combined_elev_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_elevation', 'Elevation Comparison', 'Elevation (ft)')
        st.altair_chart(combined_elev_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_elevation'].isnull().all() and not agg_df2['median_elevation'].isnull().all():
            combined_elev_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_elevation', 'Elevation Comparison', 'Elevation (ft)')
            st.altair_chart(combined_elev_chart, use_container_width=True)
        
    # Cadence Comparison
    if not agg_df1['mean_cadence'].isnull().all() and not agg_df2['mean_cadence'].isnull().all():
        combined_elev_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'mean_cadence', 'Cadence Comparison', 'rpm')
        st.altair_chart(combined_elev_chart, use_container_width=True)
    if display_median:
        if not agg_df1['median_cadence'].isnull().all() and not agg_df2['median_cadence'].isnull().all():
            combined_elev_chart = h.create_chart(uploaded_file1.name, uploaded_file2.name, agg_df1, agg_df2, 'median_cadence', 'Cadence Comparison', 'rpm')
            st.altair_chart(combined_elev_chart, use_container_width=True)