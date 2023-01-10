from lexer import *
from util import eprint

class Parser:
    comparison_tokens = [
        TokenKind.GREATER_THAN, TokenKind.LESS_THAN, TokenKind.DOUBLE_EQUAL, TokenKind.NOT_EQUAL,
        TokenKind.GREATER_THAN_EQUAL, TokenKind.LESS_THAN_EQUAL,
    ]
    expression_tokens = [
        TokenKind.IDENTIFIER, TokenKind.LITERAL_INT, TokenKind.LITERAL_BOOL, TokenKind.LITERAL_FLOAT,
        TokenKind.LITERAL_STRING, TokenKind.PLUS, TokenKind.DASH, TokenKind.ASTERISK, TokenKind.SLASH_FORWARD,
        TokenKind.LPAREN, TokenKind.RPAREN, 
    ]
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
    
    #we rely on dynamic typing for this function so im not sure how to type annotate it
    #basically it returns a list of tokens and list of tokens which may also contain further nested lists
    #or just tokens
    #does consume the until unlike get_until method
    def parse_until(self, until:list[TokenKind]=[TokenKind.EOF]):
        result = []
        token = self.lexer.next()
        while token.kind not in until:
            match token.kind:
                case TokenKind.EXTERN:
                    code = []
                    result.append(token)
                    code.extend(self.parse_function_signature(TokenKind.NEWLINE))
                    result.append(code)
                case TokenKind.PROC:
                    code = []
                    result.append(token)
                    code.extend(self.parse_function_signature())
                    code.append(self.parse_until([TokenKind.END]))
                    result.append(code)
                case TokenKind.IF | TokenKind.WHILE:
                    code = []
                    result.append(token)
                    code.extend(self.get_tokens_until(Parser.comparison_tokens))
                    operator = self.lexer.next()
                    code.extend(self.get_tokens_until([TokenKind.DO]))
                    code.append(operator)
                    code.append(self.parse_until([TokenKind.END]))
                    result.append(code)
                case TokenKind.RETURN:
                    result.append(token)
                    result.append(self.get_tokens_until())
                case TokenKind.IDENTIFIER:
                    next_ = self.lexer.next()
                    result.append(token)
                    result.append(next_)
                    if next_.kind == TokenKind.COLON:
                        type_ = self.parse_type()
                        result.append(type_)
                        if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                            _ = self.lexer.next()
                            result.append(self.get_tokens_until())
                    elif next_.kind == TokenKind.SINGLE_EQUAL:
                        result.append(self.get_tokens_until())
                    else:
                        eprint(f"Unexpected Token After Identifier {next_}")
                case _:
                    pass
                    

            token = self.lexer.next()
        return result

    #returns all tokens between brackets (not recursive)
    #the type of bracket can be passed in as a parameter
    #has the same type as the parse function a funky list of tokens
    #consumes the last brakcet
    def parse_brackets(self, bracket:TokenKind=TokenKind.RPAREN):
        result = []
        while True:
            result.append(self.get_tokens_until([TokenKind.COMMA, bracket]))
            if self.lexer.next().kind == bracket:
                return result
    
    #get tokens until an a certain type does not consume the last one
    def get_tokens_until(self, until: list[TokenKind]=[TokenKind.NEWLINE]) -> list[Token]:
        tk = self.lexer.peek_next_token()
        result = []
        while tk.kind not in until:
            tk = self.lexer.next()
            result.append(tk)
            tk = self.lexer.peek_next_token()
        return result
    
    #returns a list becuase a pointer type such as ^int is two tokens
    #joining them would lead to innacurate errors down the line.
    #returns none if the token is not a type
    def parse_type(self) -> Optional[Token]:
        start_tk = self.lexer.peek_next_token()
        match start_tk.kind:
            case TokenKind.IDENTIFIER:
                _ = self.lexer.next()
                return start_tk
            case TokenKind.HAT:
                _ = self.lexer.next()
                name = self.expect(TokenKind.IDENTIFIER).value
                start_tk.value += name
                start_tk.kind = TokenKind.IDENTIFIER
                return start_tk
            case _:
                return None
    
    #returns a nested list of token and token lists of a function signature
    #the user can specify what token they expect at the end of the signature
    #for extern this is a newline for proc this is do.
    def parse_function_signature(self, expected_after_end: TokenKind = TokenKind.DO):
        result = []
        
        #function name
        result.append(self.lexer.next())

        _ = self.expect(TokenKind.LPAREN)
        #add our parameters (if any)
        result.append(self.parse_brackets())

        #see if we have return type
        possible_type = self.parse_type()
        #if there is not a type we expect the extern defintion to be over so a newline
        if not possible_type:
            _ = self.expect(expected_after_end)
        else:
            result.append(possible_type)
        return result
    
    #makes sure the next token is of a certain type returns that token back to the caller if so
    def expect(self, kind:TokenKind) -> Token:
        if self.lexer.peek_next_token().kind != kind:
            eprint(f"Unexpected Token {self.lexer.next()} expected {kind.name}")
        return self.lexer.next()
        