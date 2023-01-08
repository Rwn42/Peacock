# Peacock
Language that compiles to web-assembly. served as a learning experience to learn about wasm/wat.

## The Hello World
```
extern puts(x int, y int) end

pub proc main() do
    puts("Hello, world")
end
```

## Future plans
- [x] improve lexer (make newlines tokens, tokenize . correctly)
- [x] implement better type system (types should have size, pointers ect.)
- [x] maybe implement a rudimentry AST before compilation
(not an ast but we did some parsing so ill mark as complete)
- [x] implement local memory so the lm_head moves back at the end of the function
- [] compile to IR so I could make a custom interpreter if i wanted
- [x] implement load/store operator for linear memory
- [] remove structs in favour of a standard library implementation using load/store instructions
- [] implement more on strings allowing passing to functions ect.
    (note for me we cant treat strings as struct because using linear memory
    instead of pushing length onto stack seems like a bad idea. current idea is make String type a macro for (start: int, length: int)
- [] add ability to include other files perhaps with namespacing
- [] improve environment move to a node environment to allow for file reading ect
- [] string methods such as compare, length ect
- [] dynamic memory allocation (unlikely to get here but would be cool)
- [] better cli
- [] re-write in compiled language (rust probably, maybe c++ or go tho.)

## Quickstart
the language currently only supports a custom WASM environment (the js code is included). Additionally, it compiles to .wat files so a tool like wat2wasm will be required.

### A note on WASI
originally I was targetting a wasi interface but I found the project more fun, easier and more flexible if I made my own JS envrironment. WASI support is not ruled out for the future.

### Building and Running
compile command: <br>
`python src/main.py examples/test.pk`<br>
`wat2wasm output.wat`<br>
`mv output.wasm web-env/output.wasm`
running:
```sh
cd web-env
python -m http.server 8080
```
navigate to the provided link



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

### While Loop
```
i: int = 10
while i < 10 do
    i = i 1 +
end
```

### Variables
declaration: `name:type` <br>
assignment: `name = expression` <br>
declaration and assignment: `name:type = expression `

### Constants (Not Implemented in Current Version)
declaration: `name:type:value end` <br>

### Functions
```
proc add(x int, y int) int do
    return x y +
end
```
by adding the `pub` keyword a function is visible
to the host environment.

### Extern Keyword
Since web-assembly supports calling functions from other environments such as JavaScript or the runtime like wasmtime the extern keyword gives the compiler nessecary information about functions you may call from the host environment.
`extern some_function(x int, y int) int end`


### Memory
the memory keyword statically allocates some linear memory.
the `x` identifier in this case is a pointer to the start
```
extern puti(x int) end

proc main() do 
    //allocate 10 integers or 40 bytes (the size must be known at compile time)
    //dynamic allocation not yet supported
    memory x int 10

    //store 10 at position 0 in the allocated chunk
    x.0 <- 10

    //accesses position 0 and print
    puti(x.0)
end
```