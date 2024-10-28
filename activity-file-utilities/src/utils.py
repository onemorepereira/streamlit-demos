from datetime import datetime
from functools import wraps
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import OpenCage
from math import radians, sin, cos, sqrt, atan2
from time import time
from typing import Literal
import altair as alt
import fitparse
import folium
import gpxpy
import json
import os
import pandas as pd
import logging
import joblib

os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import tensorflow as tf
from tensorflow.keras.models import load_model

logging.basicConfig(format='%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] [%(threadName)s] - %(message)s', level=logging.INFO)

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        tt = te-ts
        if tt > 1:
            logging.info("""
------------------------------------------
Long running function detected.
Function: {}\t{} secs
------------------------------------------
                         """.format(f.__name__, round(tt,2)))
        return result
    return wrap

@timing
def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # The haversine formula determines the great-circle distance between two points on a sphere given their longitudes and latitudes.
    # https://en.wikipedia.org/wiki/Haversine_formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a    = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c    = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Distance in meters
    distance = R * c * 1000
    
    return distance

@timing
def gpx_to_dataframe(gpx_file) -> pd.DataFrame:
    NAMESPACES = {'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}
    gpx  = gpxpy.parse(gpx_file)
    data = {
        'latitude': [],
        'longitude': [],
        'elevation': [],
        'time': [],
        'temperature': [],
        'heart_rate': [],
        'cadence': [],
        'distance': [],
        'speed': [],  # meters / second
        'power': []
    }
    
    # Iterate through track points in all tracks and segments
    previous_point = None
    previous_time = None
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # Basic trackpoint data
                data['latitude'].append(point.latitude)
                data['longitude'].append(point.longitude)
                data['elevation'].append(point.elevation * 3.281) #in feet
                data['time'].append(point.time)
                
                # Initialize default None values for optional extensions
                atemp = None
                hr    = None
                cad   = None
                pwr   = None

                # Check for extensions and extract additional attributes if present
                if point.extensions:
                    for ext in point.extensions:
                        if ext.tag == 'power':  # Check if the tag is exactly 'power'
                            pwr = int(ext.text)
                        
                        hr_el = ext.find('ns3:hr', NAMESPACES)
                        if hr_el is not None:
                            hr = int(hr_el.text)
                        else:
                            hr = None
                        
                        cad_el = ext.find('ns3:cad', NAMESPACES)
                        if cad_el is not None:
                            cad = int(cad_el.text)
                        else:
                            cad = None
                        
                # Append the extension attributes to the data lists
                # Farenheit temperature
                data['temperature'].append(((atemp * 9/5) + 32) if atemp is not None else 0)
                
                data['heart_rate'].append(hr)
                data['cadence'].append(cad)
                data['power'].append(pwr)
                
                # Calculate the distance from the previous point
                if previous_point is not None:
                    dist      = haversine(previous_point['latitude'], previous_point['longitude'], point.latitude, point.longitude)
                    time_diff = (point.time - previous_time).total_seconds()
                    
                    # Calculate speed (miles per hour)
                    speed = dist / time_diff * 2.237 if time_diff > 0 else 0
                else:
                    dist  = 0
                    speed = 0
                
                # Append the calculated values
                data['distance'].append(dist)
                data['speed'].append(speed)
                
                # Update the previous point and time
                previous_point = {
                    'latitude': point.latitude,
                    'longitude': point.longitude
                }
                previous_time = point.time
    
    df = pd.DataFrame(data)
    return df

@timing
def aggregate_gpx_data(df: pd.DataFrame) -> pd.DataFrame:
    # Round the time column to the nearest minute
    df['time'] = df['time'].dt.round('min')
    
    # Distance Traveled
    df['distance'] = df['distance'].cumsum().div(1000) # in kilometers

    # Group by the rounded time (minute)
    grouped = df.groupby('time').agg({
        'latitude':             'median',
        'longitude':            'median',
        'elevation':           ['mean', 'median'],
        'temperature':         ['mean', 'median'],
        'heart_rate':          ['mean', 'median'],
        'speed':               ['mean', 'median'],
        'cadence':             ['mean', 'median'],
        'distance':             'last',
        'power':               ['mean', 'median'],
    })
    
    # Flatten the MultiIndex columns created by aggregation
    grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
    
    # Rename columns for clarity
    grouped.rename(columns={
        'latitude_median':      'latitude',
        'longitude_median':     'longitude',
        'elevation_mean':       'mean_elevation',
        'elevation_median':     'median_elevation',
        'temperature_mean':     'mean_temperature',
        'temperature_median':   'median_temperature',
        'heart_rate_mean':      'mean_heart_rate',
        'heart_rate_median':    'median_heart_rate',
        'cadence_mean':         'mean_cadence',
        'cadence_median':       'median_cadence',
        'speed_mean':           'mean_speed',
        'speed_median':         'median_speed',
        'power_mean':           'mean_power',
        'power_median':         'median_power',
        'distance_last':        'distance'
    }, inplace=True)
    
    return grouped.reset_index()

@timing
def create_dual_chart(source_df1: str, source_df2: str, agg_df1: pd.DataFrame, agg_df2: pd.DataFrame, y_column: str, title: str, y_label: str):
    # Add a source column for each DataFrame
    agg_df1['source'] = source_df1
    agg_df2['source'] = source_df2
    
    combined_df = pd.concat([agg_df1, agg_df2])

    # Eyeballing a min/max value for "Y"
    y_min = combined_df[y_column].min() * 0.9
    y_max = combined_df[y_column].max() * 1.1

    return alt.Chart(combined_df).mark_line().encode(
        x=alt.X(
            'distance',
            title='distance (km)'
        ),
        y=alt.Y(
            y_column,
            title=y_label,
            scale=alt.Scale(domain=(y_min, y_max))
        ),
        color=alt.Color('source:N'
                        ).title('Average {}'.format(y_column),
                                ).scale(scheme='darkred'
                                        ).legend(alt.Legend(orient='top', titleLimit=0, labelLimit=0)
        )
    ).properties(
        title=title,
        width=700,
        height=400
    ).interactive()

@timing
def create_chart(df: pd.DataFrame, y_column: str, title: str, y_label: str):
    # Implement sensible smoothing of chart data
    samples = round(len(df))
    if samples < 1000:
        smoothing = round(len(df) * 0.1)
    elif samples >= 1000:
        smoothing = round(len(df) * 0.01)
    elif samples >= 10000:
        smoothing = round(len(df) * 0.001)
    elif samples >= 50000:
        smoothing = round(len(df) * 0.001)
    else:
        smoothing = 0
    
    # Eyeballing a min/max value for "Y"
    df[y_column] = df[y_column].rolling(smoothing).mean()
    y_min = df[y_column].min() * 1
    y_max = df[y_column].max() * 1

    return alt.Chart(df).mark_line().encode(
        x=alt.X(
            'timestamp',
            title=None,
            axis=alt.Axis(labels=False,)
        ),
        y=alt.Y(
            y_column,
            title=None,
            scale=alt.Scale(domain=(y_min, y_max)),
            axis=alt.Axis(labels=False,),
        ),
        color=alt.value("#FF0000"),
        strokeWidth=alt.value(0.75),
        strokeOpacity=alt.value(1),
    ).properties(
        title=title,
        # width=200,
        height=100,
    ).configure_axis(grid=False)
    
@timing
def parse_fit_file(fit_file) -> pd.DataFrame:
    fitfile = fitparse.FitFile(fit_file)
    rdata, edata, sdata = [], [], []
    
    # Single iteration through all messages
    for message in fitfile:
        data_dict = {field.name: field.value for field in message}

        # Categorize message by type
        if message.name == "record":
            rdata.append(data_dict)
        elif message.name == "event":
            edata.append(data_dict)
        elif message.name == "session":
            sdata.append(data_dict)

    # Construct DataFrames
    record_df  = pd.DataFrame(rdata)
    event_df   = pd.DataFrame(edata)
    session_df = pd.DataFrame(sdata)

    return record_df, event_df, session_df

@timing
def plot_map(df: pd.DataFrame):
    # NOTE: looks like Panda.DataFrame as shared in-memory objects; beware, this function is not "safe"
    if "position_lat" in df.columns and "position_long" in df.columns:
        # Convert semi-circles to degrees (standard for GPS lat/lon)
        df["latitude"]  = df["position_lat"] * (180 / 2**31)
        df["longitude"]  = df["position_long"] * (180 / 2**31)

    df = df.dropna(subset=["latitude", "longitude"])

    # Create a map centered at the mean latitude/longitude
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Plot the route by adding a polyline to the map
    route = list(zip(df["latitude"], df["longitude"]))
    folium.PolyLine(route, color="blue", weight=2.5, opacity=1).add_to(m)

    # Add markers every 10 km
    total_distance = 0
    previous_point = route[0]
    cumulative_distance = 0
    total_distance = 0

    for i in range(1, len(route)):
        current_point = route[i]
        distance = geodesic(previous_point, current_point).kilometers
        cumulative_distance += distance  # Update the cumulative distance

        # Check if the cumulative distance exceeds the next 10 km mark
        if cumulative_distance >= 10.0:
            total_distance += cumulative_distance
            folium.Marker(
                location=current_point,
                popup=f"{total_distance:.0f} km",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(m)
            # Reset cumulative distance after placing a marker
            cumulative_distance = 0
        previous_point = current_point

    # Start & End markers
    folium.Marker(
        location=route[0],
        popup="Start",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)

    folium.Marker(
        location=route[-1], popup="End", icon=folium.Icon(color="red", icon="stop")
    ).add_to(m)

    m.fit_bounds(route)

    return m

@timing
def get_summary(df: pd.DataFrame, ftp: float, format: Literal["gpx", "fit"]) -> pd.DataFrame:
    if "heart_rate" in df:
        heart_rate_avg = round(df[df["heart_rate"] != 0]["heart_rate"].mean(skipna=True))
        heart_rate_max = round(df["heart_rate"].max())
    else:
        heart_rate_avg = heart_rate_max = None

    if "timestamp" in df:
        ts_column = "timestamp"
    elif "time" in df:
        ts_column = "time"
        
    if "power" in df:
        if "enhanced_speed" in df:
            power_avg = round(df[(df["enhanced_speed"] > 0)]["power"].mean(skipna=True))
        else:
            power_avg = round(df[df["speed"] > 0]["power"].mean(skipna=True))
            
        power_max        = round(df["power"].max())
        power_np         = get_normalized_power(df)
        intensity_factor = get_intensity_factor(power_np, ftp)
        tss              = get_tss(power_np, ftp, get_duration_seconds(df, ts_column), intensity_factor)
        power_5          = get_max_avg_pwr(df, 5, ts_column)
        power_10         = get_max_avg_pwr(df, 10, ts_column)
        power_20         = get_max_avg_pwr(df, 20, ts_column)
        power_60         = get_max_avg_pwr(df, 60, ts_column)
        power_30s        = get_max_avg_pwr(df, 0.5, ts_column)
    else:
        power_avg = power_max = power_np = intensity_factor = power_5 = power_10 = power_20 = power_60 = power_30s = tss = 0

    if "cadence" in df:
        cadence_avg = round(df["cadence"].mean(skipna=True))
        cadence_max = round(df["cadence"].max())
    else:
        cadence_avg = cadence_max = 0

    if "enhanced_speed" in df:
        speed_avg        = round(df["enhanced_speed"].mean(skipna=True) * 3.6)
        speed_moving_avg = round(df[df["enhanced_speed"] > 4]["enhanced_speed"].mean(skipna=True) * 3.6)
        speed_max        = round(df["enhanced_speed"].max() * 3.6)
    elif "speed" in df:
        speed_avg        = round(df["speed"].mean(skipna=True) * 1.609)
        speed_moving_avg = round(df[df["speed"] > 8]["speed"].mean(skipna=True) * 1.609)
        speed_max        = round(df["speed"].max() * 1.609)
    else:
        speed_avg = speed_max = speed_moving_avg = 0

    if "temperature" in df:
        try:
            temperature_avg = round(df["temperature"].mean(skipna=True))
            temperature_max = round(df["temperature"].max(skipna=True))
        except Exception:
            temperature_avg = temperature_max = 0
    else:
        temperature_avg = temperature_max = 0

    if format == "fit":
        distance_km = round(df["distance"].max() / 1000)
    else:
        distance_km = round(df["distance"].max())
        
    if 'timestamp' in df:
        coasting_time_string  = get_coasting(df, time_column='timestamp')[0]
        coasting_time_seconds = get_coasting(df, time_column='timestamp')[1]
        stopped_time_string   = get_stopped_time(df, time_column='timestamp')[0]
        stopped_time_seconds  = get_stopped_time(df, time_column='timestamp')[1]
        moving_time_string    = get_moving_time(df, time_column='timestamp')[0]
        moving_time_seconds   = get_moving_time(df, time_column='timestamp')[1]
        work_time_string      = get_work_time(df, time_column='timestamp')[0]
        work_time_seconds     = get_work_time(df, time_column='timestamp')[1]
        total_time_string     = get_total_time(df, time_column='timestamp')[0]
        total_time_seconds    = get_total_time(df, time_column='timestamp')[1]
    elif 'time' in df:
        coasting_time_string  = get_coasting(df, time_column='time')[0]
        coasting_time_seconds = get_coasting(df, time_column='time')[1]
        stopped_time_string   = get_stopped_time(df, time_column='time')[0]
        stopped_time_seconds  = get_stopped_time(df, time_column='time')[1]
        moving_time_string    = get_moving_time(df, time_column='time')[0]
        moving_time_seconds   = get_moving_time(df, time_column='time')[1]
        work_time_string      = get_work_time(df, time_column='time')[0]
        work_time_seconds     = get_work_time(df, time_column='time')[1]
        total_time_string     = get_total_time(df, time_column='time')[0]
        total_time_seconds    = get_total_time(df, time_column='time')[1]
    else:
        coasting_time_string  = '0m'
        coasting_time_seconds = 0
        stopped_time_string   = '0m'
        stopped_time_seconds  = 0
        moving_time_string    = '0m'
        moving_time_seconds   = 0
        work_time_string      = '0m'
        work_time_seconds     = 0
        total_time_string     = '0m'
        total_time_seconds    = 0
    
    df0 = pd.DataFrame({
        'hr_avg':                [heart_rate_avg],
        'hr_max':                [heart_rate_max],
        'power_avg':             [power_avg],
        'power_max':             [power_max],
        'power_max_avg_30s':     [power_30s],
        'power_max_avg_5m':      [power_5],
        'power_max_avg_10m':     [power_10],
        'power_max_avg_20m':     [power_20],
        'power_max_avg_60m':     [power_60],
        'power_normalized':      [power_np],
        'intensity_factor':      [intensity_factor],
        'tss':                   [tss],
        'cadence_avg':           [cadence_avg],
        'cadence_max':           [cadence_max],
        'speed_avg':             [speed_avg],
        'speed_moving_avg':      [speed_moving_avg],
        'speed_max':             [speed_max],
        'temp_avg':              [temperature_avg],
        'temp_max':              [temperature_max],
        'distance_total':        [distance_km],
        'time_coasting_string':  [coasting_time_string],
        'time_stopped_string':   [stopped_time_string],
        'time_moving_string':    [moving_time_string],
        'time_working_string':   [work_time_string],
        'time_total_string':     [total_time_string],
        'time_coasting_seconds': [coasting_time_seconds],
        'time_stopped_seconds':  [stopped_time_seconds],
        'time_moving_seconds':   [moving_time_seconds],
        'time_working_seconds':  [work_time_seconds],
        'time_total_seconds':    [total_time_seconds],
    })
    
    return df0

@timing
def get_normalized_power(df: pd.DataFrame) -> float:
    if "power" not in df:
        raise ValueError("The DataFrame does not contain a 'power' column")
    
    # Drop null values from the 'power' column
    df = df.dropna(subset=["power"])
    
    # Check if there are still values left after dropping nulls
    if df.empty:
        raise ValueError("The DataFrame contains only null values in the 'power' column")
    
    rolling_power       = df['power'].rolling(window=30, min_periods=1).mean()
    rolling_power_4th   = rolling_power ** 4
    avg_4th_power       = rolling_power_4th.mean()
    normalized_power    = avg_4th_power ** (1 / 4)

    return round(normalized_power)


    return round(normalized_power)

@timing
def get_intensity_factor(normalized_power: float, ftp: float) -> float:
    if ftp <= 0:
        return 0

    intensity_factor = normalized_power / ftp
    return round(intensity_factor, 3)

@timing
def get_tss(normalized_power: float, ftp: float, duration_seconds: float, intensity_factor: float) -> float:
    if ftp <= 0 or duration_seconds <= 0:
        return 0
    
    tss = (duration_seconds * normalized_power * intensity_factor) / (ftp * 3600) * 100
    return round(tss, 1)

@timing
def get_duration_seconds(df: pd.DataFrame, column: str = 'timestamp') -> float:
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in the DataFrame")

    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        try:
            df[column] = pd.to_datetime(df[column])
        except Exception as e:
            raise ValueError(f"Error converting '{column}' to datetime: {e}")

    time_difference = df[column].max() - df[column].min()
    elapsed_seconds = time_difference.total_seconds()

    return elapsed_seconds

@timing
def get_max_avg_pwr(df: pd.DataFrame, minutes: float, time_column: str = 'timestamp') -> float:
    if 'power' not in df or time_column not in df:
        raise ValueError(f"The DataFrame must contain 'power' and '{time_column}' columns")

    # Ensure the DataFrame is sorted by the time column and convert it to datetime if needed
    df = df.sort_values(by=time_column).reset_index(drop=True)
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])

    # Convert the time column to seconds since the start to calculate the window
    df['time_seconds'] = (df[time_column] - df[time_column].min()).dt.total_seconds()

    window_seconds  = minutes * 60
    total_time_span = df['time_seconds'].max()

    if total_time_span < window_seconds:
        return 0

    # Use a rolling window to calculate the mean power over the specified window duration
    if "enhanced_speed" in df:
        rolling_avg_power = df[df['enhanced_speed'] > 0]['power'].rolling(window=int(window_seconds), min_periods=1).mean()
    else:
        rolling_avg_power = df[df['speed'] > 0]['power'].rolling(window=int(window_seconds), min_periods=1).mean()

    # Return the maximum average power over the rolling window
    max_avg_power = rolling_avg_power.max()

    return round(max_avg_power)

