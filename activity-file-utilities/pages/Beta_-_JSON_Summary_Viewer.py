import os
import json
import pandas as pd
import streamlit as st
from src import utils as h



# Function to process and load JSON files from a directory
def load_json_files(directory):
    data = []
    
    # Loop through all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            # Load the JSON data from each file
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                
                # Flatten the JSON and add to list
                for key, value in json_data.items():
                    flat_record = {"activity_id": key, **value}  # Add the activity ID as a column
                    data.append(flat_record)

    # Convert the list of records to a DataFrame
    df = pd.DataFrame(data)
    return df

def chart(df: pd.DataFrame):
    df['date'] = pd.to_datetime(df['activity_start_time'])
    filtered_df = df[df['date'] > '2024-01-01']
    grouped = filtered_df.groupby(filtered_df['date'].dt.to_period('D'))[[
        'activity_distance',
        'time_stopped',
        'time_coasting',
        'time_moving',
        'time_working',
        'time_total',
        'power_time_in_zone_1',
        'power_time_in_zone_2',
        'power_time_in_zone_3',
        'power_time_in_zone_4',
        'power_time_in_zone_5',
        'power_time_in_zone_6',
        'power_time_in_zone_7',
        'hr_time_in_zone_1',
        'hr_time_in_zone_2',
        'hr_time_in_zone_3',
        'hr_time_in_zone_4',
        'hr_time_in_zone_5',
        'te_aerobic',
        'te_anaerobic',
        'training_stress_score'
    ]].sum(numeric_only=True)
    return grouped


# Streamlit app interface
st.title("Local Directory JSON Loader")

# Text input for directory selection
directory = st.text_input("Enter the directory path containing JSON files:")

# Load data if a directory is provided
if directory:
    try:
        df = load_json_files(directory)
        
        if not df.empty:
            # # Show the DataFrame in Streamlit
            # st.subheader("Loaded Data")
            # st.write(df)

            # Optional: Show some basic statistics or analysis
            st.subheader("Summary Statistics")
            chart_data = chart(df)
            st.write(chart_data)
            
            st.scatter_chart(chart_data[[
                'training_stress_score',
                'time_total'
            ]],
                             size='time_total')
            
        else:
            st.write("No JSON files found in the provided directory.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.write("Please enter a valid directory path.")
