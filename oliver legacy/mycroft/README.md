# Mycroft



## Getting started

You need to install the following to make this work, via pip install:

- wikipedia
- openai
- chroma (or chromadb, I can't remember)
- langchain

Then, put all of the files into their own directory and create a subdirectory called "projects". Mycroft will take care of the rest.

## Creating a new Mycroft project or loading an existing one

When you run Mycroft using ```python mycroft.py``` (often "python3" instead if you're on Linux), you will be prompted to enter a project name. If this is the name of an existing project, it will load the relevant contextual information. Otherwise, it will prompt you to create the project. If you say "yes" it will create the necessary subdirectories. If you say "no" it will exit the program.

## Using Mycroft

When you make a new project, navigate to the "projects/your_project_name" folder. You will see a folder called "rawpdf". This is where you put the pdfs you want Mycroft to ingest. With Mycroft running, put pdfs into that directory and type the command "INGEST" followed by the enter key into Mycroft's prompt. It will ingest the PDFs into the project's vector database. This step can be repeated if you want to add more pdfs, but there is currently no way to delete the pdfs from the database. Depending on your computer and the size of the pdfs this may take a while.

You may query Mycroft with a question or thought, and Mycroft will search the database for relevant context then query the LLM. Mycroft has a limited memory of about 8 - 15 interactions, and I've found that this is actually too much. It tends to get confused with too much memory.

If you want to add a custom idea, which is just a small thought that you want Mycroft to consider in its responses, type the command "IDEA" followed by enter. You will then be prompted to enter your idea, and Mycroft will try to incorporate that idea into future interactions.

If you are finding that Mycroft is talking about past and irrelevant things, type CLEAR then hit enter, which clears the memory but not the databases or ideas.
