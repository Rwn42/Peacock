# Peacock
Stack-based, concatenative language that compiles (hopefully) to wasi compliant web assembly.

## The Hello World
```
extern fd_write(x, y, z, w) int end

proc main() do
    fd_write("Hello, world\n", 1, 0, 1, 20)
    drop
end
```
the drop keyword will hopefully be removed when variable declarations are
implemented in favour of syntax such as <br>
`_ = fd_write("Hello, world\n", 1, 0, 1, 20)`

## Quickstart
the language currently only supports WASI compliant WASM runtimes such as wasmtime. Additionally, it compiles to .wat files so a tool like wat2wasm may be required for non wasmtime runtimes. (wasmtime can run wat files)

compile command: <br>
`python src/main.py examples/test.pk`
`wasmtime output.wat`



## Overview

### Expressions
expressions are written in reverse polish notation.
`5 4 +` -> is equivalent to 5 + 4 in a normal language
note only normal expressions behave this way
comparison, variable assignment, function calls ect
all behave as you would expect

### Comparison
`2 3 + == 4 1 +` -> checks if the rhs is equal to the lhs

