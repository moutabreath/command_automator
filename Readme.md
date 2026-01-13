This software is used for two things:
1. A general purpose script runner. This is used to run various scripts.
2. An LLM Tab that can mimic a client for LLM. It acts as an agent for Gemini and sends requests to it, just like you would, for exapmle, gemini, or chatGPT.
   With this, you can also create a tailored resume and cover letter specific to a given job description.
3. Search jobs from the internet.
4. Track applied/referred jobs.

Script Manager:

It supports:

    - cmd   
    - python    
    - shell
    
To Add a new one:

Put the script under matching folder under
'user_scripts' folder.

Add its description under
config/scripts_config.json

To extend the main GUI:
run uv sync

To make an exe out of it:

 -  publish.cmd
The exe will be located at C:\Users\<user-name>\AppData\Roaming\commands_automator\

LLM:

Prefconfigure LLM usage:

    1. Open the file set_google_api_key.cmd in notepad
    2. Replace 'your_api_key_here' with your google_Api_key
    3. Click on it

Usage:

1. To use it like any other LLM client (AI), write you text in the query text field, and hit the arrow button (or hit ctrl+enter).

2. For automatic resume and cover letter creation create or replace the files in the following paths: 
 - the resume file: C:\Users\<user-name>\AppData\Roaming\commands_automator\mcp_servers\resume\resources\Tal_Druckmann.txt
 - the job description: C:\Users\<user-name>\AppData\Roaming\commands_automator\mcp_servers\resume\resources\additional_files\job_description.txt
 - choose an output folder for the resume and cover letter.
Ask the chat in a natural language to modify your resume according to the job descripton
For example, type "help me rewrite my resume according to job description".

3. For job search, edit:
C:\Users\<user-name>\AppData\Roaming\commands_automator\mcp_servers\resume\job_search\config\job_keywords.json
to add your desired job keywords.
Then, ask the chat in a natural language to find jobs from the internet.
for example "help me find jobs from the internet"

4. For applied jobs/ referred jobs, you must install MongoDb: https://www.mongodb.com/products/platform/atlas-database
Login: Enter your own email. It can be a fake email as well. No passwords needed, yet. Everything is saved locally, and thus no one else has access to the details you put in.