import * as Ast from "./ast.ts";

export class WasmCompiler{
    ast: Ast.AST;
    functions: Array<string>;
    exports: Array<string>;
    imports: Array<string>;
    constants: Array<string>;
    string_literals: Array<string>;
    constant_identifiers: Array<string>;
    memory_head: number;
    loops_added: number

    constructor(ast: Ast.AST){
        this.ast = ast;
        this.functions = [];
        this.exports = [];
        this.imports = [];
        this.constants = [];
        this.string_literals = [];
        this.constant_identifiers = [];
        this.memory_head = 4;
        this.loops_added = 0;
    }

    async compile(){
        for(const node_key in this.ast){
            const node = this.ast[node_key];
            switch(node.kind){
                case Ast.DefintionType.Procedure:
                    this.compileProcedure(node as Ast.Procedure);
                    break;
                case Ast.DefintionType.EnvironmentDeclaration:
                    this.compileEnvironment(node as Ast.EnvironmentDeclaration);
                    break;
                case Ast.DefintionType.ConstantDefinition:
                    await this.compileConstant(node as Ast.ConstantDeclaration);
                    break;
                    
            }
        }
    }

    //UTILITY

    linear_write_num(wasm_type: string, value: number): string{
        let write_code = `global.get $mem_head\n${wasm_type}.const ${value}\n`;
        write_code += `${wasm_type}.store\n`;
        let memory_inc = `i32.const 4\nglobal.get $mem_head i32.add\n`;
        memory_inc += "global.set $mem_head\n";
        return write_code + memory_inc;
    }

    compileProcedure(proc: Ast.Procedure){
        const proc_code = [`(func $${proc.name}`];
        const public_signature = `(export "${proc.name}"` + proc_code + '))\n';

        proc.params?.forEach(
            param => 
            proc_code.push(`(param $${param.name} ${wasmType(param.type)})`)
        );

        if(proc.return_type) 
            proc_code.push(`(result ${wasmType(proc.return_type)})`);
        

        const decls = proc.body.filter(s => s.kind == Ast.StatementType.VariableDeclaration);
        decls.forEach( node => {
            const decl = node as Ast.VariableDeclaration;
            proc_code.push(`(local $${decl.name} ${wasmType(decl.type)})`)
        });   
    

        //the reason for the get and set between the body is to restore
        //the mem head to its previous position (freeing memory used by the proc)
        //proc_code.push("global.get $mem_head");
        proc.body.forEach(
            statement => proc_code.push(this.compileStatement(statement))
        );
        //proc_code.push("global.set  $mem_head")

        proc_code.push(")");

        if(proc.is_public) this.exports.push(public_signature);
        this.functions.push(proc_code.join("\n"));
    }

    compileEnvironment(node: Ast.EnvironmentDeclaration){
        let signature = `(func $${node.name} `;
        node.params?.forEach(param => {
            signature += `(param $${param.name} ${wasmType(param.type)})`
        })
        if(node.return_type) signature += `(result ${wasmType(node.return_type)})`;
        
        this.imports.push(`(import "env" "${node.name}" ${signature} ))`);
    }

    async compileConstant(node: Ast.ConstantDeclaration){
        const {name, type, assignment} = node.declaration;
        this.constant_identifiers.push(name);
        const assign = assignment as Ast.Expression;
        const value = await this.comptimeEval(assign);
        this.constants.push(`(global $${name} ${wasmType(type)} (${wasmType(assign.type)}.const ${value}))`);
    }

    compileStatement(node: Ast.Statement): string{
        const result: Array<string> = [];
        switch(node.kind){
            case Ast.StatementType.Return:
                result.push(this.compileExpression((node as Ast.Return).body))
                result.push("return");
                break;
            case Ast.ExpressionType.ProcedureInvokation:{
                const pi = node as Ast.ProcedureInvokation;
                pi.args.forEach(arg => result.push(this.compileExpression(arg)));
                result.push(`call $${pi.name}`);
                break;
            }

            case Ast.StatementType.VariableDeclaration:{
                const decl = node as Ast.VariableDeclaration;
                if(decl.assignment){
                    result.push(this.compileExpression((decl).assignment as Ast.Expression));
                    result.push(`\nlocal.set $${node.name}`);
                }
                break;
            }
            case Ast.StatementType.VariableAssignment:{
                const assign = node as Ast.VariableAssignment;
                result.push(this.compileExpression((assign).body as Ast.Expression));
                result.push(`\nlocal.set $${node.name}`);
                break;
            }
            case Ast.StatementType.ConditionalBlock:{
                result.push(this.compileConditional(node as Ast.ConditionalBlock));
            }
        }
        return result.join("\n")
    }
    
