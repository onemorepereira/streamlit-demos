from datetime import datetime
from src.core import UserProfile
import hashlib as hash
import json
import os
import pandas as pd
import src.utils as h

def convert_timestamp_to_serializable(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    else:
        return obj
    
def json_serializer(obj):
    return convert_timestamp_to_serializable(obj)

profile = UserProfile()
FTP                 = profile.get_ftp()
BIO_HR_MAX          = profile.get_max_hr()
BIO_HR_RESTING      = profile.get_resting_hr()
LATEST_HR_ZONES     = profile.get_hr_zones()
LATEST_POWER_ZONES  = profile.get_power_zones()
API_KEY             = profile.get_api_key()

ext_filter  = 'fit'
root        = './samples'
files       = os.listdir(root)

for file in files:
    if file.endswith(ext_filter):
        print(f"{root}/{file}")
        full_path = f"{root}/{file}"
        with open(full_path, 'rb') as fitfile:
            fitfile        = h.parse_fit_file(fitfile)
            fit_records_df = fitfile[0]
            fit_events_df  = fitfile[1]
            fit_session_df = fitfile[2]
            summary_df     = h.get_summary(fit_records_df, ftp = FTP, format=ext_filter)
            
            activity_type       = fit_session_df['sport'].iloc[-1]
            activity_sub_type   = fit_session_df['sub_sport'].iloc[-1]
            activity_start_time = fit_events_df['timestamp'].iloc[0] if fit_events_df['timestamp'].iloc[0] else None
            activity_end_time   = fit_events_df['timestamp'].iloc[-1] if fit_events_df['timestamp'].iloc[0] else None
            
            activity_distance = summary_df['distance_total'].iloc[0]
            speed_average     = summary_df['speed_avg'].iloc[0]
            speed_max         = summary_df['speed_max'].iloc[0]
            
            if 'indoor' not in activity_sub_type:
                try:
                    activity_start_latitude  = fit_records_df['position_lat'].iloc[0]*(180 / 2**31)
                    activity_start_longitude = fit_records_df['position_long'].iloc[0]*(180 / 2**31)

                    rgeo_start = h.get_location_details(api_key=API_KEY,
                                                        latitude=activity_start_latitude,
                                                        longitude=activity_start_longitude)

                    activity_start_city     = rgeo_start['city']
                    activity_start_state    = rgeo_start['state']
                    activity_start_zip      = rgeo_start['postal_code']
                    activity_start_country  = rgeo_start['country']
                    
                except Exception as e:
                    print(e)
                    activity_start_city     = None
                    activity_start_state    = None
                    activity_start_zip      = None
                    activity_start_country  = None
            
                try:
                    activity_end_latitude  = fit_records_df['position_lat'].iloc[-1]*(180 / 2**31)
                    activity_end_longitude = fit_records_df['position_long'].iloc[-1]*(180 / 2**31)
                
                    rgeo_end = h.get_location_details(api_key=API_KEY,
                                                    latitude=activity_end_latitude,
                                                    longitude=activity_end_longitude)
                    
                    activity_end_city     = rgeo_end['city']
                    activity_end_state    = rgeo_end['state']
                    activity_end_zip      = rgeo_end['postal_code']
                    activity_end_country  = rgeo_end['country']
                    
                except Exception as e:
                    print(e)
                    activity_end_city     = None
                    activity_end_state    = None
                    activity_end_zip      = None
                    activity_end_country  = None
            else:
                activity_start_city     = None
                activity_start_state    = None
                activity_start_zip      = None
                activity_start_country  = None
            
            activity_id = hash.sha256(f"{activity_type} {activity_sub_type} {activity_start_time}".encode('utf-8')).hexdigest()
            
            time_coasting = summary_df['time_coasting_seconds'].iloc[0]
            time_stopped  = summary_df['time_stopped_seconds'].iloc[0]
            time_working  = summary_df['time_working_seconds'].iloc[0]
            time_total    = summary_df['time_total_seconds'].iloc[0]
            
            power_average       = summary_df['power_avg'].iloc[0]
            power_max           = summary_df['power_max'].iloc[0]
            power_normalized    = summary_df['power_normalized'].iloc[0]
            power_30s_max_avg   = summary_df['power_max_avg_30s'].iloc[0]
            power_5m_max_avg    = summary_df['power_max_avg_5m'].iloc[0]
            power_10m_max_avg   = summary_df['power_max_avg_10m'].iloc[0]
            power_20m_max_avg   = summary_df['power_max_avg_20m'].iloc[0]
            power_60m_max_avg   = summary_df['power_max_avg_60m'].iloc[0]
            
            cadence_average = summary_df['cadence_avg'].iloc[0]
            cadence_max     = summary_df['cadence_max'].iloc[0]
            
            hr_average  = summary_df['hr_avg'].iloc[0]
            hr_max      = summary_df['hr_max'].iloc[0]
            
            intensity_factor    = summary_df['intensity_factor'].iloc[0]
            
            hr_zone_time = h.calculate_hr_zone_time(fit_records_df, LATEST_HR_ZONES)

            te = h.calculate_training_effect(hr_zone_time, intensity_factor)
            
            te_aerobic              = te[0]
            te_anaerobic            = te[1]
            training_stress_score   = summary_df['tss'].iloc[0]
            
            bio_hr_resting    = BIO_HR_RESTING
            bio_hr_max        = BIO_HR_MAX
            bio_hr_zone_1_min = LATEST_HR_ZONES['zone.1.low_hr']
            bio_hr_zone_1_max = LATEST_HR_ZONES['zone.1.max_hr']
            bio_hr_zone_2_min = LATEST_HR_ZONES['zone.2.low_hr']
            bio_hr_zone_2_max = LATEST_HR_ZONES['zone.2.max_hr']
            bio_hr_zone_3_min = LATEST_HR_ZONES['zone.3.low_hr']
            bio_hr_zone_3_max = LATEST_HR_ZONES['zone.3.max_hr']
            bio_hr_zone_4_min = LATEST_HR_ZONES['zone.4.low_hr']
            bio_hr_zone_4_max = LATEST_HR_ZONES['zone.4.max_hr']
            bio_hr_zone_5_min = LATEST_HR_ZONES['zone.5.low_hr']
            bio_hr_zone_5_max = LATEST_HR_ZONES['zone.5.max_hr']
            
            hr_time_in_zone_1 = hr_zone_time.loc[hr_zone_time['zone'] == 'zone1', 'time_in_seconds'].values[0]
            hr_time_in_zone_2 = hr_zone_time.loc[hr_zone_time['zone'] == 'zone2', 'time_in_seconds'].values[0]
            hr_time_in_zone_3 = hr_zone_time.loc[hr_zone_time['zone'] == 'zone3', 'time_in_seconds'].values[0]
            hr_time_in_zone_4 = hr_zone_time.loc[hr_zone_time['zone'] == 'zone4', 'time_in_seconds'].values[0]
            hr_time_in_zone_5 = hr_zone_time.loc[hr_zone_time['zone'] == 'zone5', 'time_in_seconds'].values[0]

            
            power_zone_time = h.calculate_power_zone_time(fit_records_df, LATEST_POWER_ZONES)
            
            power_time_in_zone_1 = power_zone_time.loc[power_zone_time['zone'] == 'zone1', 'time_in_seconds'].values[0]
            power_time_in_zone_2 = power_zone_time.loc[power_zone_time['zone'] == 'zone2', 'time_in_seconds'].values[0]
            power_time_in_zone_3 = power_zone_time.loc[power_zone_time['zone'] == 'zone3', 'time_in_seconds'].values[0]
            power_time_in_zone_4 = power_zone_time.loc[power_zone_time['zone'] == 'zone4', 'time_in_seconds'].values[0]
            power_time_in_zone_5 = power_zone_time.loc[power_zone_time['zone'] == 'zone5', 'time_in_seconds'].values[0]
            power_time_in_zone_6 = power_zone_time.loc[power_zone_time['zone'] == 'zone6', 'time_in_seconds'].values[0]
            power_time_in_zone_7 = power_zone_time.loc[power_zone_time['zone'] == 'zone7', 'time_in_seconds'].values[0]

            bio_power_ftp        = FTP
            bio_power_zone_1_min = LATEST_POWER_ZONES['zone.1.low_pwr']
            bio_power_zone_1_max = LATEST_POWER_ZONES['zone.1.max_pwr']
            bio_power_zone_2_min = LATEST_POWER_ZONES['zone.2.low_pwr']
            bio_power_zone_2_max = LATEST_POWER_ZONES['zone.2.max_pwr']
            bio_power_zone_3_min = LATEST_POWER_ZONES['zone.3.low_pwr']
            bio_power_zone_3_max = LATEST_POWER_ZONES['zone.3.max_pwr']
            bio_power_zone_4_min = LATEST_POWER_ZONES['zone.4.low_pwr']
            bio_power_zone_4_max = LATEST_POWER_ZONES['zone.4.max_pwr']
            bio_power_zone_5_min = LATEST_POWER_ZONES['zone.5.low_pwr']
            bio_power_zone_5_max = LATEST_POWER_ZONES['zone.5.max_pwr']
            bio_power_zone_6_min = LATEST_POWER_ZONES['zone.6.low_pwr']
            bio_power_zone_6_max = LATEST_POWER_ZONES['zone.6.max_pwr']
            bio_power_zone_7_min = LATEST_POWER_ZONES['zone.7.low_pwr']
            bio_power_zone_7_max = LATEST_POWER_ZONES['zone.7.max_pwr']
            

        activity_data = dict()
        with open(f"{root}/summary_{file}.json", 'w') as json_file:
            activity_data[activity_id] = {
                'activity_type':            activity_type,
                'activity_sub_type':        activity_sub_type,
                'activity_start_time':      convert_timestamp_to_serializable(activity_start_time),
                'activity_end_time':        convert_timestamp_to_serializable(activity_end_time),
                'activity_start_latitude':  activity_start_latitude,
                'activity_start_longitude': activity_start_longitude,
                'activity_start_city':      activity_start_city,
                'activity_start_state':     activity_start_state,
                'activity_start_zip':       activity_start_zip,
                'activity_start_country':   activity_start_country,
                'activity_end_latitude':    activity_end_latitude,
                'activity_end_longitude':   activity_end_longitude,
                'activity_end_city':        activity_end_city,
                'activity_end_state':       activity_end_state,
                'activity_end_zip':         activity_end_zip,
                'activity_end_country':     activity_end_country,
                'activity_distance':        round(float(activity_distance), 2),
                'time_coasting':            int(time_coasting),
                'time_stopped':             int(time_stopped),
                'time_working':             int(time_working),
                'time_total':               int(time_total),
                'speed_average':            round(float(speed_average), 2),
                'speed_max':                round(float(speed_max), 2),
                'power_average':            round(float(power_average),2),
                'power_max':                round(float(power_max),2),
                'power_normalized':         round(float(power_normalized), 2),
                'power_30s_max_avg':        round(float(power_30s_max_avg), 2),
                'power_5m_max_avg':         round(float(power_5m_max_avg), 2),
                'power_10m_max_avg':        round(float(power_10m_max_avg), 2),
                'power_20m_max_avg':        round(float(power_20m_max_avg), 2),
                'power_60m_max_avg':        round(float(power_60m_max_avg), 2),
                'power_time_in_zone_1':     int(power_time_in_zone_1),
                'power_time_in_zone_2':     int(power_time_in_zone_2),
                'power_time_in_zone_3':     int(power_time_in_zone_3),
                'power_time_in_zone_4':     int(power_time_in_zone_4),
                'power_time_in_zone_5':     int(power_time_in_zone_5),
                'power_time_in_zone_6':     int(power_time_in_zone_6),
                'power_time_in_zone_7':     int(power_time_in_zone_7),
                'cadence_max':              int(cadence_max),
                'cadence_average':          int(cadence_average),
                'hr_max':                   int(hr_max),
                'hr_average':               int(hr_average),
                'hr_time_in_zone_1':        int(hr_time_in_zone_1),
                'hr_time_in_zone_2':        int(hr_time_in_zone_2),
                'hr_time_in_zone_3':        int(hr_time_in_zone_3),
                'hr_time_in_zone_4':        int(hr_time_in_zone_4),
                'hr_time_in_zone_5':        int(hr_time_in_zone_5),
                'te_aerobic':               round(float(te_aerobic), 2),
                'te_anaerobic':             round(float(te_anaerobic), 2),
                'intensity_factor':         round(float(intensity_factor), 4),
                'training_stress_score':    int(training_stress_score),
                'bio_hr_resting':           bio_hr_resting,
                'bio_hr_max':               bio_hr_max,
                'bio_hr_zone_1_min':        int(bio_hr_zone_1_min),
                'bio_hr_zone_1_max':        int(bio_hr_zone_1_max),
                'bio_hr_zone_2_min':        int(bio_hr_zone_2_min),
                'bio_hr_zone_2_max':        int(bio_hr_zone_2_max),
                'bio_hr_zone_3_min':        int(bio_hr_zone_3_min),
                'bio_hr_zone_3_max':        int(bio_hr_zone_3_max),
                'bio_hr_zone_4_min':        int(bio_hr_zone_4_min),
                'bio_hr_zone_4_max':        int(bio_hr_zone_4_max),
                'bio_hr_zone_5_min':        int(bio_hr_zone_5_min),
                'bio_hr_zone_5_max':        int(bio_hr_zone_5_max),
                'bio_power_ftp':            bio_power_ftp,
                'bio_power_zone_1_min':     0,
                'bio_power_zone_1_max':     int(bio_power_zone_1_max),
                'bio_power_zone_2_min':     int(bio_power_zone_2_min),
                'bio_power_zone_2_max':     int(bio_power_zone_2_max),
                'bio_power_zone_3_min':     int(bio_power_zone_3_min),
                'bio_power_zone_3_max':     int(bio_power_zone_3_max),
                'bio_power_zone_4_min':     int(bio_power_zone_4_min),
                'bio_power_zone_4_max':     int(bio_power_zone_4_max),
                'bio_power_zone_5_min':     int(bio_power_zone_5_min),
                'bio_power_zone_5_max':     int(bio_power_zone_5_max),
                'bio_power_zone_6_min':     int(bio_power_zone_6_min),
                'bio_power_zone_6_max':     int(bio_power_zone_6_max),
                'bio_power_zone_7_min':     int(bio_power_zone_7_min),
                'bio_power_zone_7_max':     int(bio_power_zone_7_max),
            }
            
            json.dump(activity_data, json_file, indent=4)