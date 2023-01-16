export enum TokenType{
    LiteralInt,
    LiteralFloat,
    LiteralBool,
    LiteralString,
    Identifier,
    Newline,
    EOF,
}

export interface Token{
    kind: TokenType,
    value: string,
    row: number,
    col: number,
    filename: string,

}

type FilterFunction = (x: string) => boolean;


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
        if(this.pos >= this.filestring.length-1) return null;
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
        let result = []
        while(true){
            if(this.peek() == null || !filter_function(this.peek() as string)) break;
            result.push(this.char())
        }
        return result;
    }



    next(): Token{

        if(this.peek()){
            if(this.peek() == "\n"){
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
        }
        
        return token;
    }
    
}