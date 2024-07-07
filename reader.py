import os
import sys


# Function to read hosts from a file
def read_hosts(file_path):
    if not os.path.exists(file_path):
        print(f'Error: The file {file_path} does not exist.')
        sys.exit(1)  # Exit the program with an error code
    try:
        with open(file_path, 'r') as file:
            hosts = file.read().splitlines()  # Read lines and strip newline characters
        if not hosts:
            print(f'Error: The file {file_path} is empty.')
            sys.exit(1)  # Exit the program with an error code
        return hosts
    except Exception as e:
        print(f'Error reading file {file_path}: {e}')
        sys.exit(1)  # Exit the program with an error code
