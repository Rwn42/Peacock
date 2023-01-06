from enum import Enum, auto 
from typing import Optional

class TokenKind(Enum):
    PLUS = auto(),
    DASH = auto(),
    ASTERISK = auto()
    SLASH_FORWARD = auto(),
    NEWLINE = auto(),
    EOF = auto()
    LITERAL_INT = auto(),
    LITERAL_FLOAT = auto(),
    LITERAL_STRING = auto(),
    LITERAL_BOOL = auto(),
    DOUBLE_EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    LESS_THAN_EQUAL = auto()
    GREATER_THAN_EQUAL = auto()
    DOT = auto(),
    SEMICOLON = auto()
    COLON = auto()
    EXCLAMATION_MARK = auto()
    LPAREN = auto(),
    RPAREN = auto(),
    SINGLE_EQUAL = auto(),
    PROC = auto(),
    DO = auto()
    WHILE = auto()
    IF = auto()
    END = auto()
    IDENTIFIER = auto()


class Token:
    def __init__(self, kind:TokenKind, value:str, row:int, col:int, filename:str):
        self.kind = kind
        self.value = value
        self.row = row
        self.col = col
        self.file = filename
    
    def __repr__(self):
         rep = f"{self.value}, of kind {self.kind.name}, at row: {self.row+1} col: {self.col+1}"
         return rep


class Lexer:
    def __init__(self, code: str, filename:str):
        self.code = code
        self.pos = 0
        self.row = 0
        self.col = 0
        self.filename = filename
    
    
    def __char(self) -> str:
        self.__consume()
        return self.code[self.pos-1]
    
    def __consume(self):
        self.pos += 1
        self.col += 1
    
    def __peek_char(self) -> Optional[str]:
        if self.pos > len(self.code)-1: return None
        return self.code[self.pos]
    
    def __peek_next_char(self) -> Optional[str]:
        if self.pos+1 > len(self.code)-1: return None
        return self.code[self.pos+1]
    
    #returns true if reached end of file
    def __skip_whitespace(self) -> bool:
        while True:
            if self.__peek_char():
                if self.__peek_char().isspace():
                   self.__consume()
                else:
                    return False
            else:
                return True
    
    def __get_characters_while(self, filter_function) -> str:
        characters = ""
        while True:
            if self.__peek_char() == None:
                return characters
            if not filter_function(self.__peek_char()):
                return characters
            characters += self.__char()
    
    def next(self) -> Token:
        #since newline counts as whitespace this mandatory to check before
        if self.__peek_char():
            if self.__peek_char() == "\n":
                self.__consume()
                self.row += 1
                self.col = 0
                return Token(TokenKind.NEWLINE, "\n", self.row, self.col, self.filename)
        else:
            return Token(TokenKind.EOF, "", self.row, self.col, self.filename)
        
        #skip to first character of next token
        eof = self.__skip_whitespace()
        if eof: return Token(TokenKind.EOF, "", self.row, self.col, self.filename)

        #create our token object
        token = Token(None, "", self.row, self.col, self.filename)
        
        #get the first character of our token
        first_character = self.__char()

        match first_character:
            case "+": token.kind = TokenKind.PLUS
            case "-": token.kind = TokenKind.DASH
            case "*": token.kind = TokenKind.ASTERISK
            case "/": token.kind = TokenKind.SLASH_FORWARD
            case "#":
                _ = self.__get_characters_while(lambda x: x != "\n")
                if self.__peek_char() == None:
                    token.kind = TokenKind.EOF
                else:
                    return self.next()
            case "\"":
                token.kind = TokenKind.LITERAL_STRING
                token.value = self.__get_characters_while(lambda x: x != "\"")
                assert self.__peek_char() != None, f"Expected \" to end string literal started at row: {token.row+1} col: {token.col+1}"
                self.__consume()
            
            case ".": token.kind = TokenKind.DOT
            case "(": token.kind = TokenKind.LPAREN
            case ")": token.kind = TokenKind.RPAREN
            case ";": token.kind = TokenKind.SEMICOLON
            case ":": token.kind = TokenKind.COLON

            case "=":
                assert self.__peek_char() != None, f"cannot end file on {first_character}"
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.DOUBLE_EQUAL
                else: token.kind = TokenKind.SINGLE_EQUAL
            
            case ">":
                assert self.__peek_char() != None, f"cannot end file on {first_character}"
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.GREATER_THAN_EQUAL
                else: token.kind = TokenKind.GREATER_THAN

            case "<":
                assert self.__peek_char() != None, f"cannot end file on {first_character}"
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.LESS_THAN_EQUAL
                else: token.kind = TokenKind.LESS_THAN
            
            case "!":
                assert self.__peek_char() != None, f"cannot end file on {first_character}"
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.NOT_EQUAL
                else: token.kind = TokenKind.EXCLAMATION_MARK
            #this would be a keyword, identifier or an integer/float
            case _:
                value = first_character
                value += self.__get_characters_while(lambda x: x.isalnum() or x == "_")
                if value.isnumeric():
                    if self.__peek_char():
                        if self.__peek_char() != ".":
                            token.kind = TokenKind.LITERAL_INT
                        else:
                            token.kind = TokenKind.LITERAL_FLOAT
                            value += self.__char()
                            rest = self.__get_characters_while(lambda x: x.isnumeric())
                            value += rest
                else:
                    match value:
                        case "proc": token.kind = TokenKind.PROC
                        case "do": token.kind = TokenKind.DO
                        case "if": token.kind= TokenKind.IF
                        case "while": token.kind = TokenKind.WHILE
                        case "end": token.kind = TokenKind.END
                        case "true" | "false": token.kind = TokenKind.LITERAL_BOOL
                        case _: token.kind = TokenKind.IDENTIFIER
                token.value = value

        
        return token


        
        
        








