from enum import Enum, auto 
from typing import Optional
from util import eprint

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
    COMMA = auto()
    EXCLAMATION_MARK = auto()
    LPAREN = auto(),
    RPAREN = auto(),
    SINGLE_EQUAL = auto(),
    PROC = auto(),
    DO = auto()
    HAT = auto()
    SLIM_ARROW = auto()
    TYPE_ = auto()
    COLON = auto()
    WHILE = auto()
    IF = auto()
    END = auto()
    ELSE = auto()
    MEMORY = auto()
    RETURN = auto()
    EXTERN = auto()
    PUB = auto()
    IDENTIFIER = auto()


class Token:
    def __init__(self, kind:TokenKind, value:str, row:int, col:int, filename:str):
        self.kind = kind
        self.value = value
        self.row = row
        self.col = col
        self.file = filename
    
    def __repr__(self):
         name_or_kind = self.kind.name
         if self.value != "" and not self.value.isspace():
            name_or_kind = self.value
         rep = f"{name_or_kind} in {self.file} at line: {self.row+1} and column: {self.col+1}"
         return rep


class Lexer:
    def __init__(self, code: str, filename:str):
        self.code = code
        self.pos = 0
        self.row = 0
        self.col = 0
        self.filename = filename
    
    #returns the current character pointed to by the lexer.
    def __char(self) -> str:
        self.__consume()
        return self.code[self.pos-1]
    
    #advances the lexer 
    def __consume(self):
        self.pos += 1
        self.col += 1
    
    #returns the current character without advancing the lexer
    #returns none if we reached the end of the file
    def __peek_char(self) -> Optional[str]:
        if self.pos > len(self.code)-1: return None
        return self.code[self.pos]
    
    
    #advances the lexer until there is no whitespace returns true if reached end of file
    def __skip_whitespace(self) -> bool:
        while True:
            if self.__peek_char():
                if self.__peek_char().isspace():
                   self.__consume()
                else:
                    return False
            else:
                return True
    
    #return every character collected until the filter function returns false
    def __get_characters_while(self, filter_function) -> str:
        characters = ""
        while True:
            if self.__peek_char() == None:
                return characters
            if not filter_function(self.__peek_char()):
                return characters
            characters += self.__char()
    
    #returns the next token returns EOF token if we reached the end.
    def next(self) -> Token:
        #since newline counts as whitespace this mandatory to check before skipping whitespace
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

        token.value += first_character

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
                if self.__peek_char() == None:
                    eprint(f"Expected \" to end string literal started at row: {token.row+1} col: {token.col+1}")
                self.__consume()
            
            case ".": token.kind = TokenKind.DOT
            case "(": token.kind = TokenKind.LPAREN
            case ")": token.kind = TokenKind.RPAREN
            case ";": token.kind = TokenKind.SEMICOLON
            case ",": token.kind = TokenKind.COMMA
            case "^": token.kind = TokenKind.HAT
            case ":": token.kind = TokenKind.COLON
            case ";": token.kind = TokenKind.SEMICOLON
            case "=":
                if self.__peek_char() == None: eprint( f"cannot end file on {first_character}")
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.DOUBLE_EQUAL
                else: token.kind = TokenKind.SINGLE_EQUAL
            
            case ">":
                if self.__peek_char() == None: eprint( f"cannot end file on {first_character}")
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.GREATER_THAN_EQUAL
                else: token.kind = TokenKind.GREATER_THAN

            case "<":
                if self.__peek_char() == None: eprint( f"cannot end file on {first_character}")
                if self.__peek_char() == "=":
                    self.__consume()
                    token.kind = TokenKind.LESS_THAN_EQUAL
                elif self.__peek_char() == "-":
                    self.__consume()
                    token.kind = TokenKind.SLIM_ARROW
                else: token.kind = TokenKind.LESS_THAN
            
            case "!":
                if self.__peek_char() == None: eprint( f"cannot end file on {first_character}")
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
                        case "else": token.kind = TokenKind.ELSE
                        case "while": token.kind = TokenKind.WHILE
                        case "end": token.kind = TokenKind.END
                        case "true" | "false": token.kind = TokenKind.LITERAL_BOOL
                        case "return": token.kind = TokenKind.RETURN
                        case "memory": token.kind = TokenKind.MEMORY
                        case "extern": token.kind = TokenKind.EXTERN
                        case "pub": token.kind = TokenKind.PUB
                        case _: token.kind = TokenKind.IDENTIFIER
                token.value = value

        
        return token

    def peek_next_token(self) -> Token:
        cur_pos = self.pos
        cur_row = self.row
        cur_col = self.col
        tk = self.next()
        self.pos = cur_pos
        self.row = cur_row
        self.col = cur_col
        return tk

        
        
        








