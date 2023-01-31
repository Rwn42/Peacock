//---AST Type Defintions: Expressions---

export enum ExpressionType{
    ProcedureInvokation, //THIS HAS TO BE FIRST BECAUSE ITS USED IN ANOTHER ENUM THAT STARTS AT 1
    Literal,
    VariableUsage,
    MemoryAllocation,
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

export interface MemoryAllocation{
    kind: ExpressionType.MemoryAllocation,
    amount: Expression,
    size_of?: number,
    type: string,
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

export type ExpressionNode = 
    |ProcedureInvokation 
    | Literal 
    | VariableUsage 
    | MemoryLoad 
    | BinaryOp
    | MemoryAllocation

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




export type Statement = 
    | ConditionalBlock
    | VariableAssignment
    | VariableDeclaration
    | MemoryStore
    | ProcedureInvokation
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
    StructureDefinition,
    ConstantDefinition,
    EnvironmentDeclaration,
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

export interface ConstantDeclaration{
    kind: DefintionType.ConstantDefinition,
    declaration: VariableDeclaration,
}

export interface EnvironmentDeclaration{
    name: string,
    params?: Array<NameTypePair>
    return_type?: string,
    kind: DefintionType.EnvironmentDeclaration
}


export type Definition = 
    |Procedure
    | StructureDefinition
    | ConstantDeclaration
    | EnvironmentDeclaration;

//----------------------------------//

export type AST = Array<Definition>