from extract_api import *
from evaluate_api import *
import os
import re
prompt_path = "prompts"
images_out = "images"
results_path = "results_openai"

with open("rubric.txt",'r',encoding='utf-8',errors='ignore') as reader:
  rubric_lines = reader.readlines()
  
# Filter out lines that start with '#' or are blank
filtered_lines = [line for line in rubric_lines if line.strip() and not line.strip().startswith('#')]
# Step 2: Combine every N lines into a single string
N = 3
combined_lines = [' '.join(filtered_lines[i:i+N]) for i in range(0, len(filtered_lines), 3)]
#combined_lines = filtered_lines

preamble = "You are a helpful teaching assistant reading student reports and helping the students to understand whether their reports meet certain standards. You are considering up to three standards at a time, but you must consider each one individually even if you are provided multiple to consider. In your reponse, make sure you finish answering about one thing before moving on to the next, but still make sure you address everything you are asked. You must never infer that because a report meets some other standard, it must therefore also meet the one under current consideration. The current set of standards you are considering is: "

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


evaluator_evals = ImageToTextEvaluator(images_out, prompts, results_path,endpoint=openAI_image_text_endpoint)
evaluator_evals.run_evaluation()
