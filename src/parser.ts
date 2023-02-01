import { Lexer, TokenType, Token, token_repr} from "./lexer.ts";
import * as Ast from "./ast.ts"
import { basename } from "https://deno.land/std@0.175.0/path/mod.ts";


interface IdentifierInformation{
    type:string,
    sizeof_type?: number, //not size of type on stack for pointers but size of pointed to type
}
/*
TODO:
enumerations
support for x.(0).y (array of structs)
*/

export class Parser{
    lexer: Lexer
    declared_identifiers: Map<string, IdentifierInformation>
    addedLocals: string[]
    static comparison_tokens = [
        TokenType.LessThan, TokenType.GreaterThan,
        TokenType.DoubleEqual, TokenType.NotEqual,
        TokenType.GreaterThanEqual, TokenType.LessThanEqual
    ]

    constructor(lexer: Lexer){
        this.lexer = lexer;
        this.declared_identifiers = new Map();
        this.addedLocals = [];
        
    }

    expect(expectKind: TokenType): Token{
        const token = this.lexer.next();
        if(token.kind == TokenType.Newline) return this.expect(expectKind);
        if(token.kind != expectKind) Parser.unexpected_token(token);
        return token;
    }

    parse(): Ast.AST{
        const result: Ast.AST = [];

        while(this.lexer.peek_next().kind != TokenType.EOF){
            const token = this.lexer.next()
            switch(token.kind){
                case TokenType.Pub:
                    result.push(this.parseProcedureDefinition(true)); break;
                case TokenType.Proc:
                    result.push(this.parseProcedureDefinition(false)); break;
                case TokenType.Struct:
                    this.parseStructureDefinition(); break;
                case TokenType.Const:
                    result.push(this.parseConstantDefinition()); break;
                case TokenType.Environment:
                    result.push(this.parseEnvironmentDeclaration()); break;
                case TokenType.Include:
                    result.push(...this.parseInclude()); break;
                case TokenType.EOF:
                    return result;
                case TokenType.Newline: break;
            }
        }
        return result;
    }

    /*
    Top Level Defintion Parsing 
    */

    parseProcedureDefinition(is_public: boolean): Ast.Procedure{

        if(is_public) this.expect(TokenType.Proc);

        const name = this.expect(TokenType.Identifier).value
        this.expect(TokenType.Lparen);
        const args = this.parseParams();
        const return_type = this.lexer.peek_next().kind == TokenType.Do ? undefined : this.parseType();
        this.lexer.next();

        this.declared_identifiers.set(name, {type: return_type || ""})

        const body = this.parseStatements();
        this.lexer.next();
        
        this.addedLocals.forEach(local => this.declared_identifiers.delete(local));
        args.forEach(arg => this.declared_identifiers.delete(arg.name));

        return{
            body: body,
            name: name, 
            params: args || null, 
            return_type: return_type, 
            is_public: is_public,
            kind: Ast.DefintionType.Procedure,
        };
        
    }

    parseInclude(): Ast.AST{
        const import_file = this.expect(TokenType.LiteralString).value + ".pk";
        const filepath = Deno
        .realPathSync(this.lexer.filename)
        .replace(basename(this.lexer.filename), import_file);
        const filestring = Deno.readTextFileSync(filepath);
        const l = new Lexer(filestring, filepath);
        const p = new Parser(l);
        const result = p.parse();
        for(const [key, value] of p.declared_identifiers.entries()){
            this.declared_identifiers.set(key, value);
        }
        return result;

    }

    parseEnvironmentDeclaration(): Ast.EnvironmentDeclaration{
        const name = this.expect(TokenType.Identifier).value
        this.expect(TokenType.Lparen);
        const args = this.parseParams();
        const next_kind = this.lexer.peek_next().kind;
        let return_type = undefined;
        if(next_kind == TokenType.Newline || next_kind == TokenType.Semicolon || next_kind == TokenType.EOF){
            return_type = undefined;
            this.lexer.next();
        }else{
            return_type = this.parseType();
        }
        
        this.declared_identifiers.set(name, {type: return_type || ""});

        return{
            name: name, 
            params: args || null, 
            return_type: return_type, 
            kind: Ast.DefintionType.EnvironmentDeclaration,
        };
        

    }

