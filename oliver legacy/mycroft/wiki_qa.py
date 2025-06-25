from cognitive_stack import CognitiveStack
import wikipedia
import re
import chroma_utils
import chromadb
import llm
import traceback
"""
    Extracts bulleted list items from the given text.

    Args:
        text (str): The input text containing a bulleted list.

    Returns:
        list: A list of sanitized bulleted list items without the bullet points
              and leading spaces.
"""
def get_search_terms(text):
    pattern = r'^[-•] (.*)?$'  # Assumes bullet points start with a hyphen and a space
    bulleted_list = re.findall(pattern, text, re.MULTILINE)
    return bulleted_list

#Requires an LLM of some sort, pre-initialized
class wiki_QA:
    
    def __init__(self,llm):
        self.llm = llm
        
    #input/output query with cognitive stack background - this relies on the generic "query" function, so it goes here
    def query_with_cog_stack_and_wiki(self,input_string,N=1,new_tokens_max = 1024,print_intermediate=False):
    
        stack_output =  self.llm.cog_stack.query_stack(input_string,N)
        if(print_intermediate == True):
            print(stack_output)
        
        stack_help = self.llm.query("Here is some background information. Read the background information, and summarize only the information that is relevant to the query. Ignore the rest. If there is nothing in the background information that is relevant to the query, you must output the string `none present`. Do not make up information. The query is: " + input_string + "\n and the background information is: " + stack_output)
        
        if 'none present' in stack_help.lower():
            try:
                print("Hm, my background information doesn't have anything relevant about that. I'll look it up for you. Give me a minute please....")
                get_search_prompt = "You have been given a query but you don't seem to have any information about it. Given the following query, generate a list of three Wikipedia search terms that the user can use to learn more on their own. Return your list as a bulleted list without any other explanation. You may use hyphens and letters, but no other characters. The original query is: " + input_string
                search_output = self.llm.query(get_search_prompt,new_tokens_max)
                terms = get_search_terms(search_output)
                
                if(print_intermediate == True):
                    print("Output: " + search_output + "\nTerms: ")
                    print(terms)
                
                pages = []
                for term in terms:
                    pages = list(set(pages + wikipedia.search(terms[0])))
                    
                for page in pages:
                    try:
                        pg = wikipedia.page(page).content
                        print("I think I have something here. Just a second")
                        chroma_utils.add_to_chroma(pg,page,self.llm.working_memory_collection)
                    except:
                        traceback.print_exc()
                        print("Ope, that didn't work, let's see what else I can do.")
                
                working_output = " ".join(chroma_utils.get_top_N_from_chroma(self.llm.working_memory_collection,input_string,N))
                stack_help = self.llm.query("Here is some background information. Some of it may be irrelevant. Read the background information, and summarize the information that is relevant to the query. Ignore the rest. If there is nothing relevant in the background information, you must output the string `none present`. Do not make up information. The query is: " + input_string + "\n and the background information is: " + working_output)
            except:
                print("Uh oh! It looks like my information stores just can't figure it out. Sorry!")
                stack_help = "There is no information in the background information provided about that query. You should tell the user without generating any other output."
        if(print_intermediate == True):
            print(stack_help)
        
        stack_useful = "Here is some extra information that may help you: " + stack_help + "\nIf this information is not useful to the query, say so. Do not make up information. The query is: "
        
        return self.llm.query(stack_useful + "\n" + input_string,new_tokens_max)