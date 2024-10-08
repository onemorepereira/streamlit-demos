from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2
from typing import Literal
import altair as alt
import fitparse
import folium
import gpxpy
import json
import os
import pandas as pd


NAMESPACES = {
    'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
}

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

def gpx_to_dataframe(gpx_file) -> pd.DataFrame:
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

def create_chart(source_df1: str, source_df2: str, agg_df1: pd.DataFrame, agg_df2: pd.DataFrame, y_column: str, title: str, y_label: str):
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
    
def parse_fit_file(fit_file) -> pd.DataFrame:
    fitfile = fitparse.FitFile(fit_file)
    data = []

    for record in fitfile.get_messages("record"):
        record_data = {}
        for data_field in record:
            record_data[data_field.name] = data_field.value
        data.append(record_data)

    df = pd.DataFrame(data)
    return df

def plot_map(df):
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

def get_summary(df: pd.DataFrame, ftp: float, format: Literal["gpx", "fit"]) -> pd.DataFrame:
    if "heart_rate" in df:
        heart_rate_avg = round(df[df["heart_rate"] != 0]["heart_rate"].mean(skipna=True))
        # heart_rate_max = round(df["heart_rate"].quantile(q=0.99, interpolation="linear"))
        heart_rate_max = round(df["heart_rate"].max())
    else:
        heart_rate_avg = heart_rate_max = None

    if "timestamp" in df:
        ts_column = "timestamp"
    elif "time" in df:
        ts_column = "time"
        
    if "power" in df:
        power_avg        = round(df[df["power"] != 0]["power"].mean(skipna=True))
        # power_max        = round(df["power"].quantile(q=0.99, interpolation="linear"))
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
        # cadence_max = round(df["cadence"].quantile(q=0.99, interpolation="linear"))
        cadence_max = round(df["cadence"].max())
    else:
        cadence_avg = cadence_max = 0

    if "enhanced_speed" in df:
        speed_avg = round(df["enhanced_speed"].mean(skipna=True) * 3.6)
        # speed_max = round(df["enhanced_speed"].quantile(q=0.99, interpolation="linear") * 3.6)
        speed_max = round(df["enhanced_speed"].max() * 3.6)
    elif "speed" in df:
        # For now, GPX files appear to contain `speed` expressed in mph; converting it to kmh
        speed_avg = round(df["speed"].mean(skipna=True) * 1.609)
        # speed_max = round(df["speed"].quantile(q=0.99, interpolation="linear") * 1.609)
        speed_max = round(df["speed"].max() * 1.609)
    else:
        speed_avg = speed_max = 0

    if "temperature" in df:
        temperature_avg = round(df["temperature"].mean(skipna=True))
        # temperature_max = round(df["temperature"].quantile(q=0.99, interpolation="linear"))
        temperature_max = round(df["temperature"].max())
    else:
        temperature_avg = temperature_max = 0

    if format == "fit":
        distance_km = round(df["distance"].max() / 1000)
    else:
        distance_km = round(df["distance"].max())
        
    if 'timestamp' in df:
        coasting_time = get_coasting(df, time_column='timestamp')
        stopped_time  = get_stopped_time(df, time_column='timestamp')
        work_time     = get_work_time(df, time_column='timestamp')
        total_time    = get_total_time(df, time_column='timestamp')
    elif 'time' in df:
        coasting_time = get_coasting(df, time_column='time')
        stopped_time  = get_stopped_time(df, time_column='time')
        work_time     = get_work_time(df, time_column='time')
        total_time    = get_total_time(df, time_column='time')
    else:
        coasting_time = '0m'
        stopped_time  = '0m'
        work_time     = '0m'
        total_time    = '0m'
    
    df0 = pd.DataFrame({
        'hr_avg':               [heart_rate_avg],
        'hr_max':               [heart_rate_max],
        'power_avg':            [power_avg],
        'power_max':            [power_max],
        'power_max_avg_30s':    [power_30s],
        'power_max_avg_5m':     [power_5],
        'power_max_avg_10m':    [power_10],
        'power_max_avg_20m':    [power_20],
        'power_max_avg_60m':    [power_60],
        'power_normalized':     [power_np],
        'intensity_factor':     [intensity_factor],
        'tss':                  [tss],
        'cadence_avg':          [cadence_avg],
        'cadence_max':          [cadence_max],
        'speed_avg':            [speed_avg],
        'speed_max':            [speed_max],
        'temp_avg':             [temperature_avg],
        'temp_max':             [temperature_max],
        'distance_total':       [distance_km],
        'time_coasting':        [coasting_time],
        'time_stopped':         [stopped_time],
        'time_working':         [work_time],
        'time_total':           [total_time],
    })
    
    return df0

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

