import json
import os
import streamlit as st


# Helper function to load the data from a selected JSON file
def load_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Helper function to extract and display metrics
def display_metrics(data):
    key = list(data.keys())[0]
    activity_data = data[key]
    
    # Columns for displaying various data
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.subheader("Heart Rate")
        st.metric(label="Max HR (bpm) ❤️", value=activity_data.get("hr_max", "N/A"))
        st.metric(label="Avg HR (bpm) ❤️", value=activity_data.get("hr_average", "N/A"))
        st.metric(label="Resting HR (bpm) ❤️", value=activity_data.get("bio_hr_resting", "N/A"))
        st.metric(label="HR Zone 1 (s)", value=activity_data.get("hr_time_in_zone_1", "N/A"))
        st.metric(label="HR Zone 2 (s)", value=activity_data.get("hr_time_in_zone_2", "N/A"))
        st.metric(label="HR Zone 3 (s)", value=activity_data.get("hr_time_in_zone_3", "N/A"))
        st.metric(label="HR Zone 4 (s)", value=activity_data.get("hr_time_in_zone_4", "N/A"))
        st.metric(label="HR Zone 5 (s)", value=activity_data.get("hr_time_in_zone_5", "N/A"))

    with col2:
        st.subheader("Power")
        st.metric(label="Avg Power (W) ⚡", value=activity_data.get("power_average", "N/A"))
        st.metric(label="Max Power (W) ⚡", value=activity_data.get("power_max", "N/A"))
        st.metric(label="Normalized Power (W) ⚡", value=activity_data.get("power_normalized", "N/A"))
        st.metric(label="Power Zone 1 (s)", value=activity_data.get("power_time_in_zone_1", "N/A"))
        st.metric(label="Power Zone 2 (s)", value=activity_data.get("power_time_in_zone_2", "N/A"))
        st.metric(label="Power Zone 3 (s)", value=activity_data.get("power_time_in_zone_3", "N/A"))
        st.metric(label="Power Zone 4 (s)", value=activity_data.get("power_time_in_zone_4", "N/A"))
        st.metric(label="Power Zone 5 (s)", value=activity_data.get("power_time_in_zone_5", "N/A"))

    with col3:
        st.subheader("Intensity & Speed")
        st.metric(label="Intensity Factor", value=activity_data.get("intensity_factor", "N/A"))
        st.metric(label="TSS®", value=activity_data.get("training_stress_score", "N/A"))
        st.metric(label="Avg Speed (km/h) 🚴", value=activity_data.get("speed_average", "N/A"))
        st.metric(label="Max Speed (km/h) 🚴", value=activity_data.get("speed_max", "N/A"))
        st.metric(label="Distance (km) 📏", value=activity_data.get("activity_distance", "N/A"))

# Streamlit Page Setup
st.set_page_config(
    page_title="Browse JSON Activity Files",
    layout="wide",
    page_icon="📊"
)

st.title("Browse JSON Activity Files")

# Directory selection
directory = st.text_input("Enter the directory path containing JSON files:", value="")

if os.path.isdir(directory):
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    if json_files:
        selected_file = st.selectbox("Select a JSON file", json_files)
        
        # Load the selected JSON file
        file_path = os.path.join(directory, selected_file)
        data = load_json_file(file_path)

        if data:
            st.success(f"Displaying data for: {selected_file}")
            
            # Display the metrics in a structured format
            display_metrics(data)
            
            # Display the full JSON data (optional)
            if st.checkbox("Show raw JSON data", value=False):
                st.json(data)
        else:
            st.error("Failed to load the JSON file.")
    else:
        st.error("No JSON files found in the selected directory.")
else:
    st.error("The directory path is invalid. Please provide a valid path.")
