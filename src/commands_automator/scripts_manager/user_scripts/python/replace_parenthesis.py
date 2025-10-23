
import sys


def replace_and_remove_parenthesis(text):    
    old_text = text
    x = text
    text = text.replace("[", "{")
    text = text.replace("]", "}")
    old_text = old_text.replace("{","[")
    old_text = old_text.replace("}","]")
    x = run_remove_parenthesis(text)
    print(old_text)
    print(text)
    print(x)


def run_remove_parenthesis(text):
    x = text.replace("{", "")
    x = x.replace("}", "")
    x = x.replace("[", "")
    x = x.replace("]", "")
    return x

def run_replace_string():
    if len(sys.argv) <= 1:
        print("Usage: python <text> ")
        sys.exit(1)
    replace_and_remove_parenthesis(sys.argv[1])

if __name__ == "__main__":
    run_replace_string()