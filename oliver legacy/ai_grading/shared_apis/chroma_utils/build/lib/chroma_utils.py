# from langchain.text_splitter import CharacterTextSplitter
# from langchain.document_loaders import PyPDFLoader
from textextract_api import *


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


def add_to_chroma(text, page_title, collection):
    splitScript = split_string_into_chunks(text, 200)
    ids = generate_indexed_strings(page_title, len(splitScript))
    collection.add(documents=splitScript, ids=ids)


def ingest_pdf(pdf, print_output=False):
    # pass
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
    if print_output == True:
        print("Ingesting: " + pdf + "\n")
    text_content = ocr_pdf(pdf, save_to_file=True)
    # print(text_content)
    return text_content


def ingest_pdfs(dir, print_output=False):
    # pass
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
    text_content = ''
    for pdf in os.listdir(dir):
        if not pdf.endswith('.pdf'):
            continue
        if print_output == True:
            print("Ingesting: " + pdf + "\n")
        text_content = text_content + ocr_pdf(pdf, save_to_file=True)
        # print(text_content)
    return text_content


"""
    Queries the chroma DB and gets the top N results, returned as a list of strings
"""


def get_top_N_from_chroma(collection, query, N):
    try:
        chroma_results = collection.query(query_texts=[query], n_results=N)['documents'][0]
        return chroma_results
    except:
        print("Something went wrong")
        return
