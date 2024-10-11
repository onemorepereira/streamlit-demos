import json
import pandas as pd
import streamlit as st

# Title of the application
st.title("JSON to DataFrame Viewer")

# File uploader for the JSON file
uploaded_file = st.file_uploader("Upload a JSON file", type=["json"])

if uploaded_file is not None:
    # Load the JSON data
    try:
        json_data = json.load(uploaded_file)
        df = pd.json_normalize(json_data)
        
        pattern = 'unknown'
        columns_to_drop = [col for col in df.columns if pattern in col]
        df.drop(columns=columns_to_drop, inplace=True)
        df.dropna(subset=['timestamp.value'], inplace=True)
        
        if df is not None:
            st.subheader("DataFrame Representation")
            st.dataframe(df)
            
            df_dict = []
            for index, column in enumerate(df.columns):
                if 'unknown' not in column:
                    col = {
                        'id':  index,
                        'column': column
                    }
                    df_dict.append(col)
            st.dataframe(df_dict)
    except json.JSONDecodeError:
        st.error("Invalid JSON file format")