    compileConditional(node: Ast.ConditionalBlock): string{
        const result = [];
        if(node.is_while){
            const loop_id = this.loops_added++;
            result.push(`(loop $${loop_id}`);
            node.body.forEach(s => result.push(this.compileStatement(s)));
            result.push(this.compileExpression(node.comparison_lhs))
            result.push(this.compileExpression(node.comparison_rhs))
            result.push(compileComparisonOperator(
                node.comparison_operator, node.comparison_lhs.type
            ));
            result.push(`br_if $${loop_id}`)
        }else{
            result.push(this.compileExpression(node.comparison_lhs))
            result.push(this.compileExpression(node.comparison_rhs))
            result.push(compileComparisonOperator(
                node.comparison_operator, node.comparison_lhs.type
            ));
            result.push("(if");
            result.push("(then");
            node.body.forEach(s => result.push(this.compileStatement(s)));
            result.push(")");
        }
        result.push(")");
        return result.join("\n");
    }

    compileExpression(expr: Ast.Expression){
        const result: Array<string> = [];
        expr.body.forEach(node => {
            switch(node.kind){
                case Ast.ExpressionType.BinaryOp: 
                    result.push(compileBinaryOp(node, wasmType(expr.type)));
                    break;
                case Ast.ExpressionType.VariableUsage:
                    if(this.constant_identifiers.includes(node.name)){
                        result.push(`global.get $${node.name}`);
                    }else{
                        result.push(`local.get $${node.name}`);
                    }
                    break;
                case Ast.ExpressionType.ProcedureInvokation:
                    node.args.forEach(arg => result.push(this.compileExpression(arg)));
                    result.push(`call $${node.name}`);
                    break;
                case Ast.ExpressionType.Literal:
                    if(node.type != "^string"){
                        result.push(`${wasmType(node.type)}.const ${node.value}\n`);
                        break;
                    }
                    this.string_literals.push('"' + node.value + '"');

                    result.push(`global.get $mem_head`);
                    
                    //push the string `struct values` into linear memory
                    result.push(this.linear_write_num("i32", this.memory_head));
                    result.push(this.linear_write_num("i32", node.value.length));
                    
                    
                    
                    //increment comptime memory head by string length
                    this.memory_head += node.value.length;
                    break;
                case Ast.ExpressionType.MemoryLoad:
                    console.error("Memory Load Not Implemented. ");
                    Deno.exit(1);
                    break;
            }
        });
        return result.join("\n")
    }
    //TODO get wasm2wat path from config
    async comptimeEval(expr: Ast.Expression): Promise<number>{
        const source_text = `
        (module
            (export "main"(func $main))
            ${this.constants.join("\n")}
            (func $main (result ${wasmType(expr.type)})
                ${this.compileExpression(expr)}
            )
        )
        `;

        await Deno.writeTextFile("comptime.wat", source_text);

        const p = Deno.run({cmd: ["/home/rwn/tools/wabt-1.0.32/bin/wat2wasm", "./comptime.wat"]});
        await p.status()

        const wasmFile = await Deno.readFile("comptime.wasm");
        const module = new WebAssembly.Module(wasmFile)
        const instance = new WebAssembly.Instance(module, {});
        
        const func = instance.exports.main as CallableFunction;
        const res: number = func();

        Deno.remove("comptime.wat")
        Deno.remove("comptime.wasm")

        return res
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

function compileBinaryOp(op: Ast.BinaryOp, wasmType:string): string{
    switch(op.operation){
        case "+":
            return `${wasmType}.add`;
        case "-":
            return `${wasmType}.sub`;
        case "*":
            return `${wasmType}.mul`;
        case "/":
            return `${wasmType}.div`;
        default:
            console.error("Unimplemented Binary Operation ", op.operation);
            Deno.exit(1);
    }  
}






function wasmType(type: string): string{
    if(type == "float") return "f32";
    return "i32";
}


export function saveAsWat(compiler: WasmCompiler, filepath: string){
    let result = '(module\n';
    result += compiler.imports.join("\n");
    result += "(memory 1)\n";
    result += '(export "memory" (memory 0))\n';
    result += compiler.exports.join("\n");
    result += compiler.constants.join("\n");
    result += `\n(global $mem_head (mut i32) (i32.const ${compiler.memory_head})) \n`;
    result += `(data (i32.const 4) ${compiler.string_literals.join(' ')})\n`;
    result += compiler.functions.join("\n") + ")";
    Deno.writeTextFile(filepath + ".wat", result);
}