# Right associative application lambda calculus

I always wonder what implications would rigth associative applications 
bring. This is a simple implementation of lambda calculus with a simple
parser and eval function and some tests

# Grammar

* Abstraction :  `VAR "=>" expr`, right associative
* Variable : `VAR`
* Application `expr expr`, rigth associative
* `VAR` : Basically a regex `\w+` 

# Right Associativity

While common lambda calculus have left associative applications, this one
have right associative application.

* Left associative `f a b c` = `(((f a) b) c)` 
* Right associative `c b a f` = `(c (b (a f)))`
