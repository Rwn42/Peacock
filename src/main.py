import sys
from lexer import Lexer, TokenKind, Token

def main():
    source_file = sys.argv[1]

    f = open(source_file)
    lexer = Lexer(f.read())
    f.close()
    
    while True:
        tk = lexer.next()
        if tk.kind == TokenKind.EOF:
            break
        print(tk)





if __name__ == "__main__":
    main()