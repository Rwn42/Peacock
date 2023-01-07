from lexer import *
import sys

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
    def __init__(self, lexer:Lexer):
        self.lexer = lexer
        self.functions = {}
        self.next_function_public = False
        self.current_function = None
    
    
    def get_until(self, until: list[TokenKind], allowed: list[TokenKind] = expression_tokens) -> list[Token]:
        result = []
        while True:
            if self.lexer.peek_next_token().kind == TokenKind.IDENTIFIER:
                tk = self.lexer.next()
                if self.lexer.peek_next_token().kind == TokenKind.LPAREN:
                    _ = self.lexer.next()
                    while self.lexer.peek_next_token().kind != TokenKind.RPAREN:
                        result.extend(self.get_until([TokenKind.COMMA, TokenKind.RPAREN]))
                        if self.lexer.peek_next_token().kind == TokenKind.COMMA:
                            _ = self.lexer.next()
                            continue
                    _ = self.lexer.next()
                    result.append(tk)
                    pass
                else:
                    result.append(tk)
                    continue
            if self.lexer.peek_next_token().kind in until:
                return result
            if self.lexer.peek_next_token().kind not in allowed:
                print(f"Token {self.lexer.next()} Not Allowed in expression")
                sys.exit()
            result.append(self.lexer.next())
    

    def organize_statement(self) -> list[Token]:
        result = []
        token = self.lexer.next()
        match token.kind:
            case TokenKind.IF:
                result.append(token)
                result.extend(self.get_until(Parser.comparison_tokens))
                comparison_token = self.lexer.next()
                result.extend(self.get_until([TokenKind.DO]))
                result.append(comparison_token)
                result.append(self.lexer.next())
                while self.lexer.peek_next_token().kind != TokenKind.END:
                    result.extend(self.organize_statement())
                result.append(self.lexer.next())
            case TokenKind.WHILE:
                comparison_rhs = self.get_until(Parser.comparison_tokens)
                comparison_token = self.lexer.next()
                comparison_lhs = self.get_until([TokenKind.DO])
                result.append(token)
                while self.lexer.peek_next_token().kind != TokenKind.END:
                    result.extend(self.organize_statement())
                result.extend(comparison_rhs)
                result.extend(comparison_lhs)
                result.append(comparison_token)
                result.append(self.lexer.next())

            case TokenKind.IDENTIFIER:
                if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                    equal_token = self.lexer.next()
                    result.extend(self.get_until([TokenKind.NEWLINE, TokenKind.SEMICOLON]))
                    result.append(equal_token)
                    result.append(token)
                elif self.lexer.peek_next_token().kind == TokenKind.COLON:
                    _ = self.lexer.next()
                    type_ = self.parse_type().value
                    if self.current_function:
                        self.functions[self.current_function]["locals"][token.value] = type_
                    else:
                        print("globals not yet supported")

                    if self.lexer.peek_next_token().kind == TokenKind.SINGLE_EQUAL:
                        equal_token = self.lexer.next()
                        result.extend(self.get_until([TokenKind.NEWLINE, TokenKind.SEMICOLON]))
                        result.append(equal_token)
                        result.append(token)
            case TokenKind.MEMORY:
                result.append(token)
                name = self.lexer.next()
                type_ = self.parse_type()
                result.extend(self.get_until([TokenKind.NEWLINE, TokenKind.SEMICOLON]))
                result.append(name)
                result.append(type_)
                _ = self.lexer.next()
            case TokenKind.RETURN:
                result.extend(self.get_until([TokenKind.NEWLINE, TokenKind.SEMICOLON]))
            case TokenKind.ELSE: result.append(token)
            case TokenKind.NEWLINE: pass
        return result
    
    def parse_type(self) -> Token:
        first = self.lexer.next()
        result = Token(TokenKind.TYPE_, "", first.row, first.col, first.file)
        if first.kind == TokenKind.HAT:
            result.value = "^"+self.expect(TokenKind.IDENTIFIER).value
        else:
            if first.kind != TokenKind.IDENTIFIER:
                print(f"Unexpected Token {first} expected type")
                sys.exit()
            result.value = first.value
        return result

    def parse(self):
        token = self.lexer.next()
        match token.kind:
            case TokenKind.PUB:
                self.next_function_public = True
            case TokenKind.PROC:
                name = self.lexer.next().value
                params = {}
                return_type = ""
                body = []
                _ = self.expect(TokenKind.LPAREN)
                while self.lexer.peek_next_token().kind != TokenKind.RPAREN:
                    p_name = self.lexer.next().value
                    p_type = self.parse_type().value
                    params[p_name] = p_type
                    if self.lexer.peek_next_token().kind == TokenKind.COMMA:
                        _ = self.lexer.next()
                    else:
                        break
                _ = self.lexer.next()
                if self.lexer.peek_next_token().kind != TokenKind.DO:
                    return_type = self.parse_type().value
                    _ = self.expect(TokenKind.DO)
                else:
                    _ = self.lexer.next()
                
                self.functions[name] = {"params": params,"return_type": return_type, "public": self.next_function_public, "locals": {}}
                self.current_function = name
                while self.lexer.peek_next_token().kind != TokenKind.END:
                    body.extend(self.organize_statement())
                self.functions[name]["body"] = body
                if self.next_function_public:
                    self.next_function_public = False
            case TokenKind.EOF:
                return
        self.parse()
    
    def expect(self, expected:TokenKind) -> Token:
        if self.lexer.peek_next_token().kind != expected:
            print(f"Error Unexpected Token {self.lexer.next()}")
            sys.exit()  
        else:
            return self.lexer.next()
              
        
