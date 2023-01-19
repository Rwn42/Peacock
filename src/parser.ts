import { Lexer, TokenType, Token, token_repr} from "./lexer.ts";
import * as Ast from "./ast.ts"


interface IdentifierInformation{
    type:string,
    sizeof_type?: number, //not size of type on stack for pointers but size of pointed to type
}
/*
TODO:
Static analysis
remove declared identifiers after function body is over
add memory keyword (perhaps static so its exists after function)
structures, enumerations
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

    expect(expectKind: TokenType): Token{
        const token = this.lexer.next();
        if(token.kind != expectKind) Parser.unexpected_token(token);
        return token;
    }

    parse(): Ast.AST{
        const token = this.lexer.next()
        const result: Ast.AST = [];

        switch(token.kind){
            case TokenType.Pub:
                result.push(this.parseProcedureDefinition(true)); break;
            case TokenType.Proc:
                    result.push(this.parseProcedureDefinition(false)); break;
               
        }

        return result;
    }

    /*
    Top Level Defintion Parsing 
    */

    parseProcedureDefinition(is_public: boolean): Ast.Procedure{

        if(is_public) this.expect(TokenType.Proc);

        const name = this.expect(TokenType.Identifier).value
        const args = this.parseParams();
        const return_type = this.lexer.peek_next().kind == TokenType.Do ? undefined : this.parseType();
        this.lexer.next();

        this.declared_identifiers.set(name, {type: return_type || ""})

        const body = this.parseStatements();
        this.lexer.next();
       

        return{
            body: body,
            name: name, 
            params: args || null, 
            return_type: return_type, 
            is_public: is_public,
            kind: Ast.DefintionType.Procedure,
        };
        
    }

    private parseParams(): Array<Ast.NameTypePair>{
        const args: Array<Ast.NameTypePair> = [];

        this.expect(TokenType.Lparen);

        while(this.lexer.peek_next().kind != TokenType.Rparen){
            const name = this.expect(TokenType.Identifier).value
            this.expect(TokenType.Colon)
            const type = this.parseType()

            args.push({name:name, type: type})

            this.declared_identifiers.set(name, {type: type})

            if(this.lexer.peek_next().kind == TokenType.Rparen) break;

            this.expect(TokenType.Comma);
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
                    if(next.kind == TokenType.Dot) result.push(this.parseMemoryStore(initial));
                    else if(next.kind == TokenType.Colon) result.push(this.parseVarDecl(initial));
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
                    if(initial.kind != TokenType.Newline) Parser.unexpected_token(initial);
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
    
    parseMemoryStore(id_tk: Token): Ast.MemoryStore{
        const result: Partial<Ast.MemoryStore> = {identifier: id_tk.value, kind: Ast.StatementType.MemoryStore};
        const next = this.lexer.next();
        if(next.kind == TokenType.Lparen){
            const info = this.declared_identifiers.get(id_tk.value) ?? Parser.undeclared_identifier(id_tk);
            result.type = info.type;
            result.sizeof = info.sizeof_type;
            result.offset = this.parseExpression([TokenType.Rparen])
            this.lexer.next();
        }else if(next.kind == TokenType.Identifier){
            const info = this.declared_identifiers.get(next.value) ?? Parser.undeclared_identifier(next);
            result.type = info.type;
            result.sizeof = info.sizeof_type;
            result.offset = next.value;
        }else{
            Parser.unexpected_token(next);
        }
        this.expect(TokenType.SingeEqual);
        result.body = this.parseExpression();
        return result as Ast.MemoryStore;
    }

    parseVarDecl(id_tk: Token): Ast.VariableDeclaration{
        const type = this.parseType();

        let assignment;
        if(this.lexer.peek_next().kind == TokenType.SingeEqual){
            this.lexer.next(); 
            assignment = this.parseExpression();
        }

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

                if(next.kind == TokenType.Dot) return this.parseMemoryLoad(initial);
                if(next.kind == TokenType.Lparen) return this.parseProcedureInvokation(initial);

                const info = this.declared_identifiers.get(initial.value) ?? Parser.undeclared_identifier(initial);
                return {name: initial.value, type: info.type, kind: Ast.ExpressionType.VariableUsage};
            }
            default:
                Parser.unexpected_token(initial, "In expression.");
        }
    }

    parseMemoryLoad(id_tk: Token): Ast.MemoryLoad{
        this.lexer.next();
        const next = this.lexer.next();
        const result: Partial<Ast.MemoryLoad> = {identifier: id_tk.value, kind: Ast.ExpressionType.MemoryLoad};
        // x.(y): array access at pos y
        if(next.kind == TokenType.Lparen){
            const info = this.declared_identifiers.get(id_tk.value) ?? Parser.undeclared_identifier(id_tk);
            result.type = info.type;
            result.sizeof = info.sizeof_type;
            result.offset = this.parseExpression([TokenType.Rparen])
            this.lexer.next();
        //x.y: structure access
        }else if(next.kind == TokenType.Identifier){
            const info = this.declared_identifiers.get(next.value) ?? Parser.undeclared_identifier(next);
            result.type = info.type;
            result.sizeof = info.sizeof_type;
            result.offset = next.value;
            
        }else{
            Parser.unexpected_token(next);
        }
        return result as Ast.MemoryLoad;
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