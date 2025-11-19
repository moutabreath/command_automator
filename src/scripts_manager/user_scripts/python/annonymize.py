import sys

def replace_after_argument(input_string, argument):
    if argument in input_string:
        index = input_string.index(argument) + len(argument)
        return input_string[:index] + " dummy" + input_string[index:]
    else:
        return input_string


def write_annonymized_string_to_file(file_name, new_string):
    try:
        with open('temp.txt', 'w') as file:
            file.write(new_string)
        
    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""
    
def get_annonymized_string(file_name, argument):
    try:
        new_string = ""
        with open(file_name, 'r') as file:
          for line_number, line in enumerate(file, start=1):
              new_line = replace_after_argument(line, argument)
              new_string += new_line
        return new_string
    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def run_annoymize():
    if len(sys.argv) != 3:
        print("Usage: python script.py <file_name> <argument>")
        sys.exit(1)

    file_name = sys.argv[1]
    argument = sys.argv[2]

    new_string = get_annonymized_string(file_name, argument)
        
    write_annonymized_string_to_file(file_name, new_string)


if __name__ == '__main__':
    run_annoymize()