from vega_datasets import data
import altair as alt
import ipaddress
import json
import logging
import pandas as pd
import re
import requests
import socket
import streamlit as st


logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s', level=logging.INFO)

states = alt.topo_feature(data.world_110m.url, feature='countries')

st.set_page_config(
    page_title="IP Address Details",
    layout="wide",
)

@st.cache_data
def get_ip_details(ip: str):
    response = requests.get('http://ip-api.com/json/{}'.format(ip))
    content = json.loads(response.content)
    logging.info(content)

    if response.status_code == 200 and content['status'] == 'success':
        data     = response.json()
        df       = pd.DataFrame([data])
        return df
    else:
        return None

def get_ip_address(host):
    try:
        ip = socket.gethostbyname(host)
        logging.info(ip)
        return ip
    except socket.gaierror as e:
        logging.error(e)
        return None

def is_ip_address(input_str):
    try:
        ipaddress.ip_address(input_str)
        logging.info("This is a valid IP address")
        return True
    except ValueError as e:
        logging.error(e)
        return False

def is_fqdn(input_str):
    fqdn_regex = re.compile(
        r'^(?=.{1,253}$)'  # Ensure total length is between 1 and 253 characters
        r'([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+'  # Subdomains, allowing dashes
        r'[a-zA-Z]{2,63}$'  # Top-level domain (TLD)
    )
    return bool(fqdn_regex.match(input_str))


st.title('IP Address Lookup')

ip_address = st.text_input("Enter an IP or hostname",
                           value     = None,
                         )

if not ip_address:
    st.error("Please enter a valid IPv4 address or FQDN")
    exit()
    
if is_fqdn(input_str=ip_address):
    ip_address = get_ip_address(host = ip_address)
    
if ip_address:
    data = get_ip_details(ip_address)
    st.write("Details", data)
        
    try:
        background = alt.Chart(states).mark_geoshape(
        fill="lightgray",
        stroke="white"
        ).properties(
            width=1200,
            height=600,
        ).project("equalEarth").interactive()

        # airport positions on background
        points = alt.Chart(data).mark_circle(
            size=50,
            color="red",
        ).encode(
            longitude="lon:Q",
            latitude="lat:Q",
            tooltip=["query", "isp", "city", "regionName", "lat", "lon"],
        ).interactive()

        background + points
    except Exception as e:
        st.error("Please enter a valid IPv4 address or FQDN")