@timing
def get_coasting(df: pd.DataFrame, time_column: str = 'timestamp'):
    if 'power' not in df or 'cadence' not in df or ('speed' not in df and 'enhanced_speed' not in df) or time_column not in df:
        logging.error(f"Missing at least power, cadence, speed or enhanced_speed, or {time_column}")
        return None, None
    
    # Ensure the time column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # Calculate the time difference between consecutive rows
    df['time_diff'] = df[time_column].diff().dt.total_seconds().fillna(0)
    
    # Filter rows where either power or cadence is 0, and speed is greater than 0 (moving)
    if 'speed' in df:
        zero_power_or_cadence_while_moving = df[(df['speed'] > 0) & ((df['power'] == 0) | (df['cadence'] == 0))]
    elif 'enhanced_speed' in df:
        zero_power_or_cadence_while_moving = df[(df['enhanced_speed'] > 0) & ((df['power'] == 0) | (df['cadence'] == 0))]
    
    total_time_seconds = zero_power_or_cadence_while_moving['time_diff'].sum()
    total_seconds      = int(total_time_seconds)
    hours, remainder   = divmod(total_seconds, 3600)
    minutes, seconds   = divmod(remainder, 60)

    return f"{hours}h {minutes}m {seconds}s", total_seconds

@timing
def get_stopped_time(df: pd.DataFrame, time_column: str = 'timestamp'):
    if ('speed' not in df and 'enhanced_speed' not in df) or time_column not in df:
        logging.error(f"The DataFrame must contain 'speed' or 'enhanced_speed', or '{time_column}' columns")
        return None, None
        
    # Ensure the time column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # Calculate the time difference between consecutive rows
    df['time_diff'] = df[time_column].diff().dt.total_seconds().fillna(0)
    
    # Filter rows where speed or enhanced_speed is 0 (stationary time)
    if 'speed' in df:
        stationary_time_df = df[df['speed'] == 0]
    elif 'enhanced_speed' in df:
        stationary_time_df = df[df['enhanced_speed'] == 0]
    
    total_stationary_seconds = stationary_time_df['time_diff'].sum()
    total_seconds            = int(total_stationary_seconds)
    hours, remainder         = divmod(total_seconds, 3600)
    minutes, seconds         = divmod(remainder, 60)

    return f"{hours}h {minutes}m {seconds}s", total_seconds

