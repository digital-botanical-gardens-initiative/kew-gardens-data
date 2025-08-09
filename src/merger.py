# This python script, reads .xlsx files from the data/input directory.
# It then merges them in a singl .csv file in the data/output directory.
# The merged file is named 'kew-species-list.csv'.

import os
import pandas as pd


def merge_excel_files(input_directory, output_file):
    # List all Excel files in the input directory
    all_files = [f for f in os.listdir(input_directory) if f.endswith('.xlsx')]
    
    # Initialize an empty list to hold dataframes
    dataframes = []
    
    # Read each Excel file and append its dataframe to the list
    for file in all_files:
        file_path = os.path.join(input_directory, file)
        df = pd.read_excel(file_path)
        dataframes.append(df)

    # Printe the column names of the files being merged
    for i, df in enumerate(dataframes):
        print(f'File {i+1}: {os.path.basename(all_files[i])} - Columns: {list(df.columns)}')
    
    # Check if the files contain the same columns
    if not all(set(df.columns) == set(dataframes[0].columns) for df in dataframes):
        raise ValueError("Not all files have the same columns. Please check the input files.")

    # We add a new column to each dataframe to indicate the source file
    for i, df in enumerate(dataframes):
        df['source_file'] = os.path.basename(all_files[i])
        print(f'Added source_file column to {os.path.basename(all_files[i])}')

    # Concatenate all dataframes into a single dataframe
    merged_df = pd.concat(dataframes, ignore_index=True)

    # We also check that they are no duplicate rows
    # and inform the user if there are any
    initial_row_count = len(merged_df)
    merged_df.drop_duplicates(inplace=True)
    final_row_count = len(merged_df)
    if initial_row_count != final_row_count:
        print(f'Removed {initial_row_count - final_row_count} duplicate rows from the merged dataframe.')

    # Save the merged dataframe to a CSV file
    merged_df.to_csv(output_file, index=False)
    return merged_df

# Another function to output a json suited for vega visualization
def output_vega_json(merged_df, output_file):
    # Convert the DataFrame to a dictionary format suitable for Vega
    vega_data = merged_df.to_dict(orient='records')
    
    # Save the dictionary to a JSON file
    with open(output_file, 'w') as f:
        import json
        json.dump(vega_data, f, indent=4)


## Bar chart example for Vega visualization

# The following function will output a barchart of all entries at the Family level

def output_family_barchart(merged_df, output_file):
    # Group by 'Family' and count occurrences
    family_counts = merged_df['Family'].value_counts().reset_index()
    family_counts.columns = ['Family', 'Count']
    
    # Create a Vega JSON structure for the bar chart
    vega_spec = {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "description": "Bar chart of species counts by Family",
        "width": 400,
        "height": 200,
        "padding": 5,
        "data": [
            {
                "name": "table",
                "values": family_counts.to_dict(orient='records')
            }
        ],
        "scales": [
            {
                "name": "xscale",
                "type": "band",
                "domain": {"data": "table", "field": "Family"},
                "range": "width",
                "padding": 0.05,
                "round": True
            },
            {
                "name": "yscale",
                "domain": {"data": "table", "field": "Count"},
                "nice": True,
                "range": "height"
            }
        ],
        "axes": [
            {"orient": "bottom", "scale": "xscale"},
            {"orient": "left", "scale": "yscale"}
        ],
        "marks": [
            {
                "type": "rect",
                "from": {"data":"table"},
                "encode": {
                    "enter": {
                        "x": {"scale": "xscale", "field": "Family"},
                        "width": {"scale": "xscale", "band": 1},
                        "y": {"scale": "yscale", "field": "Count"},
                        "y2": {"scale": "yscale", "value": 0}
                    },
                    "update": {
                        "fill": {"value": "#4682b4"}
                    },
                    "hover": {
                        "fillOpacity": {"value": 0.7}
                    }
                }
            },
            {
                "type": 'text',
                'encode': {
                    'enter': {
                        'align': {'value': 'center'},
                        'baseline': {'value': 'bottom'},
                        'fill': {'value': '#333'}
                    },
                    'update': {
                        'x': {'scale': 'xscale', 'field': 'Family', 'band': 0.5},
                        'y': {'scale': 'yscale', 'field': 'Count', 'offset': -2},
                        'text': {'field': 'Count'},
                        'fillOpacity': [
                            {'test': 'datum.Count > 0', 'value': 1},
                            {'value': 0}
                        ]
                    }
                }
            }   
        ]
    }   

    # Save the Vega JSON to a file
    with open(output_file, 'w') as f:
        import json
        json.dump(vega_spec, f, indent=4)


if __name__ == "__main__":
    input_directory = 'data/input'
    output_file = 'data/output/kew-species-list.csv'
    
    merge_excel_files(input_directory, output_file)
    print(f'Merged data saved to {output_file}')

    vega_output_file = 'data/output/kew-species-list.json'
    output_vega_json(pd.read_csv(output_file), vega_output_file)
    print(f'Vega JSON data saved to {vega_output_file}')

    family_barchart_file = 'data/output/kew-family-barchart.json'
    output_family_barchart(pd.read_csv(output_file), family_barchart_file)
    print(f'Family bar chart JSON saved to {family_barchart_file}')
else:
    print("This script is intended to be run as a standalone program.")
