# Function to stack the data from each sheet
import pandas as pd
import os 
import zipfile
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import matplotlib
import xlrd
matplotlib.use('Agg')

def extract_zip(zip_path):
    # Create a temporary folder to extract the files
    temp_folder = "temp"
    os.makedirs(temp_folder, exist_ok=True)

    # Extract the ZIP file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder)

    return temp_folder



def stack_excel_data(folder_path):
    # Get a list of all files in the folder
    files = os.listdir(folder_path)

    # Create an empty DataFrame to store the stacked data
    stacked_df = pd.DataFrame(columns=['Name', 'Signal', 'Prediction', 'Duration', 'Date'])

    # Iterate over each file
    for file in files:
        # Check if the file is an Excel file
        if file.endswith('.xlsx') or file.endswith('.xls'):
            # Construct the full file path
            file_path = os.path.join(folder_path, file)

            # Load the Excel sheet into a DataFrame
            df_sheet1 = pd.read_excel(file_path, sheet_name=0)
            df_sheet2 = pd.read_excel(file_path, sheet_name=1)
            date_str = df_sheet1.columns[8]
            date = pd.to_datetime(date_str, format='%d_%b_%Y')

            # Function to stack the data from each sheet
            def stack_data(df, stacked_df, date):
                # Iterate through the desired column ranges
                column_ranges = [(1, 6), (7, 12), (13, 18)]
                for start_col, end_col in column_ranges:
                    # Extract the relevant columns
                    part_df = df.iloc[:, start_col:end_col]

                    # Create a temporary DataFrame to hold the stacked data for this iteration
                    temp_df = pd.DataFrame(columns=['Name', 'Signal', 'Prediction'])

                    # Iterate over the rows starting from row index 4
                    i = 4
                    while i < part_df.shape[0]:
                        if part_df.iloc[i].isnull().any():
                            i += 3  # Skip the current row and the next two rows
                        else:
                            # Extract the values for each column in the row
                            values_name = part_df.iloc[i].values
                            values_signal = part_df.iloc[i + 1].values
                            values_prediction = part_df.iloc[i + 2].values

                            # Append the values to the temporary DataFrame
                            temp_df = pd.concat([temp_df, pd.DataFrame({
                                'Name': values_name,
                                'Signal': values_signal,
                                'Prediction': values_prediction
                            })], ignore_index=True)

                        i += 3

                    # Reset the index of the temporary DataFrame
                    temp_df = temp_df.reset_index(drop=True)

                    # Extract the string value from the first four rows
                    string_value = part_df.iloc[:4].values.flatten().tolist()
                    string_value = next((str_val for str_val in string_value if isinstance(str_val, str)), None)

                    # Store the string value in a duration variable
                    duration = string_value

                    # Add the duration and date columns to the temporary DataFrame
                    temp_df['Duration'] = duration
                    temp_df['Date'] = date

                    # Append the temporary DataFrame to the stacked DataFrame
                    stacked_df = pd.concat([stacked_df, temp_df], ignore_index=True)

                return stacked_df

            # Stack the data from sheet one
            stacked_df = stack_data(df_sheet1, stacked_df, date)
            # Stack the data from sheet two
            stacked_df = stack_data(df_sheet2, stacked_df, date)

    # Sort the DataFrame by the index (Date) in ascending order
    stacked_df.sort_values('Date', inplace=True)

    # Set the 'Date' column as the index of the DataFrame
    stacked_df.set_index('Date', inplace=True)
    stacked_df['Cumulative Value'] = stacked_df['Signal'] * stacked_df['Prediction']

    return stacked_df






def plot_stock_data(stacked_data, start_date, end_date, duration, stock_names, plot_variable,log_scale=False):
    # Convert start_date and end_date to datetime objects
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    # Find the nearest available start and end dates in the DataFrame
    nearest_start_date = min(stacked_data.index, key=lambda x: abs((x - start_datetime).days))
    nearest_end_date = min(stacked_data.index, key=lambda x: abs((x - end_datetime).days))

    # Filter the data based on nearest_start_date, nearest_end_date, and duration
    filtered_data = stacked_data.loc[(stacked_data.index >= nearest_start_date) & 
                                     (stacked_data.index <= nearest_end_date) & 
                                     (stacked_data['Duration'] == duration)]

    filtered_data = filtered_data[filtered_data['Name'].isin(stock_names)]
    # Pivot the data to have stock names as columns and dates as index
    pivot_data = filtered_data.pivot(columns='Name', values=plot_variable)

    # Set the figure size
    plt.figure(figsize=(12, 8))  # Adjust the width and height as per your preference

    # Plot the variable for each stock name
    lines = []
    legend_labels = []
    for stock_name in stock_names:
        line, = plt.plot(pivot_data.index, pivot_data[stock_name], linewidth=2)  # Adjust the linewidth
        lines.append(line)
        legend_labels.append(stock_name)

    # Set the plot title and labels
    plt.title(f'{plot_variable} for Stocks over {duration} from {nearest_start_date.date()} to {nearest_end_date.date()}')
    plt.xlabel('Date')
    plt.ylabel(plot_variable)

    # Move the legend to the side
    plt.legend(lines, legend_labels, bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)

    # Add a grid
    plt.grid(True)
    if log_scale:
        plt.yscale('log')
    # Save the figure as a PNG file
    plot_file_path = 'website/static/stock_data_plot.png'  # Modify the file path as needed
    plt.savefig(plot_file_path, dpi=300, bbox_inches='tight')
    
    plt.close()



import numpy as np

import matplotlib.patches as mpatches

def plot_single_daily_data(data, ticker, time, log_scale=False):
    # Filter the data for the desired ticker and closest time
    filtered_data = data[data['Name'] == ticker]
    closest_time = min(filtered_data.index, key=lambda x: abs(x - time))

    # Create bar charts for single daily data set
    plt.figure(figsize=(12, 6))
    bar_width = 0.2
    opacity = 0.8
    categories = filtered_data['Duration'].unique()  # Get unique categories for the ticker
    colors = ['red', 'green', 'blue']  # Assign colors to prediction, cumulative value, and signal

    for i, category in enumerate(categories):
        category_data = filtered_data[filtered_data['Duration'] == category]
        x = [i + j * bar_width for j in range(3)]  # Three bars for each category
        y = [
            category_data[category_data.index == closest_time]['Prediction'].mean(),
            category_data[category_data.index == closest_time]['Cumulative Value'].mean(),
            category_data[category_data.index == closest_time]['Signal'].mean()
        ]
        plt.bar(x, y, width=bar_width, alpha=opacity, color=colors)

    plt.xlabel('Time Category')
    plt.ylabel('Mean')
    plt.title(f'Single Daily Data Set - Ticker: {ticker} - Closest Time: {closest_time}')
    plt.xticks([i + bar_width for i in range(len(categories))], categories)
    
    # Create custom legend
    legend_patches = [
        mpatches.Patch(color='red', label='Prediction'),
        mpatches.Patch(color='green', label='Cumulative Value'),
        mpatches.Patch(color='blue', label='Signal')
    ]
    plt.legend(handles=legend_patches, loc='upper right')

    plt.tight_layout()
    
    if log_scale:
        plt.yscale('log')
    plot_file_path = 'website/static/stock_data_plot_daily.png'  # Modify the file path as needed
    plt.savefig(plot_file_path, dpi=300, bbox_inches='tight')
    plt.close()







from datetime import datetime

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
