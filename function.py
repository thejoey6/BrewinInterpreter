# My Code

from environment import Environment, Variable, Reference
from nil_module import Nil
from intbase import ErrorType
import copy

class Function:

    def __init__(self, name, params=[], statements=[]):
        self.name = name
        self.statements = statements
        self.params = params
        self.selfo = None

    def __str__(self):
        typeSignatures = ""

        for param in self.params:
            if param.elem_type == 'arg':
                pName = param.get('name')
                t = pName[-1]

                if t != 's' and t != 'i' and t != 'b' and t != 'o' and t != 'f' and not t.isupper():
                    return ErrorType.TYPE_ERROR
                
                if t.isupper():
                    typeSignatures += 'o'
                else:
                    typeSignatures += t

        return f"{self.name}{typeSignatures}"


    def call(self, caller, args=[], isLambda=False):
        if isLambda == True:
            env = self.env
        else:
            env = Environment()

        my_type = self.name[-1]
        if self.selfo is not None:
            env.variables['selfo'] = self.selfo

        if len(args) != len(self.params):
            return ErrorType.NAME_ERROR
        
        for param, arg in zip(self.params, args):  
            pName = param.get('name')
            isRef = param.get('ref')       # True if declared with & and false otherwise
            
            eval_arg = arg.get_val() if isinstance(arg, Variable) else arg
            if not env.compare_types(pName, eval_arg, caller):
                return ErrorType.TYPE_ERROR

            def_ret = env.define(param, True)
            if def_ret:
                return def_ret

            if isRef:
                if isinstance(arg, Variable):
                    env.variables[pName] = Reference(arg)
                else:
                    temp = Variable(arg)
                    env.variables[pName] = Reference(temp)
            else:
                literal = arg.get_val() if isinstance(arg, Variable) else arg

                if isinstance(literal, dict):
                    ass_ret = env.assign(pName, literal, caller)
                else:
                    ass_ret = env.assign(pName, copy.copy(literal), caller)
                
                if ass_ret:
                    return ass_ret


            # call function
        for statement in self.statements:
            
            if statement.elem_type == 'return':

                val = statement.get('expression')

                if val is None:
                    break
                else:
                    if my_type == 'f':
                        n = val.get('name')

                        if n[:-1] == 'lambda':
                            fcn = LambdaFcn(env, n, val.get('args'), val.get('statements'))
                        else:
                            fcn = env.retrieve_function(n, caller)

                        if isinstance(fcn, ErrorType):
                            return fcn

                        return fcn.call(caller, args)
                    
                    else:
                        ret = caller.evaluate_expression(val, env)
                    
                    if isinstance(ret, ErrorType):
                        return ret

                    return self.ret(ret, caller)
            
            ret_val = caller.evaluate_statement(statement, env)
            
            if ret_val is not None:
                if isinstance(ret_val, ErrorType):
                    return ret_val
                return self.ret(ret_val, caller)


        if self.name[-1] == 'v' or self.name == 'main':
            return None
        
        t = env.get_type_signature(self.name) 
        return t
    
        
    def ret(self, val, caller=None):

        t_val = self.name[-1]
        literal = val.get_val() if isinstance(val, Variable) else val

        if self.name == 'main' and literal is not None:
            return ErrorType.TYPE_ERROR
        
        if t_val == 'v': 
            if literal is not None:
                return ErrorType.TYPE_ERROR
            return None
        
        if literal is None:
            return None

        match t_val:
            case 'i':
                if type(literal) != int:
                    return ErrorType.TYPE_ERROR
            case 's':
                if type(literal) != str:
                    return ErrorType.TYPE_ERROR
            case 'o':
                if type(literal) != dict and literal is not Nil:
                    return ErrorType.TYPE_ERROR
            case 'b':
                if type(literal) != bool:
                    return ErrorType.TYPE_ERROR
            case 'f':
                if not isinstance(literal, Function):
                    return ErrorType.TYPE_ERROR
            case _:
                if t_val.isupper() and (type(literal) is dict or literal is Nil):
                    if self.check_interface_compatibility(self.name, literal, caller) == True:
                        return literal
                return ErrorType.TYPE_ERROR

        return literal



    def check_interface_compatibility(self, variable, value, caller):           # Taken from environment.py... I just didnt want to propagate env to func ret
        var_type = variable[-1]

        if caller == None:              # Safety --- should never reach this
            return False
        
        if var_type not in caller.interface_defs:       # Is interface declared?
            return False
        
        if value == Nil:
            return True
        
        interface = caller.interface_defs[var_type]     # var_type is a single uppercase char, which would be the name of interface

        for field in interface['variables']:
            if field not in value:
                return False
        
        for field in interface['functions']:
            if field not in value:
                return False
            # ('here i should check param types')

        return True


### ###### ###
### LAMBDA ###
### ###### ###


class LambdaFcn(Function):

    def __init__(self, closure, name, params=[], statements=[]):
        super().__init__(name, params, statements)
        self.env = Environment()


        self.env.variables = self.populate(closure)
    

    def populate(self, closure):
        vars = {}
        current = closure

        while current:
            for n,v in current.variables.items():
                if n not in vars:
                    vars[n] = copy.copy(v)
            current = current.parent

        return vars

    def call(self, caller, args=[], isLamba=True):
        return super().call(caller, args, isLambda=True)