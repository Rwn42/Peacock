import sys
from lexer import *
from compiler import *

def main():
    source_file = sys.argv[1]

    f = open(source_file)
    lexer = Lexer(f.read())
    f.close()

    # token = lexer.next()
    # while token.kind != TokenKind.EOF:
    #     print(token)
    #     counter += 1
    #     token = lexer.next()

    c = Compiler(lexer)
    print(c.compile_until(until=[TokenKind.EOF]))





if __name__ == "__main__":
    main()