import chromadb #pip install...
import chroma_utils

class CognitiveStack:
    def __init__(self):
        self.cog_stack = []
        self.ids = []

    def add_db(self, stack_id, new_stack):
        self.cog_stack.append(new_stack)
        self.ids.append(stack_id)

    """
        Query the cognitive stack for the top N results from each stack, and return a single string
    """
    def query_stack(self,query,N=1):
        try:
            out_string = ""
            for index,stack in enumerate(self.cog_stack):
                res = chroma_utils.get_top_N_from_chroma(stack,query,N)
                out_string = out_string + "\n" + self.ids[index] + "\n" + " ".join(res)
            return out_string
        except:
            return None