    parseConstantDefinition(): Ast.ConstantDeclaration{
        const id_tk = this.lexer.next();
        this.expect(TokenType.Colon);
        return{
            kind: Ast.DefintionType.ConstantDefinition,
            declaration: this.parseVarDecl(id_tk, false),
        };
    }

    parseStructureDefinition(){
        console.log("Not Implemented")
        Deno.exit(1)
    }

    private parseParams(delimiter = TokenType.Comma, end = TokenType.Rparen): Array<Ast.NameTypePair>{
        const args: Array<Ast.NameTypePair> = [];

        while(this.lexer.peek_next().kind != end){
            const name = this.expect(TokenType.Identifier).value
            this.expect(TokenType.Colon)
            const type = this.parseType()

            args.push({name:name, type: type})

            this.declared_identifiers.set(name, {type: type})
            if(this.lexer.peek_next().kind == end) break;

            this.expect(delimiter);
            if(this.lexer.peek_next().kind == TokenType.Newline){this.lexer.next(); continue}
        }
        this.lexer.next();
        return args;
    }

    private parseType(): string{
        const initial = this.lexer.next();
        if(initial.kind == TokenType.Hat){
            return initial.value += this.expect(TokenType.Identifier).value
        }else if(initial.kind == TokenType.Identifier){
            return initial.value
        }else{
            Parser.unexpected_token(initial);
        }
    }


    /*
    Functions for parsing statements
    */

    //the consume first is here mainly to clean ip the conditional block code 
    //so i dont have to consume the do token and can just return the object right away.
    parseStatements(until = [TokenType.End], consume_first=false): Array<Ast.Statement>{
        const result: Array<Ast.Statement> = [];
        if(consume_first) this.lexer.next();
        while(true){
            const initial = this.lexer.next();
            if(until.includes(initial.kind)) return result;
            switch(initial.kind){
                case TokenType.If:
                    result.push(this.parseConditionalBlock(false)); 
                    this.lexer.next(); break;
                case TokenType.While:
                    result.push(this.parseConditionalBlock(true));
                    this.lexer.next(); break;
                case TokenType.Return:
                    result.push({kind: Ast.StatementType.Return, body: this.parseExpression()});
                    break;
                case TokenType.Identifier:{
                    const next = this.lexer.next();
                    if(next.kind == TokenType.Colon) result.push(this.parseVarDecl(initial));
                    else if(next.kind == TokenType.Lparen) result.push(this.parseProcedureInvokation(initial))
                    else if(next.kind == TokenType.SingeEqual){
                        result.push({
                            kind: Ast.StatementType.VariableAssignment,
                            name: initial.value,
                            body: this.parseExpression()
                        });
                    }else{
                        Parser.unexpected_token(next, "After Identifier");
                    }
                    break;
                }
                default:
                    if(initial.kind != TokenType.Newline && initial.kind != TokenType.Semicolon){
                        Parser.unexpected_token(initial);
                    } 
                        
            }

        }
    }

    parseConditionalBlock(isWhile: boolean): Ast.ConditionalBlock{
        return {
            comparison_lhs: this.parseExpression(Parser.comparison_tokens),
            comparison_operator: this.lexer.next().value,
            comparison_rhs: this.parseExpression([TokenType.Do]),
            body: this.parseStatements([TokenType.End], true),
            is_while: isWhile,
            kind: Ast.StatementType.ConditionalBlock,
        }
    }

    parseVarDecl(id_tk: Token, local=true): Ast.VariableDeclaration{
        const type = this.parseType();

        let assignment;
        if(this.lexer.peek_next().kind == TokenType.SingeEqual){
            this.lexer.next(); 
            assignment = this.parseExpression();
        }

        this.declared_identifiers.set(id_tk.value, {type: type});
        if(local) this.addedLocals.push(id_tk.value);

        return {
            name: id_tk.value, 
            kind: Ast.StatementType.VariableDeclaration,
            type: type,
            assignment: assignment,
        };
    }

