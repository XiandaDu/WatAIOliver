from evaluate_api import *
import os

prompt = "Convert all text in the image into valid Markdown. Ensure that you are respecting formatting, especially that of lists and tables"

# List and sort image files by their numeric part
image_files = [f for f in os.listdir("sub_images") if f.endswith(".jpeg")]
image_files.sort(key=lambda x: int(os.path.splitext(x)[0]))

response = ""
for img in image_files:
    response = response + nebula_api_image_text_endpoint(os.path.join("sub_images", img), prompt)['response'] + "\n"
    print(response)

with open("OCR_text.txt", 'w') as writer:
    writer.write(response)