@timing
def get_moving_time(df: pd.DataFrame, time_column: str = 'timestamp'):
    if ('speed' not in df and 'enhanced_speed' not in df) or time_column not in df:
        logging.error(f"The DataFrame must contain 'speed' or 'enhanced_speed', or '{time_column}' columns")
        return None, None
    
    # Ensure the time column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # Calculate the time difference between consecutive rows
    df['time_diff'] = df[time_column].diff().dt.total_seconds().fillna(0)
    
    # Filter rows where speed or enhanced_speed is 0 (stationary time)
    if 'speed' in df:
        moving_time_df = df[df['speed'] > 1]
    elif 'enhanced_speed' in df:
        moving_time_df = df[df['enhanced_speed'] > 1]
    
    total_moving_seconds = moving_time_df['time_diff'].sum()
    total_seconds            = int(total_moving_seconds)
    hours, remainder         = divmod(total_seconds, 3600)
    minutes, seconds         = divmod(remainder, 60)

    return f"{hours}h {minutes}m {seconds}s", total_seconds

@timing
def get_work_time(df: pd.DataFrame, time_column: str = 'timestamp'):
    if 'power' not in df or 'cadence' not in df or time_column not in df:
        logging.error(f"The DataFrame must contain 'speed' or 'enhanced_speed', or '{time_column}' columns")
        return None, None
    
    # Ensure the time column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # Calculate the time difference between consecutive rows
    df['time_diff'] = df[time_column].diff().dt.total_seconds().fillna(0)
    
    # Filter rows where either power or cadence is greater than 0
    active_time_df       = df[(df['power'] > 0) | (df['cadence'] > 0)]
    total_active_seconds = active_time_df['time_diff'].sum()
    total_seconds        = int(total_active_seconds)
    hours, remainder     = divmod(total_seconds, 3600)
    minutes, seconds     = divmod(remainder, 60)

    return f"{hours}h {minutes}m {seconds}s", total_seconds

