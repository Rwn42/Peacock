# Peacock
A small language that compiles to WebAssembly. Served as a learning experience to learn about how WebAssembly works.

## Hello, World
```ruby
environment puts(s: ^string)

pub proc main() do
    puts("Hello, World!")
end
```

## Overview

### Expressions
Expressions are in reverse polish notation
```ruby
1 2 + #the same as 1 + 2 in other languages
```

### Control Flow
```ruby
if a 1 + == b do
    ...
end

while a < b do
    ...
end
```

### Variables
```
x: int = 10 2 +
```

### Procedures
```ruby
proc add(x: int, y: int) int do
    return x y +; #semicolon optional
end

#use pub to make a function accesible by the host environment
pub proc add(x: int, y:int) int ...
```

### Environment
To call functions from the host environment declare them with the following:
```ruby
external add(x: int, y: int) int 
#this can now be used like a normal function in the code
```

### Constants
constants must be outside of any block
```ruby
const x: int = 10 2 +
const y: int = x 2 + #constants can use other constants declared above them
```

### Include
Peacock has a C-style include. at the point of include
the entire AST for the other file is injected into the current AST.
```
include "some_file"
```


