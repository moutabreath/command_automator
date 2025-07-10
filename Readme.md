This software is used for two things:
1. A general purpose script runner. This is used to run various scripts.
2. An LLM Tab that can mimic a client for LLM. It acts as an agent for Gemini and sends requests to it, just like you would, for exapmle, windows CoPilot.
   With this, you can also create a tailored resume and cover letter specific to a given job description.

Script Manager:

It supports:

    - cmd   
    - python    
    - shell
    
To Add a new one:

Put the script under matching folder under
'user_sctipts' folder.

Add its description under
config/scripts_config.json

To extend the main GUI:
run poetry install

To make an exe out of it:

 -  pyinstaller command_automator_api.pyw -i ui/resources/Commands_Automator.ico -F --add-data "ui;ui"

Put the exe file at the root of the
project.

LLM:

Prefconfigure LLM usage:
    set GOOGLE_API_KEY=your_api_key_here


To use it like copilot, write you text in the query text field, and hit the arrow button.
For automatic resume and cover letter creation, replace:
 - the resume file : llm\resources\resume\Tal_Druckmann.txt
 - the job description: llm\resources\resume\addtional_files\job_description.txt
 - choose an output folder for the resume and cover letter.
Ask the chat in a natural language to modify your resume according to the job descripton