export enum TokenType{
    LiteralInt,
    LiteralFloat,
    LiteralBool,
    LiteralString,
    Identifier,
    Plus,
    Dash,
    SlashForward,
    Asterisk,
    LessThan,
    LessThanEqual,
    GreaterThan,
    GreaterThanEqual,
    SingeEqual,
    DoubleEqual,
    NotEqual,
    ExclamationMark,
    Lparen,
    Rparen,
    Semicolon,
    Colon,
    Comma,
    Dot,
    Hat,
    If,
    Do,
    While,
    Proc,
    End,
    Return,
    Memory,
    Alloc,
    Struct,
    Const,
    Pub,
    Newline,
    EOF,
    Environment,
}

export interface Token{
    kind: TokenType,
    value: string,
    row: number,
    col: number,
    filename: string,

}

export const token_repr = function(t: Token): string {
    const type = TokenType[t.kind];
    let repr = `${t.value} at line: ${t.row+1} col: ${t.col+1}\n`
    repr += `   The token was parsed as type ${type}`
    return repr;
}

type FilterFunction = (x: string) => boolean;

const keywords = new Map<string, TokenType>([
    ["if", TokenType.If],
    ["do", TokenType.Do],
    ["while", TokenType.While],
    ["end", TokenType.End],
    ["proc", TokenType.Proc],
    ["return", TokenType.Return],
    ["pub", TokenType.Pub],
    ["memory", TokenType.Memory],
    ["alloc", TokenType.Alloc],
    ["struct", TokenType.Struct],
    ["const", TokenType.Const],
    ["environment", TokenType.Environment],

])


export class Lexer{
    filestring: string
    filename: string
    pos: number
    row: number
    col: number
    constructor(filestring: string, filename: string){
        this.filestring = filestring;
        this.filename = filename;
        this.pos = 0;
        this.row = 0;
        this.col = 0;
    }
    
    //returns a token based on current state of the lexer
    private newToken(initial_value: string, type?:TokenType): Token{
        return {
            kind: type ?? TokenType.Identifier,
            value:initial_value, 
            row: this.row, col: this.col, 
            filename: this.filename
        };
    }

    //returns current character pointed to by the lexer and moves on
    private char(): string{
        const c = this.filestring[this.pos];
        this.advance();
        return c;

    }
    
    //returns current character but does not advance the lexer
    private peek(): string | null {
        if(this.pos > this.filestring.length-1) return null;
        return this.filestring[this.pos];
    }

    //moves the lexer to the next position
    private advance() {
        this.pos += 1
        this.col += 1
    }

    //skips until the first non-whitespace character return result indicates if at eof
    private skipWhitespace(): boolean{
        while(true){
            if(!this.peek()) return true;
            if(!/\s/.test(this.peek() as string)) return false;
            this.advance()
        }

    }

    //while the provided function is true collect characters
    private get_characters_while(filter_function: FilterFunction): Array<string>{
        const result = []
        while(true){
            if(this.peek() == null || !filter_function(this.peek() as string)) break;
            result.push(this.char())
        }
        return result;
    }



    next(): Token{

        if(this.peek()){
            if(this.peek() == "\n"){
                this.advance();
                this.row += 1;
                this.col = 0;
                return this.newToken("\n", TokenType.Newline)
            }
        }else{
            return this.newToken("eof", TokenType.EOF)
        }

        if(this.skipWhitespace()) return this.newToken("eof", TokenType.EOF);

        const first_character = this.char();
        const token = this.newToken(first_character);

        switch(first_character){
            case "\"":
                token.value = this.get_characters_while((x)=> x != "\"").join("");
                this.advance()
                token.kind = TokenType.LiteralString;
                break;
            case "#":
                this.get_characters_while((x)=> x != "\n");
                this.advance()
                return this.next()
            case ">": 
                token.kind = (this.peek() == "=" ? TokenType.LessThanEqual : TokenType.LessThan);
                token.value += this.char();
                break;
            case "<":
                token.kind = (this.peek() == "=" ? TokenType.GreaterThanEqual : TokenType.GreaterThan);
                token.value += this.char();
                break;
            case "=":
                token.kind = (this.peek() == "=" ? TokenType.DoubleEqual : TokenType.SingeEqual);
                token.value += this.char();
                break;
            case "!":
                token.kind = (this.peek() == "=" ? TokenType.NotEqual : TokenType.ExclamationMark);
                token.value += this.char();
                break;
            case "(": token.kind = TokenType.Lparen; break;
            case ")": token.kind = TokenType.Rparen; break;
            case ";": token.kind = TokenType.Semicolon; break;
            case ":": token.kind = TokenType.Colon; break;
            case "^": token.kind = TokenType.Hat; break;
            case "+": token.kind = TokenType.Plus; break;
            case ".": token.kind = TokenType.Dot; break;
            case ",": token.kind = TokenType.Comma; break;
            case "-":{
                if(!this.peek()){token.kind = TokenType.Dash; break}
                if(/[0-9]/.test(this.peek() as string)){
                    token.value += this.get_characters_while((x)=>/^\d*\.?\d*$/.test(x)).join("");
                    token.kind = token.value.includes(".") ? TokenType.LiteralFloat : TokenType.LiteralInt;
                }else{
                    token.kind = TokenType.Dash;
                }
                break;
            }
            case "/": token.kind = TokenType.SlashForward; break;
            case "*": token.kind = TokenType.Asterisk; break;
            default:
                //check for integer or float
                if(/[0-9]/.test(first_character)){
                    token.value += this.get_characters_while((x)=>/^\d*\.?\d*$/.test(x)).join("")
                    token.kind = token.value.includes(".") ? TokenType.LiteralFloat : TokenType.LiteralInt;
                    return token;
                }

                //if it wasnt that it is a keyword or identifier
                token.value += this.get_characters_while((x)=>/^[\w-]+$/.test(x)).join("")

                if(token.value == "true" || token.value == "false"){
                    token.kind = TokenType.LiteralBool;
                    return token;
                }
                
                token.kind = keywords.get(token.value) ?? TokenType.Identifier;

        }
        
        return token;
    }

    //returns the next token but does not advance the lexer
    peek_next(){
        const pos = this.pos;
        const row = this.row;
        const col = this.col;
        const result = this.next();
        this.pos = pos;
        this.row = row;
        this.col = col;
        return result;
    }
    
}