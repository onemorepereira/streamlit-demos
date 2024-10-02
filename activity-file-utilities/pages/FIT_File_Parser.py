
from streamlit_folium import st_folium
import streamlit as st
import helper as h


st.set_page_config(
    page_title="FIT File Utilities",
    layout="wide",
    page_icon="🗺️"
)

st.title("FIT File Utilities")
uploaded_file = st.file_uploader("Choose a FIT file", type=["fit"])

if uploaded_file is not None:
    try:
        activity    = h.parse_fit_file(uploaded_file)
        summary     = h.get_fit_summary(activity)
    except Exception as e:
        st.error(e)

    try:
        st.subheader("Route Map")
        route_map = h.plot_map(activity)
        if route_map:
            st_folium(
                route_map, use_container_width=True, key="map", returned_objects=[]
            )
        else:
            st.write("No latitude/longitude data available in this FIT file.")

    except Exception as e:
        st.error(f"Error processing FIT file: {e}")

    try:
        st.subheader("FIT file contents (first 10 rows)")
        st.dataframe(activity.head(10))

        st.subheader("Summary")
        st.dataframe(summary)
        
    except Exception as e:
        st.error(e)

else:
    st.info("Please upload a FIT file to inspect.")
