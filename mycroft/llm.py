from cognitive_stack import CognitiveStack
import wikipedia
import re
import chroma_utils
import chromadb


class LLM:
    def __init__(self):
        self.cog_stack = CognitiveStack() #all LLMs get one for free, even if it isn't used
        self.working_memory_client = chromadb.Client()
        self.working_memory_collection = self.working_memory_client.create_collection("working_memory")
    
    #input/output query
    def query(self,input_string):
        raise NotImplementedError("Subclasses must implement this method")
    
    #input/output query with cognitive stack background - this relies on the generic "query" function, so it goes here
    def query_with_cog_stack(self,input_string,N=1,new_tokens_max = 1024,print_intermediate=False):
        
        stack_output =  self.cog_stack.query_stack(input_string,N)
        if(print_intermediate == True):
            print(stack_output)
        
        stack_help = self.query("Here is some background information. Some of it may be irrelevant. Read the background information, and summarize the information that is relevant to the query. Ignore the rest. If there is nothing relevant in the background information, you must output the string `none present`. Do not make up information. The query is: " + input_string + "\n and the background information is: " + stack_output)
            
        stack_useful = "Here is some extra information that may help you: " + stack_help + "\nIf this information is not useful to the query, say so. Do not make up information. The query is: "
        if 'none present' in stack_help.lower():
            stack_useful = "There is no information in the background information provided about that query. You should tell the user without generating any other output."
        
        return self.query(stack_useful + "\n" + input_string,new_tokens_max)
        
        
    def add_cognitive_stack(self,stack_id,collection):
        self.cog_stack.add_db(stack_id,collection)
    
    