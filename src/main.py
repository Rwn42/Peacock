import sys
from lexer import *
from parsing import Parser
from compiler import Compiler

def print_parsing_output(p: Parser):
    p.parse()
    for f in p.functions:
        print(f"{'public ' if p.functions[f]['public'] else ''}function {f}")
        print("--------Params--------")
        for var_name in p.functions[f]["params"]:
            print(var_name, p.functions[f]["params"][var_name])
        print("--------Return--------")
        print(f"returns {p.functions[f]['return_type']}")
        print("--------Local Variables--------")
        for var_name in p.functions[f]["locals"]:
            print(var_name, p.functions[f]["locals"][var_name])
        print("----------Body--------")
        for tk in p.functions[f]["body"]:
            if tk.value != "":
                print(tk.value)
            else:
                print(tk.kind.name)
        print("--------------------")

def print_lexer_output(l: Lexer):
    t = l.next()
    while t.kind != TokenKind.EOF:
        print(t)
        t = l.next()



def main():
    source_file = sys.argv[1]

    f = open(source_file)
    lexer = Lexer(f.read(), source_file)
    f.close()
    
    p = Parser(lexer)
    # print_parsing_output(p)
    p.parse()
    c = Compiler(p)
    c.save()






if __name__ == "__main__":
    main()