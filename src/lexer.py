from enum import Enum, auto
from typing import Optional
import sys


#Each different kind of token many describe the token completely
#however the identifier and the literal_x tokens use the value feild
#of the token class
class TokenKind(Enum):
    PLUS = auto()
    DASH = auto()
    ASTERISK = auto()
    SLASH_FORWARD = auto()
    LITERAL_INT = auto()
    LITERAL_STR = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    SINGLE_EQUAL = auto()
    COLON = auto()
    SEMICOLON = auto()
    DOUBLE_EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    LESS_THAN_EQUAL = auto()
    GREATER_THAN_EQUAL = auto()
    EXCLAMATION_MARK = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    END = auto()
    DO = auto()
    PROC = auto()
    DROP = auto()
    STRUCT = auto()
    RCURLY = auto()
    LCURLY = auto()
    DOT = auto()
    EXTERN = auto()
    PUB = auto()
    TYPE_INT = auto()
    TYPE_STR = auto()
    TYPE_FLOAT = auto()
    EOF = auto()
    IDENTIFIER = auto()



class Token:
    def __init__(self,row: int, col: int, kind = TokenKind.IDENTIFIER, value=""):
        self.kind = kind
        self.value = value
        self.row = row
        self.col = col
    def __repr__(self):
        rep = f"Row: {self.row+1}, Column: {self.col+1}, Kind: {self.kind}, Value: {self.value}"
        return rep


class Lexer:
    def __init__(self, source_code:str):
        self.source_code = source_code
        self.row = 0
        self.col = 0
        self.pos = 0
        self.at_eof = False
    
    #moves the lexer position by 1 returns false if position is out of bounds
    def advance(self) -> bool:
        if self.pos == len(self.source_code) -1:
            return False
        if self.char() == "\n":
            self.row += 1
            self.col = 0
        else:
            self.col += 1
        self.pos += 1
        return True
    
    #gets the character at the current lexer position
    def char(self) -> str:
        return self.source_code[self.pos]
    
    #peeks at the next characrer but does not advance the lexer
    #may return None if the next character does not exist
    def peek(self) -> Optional[str]:
        if self.pos+1 > len(self.source_code) -1:
            return None
        return self.source_code[self.pos+1]
    
    #adanvances the lexer position up until the first non-whitespace character
    def skip_whitespace(self) -> bool:
        while self.char().isspace():
            ok = self.advance()
            if not ok:
                return False
        return True
    
    #iterates over the source code characters until the filter_function returns false
    #the function returns these characters as a string and if it reached eof 
    #it starts at the current lexer position
    def get_characters_until(self, filter_function) -> tuple[str, bool]:
        characters = ""
        while filter_function(self.char()):
            characters += self.char()
            ok = self.advance()
            if not ok:
                return (characters, True)
        self.pos -= 1
        self.col -= 1
        return (characters, False)

    #returns the next token of the file
    #returns EOF token if no new tokens can be found
    def next(self) -> Token:
        if self.at_eof:
            return Token(self.row, self.col, TokenKind.EOF)
        if not self.skip_whitespace():
            return Token(self.row, self.col, TokenKind.EOF)
        
        first_character = self.char()

        token = Token(self.row, self.col)
        match first_character:
            case "+": token.kind = TokenKind.PLUS
            case "-": token.kind = TokenKind.DASH
            case "*": token.kind = TokenKind.ASTERISK
            case ":": token.kind = TokenKind.COLON
            case "(": token.kind = TokenKind.LPAREN
            case ")": token.kind = TokenKind.RPAREN
            case "{": token.kind = TokenKind.LCURLY
            case "}": token.kind = TokenKind.RCURLY
            case ".": token.kind = TokenKind.DOT
            case ";": token.kind = TokenKind.SEMICOLON
            case ",": token.kind = TokenKind.COMMA
            case "/": 
                match self.peek():
                    #comments are covered here
                    case "/":
                        #reads until the next line
                        _, _ = self.get_characters_until(lambda x: x != "\n")
                        #if at eof dont even try and give them a token
                        if not self.advance():
                            return Token(self.row, self.col, TokenKind.EOF)
                        #return the next token after the comment
                        return self.next()
                    case _: token.kind = TokenKind.SLASH_FORWARD
            case "!":
                match self.peek():
                    case "=":
                        token.kind = TokenKind.NOT_EQUAL
                        self.advance()
                    case _: token.kind = TokenKind.EXCLAMATION_MARK
            case ">":
                match self.peek():
                    case "=":
                        token.kind = TokenKind.GREATER_THAN_EQUAL
                        self.advance()
                    case _: token.kind = TokenKind.GREATER_THAN
            case "<":
                match self.peek():
                    case "=":
                        token.kind = TokenKind.LESS_THAN_EQUAL
                        self.advance()
                    case _: token.kind = TokenKind.LESS_THAN
            case "=":
                match self.peek():
                    case "=":
                        token.kind = TokenKind.DOUBLE_EQUAL
                        self.advance()
                    case _: token.kind = TokenKind.SINGLE_EQUAL
            case "\"":
                token.kind = TokenKind.LITERAL_STR
                self.advance()
                val, eof = self.get_characters_until(lambda x: x != "\"")
                if eof:
                    print(f"ERROR! Could Not Find Matching Quotation For String Literal at Row: {token.row} Col: {token.col}")
                    sys.exit(1)
                token.value = val
                self.advance()
            case _:
                val, _ = self.get_characters_until(lambda x: x.isalnum() or x == "_")
                token.value = val
        #token may be keyword or number literal at this point
        if token.kind == TokenKind.IDENTIFIER:
            try:
                _ = int(token.value)
                token.kind = TokenKind.LITERAL_INT
            except:
                match token.value:
                    case "if": token.kind = TokenKind.IF
                    case "do": token.kind = TokenKind.DO
                    case "end": token.kind = TokenKind.END
                    case "while": token.kind = TokenKind.WHILE
                    case "else": token.kind = TokenKind.ELSE
                    case "proc": token.kind = TokenKind.PROC
                    case "int": token.kind = TokenKind.TYPE_INT
                    case "String": token.kind = TokenKind.TYPE_STR
                    case "drop": token.kind = TokenKind.DROP
                    case "extern": token.kind = TokenKind.EXTERN
                    case "float": token.kind = TokenKind.TYPE_FLOAT
                    case "pub": token.kind = TokenKind.PUB
                    case "struct": token.kind = TokenKind.STRUCT
                    case _:
                        token.kind = TokenKind.IDENTIFIER
        
        at_eof = not self.advance()
        if at_eof:
            self.at_eof = True
        return token
    def back(self, pos, row, col):
        self.pos = pos
        self.row = row
        self.col = col

    #returns the next token but does not advance the lexer
    #so a call to peek_next over and over again produces the same result
    def peek_next_token(self) -> Token:
        cur_pos = self.pos
        cur_row = self.row
        cur_col = self.col
        at_eof = self.at_eof
        tk = self.next()
        self.pos = cur_pos
        self.row = cur_row
        self.col = cur_col
        self.at_eof = at_eof
        return tk
