import sys


def convert(path):
    x = path.replace("\\", "/")
    print(x)
    return x

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_win_2_unix.py <windows_path>")
        sys.exit(1)
    path = " ".join(sys.argv[1:])
    convert(path)