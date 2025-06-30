from extract_api import *
from evaluate_api import *
import pytesseract

def pdf_to_text_faithful(input_directory,project_name):
  project_directory = project_name
  output_directory = os.path.join(project_directory,"out")
  results_path = os.path.join(output_directory,"results")
  
  #Turn every page into an image
  project = Project(project_name,input_directory,output_directory)
  pages_directory = project.add_step(PagePdfSplitter,pages_per_split=1)
  project.add_step(Converger,'converge')
  project.add_step(PDFToImageConverter,'flat')
  project.add_step(Converger,'converge')
  
  
  #Separate out the components
  split_images_out = project.add_step(ImageSplitter)
  images_out = project.add_step(Converger,'converge')
  project.run()
  
  #Now it's time to extract and reconstruct the text
  prompt = """
      The image is from an engineering report. Extract all text from the image and output it as valid markdown. Pay special attention to tables. If there are tables in the image, ensure that the output includes proper Markdown tables. Respect headings and other formatting."
  """
  
  with open("promptASFSDFAFD.txt",'w') as writer:
    writer.write(prompt)
  
  
  documents_path = images_out
  prompts = ["promptASFSDFAFD.txt"]
  output_path = f"{output_directory}/results"
  
  evaluator_evals = ImageToTextEvaluator(documents_path,prompts,output_path)
  evaluator_evals.run_evaluation()