//---AST Type Defintions: Expressions---

export interface ProcedureInvokation{
    name: string,
    args: Array<Expression>,
    type: string,
}
``
export interface Literal{
    value: string,
    type: string;
}

export interface VariableUsage{
    name: string,
    type: string,
}

export interface MemoryLoad{
    offset: Expression
    identifier: string
    type: string,
    //size of the type because offset is not in bytes
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

export enum StatementType{
    ConditionalBlock,
    VariableDeclaration,
    VariableAssignment,
    Return,
    MemoryStore,
}

export interface ConditionalBlock{
    is_while: boolean,
    comparison_lhs: Expression,
    comparison_rhs: Expression,
    comparison_operator: string,
    body: Array<Statement>,
    kind: StatementType.ConditionalBlock,
}


export interface VariableDeclaration{
    name: string,
    type: string,
    assignment?: Expression,
    kind: StatementType.VariableDeclaration,
}

export interface VariableAssignment{
    name: string,
    body: Expression,
    kind: StatementType.VariableAssignment,
}

export interface Return{
    body: Expression,
    kind: StatementType.Return,
}

export interface MemoryStore{
    identifier: string,
    offset: Expression,
    body: Expression,
    sizeof: number,
    type: string, 
    kind: StatementType.MemoryStore,
}




export type Statement = ConditionalBlock | VariableAssignment | VariableDeclaration | MemoryStore | Return;

//----------------------------------//

//---Ast Type Defintions: Definitions (top level code)---

export enum DefintionType{
    Procedure,
}   

export interface Procedure{
    name: string,
    is_public: boolean,
    //variable usage is here because it contains a name and a type
    params?: Array<VariableUsage>
    return_type?: string
    body: Array<Statement>
    kind: DefintionType.Procedure
}



export type Definition = Procedure

//----------------------------------//

export type AST = Array<Definition>