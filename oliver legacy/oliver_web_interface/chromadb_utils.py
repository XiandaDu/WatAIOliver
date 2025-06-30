import chromadb
from transformers import AutoTokenizer, AutoModel

client = chromadb.PersistentClient(path="data")
model_name = "./all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)


def split_string_into_overlapping_chunks(text, max_words_per_chunk, overlap):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words_per_chunk - overlap):
        chunk = ' '.join(words[i:i + max_words_per_chunk])
        chunks.append(chunk)
        if i + max_words_per_chunk >= len(words):
            break
    return chunks


def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).detach().numpy().tolist()[0]
    return embeddings

def collection_new(collection_name):
    collection = collection_exists(collection_name)
    if collection is not None:
        client.delete_collection(collection_name)
    return client.create_collection(collection_name, metadata={"hnsw:space": "cosine"})

def collection_remove(collection_name):
    collection = collection_exists(collection_name)
    if collection is not None:
        client.delete_collection(collection_name)

def collection_exists(name):
    try:
        collection = client.get_collection(name=name)
        return collection
    except Exception as e:
        print(f"Error checking collection existence: {e}")
        return None

def generate_indexed_strings(name, num_strings):
    indexed_strings = [f"{name}_{i}" for i in range(num_strings)]
    return indexed_strings


def add_to_chroma(text, page_title, collection):
    split_script = split_string_into_overlapping_chunks(text, 200, 50)
    for i in range(len(split_script)):
        print(i, split_script[i])

    if not split_script:
        raise ValueError("The document was split into an empty list of chunks.")

    ids = generate_indexed_strings(page_title, len(split_script))

    if not ids or len(ids) != len(split_script):
        raise ValueError(
            f"Generated IDs count {len(ids)} doesn't match the split "
            f"document chunks count {len(split_script)}.")

    # 准备元数据
    total_chunks = len(split_script)
    metadatas = []
    for idx in range(total_chunks):
        metadata = {
            'filename': page_title,
            'chunk_index': idx,
            'total_chunks': total_chunks
        }
        metadatas.append(metadata)

    text_embeddings = [get_embedding(text) for text in split_script]

    collection.add(
        documents=split_script,
        ids=ids,
        embeddings=text_embeddings,
        metadatas=metadatas
    )

def query_sentence_with_threshold(collection, sentence, N, threshold):
    # 生成问题的向量
    query_embedding = get_embedding(sentence)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=N,
        include=['documents', 'metadatas', 'distances']
    )

    relevant_docs = []
    if results['ids']:
        for i, doc_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            print(
                f"Filename: {metadata.get('filename')}, Content: {results['documents'][0][i]}, Similarity: {distance:.4f}")
            # if distance <= threshold:
            # relevant_docs.append(results['documents'][0][i])
            relevant_docs.append(results['documents'][0][i])
        if not relevant_docs:
            print(f"No documents found within the similarity threshold of {threshold}.")
    else:
        print(f"No results found for query: '{sentence}'")
    return relevant_docs

if __name__ == "__main__":
    f = ['Tigers.txt', 'Lions.txt']
    collection_name = f"collection_t"
    collection = collection_exists(collection_name)
    # if collection is not None:
    #     client.delete_collection(collection_name)
    # collection = client.create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    # for i in f:
    #     with open(i, 'r') as f:
    #         c = f.read()
    #     add_to_chroma(c, i, collection)

    # get_from_chroma('tell me about lion', collection)