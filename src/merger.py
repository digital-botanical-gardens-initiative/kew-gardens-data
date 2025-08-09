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

    # Save the merged dataframe to a CSV file
    merged_df.to_csv(output_file, index=False)
    print(f'Merged data saved to {output_file}')
    return merged_df


if __name__ == "__main__":
    input_directory = 'data/input'
    output_file = 'data/output/kew-species-list.csv'
    
    merge_excel_files(input_directory, output_file)
    print(f'Merged data saved to {output_file}')
else:
    print("This script is intended to be run as a standalone program.")
