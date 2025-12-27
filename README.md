# Brewin Interpreter (Python)

A **full interpreter for *Brewin***, a statically-typed, object-oriented mock language with interfaces, first-class functions, lambdas/closures, and method dispatch. 

Built in **Python** as a quarter-long university project focused on language implementation and runtime systems.

This interpreter parses, type-checks, and executes Brewin programs according to a formal specification, handling non-trivial scoping, interface compliance, and runtime error semantics.

---

## Scope of Concepts

This project goes beyond basic scripting or application code and focuses on **core programming language concepts**, including:

- Abstract syntax tree (AST) evaluation
- Lexical scoping and closures
- Structural interface typing
- Function values and higher-order programming
- Object methods with implicit receivers
- Precise runtime error detection


---

## Supported Language Features

### Core
- Name-suffix static typing (`i`, `s`, `b`, `o`, `f`, `v`)
- Function overloading by parameter type
- Pass-by-value and pass-by-reference semantics
- Block-scoped shadowing and lexical scoping
- Explicit runtime error handling

### Brewin Extensions
- **Structural interfaces**
- **First-class functions**
- **Lambda expressions and closures**
- **Objects with variable and function members**
- **Method calls with implicit `selfo`**
- **Interface-typed variables and returns**
- **Function equality semantics**

---

## Project Structure

The files ***interpreterv4.py***, ***function.py***, ***environment.py***, and ***nil_module.py*** are my own code. I did not write the code in any other files, they were provided by the instructor.

This project consisted of four parts, each building upon or revising the last. As such, code organization is influenced by chronology and can be hard to navigate.
 
---

## Running the Interpreter
The program, as is, contains a sample excerpt of *Brewin* code which can be found at the bottom of `interpreterv4.py` and is automatically executed (i.e., interpreted) when the program runs. 

The last line of this file executes `Interpreter.run()`, which takes a single string variable of syntactically-valid *Brewin* code as its arguments. One can create a new variable to test different features of the language, as well as some of its shortcomings.

##### Python 3.11 recommended

---

 ## Example Brewin Program

```
interface A {
  vali;
  addf(i);
}

def addi(xi) { return xi + 1; }

def main() {
  var o;
  o = @;
  o.vali = 10;
  o.addf = addi;

  var xA;
  xA = o;           /* interface compliance checked here */
  print(xA.addf(5)); /* 6 */
}
```
---

## Academic Context

This repository is coursework and is not open source.
The Brewin language and starter framework were created by  [Carey Nachenberg](http://careynachenberg.weebly.com/) with support from his TAs. 

I keep separated, private repositories for coursework: this repository will have virtually no commit history, despite consistent individual contributions over a 10-week period. It was submitted for a letter grade and passed all plagiarism and LLM checks. 

