import os
import csv
import random
import shutil
import pandas as pd
import numpy as np

# Define the input directory containing files of different formats
input_directory = 'E:\\download\\data-input\\data'
# Define the output directory where the organized structure will be created
output_directory = 'E:\\project\\data-output'
# Directory containing format-specific entropy CSV files
entropy_directory = 'E:\\download\\data-input\\data'

# Create the basic format directories (TXT, PDF, FLV, MP4, JPEG, PNG)
# formats = ['FLV', 'MP4', 'JPG', 'PNG', 'TXT', 'PDF']
# formats = ['JPG']
formats = ['TXT', 'PDF', 'FLV', 'MP4', 'PNG']
# Create directories for size and repetition combinations
size_dirs = ['small', 'large']
repetition_dirs = ['low', 'high']

# Define the number of subdirectories for each size-repetition combination
num_subdirectories = 10


# Function to determine the size category (small or large)
def get_size_category(file_size, median_size):
    return 'small' if file_size < median_size else 'large'


# Function to determine the repetition category (low or high)
def get_repetition_category(file_repetition, median_repetition):
    return 'low' if file_repetition < median_repetition else 'high'


# Iterate through the files in the input directory
for format in formats:
    input_directory_format = os.path.join(input_directory, format)
    if not os.path.exists(input_directory_format):
        continue
    print(f'Processing files in {input_directory_format}')
    # import pdb; pdb.set_trace()
    for root, _, files in os.walk(input_directory_format):
        # get the median values for size in files
        file_size_list = []
        for file in files:
            # get file size
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_size_list.append(file_size)
        median_size = np.median(file_size_list)
        for file in files:
            file_path = os.path.join(root, file)

            # Determine the file format based on its extension
            file_format = file.split('.')[-1].upper()

            # Skip files with unknown formats
            if file_format not in formats:
                continue

            # Load the format-specific entropy information from the CSV file
            entropy_file = os.path.join(entropy_directory, f'entropy_{file_format}.csv')
            entropy_data = pd.read_csv(entropy_file, sep=',', header=0)
            # median_repetition is in the second column
            # import pdb; pdb.set_trace()

            # Calculate the median values for size and repetition for the current format
            # median_size = np.median(entropy_data['Size'])
            median_repetition = np.median(entropy_data['Repetition'])

            # Get file size and repetition information from the CSV file
            file_info = entropy_data.loc[entropy_data['File'] == file, ['Repetition']]

            if not file_info.empty:
                size_category = get_size_category(os.path.getsize(file_path), median_size)
                repetition_category = get_repetition_category(file_info.iloc[0]['Repetition'], median_repetition)
            else:
                # Use median values if information is missing
                size_category = get_size_category(median_size, median_size)
                repetition_category = get_repetition_category(median_repetition, median_repetition)

            # Create the directories if they don't exist
            format_dir = os.path.join(output_directory, file_format)
            size_repetition_dir = os.path.join(format_dir, f"{size_category}-{repetition_category}")
            subdirectory = random.randint(1, num_subdirectories)
            final_dir = os.path.join(size_repetition_dir, str(subdirectory))

            os.makedirs(final_dir, exist_ok=True)
            # print(f"Moving {file} to {final_dir}")

            # copy the file to the final directory
            shutil.copyfile(file_path, os.path.join(final_dir, file))
    print(f'Processing files in {input_directory_format} completed.')
print("Organizing files completed.")
