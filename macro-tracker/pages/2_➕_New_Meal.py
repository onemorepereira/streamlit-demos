import streamlit as st
import pandas as pd
import os
import logging
from datetime import date

# Setup logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)

def write_df_to_json(df: pd.DataFrame, file_path: str, orient: str = 'records', indent: int = 4, append: bool = True):
    try:
        if append and os.path.exists(file_path):
            existing_df = pd.read_json(file_path, orient=orient)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_json(file_path, orient=orient, indent=indent)
        logging.info("DataFrame written to {} successfully.".format(file_path))

    except Exception as e:
        logging.error("Failed to write DataFrame to JSON: {}".format(e))

def load_df_from_json(file_path: str, orient: str = 'records'):
    try:
        df = pd.read_json(file_path, orient=orient)
        logging.info("Data loaded from {} successfully.".format(file_path))
        return df
    except Exception as e:
        logging.error("Failed to load data from JSON: {}".format(e))
        return None

st.set_page_config(
    layout="wide",
    page_icon="➕")

st.sidebar.success("Navigation")

# Preload a Journal object
if "journal_items" not in st.session_state:
    st.session_state["journal_items"] = []
JOURNAL_FILE = "journal.json"

if os.path.exists(JOURNAL_FILE):
    journal_df = load_df_from_json(JOURNAL_FILE)
    if journal_df is not None:
        st.session_state["journal_items"] = journal_df.to_dict(orient='records')

# Preload a food items object
if "items" not in st.session_state:
    st.session_state["items"] = []
    
NUTRITION_VALUES = "nutrition.json"
if os.path.exists(NUTRITION_VALUES):
    nutrition_df = load_df_from_json(NUTRITION_VALUES)
    if nutrition_df is not None:
        st.session_state["items"] = nutrition_df.to_dict(orient='records')

# Streamlit App Title
st.title("Nutritional Calculator")

# Ingredient Selection
st.subheader("Select Food Items")
selected_ingredients = st.multiselect("Choose Food(s):", nutrition_df['Name'], key='multiselect')

# Initialize an empty list to store results
result_list = []

# Use session state to store dynamic values for total weights
if "quantities" not in st.session_state:
    st.session_state["quantities"] = {}
if "weights" not in st.session_state:
    st.session_state["weights"] = {}
total_weight_all_ingredients = 0

# Display food items and quantities with real-time weight updates
if selected_ingredients:
    for ingredient in selected_ingredients:
        ingredient_data = nutrition_df[nutrition_df['Name'] == ingredient].iloc[0]

        st.write(f"**Details for {ingredient}**")

        # Set the default quantity value
        if ingredient not in st.session_state["quantities"]:
            st.session_state["quantities"][ingredient] = 1.0

        # User input for quantity (dynamic update)
        quantity = st.number_input(
            "How much or many of {} (g):".format(ingredient),
            min_value=0.0,
            value=st.session_state["quantities"][ingredient],
            key=f"quantity_{ingredient}"
        )

        # Store the quantity for future updates
        st.session_state["quantities"][ingredient] = quantity

        # Dynamically calculate total weight
        total_weight = quantity * ingredient_data["Weight (g)"]
        st.session_state["weights"][ingredient] = total_weight

        st.write("Total Weight for {}: {:.2f} g".format(ingredient, total_weight))

        # Accumulate total weight of all ingredients
        total_weight_all_ingredients += total_weight

# Display the total weight of all ingredients
st.write("### Total Weight: {:.2f} g".format(total_weight_all_ingredients))

# Form for submitting the journal entry
with st.form(key="nutrition_form", clear_on_submit=True):
    # User selects the date for the journal entry
    entry_date = st.date_input("Select the date for this entry:", value=date.today())

    # Add the results to a list for submission
    for ingredient in selected_ingredients:
        if ingredient in st.session_state["weights"]:
            ingredient_data = nutrition_df[nutrition_df['Name'] == ingredient].iloc[0]
            quantity        = st.session_state["quantities"][ingredient]
            total_weight    = st.session_state["weights"][ingredient]

            # Calculate the totals based on quantity
            total_fat       = ingredient_data["Fat (g)"] * quantity
            total_carbs     = ingredient_data["Carbs (g)"] * quantity
            total_protein   = ingredient_data["Protein (g)"] * quantity
            total_calories  = ingredient_data["Calories"] * quantity
            caloric_density = total_calories / total_weight if total_weight != 0 else 0
            fat_density     = total_fat / total_weight if total_weight != 0 else 0
            carb_density    = total_carbs / total_weight if total_weight != 0 else 0
            protein_density = total_protein / total_weight if total_weight != 0 else 0

            # Append the result to the list
            result_list.append({
                "Date":                     entry_date,
                "Name":                     ingredient,
                "Quantity (g)":             quantity,
                "Total Weight (g)":         total_weight,
                "Total Fat (g)":            total_fat,
                "Total Carbs (g)":          total_carbs,
                "Total Protein (g)":        total_protein,
                "Total Calories":           total_calories,
                "Caloric Density (cal/g)":  caloric_density,
                "Fat Density (g/g)":        fat_density,
                "Carb Density (g/g)":       carb_density,
                "Protein Density (g/g)":    protein_density
            })
            
    results_df = pd.DataFrame(result_list)
    st.write(results_df)
    
    # Submit button inside the form
    submit_button = st.form_submit_button(label="Save this meal")
        

# If the form is submitted, save the results and handle validation
if submit_button:
    if not result_list:
        st.warning("No valid entries to save. Please select ingredients and ensure quantities are greater than zero.")
    else:
        # Save results to DataFrame
        st.subheader("Calculated Results")

        # Save to file
        write_df_to_json(df=results_df, file_path=JOURNAL_FILE)
        st.success("Journal entry saved.")
