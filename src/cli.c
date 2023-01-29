#include "include/cli.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

CLIOptions new_CLI_options(int argc, const char** argv){
    CLIOptions options = {};
    if(argc == 2)
    {
        if(strcmp(argv[1], "help") == 0) print_help();
    }

    if(argc < 3)
    {
        fprintf(stderr, "ERROR: Expected Atleast Two Command Line Arguments\nd");
        exit(1);
    }

    if(strcmp(argv[1], "lex") == 0)
    {
        options.mode = LEX;
    }
    else if (strcmp(argv[1], "parse") == 0)
    {
        options.mode = PARSE;
    }
    else if (strcmp(argv[1], "com") == 0)
    {
        options.mode = COMPILE_WASM32;
    }
    else
    {
        fprintf(stderr, "ERROR: Invalid Compilation Mode %s Expected One of: com, lex, parse\n", argv[1]);
        exit(1);
    }

    options.input_file = argv[2];

    options.output_file = "output.out";

    if(argc < 4) return options;

    //flag parsing
    int flag_idx = 3;
    while(true){
        if(strcmp(argv[flag_idx], "--out") == 0)
        {
            options.output_file = flag_value(argc, ++flag_idx, argv);
        }
        else if(strcmp(argv[flag_idx], "--target")  == 0)
        {
            const char* target_string = flag_value(argc, ++flag_idx, argv);

            //this means we specified the com mode if not equal we tried to specify a target on lex/parse
            if(options.mode != COMPILE_WASM32){
                fprintf(stderr, "ERROR: Target Not Supported When Not Using com subcommand\n");
                exit(1);
            }
            if(strcmp(target_string, "wasm32") == 0){
                options.mode = COMPILE_WASM32;
            }else if(strcmp(target_string, "pvm") == 0){
                options.mode = COMPILE_PVM;
            }else if(strcmp(target_string, "ir") == 0){
                options.mode = COMPILE_IR;
            }else{
                fprintf(stderr, "ERROR: Unknown Target %s\n", target_string);
                exit(1);
            }
        }
        else
        {
            fprintf(stderr, "ERROR: Unknown Compiler Flag %s\n", argv[flag_idx]);
            exit(1);
        }
        if(argc <= flag_idx+1) break;
        flag_idx++;
    }
    return options;
}

const char* flag_value(int argc, int expected_index, const char** argv){
    if(argc < expected_index+1){
        fprintf(stderr, "ERROR: Expected Value After %s flag\n", argv[expected_index-1]);
        exit(1);
    }
    return argv[expected_index];
}

void print_help(){
    printf("Usage: peacock [mode] [input_file] [...options]\n");
    printf("  modes:\n");
    printf("    com -> compiles source code to executable format (defualt wasm32)\n");
    printf("    lex -> writes lexer output to a file mainly for debugging purposes\n");
    printf("    parse -> writes parser output to a file mainly for debugging purposes\n");
    printf("  options:\n");
    printf("    --target: specify compilation target, targets include...\n");
    printf("      wasm32 -> (default) compile to standalone wasm32 wat file\n");
    printf("      pvm -> compile to custom interpreter\n");
    printf("      ir -> compile to intermediate representation text format\n");
    printf("    --out: specify output file path ex. `--out myfile.wat`\n");
    exit(0);
}