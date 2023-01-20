//---AST Type Defintions: Expressions---

export enum ExpressionType{
    ProcedureInvokation, //THIS HAS TO BE FIRST BECAUSE ITS USED IN ANOTHER ENUM THAT STARTS AT 1
    Literal,
    VariableUsage,
    MemoryLoad,
    BinaryOp,
}

export interface ProcedureInvokation{
    name: string,
    args: Array<Expression>,
    type: string,
    kind: ExpressionType.ProcedureInvokation,
}
``
export interface Literal{
    value: string,
    type: string;
    kind: ExpressionType.Literal,
}

export interface VariableUsage{
    name: string,
    type: string,
    kind: ExpressionType.VariableUsage,
}

export interface MemoryLoad{
    offset: Expression | string,
    identifier: string,
    type: string,
    //multiplier for offset not size of load
    sizeof: number,
    kind: ExpressionType.MemoryLoad,
}

export interface BinaryOp{
    operation: string,
    kind: ExpressionType.BinaryOp,
}

export type ExpressionNode = ProcedureInvokation | Literal | VariableUsage | MemoryLoad | BinaryOp

export interface Expression{
    body: Array<ExpressionNode>;
    type: string;
}

//----------------------------------//

//---Ast Type Defintions: Statements---

export enum StatementType{
    ConditionalBlock = 1,
    VariableDeclaration,
    VariableAssignment,
    Return,
    MemoryStore,
    MemoryDeclaration,
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
    offset: Expression | string,
    body: Expression,
    //multiplier for offset not size of load (for now)
    sizeof: number,
    type: string, 
    kind: StatementType.MemoryStore,
}

//can be in statement or defintion
//if encountered in procedure will be assumed a statement
export interface MemoryDeclaration{
    name: string,
    type: string,
    sizeof: number,
    amount: Expression,
    cleanup: boolean
    kind: StatementType | DefintionType,
}



export type Statement = 
    | ConditionalBlock
    | VariableAssignment
    | VariableDeclaration
    | MemoryStore
    | ProcedureInvokation
    | MemoryDeclaration
    | Return;

//----------------------------------//

//---Ast Type Defintions: Definitions (top level code)---

export interface NameTypePair {
    name: string,
    type: string,
}

export enum DefintionType{
    Procedure,
    MemoryDeclaration,
    StructureDefinition
}   

export interface Procedure{
    name: string,
    is_public: boolean,
    //variable usage is here because it contains a name and a type
    params?: Array<NameTypePair>
    return_type?: string
    body: Array<Statement>
    kind: DefintionType.Procedure
}

export interface StructureDefinition{
    kind: DefintionType.StructureDefinition,
    name: string,
    fields: Array<NameTypePair>,
}



export type Definition = Procedure | MemoryDeclaration | StructureDefinition;

//----------------------------------//

export type AST = Array<Definition>