from lexer import *
from collections import namedtuple
from enum import Enum, auto
import sys

Operation = namedtuple("Operation", "opcode operand")

class Opcodes(Enum):
    PUSH = auto() #operand is value to be pushed
    ADD = auto()  #operand is mutliplier so -1 functions as minus
    MUL = auto()  #operand is exponent ne -1 functions as division
    EQ = auto()  #operand is value to be pushed if true -1 functions as !=
    CALL = auto() #index into function array inwhich to be called
    MVLV = auto() #operand index of local variable to be moved
    PSLV = auto()

# f("hi") == 2
class Compiler:
    expression_tokens = [
                        TokenKind.IDENTIFIER, TokenKind.PLUS, TokenKind.DASH,
                        TokenKind.ASTERISK, TokenKind.SLASH_FORWARD,
                        TokenKind.LPAREN, TokenKind.RPAREN,
                        TokenKind.LITERAL_INT, TokenKind.LITERAL_STR,
                    ]
    def __init__(self, lexer:Lexer):
        self.lexer = lexer
        self.program: list[Operation] = []
        self.functions = {"func": 10}
        self.locals = {"var": 0}
    
    def compile_until(self, until: list[TokenKind], whitelist: list[TokenKind] = None, blacklist: list[TokenKind] = None) -> list[Operation]:
        res = []
        
        while True:
            token = self.lexer.peek_next_token()
            if token.kind in until:
                return res
            if whitelist != None:
                if not token.kind in whitelist:
                    self.print_unexpected_token(token)
            elif blacklist != None:
                if token.kind in blacklist:
                    self.print_unexpected_token(token)
            else:
                pass
            
            token = self.lexer.next()
            match token.kind:
                case TokenKind.LITERAL_INT:
                    res.append(Operation(Opcodes.PUSH, int(token.value)))
                case TokenKind.PLUS:
                    res.append(Operation(Opcodes.ADD, 1))
                case TokenKind.DASH:
                    res.append(Operation(Opcodes.ADD, -1))
                case TokenKind.ASTERISK:
                    res.append(Operation(Opcodes.MUL, 1))
                case TokenKind.SLASH_FORWARD:
                    res.append(Operation(Opcodes.MUL, -1))
                case TokenKind.IDENTIFIER:
                    match self.lexer.peek_next_token().kind:
                        #function call
                        case TokenKind.LPAREN:
                            params = self.compile_until(until=[TokenKind.RPAREN], whitelist=[TokenKind.COMMA].extend(Compiler.expression_tokens))
                            res.extend(params.reverse())
                            res.append(Operation(Opcodes.CALL, self.functions[token.value]))
                            _ = self.lexer.next()
                        #variable assignment
                        case TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            lhs = (self.compile_until(until=[TokenKind.SEMICOLON], whitelist=Compiler.expression_tokens))
                            if token.value in self.locals:
                                res.extend(lhs)
                                res.append(Operation(Opcodes.MVLV, self.locals[token.value]))
                            else:
                                res.extend(lhs)
                                self.locals[token.value] = len(self.locals.keys())
                                res.append(Operation(Opcodes.MVLV, self.locals[token.value]))
                        #variable / constant usage
                        case _: res.extend(self.push_identifier_value(token.value))
                case _: pass

    #given and identifier generate push instruction with identifier value
    #may be a constant, variable ect.
    def push_identifier_value(self, identifier: str):
        if identifier in self.locals:
            return Operation(Opcodes.PSLV, self.locals[identifier])
    
    def compile_function_call(self, token: Token):
        res = []
        params = []
        _ = self.lexer.next()
        if self.lexer.peek_next_token().kind != TokenKind.RPAREN:
            while True:
                result = self.compile_until(
                    until=[TokenKind.COMMA, TokenKind.RPAREN], 
                    whitelist=Compiler.expression_tokens
                )
                params.append(result)
                if self.lexer.peek_next_token().kind == TokenKind.RPAREN:
                    break
                else:
                    #consume comma
                    _ = self.lexer.next()

        _ = self.lexer.next()
        #since its a stack machine paramaters have to be in reverse order.
        params.reverse()
        res.extend([j for sub in params for j in sub])
        res.append(Operation(Opcodes.CALL, self.functions[token.value]))
        return res

    def print_unexpected_token(self, tk:Token):
        print(f"Unexpected Token {tk.kind if tk.value == '' else tk.value} at Row: {tk.row+1} Col: {tk.col+1}")
        sys.exit(1)
