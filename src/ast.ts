//---AST Type Defintions: Expressions---

export interface ProcedureInvokation{
    name: string,
    args: Array<Expression>,
    type: string,
}

export interface Literal{
    value: string,
    type: string;
}

export interface VariableUsage{
    name: string,
    type: string,
}

export interface MemoryLoad{
    offset?: Expression
    identifier: string
    type: string,
    sizeof: number,
}

export type Operation = string;

export type ExpressionNode = ProcedureInvokation | Literal | VariableUsage | MemoryLoad | Operation

export interface Expression{
    body: Array<ExpressionNode>;
    type: string;
}

//----------------------------------//

//---Ast Type Defintions: Statements---


//----------------------------------//


