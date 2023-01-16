import { argv, exit } from "process"

//config interface for cli
interface Config{
    input_file: string
    action: string
    output_file:string
    target:string
}


//compile, lex and parse
const compilation_step_flags = ["-c", "-l", "-p"];

//supported targets
const compilation_targets = ["pvm", "wasm32"];

//prints the error message and exits the program
const print_error = function(msg: string) {
    console.error(msg);
    exit(1)
}

const main = function(){
    if(argv.length < 3){
        print_error("ERROR: No Input File Specified");
    }
    const user_arguments = argv.slice(2);

    //default configuration options
    const config: Config = {input_file: user_arguments[0], action: "-c", output_file: "output.bin", target: "pvm"}


    //add any specified compiler options
    let i = 1;
    while(true){
        const flag = user_arguments[i] ?? null;
        if(!flag) break;

        if(compilation_step_flags.includes(flag)) config.action = flag;
        else if(flag == "--target"){
            if(!compilation_targets.includes(user_arguments[i + 1])){
                print_error(`ERROR: Unknown or unsupported target ${user_arguments[i + 1]}`)
            }
            config.target = user_arguments[i + 1];
            i++;
        }else if (flag == "-o") config.output_file = user_arguments[++i] || "output.bin";
        else print_error(`ERROR: Unknown compiler option ${flag}`);
        i++;
    }

    if(config.input_file == "--help") print_help();
}

const print_help = function(){
    console.log("To use the compiler use the following format:")
    console.log("<js run command (bun run, node ect)> main.ts <input_file> <options>\n");
    console.log("Example: bun run main.ts my_file.pk --target wasm32 -o output.wasm\n")
    console.log("   Options:")
    console.log("   --target <target>");
    console.log("       Current Targets:")
    compilation_targets.forEach(target => console.log(`        ${target}`))
    console.log("   -o <output_file>");
    console.log("   -c (tells the compiler to do normal compilation)")
    console.log("   -p (tells the compiler to just create the AST)")
    console.log("   -l (tells the compiler to only lex the file)")
}

main();



