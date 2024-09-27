import altair as alt
import gpxpy
import pandas as pd
from xml.etree import ElementTree as ET
from math import radians, sin, cos, sqrt, atan2


# Namespace mapping
NAMESPACES = {
    'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
}

def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
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
                data['temperature'].append(((atemp * 9/5) + 32) if atemp is not None else 0)
                data['heart_rate'].append(hr)
                data['cadence'].append(cad)
                data['power'].append(pwr)
                
                # Calculate the distance from the previous point
                if previous_point is not None:
                    dist = haversine(previous_point['latitude'], previous_point['longitude'], point.latitude, point.longitude)
                    time_diff = (point.time - previous_time).total_seconds()
                    
                    # Calculate speed (miles per hour)
                    speed = dist / time_diff * 2.237 if time_diff > 0 else 0
                else:
                    dist  = 0  # No distance for the first point
                    speed = 0  # No speed for the first point
                
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
    
    # agg_df1['avg_{y_column}'] = agg_df1[y_column].mean()
    # agg_df2['max_{y_column}'] = agg_df2[y_column].mean()
    # agg_df1['avg_{y_column}'] = agg_df1[y_column].max()
    # agg_df2['max_{y_column}'] = agg_df2[y_column].max()
    
    # Combine the two DataFrames for a single chart
    combined_df = pd.concat([agg_df1, agg_df2])

    # Calculate Y min and max with +/- 10%
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
            scale=alt.Scale(domain=(y_min, y_max))  # Set the Y-axis scale
        ),
        color=alt.Color('source:N').title('Average {}'.format(y_column),).scale(scheme='darkred').legend(alt.Legend(orient='top', titleLimit=0, labelLimit=0)
        )
    ).properties(
        title=title,
        width=700,
        height=400
    ).interactive()