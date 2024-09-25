import streamlit as st
import pandas as pd
import os
import logging
import helper as h

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)
st.set_page_config(
    layout="centered",
    page_icon="🍲")

st.sidebar.success("Navigation")

# Initialize session state for items and form inputs
if "items" not in st.session_state:
    st.session_state["items"] = []

if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "itemName": "",
        "itemDescription": "",
        "itemWeight": 0.01,
        "itemFat": 0.0,
        "itemCarbs": 0.0,
        "itemProtein": 0.0,
        "itemCalories": 0.0,
    }

# Attempt to load data from nutrition.json
NUTRITION_FILE = "nutrition.json"
if os.path.exists(NUTRITION_FILE):
    df = h.load_df_from_json(NUTRITION_FILE)
    if df is not None:
        st.session_state["items"] = df.to_dict(orient='records')

# Title for the app
st.title("Nutritional Database")

# Define the form for user input
with st.form("nutrition-item", clear_on_submit=True):
    st.write("##### Add a new food item")
    itemName        = st.text_input(label="Name", value=st.session_state["form_data"]["itemName"])
    itemDescription = st.text_input(label="Description", value=st.session_state["form_data"]["itemDescription"])
    itemWeight      = st.number_input(label="Weight", min_value=0.01, value=st.session_state["form_data"]["itemWeight"], help="Enter the weight in grams.")
    itemFat         = st.number_input(label="Fat", min_value=0.0, value=st.session_state["form_data"]["itemFat"], help="Enter fat content in grams.")
    itemCarbs       = st.number_input(label="Carbs", min_value=0.0, value=st.session_state["form_data"]["itemCarbs"], help="Enter carbs content in grams.")
    itemProtein     = st.number_input(label="Protein", min_value=0.0, value=st.session_state["form_data"]["itemProtein"], help="Enter protein content in grams.")
    itemCalories    = st.number_input(label="Calories", min_value=0.0, value=st.session_state["form_data"]["itemCalories"], help="Enter calories content.")

    # Submit button
    submitted = st.form_submit_button(label="Save")

    # Validation logic
    if submitted:
        if not itemName or not itemDescription or itemWeight <= 0 or itemFat < 0 or itemCarbs < 0 or itemProtein < 0 or itemCalories < 0:
            st.error("All fields must be filled with valid values before submission.")
        else:
            # Automatically calculate caloric density and macro nutrient densities
            itemCaloricDensity  = itemCalories / itemWeight
            itemFatDensity      = itemFat / itemWeight
            itemCarbDensity     = itemCarbs / itemWeight
            itemProteinDensity  = itemProtein / itemWeight

            # Append the current item as a dictionary to the session state list
            st.session_state["items"].append({
                "Name":                     itemName,
                "Description":              itemDescription,
                "Weight (g)":               itemWeight,
                "Fat (g)":                  itemFat,
                "Carbs (g)":                itemCarbs,
                "Protein (g)":              itemProtein,
                "Calories":                 itemCalories,
                "Caloric Density (cal/g)":  itemCaloricDensity,
                "Fat Density (g/g)":        itemFatDensity,
                "Carb Density (g/g)":       itemCarbDensity,
                "Protein Density (g/g)":    itemProteinDensity
            })
            st.success(f"Item '{itemName}' saved successfully!")

            # Clear the form inputs after submission
            st.session_state["form_data"] = {
                "itemName":         "",
                "itemDescription":  "",
                "itemWeight":       0.01,
                "itemFat":          0.0,
                "itemCarbs":        0.0,
                "itemProtein":      0.0,
                "itemCalories":     0.0,
            }

# Create a pandas DataFrame from the session state item list and display it
if st.session_state["items"]:
    df = pd.DataFrame(st.session_state["items"])
    h.write_df_to_json(df=df, file_path=NUTRITION_FILE)
    st.subheader("Saved Nutrition Items")
    table = st.data_editor(df, height=35*len(df)+38)
    
    if not table.equals(df):
        h.write_df_to_json(df = table, file_path=NUTRITION_FILE)
