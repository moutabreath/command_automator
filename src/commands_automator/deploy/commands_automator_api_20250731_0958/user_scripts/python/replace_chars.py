
import sys


def replace(text, source_to_replace, replace_to):
     text = text.replace(source_to_replace, replace_to)


def replace_and_remove_parenthesis(text):
    old_text = text
    text = replace("[", "{")
    text = replace("]", "}")
    old_text = replace("{","[")
    old_text = replace("]","}")
    x = run_remove_parenthesis(text)
    print(f'{old_text}\n')
    print(f'{text}\n')
    print(f'{x}\n')


def run_remove_parenthesis(text):
    x = text.replace("{", "")
    x = x.replace("}", "")
    x = x.replace("[", "")
    x = x.replace("]", "")

def run_replace_string():
    if len(sys.argv) <= 3:
        print("Usage: python <text>  <original char> <replace with> <original char> <replace with> ...")
        sys.exit(1)
    old_text = sys.argv[1]
    text = sys.argv[1]
  

    for i in range(2, len(sys.argv) - 1, 2):
        source_to_replace = sys.argv[i]
        replace_to = sys.argv[i + 1]        
        text = text.replace(source_to_replace, replace_to)
    print(old_text)
    print(text)

run_replace_string()
