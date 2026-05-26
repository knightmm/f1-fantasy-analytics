import os
import pandas as pd


def load_csvs_to_table(
    processed_dir,
    file_prefix,
    table_name,
    connection,
):
    matching_files = []

    # Find CSVs
    for file in os.listdir(processed_dir):
        if file.startswith(file_prefix):
            matching_files.append(file)

    matching_files.sort()
    
    if not matching_files:
        print(f"No files found for {file_prefix}")
        return

    dfs = []

    # Read CSVs and create dataframe
    for file in matching_files:
        filepath = os.path.join(processed_dir, file)

        df = pd.read_csv(filepath)

        dfs.append(df)

    # Stack CSVs
    combined_df = pd.concat(
        dfs,
        ignore_index=True,
    )

    # Write to DB
    combined_df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False,
    )

    print(f"Loaded {table_name} table")