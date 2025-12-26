from intbase import InterpreterBase
from intbase import ErrorType
import copy
from nil_module import Nil
from function import Function, LambdaFcn
from environment import Environment, Variable
from brewparse import parse_program


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        self.function_defs = {}
        self.interface_defs = {}        # Access by interface name. has variables and functions fields. variables is list [] and functions
                                        # ... is a dictionary that maps fcn names to list of args.: x =  _defs[A]["functions"]["foof"][0] wld produce the first arg of foof

    def run(self, program): # {
        ast = parse_program(program)
        self.define_interfaces(ast)
        main = self.get_main_node(ast)
        x = main.call(self)
        if isinstance(x, ErrorType):
            super().error(x, f"Error returning from main")
    # }


    def define_interfaces(self, tree):
        if tree.elem_type == 'program':
            interfaces = tree.get('interfaces')
            if not interfaces:
                return
            
            for interface in interfaces:
                name = interface.get('name')            # Add checking for duplicate interfaces?
                fields = interface.get('fields')
                variables = []          
                functions = {}

                if len(name) > 1 or not name.isupper():
                    super().error(ErrorType.NAME_ERROR, f'name not compatible')

                if name in self.interface_defs:
                    super().error(ErrorType.NAME_ERROR, f'Cannot declare the same interface {name} twice.')
                for field in fields:
                    namei = field.get('name')

                    if field.elem_type == 'field_var':
                        variables.append(namei)

                    if field.elem_type == 'field_func':
                        functions[namei] = field.get('params')      # Add checking for duplicate functions?
                
                self.interface_defs[name] = {"variables": variables, "functions": functions}
                


    def get_main_node(self, tree): # {          # Maps all functions to name and arg types: fooib, boos
        if tree.elem_type == 'program':
            functions = tree.get('functions')
            for function in functions:

                fcn = self.define_function(function)
                key = str(fcn)

                if key in self.function_defs:
                    super().error(ErrorType.NAME_ERROR, f"Cannot declare function twice")

                self.function_defs[key] = fcn
            
            if "main" in self.function_defs:
                return self.function_defs["main"]
            
            super().error(ErrorType.NAME_ERROR, "No main() function was found",)
    # }
    
    def define_function(self, function, env=None, isLambda=False):
        name = function.get('name')
        args = function.get('args')
        stmnts = function.get('statements')
        
        for param in args:
            if param.elem_type == 'arg':
                pName = param.get('name')
                t = pName[-1]                        
                if t != 's' and t != 'i' and t != 'b' and t != 'o' and t != 'f' and not t.isupper():
                    super().error(ErrorType.TYPE_ERROR, "invalid function type",)
                    
        t = name[-1]

        if t != 's' and t != 'i' and t != 'b' and t != 'o' and t != 'v' and t != 'f' and name != 'main' and not t.isupper():
            super().error(ErrorType.TYPE_ERROR, "invalid function type",)

        result = LambdaFcn(env, name, args, stmnts) if isLambda else Function(name, args, stmnts)
        return result



    def evaluate_statement(self, statement, env): # {
        statement_type = statement.elem_type
        
        match statement_type:
            case 'vardef':
                ret = env.define(statement)
                if ret:
                    super().error(ret, f"Error defining function-scope variable {statement}, probably already declared.")
            case 'bvardef':
                ret = env.define(statement)
                if ret:
                    super().error(ret, f"Error defining block-scope variable {statement}, probably already declared.")
            case '=':

                var = statement.get('var')

                if var[-1] == 'f':
                    exp_name = statement.get('expression').get('name')
                    if exp_name[:-1] != 'lambda':
                        exp = env.retrieve_function(exp_name, self)
                    else:
                        exp = self.evaluate_expression(statement.get('expression'), env)
                else:
                    exp = self.evaluate_expression(statement.get('expression'), env)

                ret = env.assign(var, exp, self)      # NOTE: This is how to properly propagate return errors

                if isinstance(ret, ErrorType):
                    super().error(ret, f"Error assigning {exp} to {var}, probably already declared or incompatible.")
                
            case 'fcall':
                self.call_function(statement, env)
            case 'if':
                ret = self.call_if(statement, env)
                if ret is not None:
                    return ret
            case 'while':
                ret = self.call_while(statement, env)
                if ret is not None:
                    return ret
            case 'return':
                return self.ret(statement, env)

            case _:
                pass    # for clarity's sake
    # }

    def call_function(self, statement, env): # {
        fcn = statement.get('name')
        raw_args = statement.get('args')

        args = []
        args_str = ""

        for arg in raw_args:
            argument = self.evaluate_expression(arg, env)
            args.append(argument)

            i = copy.deepcopy(argument)
            while isinstance(i, Variable):
                i = i.get_val()
            x = lambda s: str(s).lower() if type(s) == bool else str(s)
            args_str += x(i)


        if fcn[-1] == 'f':

            fcn = env.retrieve(fcn)
            if isinstance(fcn, ErrorType):
                super().error(fcn)
            
            while isinstance(fcn, Variable):
                fcn = fcn.get_val()

            x = fcn.call(self, args)

            if isinstance(x, ErrorType):
                super().error(x)
            else:
                return x

        match fcn:

            case 'print':
                super().output(args_str)
                return None     # void???
            
            case 'inputi':
                if len(args) > 1:
                    super().error(ErrorType.NAME_ERROR, f"No inputi() function found that takes > 1 parameter",)
                if len(args) == 1:
                    super().output(args_str)
                
                input = int(super().get_input())
                return input
            
            case 'inputs':
                if len(args) > 1:
                    super().error(ErrorType.NAME_ERROR, f"No inputs() function found that takes > 1 parameter",)
                if len(args) == 1:
                    super().output(args_str)
                
                input = str(super().get_input())
                return input

            case _:
                ts = self.get_type_signatures(args)
                key = f"{fcn}{ts}"

                if key in self.function_defs:
                    x = self.function_defs[key].call(self, args)
                    if isinstance(x, ErrorType):
                        super().error(x)
                    else:
                        return x
                else:
                    super().error(ErrorType.NAME_ERROR, f"Function {fcn} has not been defined",)
    # }



    def call_if(self, statement, env):
        cond = statement.get('condition')
        condition = self.evaluate_expression(cond, env)
        true_stmnts = statement.get('statements')
        else_stmnts = statement.get('else_statements')

        condition = condition.get_val() if isinstance(condition, Variable) else condition 

        if (condition != True and condition != False):
            return super().error(ErrorType.TYPE_ERROR, "Condition does not evaluate to a boolean",)

        block = Environment(env)

        if condition == True:
            if true_stmnts:
                for stmnt in true_stmnts:
                    ret = self.evaluate_statement(stmnt, block)
                    if ret is not None:
                        return ret
        else:
            if else_stmnts:
                for stmnt in else_stmnts:
                    ret = self.evaluate_statement(stmnt, block)
                    if ret is not None:
                        return ret


    def call_while(self, statement, env):
        condition = statement.get('condition')
        stmnts = statement.get('statements')

        cond = self.evaluate_expression(condition, env)
        cond = cond.get_val() if isinstance(cond, Variable) else cond

        if (cond != True and cond != False) and (cond != 'true' and cond != 'false'):
            return super().error(ErrorType.TYPE_ERROR, "Condition does not evaluate to a boolean",)
        
     #   block = Environment(env)

        while(self.evaluate_expression(condition, env) == True):
            block = Environment(env)
            if stmnts:
                for stmnt in stmnts:
                    ret = self.evaluate_statement(stmnt, block)
                    if ret is not None:
                        if isinstance(ret, ErrorType):
                            super().error(ret)
                        return ret
                    if stmnt.elem_type == 'return':
                        return ret


    def ret(self, statement, env):
        val = statement.get('expression')

        if val == None:
            return None
        retrn = self.evaluate_expression(val, env)
        if isinstance(retrn, ErrorType):
            return super().error(retrn, f"Error returned from {statement} in environment {env}")
        else:
            return retrn
        

    def get_type_signatures(self, xs):
        typeSignatures = ""

        for x in xs:
            
            if isinstance(x, Variable):
                x = x.get_val()

            if type(x) == str:
                typeSignatures += 's'
            elif type(x) == int:
                typeSignatures += 'i'
            elif type(x) == bool:
                typeSignatures += 'b'
            elif type(x) == dict:
                typeSignatures += 'o'
            elif x == Nil:
                typeSignatures += 'o'
            else:
                return super().error(ErrorType.TYPE_ERROR)
            # Maybe add error for if the type signature isn't s/i/b/o, then type error?
        return typeSignatures


    def evaluate_expression(self, expression, env): # {
        expression_type = expression.elem_type

        if expression.get('op1') != None:
            op1 = self.evaluate_expression(expression.get('op1'), env)
            if op1:
                while isinstance(op1, Variable):
                    op1 = op1.get_val()

        if expression.get('op2') != None:
            op2 = self.evaluate_expression(expression.get('op2'), env)
            while isinstance(op2, Variable):
                op2 = op2.get_val()

        match expression_type:

            case '+':

                if type(op1) != type(op2) or type(op1) not in (int, str):
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 + op2

            case '-':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 - op2
            
            case 'fcall':
                return_value = self.call_function(expression, env)
                return return_value

            case 'qname':
                name = expression.get('name')
                ret = env.retrieve(name, self)
                if isinstance(ret, ErrorType):
                    super().error(ret, f"Error retrieving {name}")
                return ret

            case 'int':
                val = expression.get('val')
                return val

            case 'string':
                val = expression.get('val')
                return val
            
            # V2 Additions
            case '*':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 * op2
            
            case '/':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 // op2
            
            case '==':
                if type(op1) == dict or type(op2) == dict:
                    if op1 is op2:
                        return True
                    else:
                        return False
                
                if type(op1) != type(op2):
                    return False
                
                if op1 == op2:
                    return True
                return False
            
            case '!=':

                if type(op1) == dict or type(op2) == dict:
                    if op1 is op2:
                        return False
                    else:
                        return True
                    
                if type(op1) != type(op2):
                    return True
                if op1 == op2:
                    return False
                return True
            
            case '<':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 < op2
            
            case '<=':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 <= op2
            
            case '>':

                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 > op2
            
            case '>=':
                if type(op1) != int or type(op2) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return op1 >= op2
            
            case '&&':

                if type(op1) != bool or type(op2) != bool:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for boolean operation",)
                    return
                
                true = False
                true1 = False
                true2 = False
                if op1 == True:
                    true1 = True
                if op2 == True:
                    true2 = True
                if op1 == True and op2 == True:
                    true = True
                return true
            
            case '||':

                if type(op1) != bool or type(op2) != bool:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for boolean operation",)
                    return
                
                true = False
                if op1 == True:
                    true = True
                if op2 == True:
                    true = True

                return true
            
            case 'neg':
                if type(op1) != int:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                    return
                return -op1
            
            case '!':
                if type(op1) != bool:
                    super().error(ErrorType.TYPE_ERROR, "Incompatible types for boolean operation",)
                    return
                return not op1

            case 'bool':
                val = expression.get('val')
                return val
            
            case '@':
                return {}
            
            case 'nil':
                return Nil
            
            case 'func':
                name = expression.get('name')
                if name[:-1] == 'lambda':
                    lamb = self.define_function(expression, env, True)
                    return lamb

            case 'convert':
                t = expression.get('to_type')
                subject = self.evaluate_expression(expression.get('expr'), env)
                
                while isinstance(subject, Variable):
                    subject = subject.get_val()
                
                t_expr = type(subject)
                if t_expr == dict or subject == Nil:
                    super().error(ErrorType.TYPE_ERROR, f"Incompatible type for conversion (object)")
                
                if t == 'str':
                    if t_expr == str:
                        return subject
                    
                    if t_expr == int:
                        try:
                            x =str(subject)
                            return x
                        except:
                            super().error(ErrorType.TYPE_ERROR, f"Incompatible type for conversion (object)")
                    
                    if t_expr == bool:
                        if subject == True:
                            return "true"
                        return "false"
                            
                if t == 'int':

                    if t_expr == str:
                        try:
                            x = int(subject)
                            return x
                        except:
                            super().error(ErrorType.TYPE_ERROR, f"Incompatible type for conversion (object)")
                    
                    if t_expr == int:
                        return subject
                    
                    if t_expr == bool:
                        if subject == True:
                            return 1
                        return 0
                    
                if t == 'bool':
                    if t_expr == str:
                        if subject == "":
                            return False
                        return True
                    
                    if t_expr == int:
                        if subject == 0:
                            return False
                        return True
                    
                    if t_expr == bool:
                        return subject

            case _:
                pass    # for clarity
    # }





