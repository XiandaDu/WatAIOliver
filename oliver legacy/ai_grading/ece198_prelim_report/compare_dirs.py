import os
import re

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

def compare_files(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        answer1 = extract_answer(f1.read())
        answer2 = extract_answer(f2.read())
        
        # Check for discrepancies
        if answer1 != answer2:
            return True
    return False

def compare_directories(dir1, dir2):
    discrepancies = []

    # List all text files in both directories
    files1 = sorted([f for f in os.listdir(dir1) if f.endswith('.txt')])
    files2 = sorted([f for f in os.listdir(dir2) if f.endswith('.txt')])

    # Ensure the directories contain the same files
    if files1 != files2:
        print("The directories do not contain the same files.")
        return

    # Compare corresponding files
    for filename in files1:
        file1_path = os.path.join(dir1, filename)
        file2_path = os.path.join(dir2, filename)
        
        if compare_files(file1_path, file2_path):
            discrepancies.append(filename)
    
    if discrepancies:
        print("Discrepancies found in the following files:")
        for file in discrepancies:
            print(file)
    else:
        print("No discrepancies found.")

if __name__ == "__main__":
    dir1 = input("Enter the path to the first directory: ")
    dir2 = input("Enter the path to the second directory: ")

    compare_directories(dir1, dir2)
