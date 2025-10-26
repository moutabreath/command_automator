
import sys


def run_replace_string():
    if len(sys.argv) < 2:
        print("Usage: python remove_parenthesis.py <text>")
        sys.exit(1)    
    text = sys.argv[1]
    x = text.replace("{", "")
    x = x.replace("}", "")
    x = x.replace("[", "")
    x = x.replace("]", "")
    x = x.replace("(", "")
    x = x.replace(")", "")   
    print(x)



run_replace_string()