def get_intensity_factor(normalized_power: float, ftp: float) -> float:
    if ftp <= 0:
        raise ValueError("FTP must be a positive number")

    intensity_factor = normalized_power / ftp
    return round(intensity_factor, 3)

def get_tss(normalized_power: float, ftp: float, duration_seconds: float, intensity_factor: float) -> float:
    if ftp <= 0 or duration_seconds <= 0:
        raise ValueError("FTP and duration must be positive numbers")
    
    tss = (duration_seconds * normalized_power * intensity_factor) / (ftp * 3600) * 100
    return round(tss, 1)

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

def get_max_avg_pwr(df: pd.DataFrame, minutes: float, time_column: str = 'timestamp') -> float:
    if 'power' not in df or time_column not in df:
        raise ValueError(f"The DataFrame must contain 'power' and '{time_column}' columns")
    
    df = df.sort_values(by=time_column).reset_index(drop=True)
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        df[time_column] = pd.to_datetime(df[time_column])
    
    window_seconds  = minutes * 60
    total_time_span = (df[time_column].max() - df[time_column].min()).total_seconds()

    if total_time_span < window_seconds:
        return 0
    
    # Sliding window calculation
    max_avg_power = 0
    for i in range(len(df)):
        start_time  = df.loc[i, time_column]
        end_time    = start_time + pd.Timedelta(seconds=window_seconds)
        window_data = df[(df[time_column] >= start_time) & (df[time_column] <= end_time)]
        
        if not window_data.empty:
            avg_power = window_data['power'].mean(skipna=True)
            if avg_power > max_avg_power:
                max_avg_power = avg_power
    return round(max_avg_power)

def get_coasting(df: pd.DataFrame, time_column: str = 'timestamp') -> str:
    if 'power' not in df or 'cadence' not in df or ('speed' not in df and 'enhanced_speed' not in df) or time_column not in df:
        raise ValueError(f"The DataFrame must contain 'power', 'cadence', 'speed', and '{time_column}' columns")
    
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

    return f"{hours}h {minutes}m {seconds}s"

def get_stopped_time(df: pd.DataFrame, time_column: str = 'timestamp') -> str:
    if ('speed' not in df and 'enhanced_speed' not in df) or time_column not in df:
        raise ValueError(f"The DataFrame must contain 'speed' or 'enhanced_speed', and '{time_column}' columns")
    
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

    return f"{hours}h {minutes}m {seconds}s"

def get_work_time(df: pd.DataFrame, time_column: str = 'timestamp') -> str:
    if 'power' not in df or 'cadence' not in df or time_column not in df:
        raise ValueError(f"The DataFrame must contain 'power', 'cadence', and '{time_column}' columns")
    
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

    return f"{hours}h {minutes}m {seconds}s"

def get_total_time(df: pd.DataFrame, time_column: str = 'timestamp') -> str:
    if time_column not in df:
        raise ValueError(f"The DataFrame must contain the '{time_column}' column")
    
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

    return f"{hours}h {minutes}m {seconds}s"

def get_chart_data(df: pd.DataFrame, y_col: str, x_col: str) -> pd.DataFrame:
    if not all(col in df.columns for col in [y_col, x_col]):
        raise ValueError("One or more specified columns do not exist in the DataFrame.")
    chart_data = df[[x_col, y_col]].copy()
    chart_data.set_index(x_col, inplace=True)
    return chart_data

def aggregate_by_time(df: pd.DataFrame, timestamp_col: str, interval: str = '5min') -> pd.DataFrame:
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' does not exist in the DataFrame.")
    
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df                = df.set_index(timestamp_col)
    aggregated_df     = df.resample(interval).apply(lambda x: x.quantile(0.99)).reset_index()
        
    return aggregated_df

# Profile Helpers
def load_data(data_file):
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            data = json.load(file)
            return pd.json_normalize(data)
    return pd.DataFrame()  # Return an empty DataFrame if no data exists

def save_data(data, data_file):
    with open(data_file, "w") as file:
        json.dump(data, file, indent=4)
        
def get_latest_ftp(data_file):
    df = load_data(data_file)
    if not df.empty and "ftp" in df.columns:
        ftp = df["ftp"].iloc[-1]
        if pd.notna(ftp):
            return int(ftp)
        else:
            return 0
    else:
        return 0