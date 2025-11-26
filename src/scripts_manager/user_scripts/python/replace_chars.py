
import sys


def replace(text, source_to_replace, replace_to):
     return text.replace(source_to_replace, replace_to)


def replace_and_remove_parenthesis(text):
    old_text = text
    text = replace(text, "[", "{")
    text = replace(text, "]", "}")
    x = run_remove_parenthesis(text)
    print(f'{old_text}\n')
    print(f'{text}\n')
    print(f'{x}\n')

def run_remove_parenthesis(text: str):
    return text.translate(str.maketrans('', '', '{}[]'))

def run_replace_string():
    if len(sys.argv) <= 3:
        print("Usage: python <text>  <original char> <replace with> <original char> <replace with> ...")
        return
    old_text = sys.argv[1]
    text = sys.argv[1]
  

    for i in range(2, len(sys.argv) - 1, 2):
        source_to_replace = sys.argv[i]
        replace_to = sys.argv[i + 1]        
        text = text.replace(source_to_replace, replace_to)
    print(old_text)
    print(text)

if __name__ == "__main__":
    run_replace_string()