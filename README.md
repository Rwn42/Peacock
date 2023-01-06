# Peacock
Stack-based, concatenative language that compiles (hopefully) to web assembly.

## The Hello World
```
extern puts(x:int, y:int) end

pub proc main() do
    puts("Hello, world")
end
```

## Quickstart
the language currently only supports a custom WASM environment (the js code is included). Additionally, it compiles to .wat files so a tool like wat2wasm will be required.

## A note on WASI
originally I was targetting a wasi interface but I found the project more fun, easier and more flexible if I made my own JS envrironment. WASI support is not ruled out for the future.

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
i: int = 10;
while i < 10 do
    i = i 1 +;
end
```

### Variables
declaration: `name:type` <br>
assignment: `name = expression end` <br>
declaration and assignment: `name:type = expression end`
**Instead of `end` `;` is also supported to end variable assignments**

### Constants
declaration: `name:type:value end` <br>

### Functions
```
proc add(x:int, y:int) int do
    return x y +
end
```
by adding the `pub` keyword a function is visible
to the host environment.

### Extern Keyword
Since web-assembly supports calling functions from other environments such as JavaScript or the runtime like wasmtime the extern keyword gives the compiler nessecary information about functions you may call from the host environment.
`extern some_function(x:int, y:int) int end`

### Structures
```
struct Vec2
x: int
y: int
end

//returns 5
proc access() do
    point:Vec2 = {0, 5}
    return point@y
end

proc new_vec2(x: int, y: int) Vec2 do
    v: Vec2 = {x, y}
    return v
end
```

