
from streamlit_folium import st_folium
import streamlit as st
import helper as h


st.set_page_config(
    page_title="FIT/GPX File Utilities",
    layout="wide",
    page_icon="🗺️"
)

st.title("FIT/GPX File Utilities")
ftp           = st.number_input("Functional Threshold Power (FTP): ", 200)
uploaded_file = st.file_uploader("Choose a FIT/GPX file", type=["fit", "gpx"])

if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/fits":
            activity = h.parse_fit_file(uploaded_file)
            summary  = h.get_summary(activity, ftp, format="fit")
        elif uploaded_file.type == "application/gpx+xml":
            activity = h.gpx_to_dataframe(uploaded_file)
            summary  = h.get_summary(activity, ftp, format="gpx")
        
    except Exception as e:
        st.error(e)

    try:
        st.subheader("Route Map")
        route_map = h.plot_map(activity)
        if route_map:
            st_folium(route_map, use_container_width=True, key="map", returned_objects=[])
            
        else:
            st.write("No latitude/longitude data available in this FIT file.")

    except Exception as e:
        st.error(f"Error processing FIT file: {e}")

    try:
        st.subheader("File Stats")
        st.dataframe(activity.describe())

        st.subheader("Summary")
        st.dataframe(summary)
        
    except Exception as e:
        st.error(e)

else:
    st.info("Please upload a FIT or GPX file to inspect.")
