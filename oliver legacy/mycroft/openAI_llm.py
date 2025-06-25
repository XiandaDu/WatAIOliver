#import llm
from llm import LLM
import openai
import os
"""
    A class specifically for openAI models. This can run any GPT3.5* and GPT4 chat completion models
"""
class openAI_llm(LLM):
    def __init__(self,model,API_Key,system_prompt=""):
        super().__init__() #get the cognitive stack going
        
        os.environ["OPENAI_API_KEY"] = API_Key
        openai.api_key = API_Key
        
        self.model = model
        
        self.system_prompt = system_prompt
    
    #input/output query
    def query(self,input_string,new_tokens_max=1024):
        response = openai.ChatCompletion.create(model=self.model,messages=[{"role":"system","content":self.system_prompt},{"role":"user","content":input_string}],temperature=0.1,max_tokens=new_tokens_max)
        model_out = response.choices[0].message.content
        return model_out
        
    