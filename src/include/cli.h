#pragma  once

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

typedef enum {
    COMPILE_IR,
    COMPILE_WASM32,
    COMPILE_PVM,
    PARSE,
    LEX,
}CLIMode;

typedef struct {
    CLIMode mode;
    const char* input_file;
    const char* output_file;
} CLIOptions;   


CLIOptions new_CLI_options(int argc, const char** argv);
const char* flag_value(int argc, int expected_index, const char** argv);
void print_help();