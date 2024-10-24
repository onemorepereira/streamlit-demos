import streamlit as st
import os
import logging
from datetime import date
import altair as alt
import helper as h

# Setup logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)
st.set_page_config(
    layout="centered",
    page_icon="🔍")

st.sidebar.success("Navigation")

JOURNAL_FILE = "journal.json"
if os.path.exists(JOURNAL_FILE):
    journal_df = h.load_df_from_json(JOURNAL_FILE)
    if journal_df is not None:
        st.session_state["journal_items"] = journal_df.to_dict(orient='records')
        
        # Some massaging required
        aggregated      = h.agg_df(df=journal_df)
        wky_summary     = h.weekly_nutrient_summary(journal_df)
 
        m2w_week =  wky_summary['week_start'].iloc[-3].strftime('%m/%d/%Y')
        lst_week =  wky_summary['week_start'].iloc[-2].strftime('%m/%d/%Y')
        this_week = wky_summary['week_start'].iloc[-1].strftime('%m/%d/%Y')
        
        st.subheader("Last Week vs {}".format(m2w_week))
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            st.metric(label='Proteins', value="{:,.0f}".format(
                round(wky_summary['total_protein'].iloc[-2])), 
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_protein'].iloc[-2] - wky_summary['total_protein'].iloc[-3])
                          ))
            st.divider()
        with col2:
            st.metric(label='Carbohydrates', value="{:,.0f}".format(
                round(wky_summary['total_carbs'].iloc[-2])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_carbs'].iloc[-2] - wky_summary['total_carbs'].iloc[-3])
                          ))
            st.divider()
        with col3:
            st.metric(label='Fats', value="{:,.0f}".format(
                round(wky_summary['total_fat'].iloc[-2])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_fat'].iloc[-2] - wky_summary['total_fat'].iloc[-3])
                          ))
            st.divider()
        with col4:
            st.metric(label='Calories', value="{:,.0f}".format(
                round(wky_summary['total_calories'].iloc[-2])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_calories'].iloc[-2] - wky_summary['total_calories'].iloc[-3])
                          ))
            st.divider()
            
        st.subheader("This Week vs {}".format(lst_week))
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            st.metric(label='Proteins', value="{:,.0f}".format(
                round(wky_summary['total_protein'].iloc[-1])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_protein'].iloc[-1] - wky_summary['total_protein'].iloc[-2])
                          ))
            st.divider()
        with col2:
            st.metric(label='Carbohydrates', value="{:,.0f}".format(
                round(wky_summary['total_carbs'].iloc[-1])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_carbs'].iloc[-1] - wky_summary['total_carbs'].iloc[-2])
                          ))
            st.divider()
        with col3:
            st.metric(label='Fats', value="{:,.0f}".format(
                round(wky_summary['total_fat'].iloc[-1])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_fat'].iloc[-1] - wky_summary['total_fat'].iloc[-2])
                          ))
            st.divider()
        with col4:
            st.metric(label='Calories', value="{:,.0f}".format(
                round(wky_summary['total_calories'].iloc[-1])),
                      delta='{:,.0f}'.format(
                          round(wky_summary['total_calories'].iloc[-1] - wky_summary['total_calories'].iloc[-2])
                          ))
            st.divider()
                   
        # Display the DataFrames
        st.write("### Journal Entries")
        st.dataframe(journal_df)
        
        st.write('### Primary Macro Sources by week')
        st.dataframe(wky_summary.set_index('week_start'))
else:
    st.write("No journal file found.")