@timing
def get_total_time(df: pd.DataFrame, time_column: str = 'timestamp'):
    if time_column not in df:
        logging.error(f"The DataFrame must contain a '{time_column}' column")
        return None, None
    
    # Ensure the time column is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    
    # Calculate the time difference between consecutive rows
    df['time_diff']    = df[time_column].diff().dt.total_seconds().fillna(0)
    total_time_seconds = df['time_diff'].sum()
    total_seconds      = int(total_time_seconds)
    hours, remainder   = divmod(total_seconds, 3600)
    minutes, seconds   = divmod(remainder, 60)

    return f"{hours}h {minutes}m {seconds}s", total_seconds

@timing
def get_chart_data(df: pd.DataFrame, y_col: str, x_col: str) -> pd.DataFrame:
    if not all(col in df.columns for col in [y_col, x_col]):
        raise ValueError("One or more specified columns do not exist in the DataFrame.")
    chart_data = df[[x_col, y_col]].copy()
    chart_data.set_index(x_col, inplace=True)
    return chart_data

@timing
def aggregate_by_time(df: pd.DataFrame, timestamp_col: str, interval: str = '5min') -> pd.DataFrame:
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' does not exist in the DataFrame.")
    
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df                = df.set_index(timestamp_col)
    aggregated_df     = df.resample(interval).apply(lambda x: x.quantile(0.99)).reset_index()
        
    return aggregated_df


