# Peacock
This branch is a WIP rewrite of the Python codebase to TypeScript.
I switched to TypeScript because Pythons static typing was becoming frusterating and I wanted a reason
to try the new bun JavaScript runtime (now using deno). I still plan on rewriting the compiler in a compiled language.

## Current Improvements over Python Implementation
- speed
- negative numbers lexed correctly
- CLI
- AST (more thorough leaves less up to the compiler)
- Linear Memory syntax
- AST output is presented in readable json
- Since we are using Deno compiler can be built as single (bulky) executable
- Global memory supported (in parsing stage only so far)

## Overview (based on current parser implementation may change when compiler is complete)

## Constants
constants must be outside of any block
```ruby
const x: int = 10 2 +
```

## Structures
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

## Memory
The `memory` keyword allocates some space in the memory and returns the pointer to the start of that space.
`alloc` does the same but does not clean up the memory for you (use when returning memory from functions).

```ruby
proc main() do
    #makes room for one hundred ints
    alloc some_ints int 100

    #since we used alloc this is ok to do
    return some_ints
end
```

the `memory` keyword, but not `alloc`, can also be used globally so any function can access it.

## Arrays

Arrays in Peacock make use the memory and alloc keywords.
```ruby
memory int_array int 100
int_array.(0) 
int_array.(1)

#we do support accessing elements with an expression like this
int_array.(some_var 2 +)

#setting elements
int_array.(0) = 10
```


