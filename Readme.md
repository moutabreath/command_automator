This is used to run various scripts. 


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

pyinstaller command_automator.pyw -i resources/Commands_Automator.ico -F

Put the exe file at the root of the
project.
