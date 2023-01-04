# Peacock
Stack-based, concatenative language that compiles (hopefully) to wasi compliant web assembly.

## The Hello World
```
extern fd_write(x:int, y:int, z:int, w:int) int end

proc main() do
    _:int = fd_write("Hello, world\n", 1, 0, 1, 20)
end
```

## Quickstart
the language currently only supports WASI compliant WASM runtimes such as wasmtime. Additionally, it compiles to .wat files so a tool like wat2wasm may be required for non wasmtime runtimes. (wasmtime can run wat files)

compile command: <br>
`python src/main.py examples/test.pk`<br>
running:<br>
`wasmtime output.wat`



## Overview

### Expressions
expressions are written in reverse polish notation.
`5 4 +` -> is equivalent to 5 + 4 in a normal language
note only normal expressions behave this way
comparison, variable assignment, function calls ect
all behave as you would expect.

### If-Else
```
if 3 2 + == 4 1 + do
    ...
else
    ...
end
```

### Variables
declaration: `name:type` <br>
assignment: `name = expression` <br>
declaration and assignment: `name:type = expression`

### Functions
```
proc add(x:int, y:int) int do
    x y +
end
```

### Extern Keyword
Since web-assembly supports calling functions from other environments such as JavaScript or the runtime like wasmtime the extern keyword gives the compiler nessecary information about functions you may call from the host environment.
`extern some_function(x:int, y:int) int end`



