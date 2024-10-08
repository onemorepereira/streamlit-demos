import data
import streamlit as st
import pandas as pd
import math
import altair as alt

# This definitely could use some work...
def speed(gr: float, rpm: int = 100, dia: float = 29) -> float:
    return round((rpm * gr * dia * math.pi) / 60 / 19.55, 1)


st.set_page_config(
    page_title="Cycling Gear Calculator",
    layout="centered",
    page_icon="⚙️",
    initial_sidebar_state="collapsed"
)

st.title('Cycling Gear Calculator')

CHAINRINGS = data.CHAINRINGS
CASSETTES  = data.CASSETTES
CRANKARMS  = data.CRANKARMS

cassette  = st.selectbox("Select your cassette",       CASSETTES)
chainring = st.selectbox("Select your chainring",      CHAINRINGS)
crankarms = st.selectbox("Select your crank length",   CRANKARMS, index=3)
wheels    = st.text_input("Enter you total wheel + tire diameter (inches)", value=29)

cas_details = CASSETTES[cassette]
cha_details = CHAINRINGS[chainring]

cas_details_pd = pd.DataFrame(cas_details)
cha_details_pd = pd.DataFrame(cha_details)

st.title('Selections')

# Cassette Display
st.write("Cassette selected: **{}** | Cogs: **{}**".format(
    cassette, 
    len(cas_details), 
    ))

st.slider("Gearing Range", 
          value=[min(cas_details), max(cas_details)], 
          min_value=9, 
          max_value=56, 
          disabled=True)

# Chainring Display
st.write("Chainring selected: **{}** | Rings: **{}**".format(
    chainring, 
    len(cha_details),
    ))

st.slider("Gearing Range", 
          value=cha_details, 
          min_value=9,
          max_value=56, 
          disabled=True,
          )

# Crankarm Display
st.write("Crankarm selected",  crankarms, "cm")

# Wheel Diameter Display
st.write("Wheel diamater",  wheels, "inches")

# Concatenate the pivoted DF's
frames = [ 
          cas_details_pd.rename(columns={0: "cog_teeth"}),
          cha_details_pd.pivot(columns=0, values=0)
          ]

matrix = pd.concat(frames)

# Set the DF index to the cassette teeth count
matrix.set_index('cog_teeth', inplace=True)


for chain_teeth in matrix:
    matrix[chain_teeth] = chain_teeth / matrix[chain_teeth].index

matrix.dropna(subset=cha_details, inplace=True)

st.title("Gear Ratios")
st.dataframe(matrix.reset_index(), height=35*len(matrix)+38)

st.title("Speed")
# Quick slider to select target pedaling RPM
rpm = st.slider("Pedaling RPM", value = 90, min_value=30, max_value=120, step=5)
w   = matrix.apply(speed, args=(float(rpm), float(wheels)))

# Display theoretical max speed on each gear
st.dataframe(w, height=35*len(matrix)+38)

# Chart max speed on each gear
st.line_chart(data=w, x_label="Cassette Teeth", y_label="Speed (mph)")