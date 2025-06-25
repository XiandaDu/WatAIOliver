import chromadb
from chromadb.config import Settings  # add chromadb.config
#from langchain.text_splitter import CharacterTextSplitter
#from langchain.document_loaders import PyPDFLoader
import os

# Split a long string into chunks
def split_string_into_chunks(text, max_words_per_chunk):
    words = text.split()
    chunks = [words[i:i + max_words_per_chunk] for i in range(0, len(words), max_words_per_chunk)]
    return [' '.join(chunk) for chunk in chunks]

def generate_indexed_strings(name, num_strings):
    indexed_strings = [f"{name}{i}" for i in range(num_strings)]
    return indexed_strings

"""
    Adds text with page_title to the chroma DB
"""
def add_to_chroma(text,page_title,collection):
    splitScript = split_string_into_chunks(text,200)
    ids = generate_indexed_strings(page_title,len(splitScript))
    collection.add(documents=splitScript,ids=ids)

def ingest_pdfs(rawdir,collection,print_output = False):
    pass
    """for pdf in os.listdir(rawdir):
        if print_output == True:
            print("Ingesting: " + pdf + "\n")
        loader = PyPDFLoader(os.path.join(rawdir,pdf))
        txt_docs = loader.load_and_split()
        ids = []
        ind=0
        for doc in txt_docs:
            shard_id = doc.metadata["source"].split("\\")[-1] + str(doc.metadata['page'])+"_"
            if shard_id in ids:
                shard_id = shard_id + "_" + str(ind)
                ind = ind + 1
            ids.append(shard_id)
            content = doc.page_content
            add_to_chroma(content,shard_id,collection)

            """

"""
    Queries the chroma DB and gets the top N results, returned as a list of strings
"""
def get_top_N_from_chroma(collection, query, N):
    try:
        chroma_results = collection.query(query_texts=[query],n_results=N)['documents'][0]
        return chroma_results    
    except:
        print("Something went wrong")
        return 

if __name__ == "__main__":
    # create ChromaDB client
    client = chromadb.Client(Settings(persist_directory="./chroma_db"))

    # create ChromaDB collection
    collection = client.create_collection("test_collection")

    # read uploaded document content
    with open("text.txt", "r", encoding="utf-8") as file:
        text_content = file.read()

    # add document ChromaDB
    print("Adding document to ChromaDB...")
    add_to_chroma(text_content, "text_document", collection)

    # define the queries list
    queries = [
        "when should I submit this?",
        "When should I complete this?",
        "What is the primary objective?",
        "What is the goal?"
    ]

    # print the results
    for query in queries:
        print(f"\nQuery: {query}")
        top_results = get_top_N_from_chroma(collection, query, 3)
        print("Top results:", top_results)
