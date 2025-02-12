This is used to run various scripts. 
It supports:
    - cmd
    - python
    - shell
To Add a new one:
put the script under matching folder under 'actionables' folder.
add its description under config/scripts_config.json

To extend the main GUI:
run poetry install

To make an exe out of it:
pyinstaller command_automator.pyw -i resources/CommandsAutomator.ico -F
icon taken from 
<a href="https://www.flaticon.com/free-icons/dragon" title="dragon icons">Dragon icons created by Freepik - Flaticon</a>
put the exe file at the root of the project.