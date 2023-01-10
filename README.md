# Peacock
Language that compiles to web-assembly. served as a learning experience to learn about wasm/wat.
**Note: Documentation is currently removed because so many breaking changes its not worth even including.**
Refer to previous commits for older working versions of the peacock compiler.

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
- [ ] Improve on syntax choices
- [ ] More compile time checks
- [ ] better linear memory behaviour
- [ ] compile to my own intermediate representation then go to wasm
- [ ] improve on environment
- [ ] allow for including other files
- [ ] support for function pointers as wasm supports them
- [ ] first class support for strings
- [ ] dynamic memory allocation
- [ ] try a WASI target
- [ ] macros maybe (if they seem useful)
- [ ] rewrite the compiler in a high performance language
- [ ] compile straight to web assembly not wat

Some/Most of these I dont expect to accomplish they just serve as reminders for things I may want to try.

