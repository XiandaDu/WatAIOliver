import os
import re
from collections import defaultdict

def extract_answer(text):
    # Convert to lower case and search for the answer
    text = text.lower()
    match = re.search(r'<answer>(yes|no)</answer>', text)
    if match:
        return match.group(1)
    elif 'yes' in text:
        return 'yes'
    elif 'no' in text:
        return 'no'
    return None

def compare_files_across_directories(file_paths):
    answers = set()
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            answer = extract_answer(file.read())
            answers.add(answer)
    
    # If the set contains more than one unique answer, there is a discrepancy
    return len(answers) == 1

def compare_directories_across_list(dir_list):
    file_groups = defaultdict(list)
    
    # Collect file paths grouped by filenames
    for directory in dir_list:
        files = [f for f in os.listdir(directory) if f.endswith('.txt')]
        for filename in files:
            file_groups[filename].append(os.path.join(directory, filename))
    
    consistent_files = []
    inconsistent_files = []

    # Check consistency across all directories for each file
    for filename, file_paths in file_groups.items():
        if compare_files_across_directories(file_paths):
            consistent_files.append(filename)
        else:
            inconsistent_files.append(filename)
    
    if consistent_files:
        print("Files with consistent answers across all directories:")
        for file in consistent_files:
            print(file)
    else:
        print("No consistent files found.")
    
    if inconsistent_files:
        print("\nFiles with discrepancies across directories:")
        for file in inconsistent_files:
            print(file)

if __name__ == "__main__":
    dir_list = input("Enter a space-separated list of directory paths: ").split()
    
    compare_directories_across_list(dir_list)