@timing
def load_data(data_file) -> pd.DataFrame:
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            data = json.load(file)
            return pd.DataFrame(data)
    else:
        return pd.DataFrame()

def save_data(data, data_file):
    with open(data_file, "w") as file:
        json.dump(data, file, indent=4)

@timing
def get_latest_ftp(data_file, date: datetime = None):
    df = load_data(data_file)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    if date is None:
        if not df.empty and 'ftp' in df.columns:
            ftp = df['ftp'].iloc[-1]
            if pd.notna(ftp):
                return int(ftp)
            else:
                return 0
        else:
            return 0

    # Filter the DataFrame for entries on or after the specified date
    filtered_df = df[df['timestamp'] <= pd.to_datetime(date)]
    logging.info(filtered_df)
    
    if not filtered_df.empty and 'ftp' in filtered_df.columns:
        ftp = filtered_df['ftp'].iloc[-1]
        if pd.notna(ftp):
            return int(ftp)
        else:
            return 0
    else:
        return 0

@timing    
def get_ftp_by_date(data_file, target_date):
    df = load_data(data_file)
    if not df.empty and "ftp" in df.columns and "timestamp" in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        target_date     = pd.to_datetime(target_date)
        df['date_diff'] = (df['timestamp'] - target_date).abs()
        closest_row     = df.loc[df['date_diff'].idxmin()]
        
        ftp = closest_row['ftp']
        return int(ftp) if pd.notna(ftp) else 0
    else:
        return 0

