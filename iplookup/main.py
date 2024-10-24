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
from urllib.parse import urlparse

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s', level=logging.INFO)

states = alt.topo_feature(data.world_110m.url, feature='countries')

st.set_page_config(
    page_title="IP Address Details",
    layout="wide",
    page_icon="🗺️"
)

@st.cache_data
def get_ip_details(ip: str):
    response = requests.get('http://ip-api.com/json/{}'.format(ip))
    content = json.loads(response.content)
    logging.info(content)

    if response.status_code == 200 and content['status'] == 'success':
        data = response.json()
        df = pd.DataFrame([data])
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

def extract_domain_from_url(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.hostname
        logging.info(f"Extracted domain: {domain}")
        return domain
    except Exception as e:
        logging.error(f"Error extracting domain: {e}")
        return None

def extract_domain_from_email(email):
    try:
        domain = email.split('@')[1]
        logging.info(f"Extracted domain from email: {domain}")
        return domain
    except IndexError as e:
        logging.error(f"Invalid email format: {e}")
        return None

st.title('IP/Domain/Email Lookup')

input_str = st.text_input("Enter an IP, URL, URI, or email",
                          value=None,
                         )
domain     = None
ip_address = None
if not input_str:
    st.error("Please enter a valid IP, URL, URI, or email.")
    exit()

# Determine if it's an IP address, domain, or email
if is_ip_address(input_str):
    ip_address = input_str
elif is_fqdn(input_str):
    ip_address = get_ip_address(input_str)
elif '@' in input_str:
    domain = extract_domain_from_email(input_str)
    ip_address = get_ip_address(domain)
else:
    domain = extract_domain_from_url(input_str)
    if domain:
        ip_address = get_ip_address(domain)

# Lookup IP details if a valid IP was extracted
if ip_address:
    data = get_ip_details(ip_address)
    
    # Massage displayed data a little bit
    st.write("Details for ", domain if domain else ip_address)
    small_data = data.drop(
        columns=[
            'lat',
            'lon',
            'status',
            'countryCode',
            'region',
            ]).rename(
                columns={
                    'query': 'IP Address',
                    'country': 'Country',
                    'regionName': 'Region',
                    'city': 'City',
                    'zip': 'ZIP',
                    'timezone': "Time Zone",
                    'isp': 'Service Provider',
                    'org': 'Hosting Provider',
                    'as': 'AS',
                    })[[
                        'IP Address',
                        'Service Provider',
                        'AS',
                        'Hosting Provider',
                        'Country',
                        'Region',
                        'City',
                        'ZIP',
                        'Time Zone',
                        ]]
                    
    st.dataframe(small_data, use_container_width=True)
    
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
else:
    st.error("Could not extract or resolve a valid IP address from the input.")
