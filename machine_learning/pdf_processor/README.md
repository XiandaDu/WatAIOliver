# Installation guide

cd pdf_processor
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" 
brew install python@3.10
python3.10 -m venv venv 
source venv/bin/activate 
pip install --upgrade pip
pip install -r requirements.txt
python main.py

http://0.0.0.0:8001/docs#/default/convert_pdf_upload_convert_post
drop file, click execute
see output at pdf_processor/output