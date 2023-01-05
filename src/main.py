import sys
from lexer import *
from compiler import *

def main():
    source_file = sys.argv[1]

    f = open(source_file)
    lexer = Lexer(f.read())
    f.close()

    token = lexer.next()
    while token.kind != TokenKind.EOF:
        print(token)
        token = lexer.next()
        
    # c = Compiler(lexer, "env")
    # program = c.compile_until(until=[TokenKind.EOF], whitelist=None)
    # c.save(program)





if __name__ == "__main__":
    main()