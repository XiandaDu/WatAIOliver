from extract_api import *
from evaluate_api import *
import os
import re
prompt_path = "prompts"
images_out = "images"
results_path = "results"

with open("rubric.txt",'r',encoding='utf-8',errors='ignore') as reader:
  rubric_lines = reader.readlines()
  
# Filter out lines that start with '#' or are blank
filtered_lines = [line for line in rubric_lines if line.strip() and not line.strip().startswith('#')]
# Step 2: Combine every three lines into a single string
#combined_lines = [' '.join(filtered_lines[i:i+3]) for i in range(0, len(filtered_lines), 3)]
combined_lines = filtered_lines

preamble = "You are a helpful teaching assistant reading student reports and helping the students to understand whether their reports meet certain standards. You are considering only one standard at a time, and you must focus only on that standard. You must never infer that because a report meets some other standard, it must therefore also meet the one under current consideration. The current standard you are considering is: "

postamble = ""

for i,line in enumerate(combined_lines):
  with open(os.path.join(prompt_path,f"prompt_{i}.txt"),'w') as writer:
    writer.write(preamble + line + postamble)



def extract_number_from_filename(filename):
    # This regex extracts the number from filenames like 'prompt_0.txt'
    match = re.search(r'(\d+)', filename)
    return int(match.group()) if match else float('inf')

# List all filenames in the prompt_path directory
filenames = os.listdir(prompt_path)

# Filter and sort the filenames
sorted_filenames = sorted(
    [filename for filename in filenames if filename.endswith('.txt')],
    key=extract_number_from_filename
)

# Create the full paths for each file and add to the prompts list
prompts = [os.path.join(prompt_path, filename) for filename in sorted_filenames]


evaluator_evals = ImageToTextEvaluator(images_out, prompts, results_path,endpoint=nebula_api_image_text_endpoint)
evaluator_evals.run_evaluation()