### ####### #### ###
### EXAMPLE CODE ###
### ####### #### ###

# This is not meant to demonstrate all the capabilities of the interpreter, but is an example of a few, along with basic syntax.

program1 = """

interface A {
vali;
valb;
}

interface B {
vali;
vals;
}

def foof() {
return bari;
}

def bari(xi, yi) {
return xi * yi;
}

def foobarA(xB) {
  xB.valb = false;
  return xB;
}

def main() {
var o;
o = @;
o.vali = 10;
o.vals = "Hello, world!";
o.valf = foof;
print(o.valf);
o.xo = @;
o.xo.yo = @;
o.xo.yo.funf = bari();
o.xo.yo.vali = o.xo.yo.funf(5, 10);
print(o.xo.yo.vali);
var zi;
zi = 100;
o.xo.yo.funcf = lambdai(xi, yi) { return o.vali * zi; };
print(o.xo.yo.funcf(3, zi));

var oB;
oB = o;
var oA;
oA = foobarA(oB);

print("----------");

var go;
go = @;
go.valuei = 55;

print(go.valuei);

go.bumpf = lambdav() { 
    selfo.valuei = selfo.valuei + 1;
};
go.bumpf();
print(go.valuei);

}

"""



interpreter = Interpreter()
interpreter.run(program1)