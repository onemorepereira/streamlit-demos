import logging
import pandas as pd
import os
import json

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s() - %(message)s', level=logging.INFO)


def write_df_to_json(df: pd.DataFrame, file_path: str, append: bool = False, orient: str = 'records', indent: int = 4):
    try:
        data_to_write = json.loads(df.to_json(orient=orient))
        
        # Append mode: Load existing data and combine with new data
        if append and os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
            if isinstance(existing_data, list):
                data_to_write = existing_data + data_to_write
            else:
                logging.warning("File format not compatible with appending.")
                return
        
        # Write (either new or appended) data to file
        with open(file_path, 'w') as file:
            json.dump(data_to_write, file, indent=indent)
        
        logging.info(f"DataFrame {'appended to' if append else 'written to'} {file_path} successfully.")
    
    except Exception as e:
        logging.error(f"Failed to write DataFrame to JSON: {e}")

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
        
        return grouped_df

    except Exception as e:
        logging.error(e)
        return None

def weekly_nutrient_summary(food_intake_df) -> pd.DataFrame:
    food_intake_df['Date'] = pd.to_datetime(food_intake_df['Date'])

    weekly_summary = food_intake_df.groupby(pd.Grouper(
        key='Date',
        freq='W')).agg(
            total_protein=('Total Protein (g)', 'sum'),
            total_carbs=('Total Carbs (g)', 'sum'),
            total_fat=('Total Fat (g)', 'sum'),
            total_calories=('Total Calories', 'sum'),
            )
    
    primary_sources = food_intake_df.groupby(pd.Grouper(
        key='Date',
        freq='W')).apply(
            lambda x: pd.Series({
                'primary_protein_source': x.loc[x['Total Protein (g)'].idxmax()]['Name'],
                'primary_carbs_source':   x.loc[x['Total Carbs (g)'].idxmax()]['Name'],
                'primary_fat_source':     x.loc[x['Total Fat (g)'].idxmax()]['Name'],
                'primary_caloric_source': x.loc[x['Total Calories'].idxmax()]['Name']
                })
            )
    
    weekly_summary = weekly_summary.merge(primary_sources, left_index=True, right_index=True)
    
    weekly_summary['week_start'] = weekly_summary.index - pd.to_timedelta(6, unit='D')
    
    return weekly_summary