import sys

# Converts Shift-JIS bytes to a UTF-8 string
#
# Example:
# > python3 tools/sjis2utf.py "93F18F64"
# > '二重'

def main():
    hexstring = sys.argv[1]
    raw_bytes = bytes.fromhex(hexstring)
    string = raw_bytes.decode("sjis")
    print(repr(string))

if __name__ == "__main__":
    main()