@timing
def get_latest_maxhr(data_file):
    df = load_data(data_file)
    if not df.empty and "max_hr" in df.columns:
        max_hr = df["max_hr"].iloc[-1]
        if pd.notna(max_hr):
            return int(max_hr)
        else:
            return 0
    else:
        return 0

@timing    
def get_latest_restinghr(data_file):
    df = load_data(data_file)
    if not df.empty and "resting_hr" in df.columns:
        resting_hr = df["resting_hr"].iloc[-1]
        if pd.notna(resting_hr):
            return int(resting_hr)
        else:
            return 0
    else:
        return 0

@timing
def get_latest_hr_zones(df: pd.DataFrame) -> pd.DataFrame:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    latest_row      = df.loc[df['timestamp'].idxmax()]
    
    return latest_row

@timing
def calculate_training_effect(heart_rate_zones_df: pd.DataFrame, intensity: float):
    # Define aerobic and anaerobic factors for each zone (scaled up)
    zone_factors = {
        "zone1": {"aerobic": 0.350, "anaerobic": 0.010},   # Low intensity, mostly recovery
        "zone2": {"aerobic": 0.400, "anaerobic": 0.020},   # Endurance
        "zone3": {"aerobic": 0.340, "anaerobic": 0.180},   # Steady-state cardio
        "zone4": {"aerobic": 0.100, "anaerobic": 0.800},   # Threshold/tempo
        "zone5": {"aerobic": 0.000, "anaerobic": 1.550},   # High intensity (sprints)
    }

    aerobic_te    = 0
    anaerobic_te  = 0
    duration_mins = 0

    for _, row in heart_rate_zones_df.iterrows():
        zone = row.get('zone', None)
        time_in_zone_seconds = row.get('time_in_seconds', 0)

        # Ensure zone and time_in_seconds are valid
        if zone not in zone_factors or not isinstance(time_in_zone_seconds, (int, float)):
            logging.warning(f"Skipping invalid data in row: {row}")
            continue
        
        # Convert seconds to minutes
        time_in_zone_minutes = time_in_zone_seconds / 60

        # Accumulate aerobic and anaerobic training effect
        factors        = zone_factors[zone]
        aerobic_te    += time_in_zone_minutes * factors["aerobic"]
        anaerobic_te  += time_in_zone_minutes * factors["anaerobic"]
        duration_mins += time_in_zone_minutes

    # Helper function to scale the training effect based on duration and intensity
    def scale_training_effect(te_value, duration, intensity):
        if duration <= 60:
            h, i = 60, intensity * 10
        elif duration <= 120:
            h, i = 90, intensity * 15
        elif duration <= 240:
            h, i = 180, intensity * 12
        else:
            h, i = 210, intensity * 18
        return min(5, te_value * i / h)

    # Scale aerobic and anaerobic training effects
    aerobic_te   = scale_training_effect(aerobic_te, duration_mins, intensity)
    anaerobic_te = scale_training_effect(anaerobic_te, duration_mins, intensity)

    # Return results rounded to 1 decimal place
    return round(aerobic_te, 1), round(anaerobic_te, 1)


