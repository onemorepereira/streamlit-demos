import streamlit as st
import logging


logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)
st.set_page_config(
    layout="centered",
    page_icon="🏠")

st.sidebar.success("Navigation")

st.title("Welcome to your macro nutrition Tracker")

st.write("""
         You can easily record, track, and explore your consumption of macro nutrients (fat, protein, and carbohydrates), 
         as well as your overall caloric consumption, and net weight food intake.
         
         Start by creating or adding basic meals to the database (🍲), with weight, carb/fat/protein details, as well as calories.
         Macro Tracker will automatically determine each meals macro density.
         
         You can then record your actual meals (➕), explore them in a data table (🔍) or explore some neat visualizations (📊).
         """)

