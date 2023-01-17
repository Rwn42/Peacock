import { Lexer } from "./lexer.js";


//TODO figure out how to make types for expression nodes
//like funcall, memload, ect.
interface Expression{
    body: Array<string>;
    type: string;
}


export class Parser{
    lexer: Lexer
    declared_identifiers: Map<string, string>
    constructor(lexer: Lexer){
        this.lexer = lexer;
        this.declared_identifiers = new Map();
    }

    expression(){

    }
}