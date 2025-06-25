#You need to import the class for some reason...
from cognitive_stack import CognitiveStack
#even though this already is imported in cognitive_stack, you still need to import it here, otherwise you'd need to call it
#cognitive_stack.chromadb
import chromadb
import chroma_utils
from wiki_qa import wiki_QA
from openAI_llm import openAI_llm
from collections import deque
import shutil
import os
import random
import string


def make_project(project_name):
    # Define the base directory where the "projects" folder is located
    base_directory = "projects"

    # Create a path for the project folder
    project_directory = os.path.join(base_directory, project_name)

    # Create directories if they don't exist
    directories_to_create = [
        os.path.join(project_directory, "rawpdf"),
        os.path.join(project_directory, "ingested"),
        os.path.join(project_directory, "chroma_db"),
    ]

    for directory in directories_to_create:
        os.makedirs(directory, exist_ok=True)

    print(f"Project '{project_name}' directories created.")

def load_dbs(project_name):
    chroma_client = chromadb.PersistentClient(path=os.path.join("projects",project_name))
    collection_background = chroma_client.get_or_create_collection(name="background")
    collection_ideas = chroma_client.get_or_create_collection(name="ideas")
    
    return [chroma_client, collection_background, collection_ideas]

def project_exists(project_name):
    # Define the base directory where the "projects" folder is located
    base_directory = "projects"

    # Check if the project directory exists
    project_directory = os.path.join(base_directory, project_name)
    return os.path.exists(project_directory)

def move_rawpdf_to_ingested(project_name):
    # Define the base directory where the "projects" folder is located
    base_directory = "projects"

    # Create paths for the source (rawpdf) and destination (ingested) directories
    source_directory = os.path.join(base_directory, project_name, "rawpdf")
    destination_directory = os.path.join(base_directory, project_name, "ingested")

    # Get a list of all files in the source directory
    files_to_move = os.listdir(source_directory)

    # Move each file from source to destination
    for file_name in files_to_move:
        source_file_path = os.path.join(source_directory, file_name)
        destination_file_path = os.path.join(destination_directory, file_name)
        shutil.move(source_file_path, destination_file_path)
        print(f"Moved '{file_name}' to 'ingested' directory.")


def ingest(project_name, collection):
    #ingest the pdfs first
    chroma_utils.ingest_pdfs(os.path.join(os.path.join("projects",project_name),"rawpdf"),collection)
    #move them
    move_rawpdf_to_ingested(project_name)

#Chroma requires a title, but for ideas it doesn't make much sense to create a title, so this will randomly generate one
def generate_random_string(length):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters + string.digits  # You can include other characters if needed

    # Generate a random string of the specified length
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string

    
def record_idea(idea_text,collection,idea_title=None):
    if idea_title is None:
        idea_title = generate_random_string(23)
    chroma_utils.add_to_chroma(idea_text,idea_title,collection)

query_prompt = "You are a helpful assistant working with the user on the user's project. You have access to both background information and some of the user's previous ideas. Your goal is to help with the query as best you can. Be sure to answer truthfully, but you may feel free to give your own ideas as long as it is clear that you are doing so. If you can answer using the background information or the previous ideas, you should prioritize that. If the background information or previous ideas does not have any relevant information, you must say so. You should also prompt the user with a question every now and then, to keep the conversation going or probe more deeply. Asking questions is very important. But don't just ask them what they think. Rather, add to the conversation, put in your own point of view. You are collaborating with the user, you aren't just regurgitating information."

summary_prompt = "The following is a brief conversation snippet between a helpful assistant and a user. Summarize the key points that were discussed so far."

#You need to add the key here
api_key = ''

llm = openAI_llm(model="gpt-3.5-turbo",system_prompt = query_prompt,API_Key = api_key)
#llm = openAI_llm(model="gpt-4",system_prompt = query_prompt,API_Key = api_key)
project = input("What project are we working on today? ")
if project_exists(project) == False:
    print("Hm, that project doesn't exist. Should I create it? Yes/no: ")
    response = input(">> ")
    if response == "no":
        exit()
    print("Sounds good! Let's get to it.")
    make_project(project)

dbs = load_dbs(project)
client = dbs[0]
background = dbs[1]
ideas = dbs[2]

query = input(">> ")
context = deque(maxlen=15)
context.append(query)

while(query != "EXIT"):
    
    if query == "INGEST":
        print("Ingesting new information...")
        ingest(project,background)
        print("done")
    elif query == "IDEA":
        print("Ready for your idea: ")
        new_idea = input(">> ")
        record_idea(new_idea,ideas)
    elif query == "CLEAR":
        context.clear()
    else: #not a system command, so a query
        print("Summarizing!")
        llm.system_prompt = summary_prompt
        summary = llm.query(" ".join(context))
        print("Done!")
        llm.system_prompt = query_prompt
        if query.startswith("MY_IDEAS:"):
            idea_to_use = " ".join(chroma_utils.get_top_N_from_chroma(ideas,summary+query,5))
            llm_query = "Some of our previous ideas that may be relevant are: " + idea_to_use + "\n and the user query is: " + query
            print(llm.query(llm_query))
        elif query.startswith("BACKGROUND"):
            bg = " ".join(chroma_utils.get_top_N_from_chroma(background, summary+query, 5))
            llm_query = "The background that may be relevant is: " + bg + "\n and for this one, let's use only the background and not any previous ideas. The user query is: " + query
            print(llm.query(llm_query))
        else:
            bg = " ".join(chroma_utils.get_top_N_from_chroma(background, summary + query, 5))
            idea_to_use = " ".join(chroma_utils.get_top_N_from_chroma(ideas,summary+query,5))
            llm_query = "The background that may be relevant is: " + bg + "\n And some of our previous ideas that may be relevant are: " + idea_to_use + "\n and the user query is: " + query
            print(llm.query(llm_query))
                
    query = input(">> ")
    