@timing
def calculate_hr_zone_time(df: pd.DataFrame, hr_zones: pd.DataFrame) -> pd.DataFrame:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    
    zone_numbers  = list(set([int(row.split('.')[1]) for row in hr_zones.index if 'zone.' in row]))
    num_zones     = len(zone_numbers)
    time_in_zones = {f'zone{i+1}': 0 for i in range(num_zones)}

    for i in range(1, len(df)):
        heart_rate    = df.iloc[i]['heart_rate']
        time_interval = df.iloc[i]['time_diff']

        for zone_num in zone_numbers:
            low_hr_row = f'zone.{zone_num}.low_hr'
            max_hr_row = f'zone.{zone_num}.max_hr'

            if low_hr_row in hr_zones.index and max_hr_row in hr_zones.index:
                min_hr = hr_zones.loc[low_hr_row]
                max_hr = hr_zones.loc[max_hr_row]

                if min_hr <= heart_rate <= max_hr:
                    time_in_zones[f'zone{zone_num}'] += time_interval
                    break

    time_in_zones_df = pd.DataFrame({
        'zone': list(time_in_zones.keys()),
        'time_in_seconds': list(time_in_zones.values())
    })

    return time_in_zones_df

@timing
def format_nice_date(timestamp: datetime.timestamp):
    dt  = timestamp.to_pydatetime()
    day = dt.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    formatted_date = dt.strftime(f"%A, %B {day}{suffix} %Y @ %I:%M%p")
    return formatted_date.lstrip("0")

@timing
def convert(value: float, from_to: Literal['miles_km',
                                           'km_miles',
                                           'mph_kmh',
                                           'kmh_mph',
                                           'cm_inches',
                                           'inches_cm',
                                           'celsius_fahrenheit',
                                           'fahrenheit_celsius']) -> float:
    conversion_factors = {
        'miles_km':  1.60934,     # 1 mile = 1.60934 km
        'km_miles':  1 / 1.60934, # 1 km = 0.621371 miles
        'mph_kmh':   1.60934,     # 1 mph = 1.60934 km/h
        'kmh_mph':   1 / 1.60934, # 1 km/h = 0.621371 mph
        'cm_inches': 0.393701,    # 1 cm = 0.393701 inches
        'inches_cm': 2.54         # 1 inch = 2.54 cm
    }

    # Temperature    
    if from_to == 'celsius_fahrenheit':
        return round((value * 9/5) + 32, 2)  # Celsius to Fahrenheit
    elif from_to == 'fahrenheit_celsius':
        return round((value - 32) * 5/9, 2)  # Fahrenheit to Celsius

    return round(value * conversion_factors[from_to], 1)

