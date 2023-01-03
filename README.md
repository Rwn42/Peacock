# Peacock
Stack-based, concatenative language that compiles (hopefully) to wasi compliant web assembly.

## Overview

### Expressions
expressions are written in reverse polish notation.
`5 4 +` -> is equivalent to 5 + 4 in a normal language
note only normal expressions behave this way
comparison, variable assignment, function calls ect
all behave as you would expect

### Comparison
`2 3 + == 4 1 +` -> checks if the rhs is equal to the lhs

