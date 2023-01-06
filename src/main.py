import sys
from lexer import *
#from compiler import *

def main():
    source_file = sys.argv[1]

    f = open(source_file)
    lexer = Lexer(f.read(), source_file)
    f.close()
    
    t = lexer.next()
    while t.kind != TokenKind.EOF:
        print(t)
        t = lexer.next()
    # c = Compiler(lexer, "env")
    # c.compile_file()
    # c.save()





if __name__ == "__main__":
    main()