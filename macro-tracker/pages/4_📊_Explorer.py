import streamlit as st
import pandas as pd
import os
import logging
from datetime import date
import altair as alt
import helper as h

# Setup logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)
st.set_page_config(
    layout="centered",
    page_icon="📊")

st.sidebar.success("Navigation")

JOURNAL_FILE = "journal.json"
if os.path.exists(JOURNAL_FILE):
    journal_df = h.load_df_from_json(JOURNAL_FILE)
    if journal_df is not None:
        st.session_state["journal_items"] = journal_df.to_dict(orient='records')
        
        # Some massaging required
        aggregated      = h.agg_df(df=journal_df)
        melted_data     = aggregated.melt(id_vars='Date', var_name='macros', value_name='amount')
        
        # 7 day rolling average
        melted_data['Date'] = pd.to_datetime(melted_data['Date'])
        melted_data         = melted_data.sort_values(by=['macros', 'Date'])
        
        melted_data.set_index('Date', inplace=True)
        melted_data['Running Average'] = melted_data.groupby('macros')['amount'].rolling('14D', min_periods=1).mean().reset_index(level=0, drop=True)
        
        melted_data.reset_index(inplace=True)
        
        cals_data     = melted_data[melted_data['macros'] == 'Total Calories']
        weight_data   = melted_data[melted_data['macros'] == 'Total Weight (g)']
        
        melted_data = melted_data[melted_data['macros'] != 'Total Calories']
        melted_data = melted_data[melted_data['macros'] != 'Total Weight (g)']
        
        
        macro_avg_chart = alt.Chart(data=melted_data,).mark_line().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Running Average):Q', 
                      title='Grams'
                      ),
            color = alt.Color('macros',
                              scale=alt.Scale(scheme="darkred"),
                              legend=alt.Legend(orient='top')
                              ).title('7 Day Running Average')
            )
        
        cal_avg_chart = alt.Chart(data=cals_data,).mark_line().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Running Average):Q', 
                      title='Calories'
                      ),
            color = alt.Color('macros', 
                              scale=alt.Scale(scheme="darkred"),
                              legend=alt.Legend(orient='top'),
                              ).title('7 Day Running Average')
            )

        weight_avg_chart = alt.Chart(data=weight_data,).mark_line().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Running Average):Q', 
                      title='Weight'
                      ),
            color = alt.Color('macros', 
                              scale=alt.Scale(scheme="darkred"),
                              legend=alt.Legend(orient='top'),
                              ).title('7 Day Running Average')
            )
                                  
        # Leave only carbs, protein, and fat
        filtered_data   = melted_data[melted_data['macros'] != 'Total Calories']
        filtered_data   = filtered_data[filtered_data['macros'] != 'Total Weight (g)']
        
        # Chart Macro nutrients: proteins, fats, and carbs
        macro_chart = alt.Chart(data=filtered_data,).mark_bar().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(amount):Q', 
                      stack='normalize',
                      title='Grams'
                      ),
            color = alt.Color('macros',
                              scale=alt.Scale(scheme="darkred"),
                              legend=alt.Legend(orient='top')
                              ).title('Macros')
            )

        # Chart total food weight intake in grams
        weight_chart   = alt.Chart(data=aggregated,).mark_bar().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Total Weight (g)):Q', 
                      stack='zero',
                      title='Weight (g)'
                      ),
            color = alt.Color('sum(Total Weight (g))',
                              scale=alt.Scale(scheme="darkgold"),
                              legend=alt.Legend(orient='top')
                              ).title('Weight (g)')
            )
        
        # Chart total food calories
        calories_chart = alt.Chart(data=aggregated,).mark_bar().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Total Calories):Q', 
                      stack='zero',
                      title='Calories'
                      ),
            color = alt.Color('sum(Total Calories)',
                              scale=alt.Scale(scheme="darkblue"),
                              legend=alt.Legend(orient='top')
                              ).title('Calories')
            )
        
        st.write('### Visualizations')
        st.altair_chart(macro_chart,                     use_container_width=True)
        st.altair_chart(macro_avg_chart,                 use_container_width=True)
        st.altair_chart(calories_chart + cal_avg_chart,  use_container_width=True)
        st.altair_chart(weight_chart + weight_avg_chart, use_container_width=True)

else:
    st.write("No journal file found.")
