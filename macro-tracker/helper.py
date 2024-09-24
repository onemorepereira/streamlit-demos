import logging
import pandas as pd

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)


def write_df_to_json(df: pd.DataFrame, file_path: str, orient: str = 'records', indent: int = 4):
    try:
        df.to_json(file_path, orient=orient, indent=indent)
        logging.info("DataFrame written to {} successfully.".format(file_path))
    except Exception as e:
        logging.info("Failed to write DataFrame to JSON: {}".format(e))

def load_df_from_json(file_path: str, orient: str = 'records'):
    try:
        df = pd.read_json(file_path, orient=orient)
        logging.info("Data loaded from {} successfully.".format(file_path))
        return df
    except Exception as e:
        logging.info("Failed to load data from JSON: {}".format(e))
        return None
    
def agg_df(df: pd.DataFrame):
    try:
        # Convert 'Date' from milliseconds to datetime
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')

        # Group by the 'Date' and sum the relevant columns
        grouped_df = df.groupby(df['Date'].dt.date).agg({
            'Total Protein (g)': 'sum',
            'Total Carbs (g)': 'sum',
            'Total Fat (g)': 'sum',
            'Total Calories': 'sum',
            'Total Weight (g)': 'sum'
        }).reset_index()

        # Rename the columns for clarity
        grouped_df.columns = ['Date',
                              'Total Protein (g)',
                              'Total Carbs (g)',
                              'Total Fat (g)',
                              'Total Calories',
                              'Total Weight (g)'
                              ]
        
        logging.info(grouped_df)
        return grouped_df

    except Exception as e:
        logging.error(e)
        return None