# Peacock
Language that compiles to web-assembly. served as a learning experience to learn about wasm/wat.

## CLI
```sh
#print wat code
python main.py com mycode.pk

#print lexer output
python main.py lex mycode.pk

#print parser output
python main.py parse mycode.pk

# to name the wat file for output use the following:
python main.py com mycode.pk > output.wat
```

## Goals
- [x] Improve on syntax choices
- [ ] More compile time checks
- [ ] better linear memory behaviour
- [ ] compile to my own intermediate representation then go to wasm
- [ ] improve on environment
- [x] allow for including other files
- [x] move extern defintions into a standard library
- [ ] support for function pointers as wasm supports them
- [x] first class support for strings (no string lib yet)
- [ ] dynamic memory allocation
- [ ] try a WASI target
- [ ] macros maybe (if they seem useful)
- [ ] rewrite the compiler in a high performance language
- [ ] compile straight to web assembly not wat

Some/Most of these I dont expect to accomplish they just serve as reminders for things I may want to try.

## Overview

### Hello World
```ruby
extern puts(s string)

pub proc main() do
    puts("Hello, World")
end
```
### Expressions
the simplest expressions in peacock are written in reverse-polish notation.
expressions terminate on semicolon or newline
```ruby
#not allowed
1 + 3
#allowed
1 3 +
```

### Comparison / If
```ruby
if 3 2 + == 4 1 + do
    ...
else
    ...
end
```

### While Loops
```ruby
x: int = 0
while x <= 10 do
    x = x 1 +
end
```

### Variables
```ruby
#one way
x: int
x = 12

#another way
x: int = 10 2 +
```

### Types
```ruby
#the 4 basic data types include.
int
float
bool
string
^<type> #the ^ is used to denote a pointer
```

### Procedures
```ruby
#local to the wasm module
proc add(x int, y int) int do
    return x y +
end

#accesible by javascript
pub proc add(x int, y int) int do
    return x y +
end
```

### Using External Functions
To use functions from javascript in peacock use the following
```ruby
extern add(x int, y int) int
```

### Memory
We can only load integers at this time working on loading floats too
```ruby
extern puti(i int)
proc main() do
    #allocate 4 integers or 16 bytes
    memory x ^int 16
    @x = 10
    @x 4 + = 11
    @x 8 + = 12
    @x 12 + = 13
    #this will print the numbers out to the console
    puti(x !)
    puti(x 4 + !)
    puti(x 8 + !)
    puti (x 12 + !)

end
```

### Libraries
Peacock has C-style include where the code is simply
shot into the ast when the import statement is encountered.

```ruby
import "somelibrary.pk"
```