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

