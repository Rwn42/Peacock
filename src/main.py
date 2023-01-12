import sys
from lexer import *
from compiler import *
from parsing import *
from pprint import PrettyPrinter

def print_lexer_output(l: Lexer):
    t = l.next()
    while t.kind != TokenKind.EOF:
        print("-" * (len(repr(t)) + 2))
        print("|", t, "|")
        print("-" * (len(repr(t)) + 2))
        t = l.next()

def print_parer_output(p: Parser):
    pp = PrettyPrinter(sort_dicts=False)
    pp.pprint(p.parse())

def main():
    if len(sys.argv) < 3:
        eprint("Not Enough Arguments To Peacock Compiler.")
    subcommand = sys.argv[1]
    source_file = sys.argv[2]

    f = open(source_file)
    lexer = Lexer(f.read(), source_file)
    f.close()

    parser = Parser(lexer)

    compiler = Compiler()

    match subcommand:
        case "lex": print_lexer_output(lexer)
        case "parse": print_parer_output(parser)
        case "com": compiler.compile(parser.parse())
        case _:
            eprint(f"Unknown command {subcommand}.")
    



if __name__ == "__main__":
    main()