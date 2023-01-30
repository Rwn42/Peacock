import * as Ast from "./ast.ts";

export function CompileASTToWasm(ast: Ast.AST, output_path: string){
    const procs = [];
    const constants = [];
    const public_signatures = [];
    const externalFunctions = []

    for(const node_key in ast){
        const node = ast[node_key];
        switch(node.kind){
            case Ast.DefintionType.Procedure:{
                const [proc, pub_sig] = compileProcedure(node as Ast.Procedure);
                procs.push(proc);
                public_signatures.push(pub_sig);
                break;
            }
            case Ast.DefintionType.EnvironmentDeclaration:{
                const casted_node = node as Ast.EnvironmentDeclaration;
                let signature = `(func $${node.name} `;
                casted_node.params?.forEach(param => {
                    signature += `(param $${param.name} ${wasmType(param.type)})`
                })
                if(casted_node.return_type) signature += `(result ${wasmType(casted_node.return_type)})`;
                
                externalFunctions.push(`(import "env" "${node.name}" ${signature} ))`);
                break;
            }
            case Ast.DefintionType.ConstantDefinition:{
                break;
            }
        }
    }

    const result = 
    '(module\n' +
    externalFunctions.join("\n") +
    "(memory 1)\n" +
    '(export "memory" (memory 0))\n' +
    public_signatures.join("\n") +
    procs.join("\n") + ")";
    //EXTERN SIGNATURES HERE BEFORE MEMORY
    Deno.writeTextFile(output_path, result);
}

function compileProcedure(node: Ast.Procedure): Array<string>{
    let proc_code = `(func $${node.name}\n`
    const public_signature = `(export "${node.name}"` + proc_code + '))\n';
    node.params?.forEach(param => {
        proc_code += `(param $${param.name} ${wasmType(param.type)})`
    })
    if(node.return_type) proc_code += `(result ${wasmType(node.return_type)})\n`;
    
   

    node.body.forEach(statement => proc_code += compileStatement(statement) + " \n");

    proc_code += ")";

    return [proc_code, node.is_public ? public_signature : ""];
}

function compileStatement(node: Ast.Statement): string{
    switch(node.kind){
        case Ast.StatementType.Return:
            return compileExpression((node as Ast.Return).body) + "return";
        case Ast.StatementType.VariableDeclaration:{
            let result = `(local $${node.name} ${wasmType(node.type)})\n`;
            if((node as Ast.VariableDeclaration).assignment){
                result += compileExpression((node as Ast.VariableDeclaration).assignment as Ast.Expression);
                result += `\nlocal.set $${node.name} \n`;
            } 
            return result;
        }
        case Ast.StatementType.VariableAssignment: {
            let result = ""
            result += compileExpression((node as Ast.VariableAssignment).body);
            result += `\nlocal.set $${node.name} \n`;
            return result;
        }
        case Ast.StatementType.ConditionalBlock: {
            node = node as Ast.ConditionalBlock;
            let result = "";
            if(node.is_while){
                result += "(loop"
                result += node.body.map(s => compileStatement(s)).join("\n");
                result += compileExpression(node.comparison_lhs);
                result += compileExpression(node.comparison_rhs);
                result += compileComparisonOperator(node.comparison_operator, node.comparison_lhs.type);
            }else{
                result += compileExpression(node.comparison_lhs);
                result += compileExpression(node.comparison_rhs);
                result += compileComparisonOperator(node.comparison_operator, node.comparison_lhs.type);
                result += "(if (then\n"
                result += node.body.map(s => compileStatement(s)).join("\n");
                result += ")\n"
            }
            result += ")\n"
            return result;
        }
        case Ast.ExpressionType.ProcedureInvokation:
            return compileProcedureInvokation(node);
        default:
            Deno.exit(1);
    }
}

function compileComparisonOperator(op: string, type: string): string {
    switch(op){
        case ">":
            return `${wasmType(type)}.gt_u\n`;
        case "<":
            return `${wasmType(type)}.lt_u\n`;
        case ">=":
            return `${wasmType(type)}.ge_u\n`;
        case "<=":
            return `${wasmType(type)}.le_u\n`;
        case "==":
            return `${wasmType(type)}.eq\n`;
        case "!=":
            return `${wasmType(type)}.ne\n`;
        default:
            console.error("Unkwown Comparison operator (implementation error)", op);
            Deno.exit(1);

    }
}

function compileExpression(node: Ast.Expression): string{
    const result: Array<string> = [];
    node.body.forEach(exprNode => {
        switch(exprNode.kind){
            case Ast.ExpressionType.Literal:
                if(exprNode.type == "^string"){
                    console.log("Strings Not Yet Supported!");
                    Deno.exit(1);
                }
                result.push(`${wasmType(exprNode.type)}.const ${exprNode.value}\n`); break;
            case Ast.ExpressionType.BinaryOp:{
                switch(exprNode.operation){
                    case "+":
                        result.push(`${wasmType(node.type)}.add\n`); break;
                    case "-":
                        result.push(`${wasmType(node.type)}.sub\n`); break;
                    case "*":
                        result.push(`${wasmType(node.type)}.mul\n`); break;
                    case "/":
                        result.push(`${wasmType(node.type)}.div\n`); break;
                }
                break;
            }
            case Ast.ExpressionType.VariableUsage:
                result.push(`local.get $${exprNode.name}\n`); break;
            case Ast.ExpressionType.ProcedureInvokation:
                compileProcedureInvokation(exprNode);

        }
    });
    return result.join("\n")
}

function compileProcedureInvokation(node: Ast.ProcedureInvokation): string{
    let result = node.args.map(arg => compileExpression(arg)).join("");
    result += `call $${node.name}\n`;
    return result;
}

function wasmType(type: string): string{
    if(type == "float") return "f32";
    return "i32";
}