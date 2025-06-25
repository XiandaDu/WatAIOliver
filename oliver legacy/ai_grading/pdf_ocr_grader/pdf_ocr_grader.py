from textextract_api import *
from evaluate_api import *

ocr_text = ocr_pdf("ece252_syllabus.pdf",save_to_file=True)
prompt = "You are providing helpful feedback to students. You need to determine whether this report is about a goat or not. If so, tell the student. Otherwise, inform the student that there must have been an error. The student report is: \n"

#print(text_text_eval(ocr_text,prompt))
