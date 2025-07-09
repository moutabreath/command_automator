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
'actionables' folder.

Add its description under
config/scripts_config.json

To extend the main GUI:
run poetry install

To make an exe out of it:

 -  pyinstaller command_automator_api.pyw -i ui/resources/Commands_Automator.ico -F


Put the exe file at the root of the
project.

LLM:

Prefconfigure LLM usage:
add your gemini api key at tabs\llm\config\chat_bot_keys.txt

To use it like copilot, write you text in the query text field, and hit the arrow button.
For automatic resume and cover letter creation, replace:
 - the resume file : llm\resources\resume\Tal_Druckmann.txt
 - the job description: llm\resources\resume\job_Descs.txt
 - choose an output folder for the resume and cover letter.
