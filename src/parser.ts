import { Lexer, TokenType, Token, token_repr} from "./lexer.js";
import {exit} from "process"
import * as Ast from "./ast.js"


interface IdentifierInformation{
    type: string,
    sizeof_type?: number,
}

/*
Proposed Linear Memory syntax
x.z <- this would be a struct load so load type of z
x.(z) <- this would be an array load so load somehting of type x at offset z
*/


export class Parser{
    lexer: Lexer
    declared_identifiers: Map<string, IdentifierInformation>
    constructor(lexer: Lexer){
        this.lexer = lexer;
        this.declared_identifiers = new Map();
        console.log(this.get_expression())
    }

    private get_expression(until: Array<TokenType> = [TokenType.Semicolon, TokenType.Newline]): Ast.Expression{
        let result: Ast.Expression = {body: [], type: "undefined"};
        while(true){
            if(until.includes(this.lexer.peek_next().kind) || this.lexer.peek_next().kind == TokenType.EOF) return result;
            const token = this.lexer.next();
            switch(token.kind){
                case TokenType.LiteralInt:
                    if(result.type != "undefined" && result.type != "int") Parser.mismatched_type_error(token);
                    result.type = "int";
                    result.body.push({value: token.value, type: "int"}); break;
                case TokenType.LiteralBool:
                    if(result.type != "undefined" && result.type != "bool") Parser.mismatched_type_error(token);
                    result.type = "bool";
                    result.body.push({value: token.value, type: "bool"}); break;
                case TokenType.LiteralString:
                    if(result.type != "undefined" && result.type != "^string") Parser.mismatched_type_error(token);
                    result.type = "string";
                    result.body.push({value: token.value, type: "^string"}); break;
                case TokenType.LiteralFloat:
                    if(result.type != "undefined" && result.type != "float") Parser.mismatched_type_error(token);
                    result.type = "float";
                    result.body.push({value: token.value, type: "float"}); break;
                case TokenType.Identifier:
                    //memory load
                    if(this.lexer.peek_next().kind == TokenType.Dot){
                        let _ = this.lexer.next();
                        const next = this.lexer.next();
                        if(next.kind == TokenType.Identifier){
                            //so here the var info we want is the next or the 'y' in the following 'x.y'
                            //because it is a structure access operation.
                            const info = this.declared_identifiers.get(next.value) ?? Parser.undeclared_identifier(next);
                            result.body.push({
                                //offset type is hardcodes as int because the offset type is the type we want to load
                                //but the offset expression should be of type int.
                                offset: {body: [{name: next.value, type: "int"}], type:"int"},
                                identifier: token.value,
                                type: info.type,
                                sizeof: info.sizeof_type ?? 4,
                            })
                            result.type = info.type;
                        }else if(next.kind == TokenType.Lparen){
                            const offset = this.get_expression([TokenType.Rparen]);
                            //so here the var info we want is the current token or the 'x' in the following 'x.y'
                            //because it is a array access operation we want to load the type of the array
                            const info = this.declared_identifiers.get(token.value) ?? Parser.undeclared_identifier(token);
                            result.body.push({
                                offset: offset,
                                identifier: token.value,
                                type: info.type,
                                sizeof: info.sizeof_type ?? 4,
                            })
                            result.type = info.type;
                            let _ = this.lexer.next();
                        }else{
                            Parser.unexpected_token(next);
                        }
                    }   
                    //function call
                    else if(this.lexer.peek_next().kind == TokenType.Lparen){
                        let _ = this.lexer.next();
                        const info = this.declared_identifiers.get(token.value) ?? Parser.undeclared_identifier(token);
                        const args = [];
                        if(this.lexer.peek_next().kind != TokenType.Rparen){
                            while(true){
                                args.push(this.get_expression([TokenType.Comma, TokenType.Rparen]))
                                if(this.lexer.peek_next().kind == TokenType.Rparen) break;
                                let _ = this.lexer.next()
                            }
                        }
                        _ = this.lexer.next();
                        result.body.push({name: token.value, args: args, type: info.type})
                        result.type = info.type;      
                    } 
                    //normal usage
                    else{
                        const info = this.declared_identifiers.get(token.value) ?? Parser.undeclared_identifier(token);
                        result.type = info.type;
                        result.body.push({name: token.value, type: info.type});
                        
                    }
                    break;
                case TokenType.Plus: result.body.push("+"); break;
                case TokenType.Dash: result.body.push("-"); break;
                case TokenType.SlashForward: result.body.push("/"); break;
                case TokenType.Asterisk: result.body.push("*"); break;
                default:
                    Parser.unexpected_token(token);
            }
        }
    }

    private static mismatched_type_error(token: Token): never{
        console.log("ERROR: Mismatched types in expression")
        console.log(token_repr(token))
        exit(1);
        throw new Error("Unreachable if you are seeing this there is a bug");
    }
    private static undeclared_identifier(token: Token): never{
        console.log("ERROR: Undeclared Identifier")
        console.log(token_repr(token))
        exit(1);
        throw new Error("Unreachable if you are seeing this there is a bug");
    }
    private static unexpected_token(token: Token, extra?:string): never{
        console.log("ERROR: Unexpected Token " + extra)
        console.log(token_repr(token))
        exit(1);
        throw new Error("Unreachable if you are seeing this there is a bug");
    }
}