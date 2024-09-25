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
        melted_data['Running Average'] = melted_data.groupby('macros')['amount'].rolling('7D', min_periods=1).mean().reset_index(level=0, drop=True)
        
        melted_data.reset_index(inplace=True)
        
        cals_data   = melted_data[melted_data['macros'] == 'Total Calories']
        
        melted_data = melted_data[melted_data['macros'] != 'Total Calories']
        melted_data = melted_data[melted_data['macros'] != 'Total Weight (g)']
        
        
        macro_avg_chart = alt.Chart(data=melted_data,
                                    width=400,
                                    height=425
                                    ).mark_line().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Running Average):Q', 
                      title='Grams'
                      ),
            color = alt.Color('macros',
                              scale=alt.Scale(scheme="darkred"),
                              legend=alt.Legend(orient='top')
                              ).title('7 Day Running Average')
            )
        
        cal_avg_chart = alt.Chart(data=cals_data,
                                width=400,
                                  height=425
                                  ).mark_line().encode(
            x = 'monthdate(Date):T',
            y = alt.Y('sum(Running Average):Q', 
                      title='Calories'
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
        macro_chart = alt.Chart(data=filtered_data, 
                                width=400, 
                                height=425
                                ).mark_bar().encode(
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
        weight_chart   = alt.Chart(data=aggregated, 
                                width=400,
                                   height=425
                                   ).mark_bar().encode(
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
        calories_chart = alt.Chart(data=aggregated,
                                #    width=1250,
                                   height=425
                                   ).mark_bar().encode(
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
        st.write(macro_chart,
                 macro_avg_chart,
                 calories_chart + cal_avg_chart,
                 weight_chart,
                 )

else:
    st.write("No journal file found.")
