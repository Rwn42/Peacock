# Peacock
A small language that compiles to WebAssembly. Served as a learning experience to learn about how WebAssembly works.

## Hello, World
```ruby
environment puts(s: ^string)

pub proc main() do
    #strings not yet supported :)
    puts("Hello, World!")
end
```

## Overview

## Expressions
Expressions are in reverse polish notation
```ruby
1 2 + #the same as 1 + 2 in other languages
```

## Control Flow
```ruby
if a 1 + == b do
    ...
end

while a < b do
    ...
end
```

## Variables
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
environment add(x: int, y: int) int 
#this can now be used like a normal function in the code
```

### Constants
constants must be outside of any block
```ruby
const x: int = 10 2 +
```

### Structures
A struct is Peacocks way of structuring data (structs currently do not support function members)
Syntax sugar may be added in the future for initializing structs

```ruby
#definition
struct Vec2
    x: int,
    y: int,
end

#usage
proc main() do
    memory point Vec2 1
    Vec2.x = 10
    Vec2.y = 20
end
```

### Memory
The `memory` keyword allocates some space in the memory and returns the pointer to the start of that space. The memory is invalidated at the end of the function therefore you cannot currently return anything that is not a primitive type from a function. 

```ruby
proc main() do
    #makes room for one hundred ints
    #the one hundred does not have to be constant the language supports "dynamic allocation"
    #it just gets invalidated at function end

    memory some_ints int 100

    #NOT ALLOWED
    return some_ints
end
```

the `memory` keyword can be used at the top level for every function to access

### Arrays

Arrays in Peacock make use the memory keyword.
```ruby
memory int_array int 100
int_array.(0) 
int_array.(1)

#we do support accessing elements with an expression like this
int_array.(some_var 2 +)

#setting elements
int_array.(0) = 10
```


