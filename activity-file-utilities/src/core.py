import utils as h

class UserProfile:
    HR_FILE      = './userdata/hr_profile.json'
    POWER_FILE   = './userdata/power_profile.json'
    PROFILE_FILE = './userdata/basic_profile.json'
    
    def __init__(self, profile_file=PROFILE_FILE, hr_file=HR_FILE, power_file=POWER_FILE):
        # Initialize file paths
        self.profile_file = profile_file
        self.hr_file      = hr_file
        self.power_file   = power_file
        
        # Load initial data
        self.ftp          = h.get_latest_ftp(self.profile_file)
        self.max_hr       = h.get_latest_maxhr(self.profile_file)
        self.resting_hr   = h.get_latest_restinghr(self.profile_file)
        self.hr_zones     = h.load_data(self.hr_file)
        self.power_zones  = h.load_data(self.power_file)
        self.api_key      = h.get_opencage_key(self.profile_file)
    
    # Method to reload profile data
    def reload_profile(self):
        self.ftp        = h.get_latest_ftp(self.profile_file)
        self.max_hr     = h.get_latest_maxhr(self.profile_file)
        self.resting_hr = h.get_latest_restinghr(self.profile_file)
    
    # Method to reload HR zones
    def reload_hr_zones(self):
        self.hr_zones = h.load_data(self.hr_file)
    
    # Method to reload Power zones
    def reload_power_zones(self):
        self.power_zones = h.load_data(self.power_file)
    
    # Method to reload the API key
    def reload_api_key(self):
        self.api_key = h.get_opencage_key(self.profile_file)
    
    # Method to get the user's FTP
    def get_ftp(self):
        return self.ftp
    
    # Method to get the max heart rate
    def get_max_hr(self):
        return self.max_hr
    
    # Method to get resting heart rate
    def get_resting_hr(self):
        return self.resting_hr
    
    # Method to get HR zones
    def get_hr_zones(self):
        return self.hr_zones.iloc[-1]
    
    def get_all_hr_zones(self):
        return self.hr_zones
    
    
    # Method to get power zones
    def get_power_zones(self):
        return self.power_zones.iloc[-1]
    
    def get_all_power_zones(self):
        return self.power_zones
    
    # Method to get the API key
    def get_api_key(self):
        return self.api_key
