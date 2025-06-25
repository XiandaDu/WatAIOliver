from docx import Document
import os
import sys
import torch
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans, AgglomerativeClustering
from collections import defaultdict
from transformers import BertModel, BertTokenizer
from sentence_transformers import SentenceTransformer
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
#from openai import OpenAI

from transformers import AutoTokenizer, AutoModelForCausalLM

#a function to remove stopwords from a string
def remove_stopwords(text):
    # Check if 'stopwords' dataset is downloaded, and download it if not
    if not nltk.data.find('corpora/stopwords'):
        nltk.download('stopwords')

    # Check if 'punkt' dataset is downloaded, and download it if not
    if not nltk.data.find('tokenizers/punkt'):
        nltk.download('punkt')
    try:
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Tokenize the text
        words = word_tokenize(text)

        # Remove stopwords
        words = [word for word in words if word not in stopwords.words('english')]

        # Rejoin the words into a single string
        processed_text = ' '.join(words)

        return processed_text
    except:
        return text
    
#A function to cluster a dataframe's text column using sentence transformers and agglomerative clustering
def cluster_dataframe_text_ST(data,column,num_clusters=5,print_out = False):
    # Load sentence transformer model
    #model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    # Move the model to GPU if CUDA is available
    if torch.cuda.is_available():
        model = model.to("cuda")
    # Set up an empty list to store embeddings
    embeddings = []

    problematic_documents = []  # To store the indices of problematic documents, for instance any document that doesn't correctly parse or tokenize

    # Iterate through the documents and generate ST embeddings
    for idx, text in enumerate(data[column]):
        try:
            if(print_out):
                print(f"Processing document {idx + 1}/{len(data)}")
            
            embed_text = model.encode(text,normalize_embeddings=True)
            
            embeddings.append(embed_text)
        except Exception as e:
            problematic_documents.append(idx)
            print(f"Document {idx} raised an error: {e}")

    # Filter out the problematic documents from further processing
    data_subset = data.drop(problematic_documents)

    # Perform clustering directly on the individual embeddings
    clusterer = AgglomerativeClustering(n_clusters=num_clusters, linkage='ward')

    # Fit the clusterer on the embeddings
    cluster_labels = clusterer.fit_predict(embeddings)
    # Add cluster labels to the DataFrame
    data_subset['cluster'] = cluster_labels
    if(print_out):
        print(data_subset['cluster'])  
    return data_subset    

#Clusters in batches instead of individually. Assumes that your documents won't fail though
def cluster_dataframe_text_ST_batch(data, column, num_clusters=5, print_out=False,forceDevice = False):
    # Load sentence transformer model
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')

    # Move the model to GPU if CUDA is available
    if torch.cuda.is_available() and forceDevice == False:
        model = model.to("cuda")
    else:
        mode = model.to("cpu")

    # Encode all texts at once
    embeddings = model.encode(data[column].tolist(), normalize_embeddings=True)

    # Perform clustering directly on the individual embeddings
    clusterer = AgglomerativeClustering(n_clusters=num_clusters, linkage='ward')

    # Fit the clusterer on the embeddings
    cluster_labels = clusterer.fit_predict(embeddings)

    # Add cluster labels to the DataFrame
    data['cluster'] = cluster_labels

    if print_out:
        print(data['cluster'])

    return data

# A function to save clusters to text files in a given directory
def save_clusters(original_data, cluster_data_input, output_directory, column, empty_directory=False):
    # Check if the output directory exists and handle as per the 'empty_directory' parameter
    if os.path.exists(output_directory):
        if empty_directory:
            # Remove all files in the directory
            file_list = [os.path.join(output_directory, f) for f in os.listdir(output_directory)]
            for f in file_list:
                os.remove(f)
        else:
            raise ValueError("Output directory already exists. Set 'empty_directory=True' to overwrite.")
    else:
        # Create the output directory if it doesn't exist
        os.makedirs(output_directory)

    for cluster_label in cluster_data_input['cluster'].unique():
        cluster_data_indices = cluster_data_input[cluster_data_input['cluster'] == cluster_label].index
        cluster_data = original_data.loc[cluster_data_indices, column].str.replace(",", "")
        
        # Define a filename for the cluster data
        output_filename = os.path.join(output_directory, f'cluster_{cluster_label + 1}.csv')
        
        # Save the cluster data to a CSV file
        cluster_data.to_csv(output_filename, index=False)

#Splits the input_string by extracting stuff between left string and, optionally, right string    
def extractor(input_string,left_string,right_string=""):
    candidates = input_string.split(left_string)
    
    output_strings = []
    for candidate in candidates:
        if(candidate != ""):
            if(right_string == ""):
                output_strings.append(candidate)
            else:
                output_strings.append(candidate.split(right_string)[0])
    return output_strings
    
#cleans a list of strings - strips them of leading/trailing whitespace, removes empty strings etc
def clean_strings(string_list):
    clean_list = []
    for st in string_list:
        if st != "":
            clean_list.append(st.strip())
    return clean_list
    
#This is the function you use to get a dataframe out from a list. It'save
# probably the one everyone should be using. If an output directory is supplied, it will also save the clusters to text files. To do this it saves the cleaned, but stopword-intact original data
def process_and_cluster_text(
    string_list, 
    num_clusters=5, 
    remove_stops = True,
    print_out=False, 
    forceDevice=False, 
    output_directory=None, 
    empty_directory=False
):
    # Step 1: Clean the list of strings
    cleaned_strings = clean_strings(string_list)
    
    # Step 2: Remove stopwords from each cleaned string
    if remove_stops:
        processed_strings = [remove_stopwords(text) for text in cleaned_strings]
    else:
        processed_strings = cleaned_strings
    # Step 3: Convert the list of processed strings into a DataFrame
    data = pd.DataFrame(processed_strings, columns=['text'])
    
    # Step 4: Cluster the DataFrame using the existing function
    clustered_data = cluster_dataframe_text_ST_batch(data, column='text', num_clusters=num_clusters, print_out=print_out, forceDevice=forceDevice)
    
    # If an output directory is provided, save the clusters
    if output_directory:
        # Convert the original string list to a DataFrame
        original_data = pd.DataFrame(clean_strings(string_list), columns=['text'])
        save_clusters(
            original_data=original_data, 
            cluster_data_input=clustered_data, 
            output_directory=output_directory, 
            column='text', 
            empty_directory=empty_directory
        )
    
    return clustered_data