@timing
# @retry(stop=stop_after_attempt(4), wait=wait_exponential(min=5, max=60))
def get_location_details(api_key: str, latitude: float, longitude: float):
    """
    Returns city, state, country, and postal code based on latitude and longitude using OpenCage with geopy.

    Args:
    latitude (float): Latitude of the location.
    longitude (float): Longitude of the location.
    api_key (str): Your OpenCage API key.

    Returns:
    dict: A dictionary containing city, state, country, and postal code.
    """
    if api_key:
        geolocator       = OpenCage(api_key)
        location_details = {}
        try:
            location = geolocator.reverse((latitude, longitude), exactly_one=True)
            if location:
                address = location.raw.get('components', {})
                location_details['city'] = address.get('city', address.get('town', address.get('village', '')))
                location_details['state'] = address.get('state', '')
                location_details['country'] = address.get('country', '')
                location_details['postal_code'] = address.get('postcode', '')

        except GeocoderTimedOut:
            logging.error("Error: Geocoder service timed out")
            raise GeocoderTimedOut
        except Exception as e:
            logging.error(f"Error: {e}")
            raise Exception
        
        return location_details
    else:
        return None

@timing
def get_opencage_key(data_file):
    df = load_data(data_file)
    if not df.empty and "opencage_key" in df.columns:
        opencage_key = df["opencage_key"].iloc[-1]
        if pd.notna(opencage_key):
            return str(opencage_key)
        else:
            return None
    else:
        return None

@timing    
def calculate_power_zone_time(df: pd.DataFrame, power_zones: pd.DataFrame) -> pd.DataFrame:
    if 'timestamp' not in df or 'power' not in df:
        logging.error("Main DataFrame must contain timestamp and power data")
        return pd.DataFrame()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    
    zone_numbers  = list(set([int(row.split('.')[1]) for row in power_zones.index if 'zone.' in row]))
    num_zones     = len(zone_numbers)
    time_in_zones = {f'zone{i+1}': 0 for i in range(num_zones)}

    for i in range(1, len(df)):
        power         = df.iloc[i]['power']
        time_interval = df.iloc[i]['time_diff']

        for zone_num in zone_numbers:
            low_power_row = f'zone.{zone_num}.low_pwr'
            max_power_row = f'zone.{zone_num}.max_pwr'

            if low_power_row in power_zones.index and max_power_row in power_zones.index:
                min_power = power_zones.loc[low_power_row]
                max_power = power_zones.loc[max_power_row]

                if min_power <= power <= max_power:
                    time_in_zones[f'zone{zone_num}'] += time_interval
                    break

    time_in_zones_df = pd.DataFrame({
        'zone': list(time_in_zones.keys()),
        'time_in_seconds': list(time_in_zones.values())
    })

    return time_in_zones_df

@timing
def predict_aerobic_training_effect(input_df):
    """
    Loads the pre-trained model and scaler, then predicts the aerobic training effect 
    based on the provided DataFrame.

    Args:
        input_df (pd.DataFrame): DataFrame containing the necessary features.

    Returns:
        float: Rounded predicted aerobic training effect.
    """
    
    MODEL  = load_model('./models/aerobic_training_effect_model.keras')
    SCALER = joblib.load('./models/aerobic_training_effect_scaler.pkl')

    required_keys = [
        'activity_distance',
        'hr_average',
        'hr_max',
        'hr_time_in_zone_1',
        'hr_time_in_zone_2',
        'hr_time_in_zone_3',
        'hr_time_in_zone_4',
        'hr_time_in_zone_5',
        'intensity_factor',
        'time_total',
        'training_stress_score',
    ]

    # Ensure input DataFrame contains the required keys
    input_data = {key: input_df[key].values[0] for key in required_keys if key in input_df.columns}
    if len(input_data) < len(required_keys):
        raise ValueError(f"Missing keys in input DataFrame. Required keys are: {required_keys}.")

    input_df_ordered = pd.DataFrame([input_data])[required_keys]  # Ensure the order matches
    input_scaled     = SCALER.transform(input_df_ordered)

    @tf.function(reduce_retracing=True)
    def make_prediction(input_scaled_tensor):
        return MODEL(input_scaled_tensor)

    input_scaled_tensor = tf.convert_to_tensor(input_scaled, dtype=tf.float32)
    predictions_tensor  = make_prediction(input_scaled_tensor)
    predicted_value     = min(5.0, round(float(predictions_tensor[0][0]), 1))

    return predicted_value
