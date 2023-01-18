import { Lexer, TokenType, Token, token_repr} from "./lexer.js";
import {exit} from "process"
import * as Ast from "./ast.js"


interface IdentifierInformation{
    type:string,
    sizeof_type?: number,
}

/*
Proposed Linear Memory syntax
x.z <- this would be a struct load so load type of z
x.(z) <- this would be an array load so load somehting of type x at offset z

x.z = 10
*/

/*
TODO:
Definition Parser
Static analysis
*/



export class Parser{
    lexer: Lexer
    declared_identifiers: Map<string, IdentifierInformation>
    static comparison_tokens = [
        TokenType.LessThan, TokenType.GreaterThan,
        TokenType.DoubleEqual, TokenType.NotEqual,
        TokenType.GreaterThanEqual, TokenType.LessThanEqual
    ]
    constructor(lexer: Lexer){
        this.lexer = lexer;
        this.declared_identifiers = new Map();
    }

    parse(): Ast.AST{
        const token = this.lexer.next()
        const result: Ast.AST = [];
        switch(token.kind){
            case TokenType.Proc:
                const name = this.lexer.next().value;
                let is_public = false
                if(this.lexer.peek_next().kind == TokenType.Pub){
                    this.lexer.next();
                    is_public = true;
                }
                const args = this.parse_params();
                const return_type = this.lexer.peek_next().kind == TokenType.Do ? undefined : this.parse_type();
                this.declared_identifiers.set(name, {type: return_type || ""})
                const body = this.get_statements();
                result.push({
                    body: body,
                    name: name, 
                    params: args || null, 
                    return_type: return_type, 
                    is_public: is_public,
                    kind: Ast.DefintionType.Procedure,
                });
                this.lexer.next();
               
        }
        return result;
    }

    private parse_params(): Array<Ast.VariableUsage>{
        const args: Array<Ast.VariableUsage> = [];
        if(this.lexer.peek_next().kind != TokenType.Lparen) Parser.unexpected_token(this.lexer.next())
        this.lexer.next();
        if(this.lexer.peek_next().kind != TokenType.Rparen){
            while(true){
                const name_tk = this.lexer.next();
                const name = name_tk.kind == TokenType.Identifier ? name_tk.value : Parser.unexpected_token(name_tk);
                if(this.lexer.peek_next().kind != TokenType.Colon) Parser.unexpected_token(this.lexer.next())
                this.lexer.next();
                const type = this.parse_type()
                args.push({name:name, type: type})
                this.declared_identifiers.set(name, {type: type})
                if(this.lexer.peek_next().kind == TokenType.Rparen) break;
                this.lexer.next()
            }
        }
        this.lexer.next();
        return args;
    }

    private parse_type(): string{
        const initial = this.lexer.next();
        if(initial.kind == TokenType.Hat){
            return initial.value += 
            this.lexer.peek_next().kind == TokenType.Identifier ? 
            this.lexer.next().value : Parser.unexpected_token(this.lexer.next());
        }else if(initial.kind == TokenType.Identifier){
            return initial.value
        }else{
            Parser.unexpected_token(initial);
        }
    }

    private get_statements(until: Array<TokenType> = [TokenType.End]): Array<Ast.Statement>{
        let result: Array<Ast.Statement> = [];
        while(true){
            if(until.includes(this.lexer.peek_next().kind) || this.lexer.peek_next().kind == TokenType.EOF) return result;
            const token = this.lexer.next();
            switch(token.kind){
                case TokenType.Return:
                    result.push({body: this.get_expression(), kind: Ast.StatementType.Return}); break;
                case TokenType.Identifier:
                    if(this.lexer.peek_next().kind == TokenType.Dot){
                        this.lexer.next();
                        const identifier = token.value
                        if(this.lexer.peek_next().kind == TokenType.Lparen){
                            this.lexer.next();
                            const offset = this.get_expression([TokenType.Rparen]);
                            this.lexer.next();
                            const info = this.declared_identifiers.get(identifier) ?? Parser.undeclared_identifier(token);
                            if(this.lexer.next().kind != TokenType.SingeEqual) Parser.unexpected_token(token);
                            result.push({
                                kind: Ast.StatementType.MemoryStore,
                                identifier: identifier,
                                offset: offset,
                                type: info.type,
                                sizeof: 4,
                                body: this.get_expression(),
                            });
                        }else{
                            const next = this.lexer.next();
                            if(this.lexer.peek_next().kind != TokenType.SingeEqual) Parser.unexpected_token(this.lexer.next());
                            this.lexer.next();
                            const body = this.get_expression();
                            const info = this.declared_identifiers.get(next.value) ?? Parser.undeclared_identifier(next);
                            result.push({
                                kind: Ast.StatementType.MemoryStore,
                                identifier: identifier,
                                offset: {body: [{name: next.value, type: "int"}], type:"int"},
                                type: info.type,
                                sizeof: info.sizeof_type ?? 4,
                                body: body,
                            });

                        }
                    }else if(this.lexer.peek_next().kind == TokenType.Colon){
                        this.lexer.next()
                        const name = token.value;
                        const type = this.parse_type()
                        let assignment = undefined;
                        this.declared_identifiers.set(name, {type: type})
                        if(this.lexer.peek_next().kind == TokenType.SingeEqual){
                            this.lexer.next();
                            assignment = this.get_expression();
                        }
                        result.push({name: name, type: type, assignment: assignment, kind: Ast.StatementType.VariableDeclaration});
                    }else if(this.lexer.peek_next().kind == TokenType.SingeEqual){
                        const name = token.value;
                        this.lexer.next();
                        result.push({name: name,  body: this.get_expression(), kind: Ast.StatementType.VariableAssignment});
                    }else{
                        Parser.unexpected_token(token);
                    }
                    break;
                case TokenType.If:{
                    const rhs = this.get_expression(Parser.comparison_tokens);
                    const comparison = this.lexer.next().value;
                    const lhs = this.get_expression([TokenType.Do]);
                    this.lexer.next();
                    const body = this.get_statements();
                    const is_while = false
                    this.lexer.next();
                    result.push({
                        kind: Ast.StatementType.ConditionalBlock,
                        is_while: is_while,
                        comparison_rhs: rhs,
                        comparison_lhs: lhs,
                        comparison_operator: comparison,
                        body: body,
                    });
                    break;
                }
                case TokenType.While:{
                    const rhs = this.get_expression(Parser.comparison_tokens);
                    const comparison = this.lexer.next().value;
                    const lhs = this.get_expression([TokenType.Do]);
                    this.lexer.next();
                    const body = this.get_statements();
                    const is_while = true
                    this.lexer.next();
                    result.push({
                        kind: Ast.StatementType.ConditionalBlock,
                        is_while: is_while,
                        comparison_rhs: rhs,
                        comparison_lhs: lhs,
                        comparison_operator: comparison,
                        body: body,
                    });
                    break;
                }
            }
        }
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
                    Parser.unexpected_token(token, "In expression.");
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
        console.log("ERROR: Unexpected Token " + (extra !== undefined ? extra : ""))
        console.log(token_repr(token))
        exit(1);
        throw new Error("Unreachable if you are seeing this there is a bug");
    }
}