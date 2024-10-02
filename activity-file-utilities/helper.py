from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2
import altair as alt
import fitparse
import folium
import gpxpy
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
        'latitude_median':              'latitude',
        'longitude_median':             'longitude',
        'elevation_mean':               'mean_elevation',
        'elevation_median':             'median_elevation',
        'temperature_mean':             'mean_temperature',
        'temperature_median':           'median_temperature',
        'heart_rate_mean':              'mean_heart_rate',
        'heart_rate_median':            'median_heart_rate',
        'cadence_mean':                 'mean_cadence',
        'cadence_median':               'median_cadence',
        'speed_mean':                   'mean_speed',
        'speed_median':                 'median_speed',
        'power_mean':                   'mean_power',
        'power_median':                 'median_power',
        'distance_last':                'distance'
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
        df["latitude"] = df["position_lat"] * (180 / 2**31)
        df["longitude"] = df["position_long"] * (180 / 2**31)

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

    else:
        return None

def get_fit_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "heart_rate" in df:
        heart_rate_avg = round(df["heart_rate"].mean(skipna=True))
        heart_rate_max = round(df["heart_rate"].quantile(q=0.99, interpolation="linear"))
    else:
        heart_rate_avg = heart_rate_max = None

    if "power" in df:
        power_avg = round(df["power"].mean(skipna=True))
        power_max = round(df["power"].quantile(q=0.99, interpolation="linear"))
    else:
        power_avg = power_max = None

    if "cadence" in df:
        cadence_avg = round(df["cadence"].mean(skipna=True))
        cadence_max = round(df["cadence"].quantile(q=0.99, interpolation="linear"))
    else:
        cadence_avg = cadence_max = None

    if "enhanced_speed" in df:
        speed_avg = round(df["enhanced_speed"].mean(skipna=True) * 3.6)
        speed_max = round(df["enhanced_speed"].quantile(q=0.99, interpolation="linear") * 3.6)
    else:
        speed_avg = speed_max = None

    if "temperature" in df:
        temperature_avg = round(df["temperature"].mean(skipna=True))
        temperature_max = round(df["temperature"].quantile(q=0.99, interpolation="linear"))
    else:
        temperature_avg = temperature_max = None

    distance_km = round(df["distance"].max() / 1000)
    
    df0 = pd.DataFrame({
        'Avg BPM (❤️)':   [heart_rate_avg],
        'Max BPM (❤️)':   [heart_rate_max],
        'Avg Watts (⚡)': [power_avg],
        'Max Watts (⚡)': [power_max],
        'Avg RPM (🌪️)':   [cadence_avg],
        'Max RPM (🌪️)':   [cadence_max],
        'Avg KmH (🚴)':   [speed_avg],
        'Max KmH (🚴)':   [speed_max],
        'Avg ℃ (🌡️)':    [temperature_avg],
        'Max ℃ ()':    [temperature_max],
        'Total Km (📏)':  [distance_km]
    })
    
    return df0