    /*
    Expression Parsing Functions 
    The parseExpression function will call the others no need to use directly
    from statement / definition parsing at this time
    */

    parseExpression(until: Array<TokenType> = [TokenType.Semicolon, TokenType.Newline, TokenType.End]): Ast.Expression{
        const result: Ast.Expression = {body: [], type: "undefined"};
        while(true){
            const initial_copy = this.lexer.peek_next()
            if(until.includes(initial_copy.kind)) return result;

            const next = this.parseExpressionNode();
            if(next.kind != Ast.ExpressionType.BinaryOp){
                if(result.type != "undefined" && result.type != next.type) Parser.mismatched_type_error(initial_copy);
                result.type = next.type;
            }

            result.body.push(next);
        }
    }

    parseExpressionNode(): Ast.ExpressionNode{
        const initial = this.lexer.next()
        switch(initial.kind){
            case TokenType.Plus: return ({operation: "+", kind: Ast.ExpressionType.BinaryOp});
            case TokenType.Dash: return ({operation: "-", kind: Ast.ExpressionType.BinaryOp});
            case TokenType.SlashForward: return ({operation: "/", kind: Ast.ExpressionType.BinaryOp});
            case TokenType.Asterisk: return ({operation: "*", kind: Ast.ExpressionType.BinaryOp});
            case TokenType.LiteralInt: return {value: initial.value, type: "int", kind: Ast.ExpressionType.Literal};
            case TokenType.LiteralBool: return {value: initial.value, type: "bool", kind: Ast.ExpressionType.Literal};
            case TokenType.LiteralString: return {value: initial.value, type: "^string", kind: Ast.ExpressionType.Literal};
            case TokenType.LiteralFloat: return {value: initial.value, type: "float", kind: Ast.ExpressionType.Literal};
            case TokenType.Identifier:{
                const next = this.lexer.peek_next();

                if(next.kind == TokenType.Lparen) {
                    this.lexer.next();
                    return this.parseProcedureInvokation(initial);
                }

                const info = this.declared_identifiers.get(initial.value) ?? Parser.undeclared_identifier(initial);
                return {name: initial.value, type: info.type, kind: Ast.ExpressionType.VariableUsage};
            }
            case TokenType.Memory:{
                console.log("NOT IMPLEMENTED");
                Deno.exit(1);
                break;
            }
            default:
                Parser.unexpected_token(initial, "In expression.");
        }
    }

    parseProcedureInvokation(id_tk: Token): Ast.ProcedureInvokation{  
        const result: Partial<Ast.ProcedureInvokation> = {
            name: id_tk.value, 
            kind: Ast.ExpressionType.ProcedureInvokation
        };

        const info = this.declared_identifiers.get(id_tk.value) ?? Parser.undeclared_identifier(id_tk);
        result.type = info.type;
        const args = [];
        while(this.lexer.peek_next().kind != TokenType.Rparen){
            args.push(this.parseExpression([TokenType.Comma, TokenType.Rparen]))
            if(this.lexer.peek_next().kind == TokenType.Rparen) break;
            this.lexer.next()
        }
        this.lexer.next();

        result.args = args;
        
        return result as Ast.ProcedureInvokation;
    }

    /*
    Error message utility functions.
    */

    private static mismatched_type_error(token: Token): never{
        console.log("ERROR: Mismatched types in expression")
        console.log(token_repr(token))
        Deno.exit(1);
    }
    private static undeclared_identifier(token: Token): never{
        console.log("ERROR: Undeclared Identifier")
        console.log(token_repr(token))
        Deno.exit(1);
    }
    private static unexpected_token(token: Token, extra?:string): never{
        console.log("ERROR: Unexpected Token " + (extra !== undefined ? extra : ""))
        console.log(token_repr(token))
        Deno.exit(1);
    }
}