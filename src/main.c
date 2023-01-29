#include <stdio.h>
#include "include/cli.h"


 // peacock <subcommand> <input_file> <options>
int main(int argc, const char** argv){
    CLIOptions options = new_CLI_options(argc, argv);
    printf("%s %s %d\n", options.input_file, options.output_file, options.mode);
}

