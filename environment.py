from intbase import ErrorType
from nil_module import Nil


class Variable:

    def __init__(self, val):
        self.val = val

    def set_val(self, val):
        self.val = val

    def get_val(self):
        return self.val


class Reference(Variable):

    def __init__(self, var):
        self.var = var

    def set_val(self, val):
        if self.var is not None:
            self.var.set_val(val)

    def get_val(self):
        if self.var is not None:
            return self.var.get_val()


class Environment:

    def __init__(self, parent=None):
        self.variables = {}
        self.parent = parent

    def get_type_signature(self, name):
        t = name[-1]

        val = None
        if t == 'i':
            val = 0
        if t == 's':
            val = ""
        if t == 'b':
            val = False
        if t == 'o':            # Add one for 'f'... maybe nil?
            val = Nil
        if t.isupper():
            val = Nil
        if t == 'f':
            val = Nil
        return val

    def define(self, statement, isLambda=False):
        name = statement.get('name')
        scope = statement.elem_type
        t = name[-1]

        val = self.get_type_signature(name)

        if t != 's' and t != 'i' and t != 'b' and t != 'o' and t != 'f' and not t.isupper():
            return ErrorType.TYPE_ERROR

        if scope == 'bvardef':
            
            if name in self.variables:
                return ErrorType.NAME_ERROR
            
            self.variables[name] = Variable(val)

        elif scope == 'vardef':

            if name in self.variables:
                return ErrorType.NAME_ERROR

            if self.parent and name in self.parent.variables:
                return ErrorType.NAME_ERROR

            if self.parent:
                self.parent.variables[name] = Variable(val)
            else:
                self.variables[name] = Variable(val)

        elif scope == 'arg':
            if name in self.variables and isLambda == False:
                return ErrorType.NAME_ERROR
            self.variables[name] = Variable(val)



    def assign(self, var, exp, caller=None):

        ret = self.handle_segments(var)
        if isinstance(ret, ErrorType):
            return ret 
        
        prev = ret[0]
        cur = ret[1]

        ac_exp = exp
        if isinstance(exp, Variable):
            ac_exp = exp.get_val()

        if not self.compare_types(cur, ac_exp, caller):
            return ErrorType.TYPE_ERROR  #   REPLACE WITH ERROR OF INVALID TYPES
        
        if '.' in var and var[-1] == 'f':
            from function import Function
            if isinstance(ac_exp, Function):
                ac_exp.selfo = prev

        if cur not in prev:
            prev[cur] = Variable(ac_exp)
        else:
            prev[cur].set_val(ac_exp)


    def retrieve(self, var, caller=None):
        
        tup = self.handle_segments(var)
        if isinstance(tup, ErrorType):
            return tup 

        prev = tup[0]
        cur = tup[1]

        if cur in prev:
            return prev[cur]   
        elif self.parent:
            return self.parent.retrieve(var)
        else:
            return ErrorType.NAME_ERROR


    def handle_segments(self, var, exp=None):

        segments = var.split('.')
        prev = self.variables

        for segment in segments:

            if prev is Nil:
                return ErrorType.FAULT_ERROR
            
#            if segment == 'selfo':

            if segment == segments[0]:
                scope = self.search_scopes(segment)
                if scope is None:
                    return ErrorType.NAME_ERROR
                else:
                    prev = scope
                

            if isinstance(prev, Variable):
                prev = prev.get_val()
                
            if prev is Nil:
                return ErrorType.FAULT_ERROR
            
            t = segment[-1]
            if segment != segments[-1]:
                if t != 'o' and not t.isupper():
                    return ErrorType.TYPE_ERROR
                if segment not in prev:
                    return ErrorType.NAME_ERROR
                
                prev = prev[segment]
                if isinstance(prev, Variable):
                    prev = prev.get_val()

            else:
                return (prev, segment)  #final segment
        
        return ErrorType.NAME_ERROR


    def search_scopes(self, var):
        if var in self.variables:
            return self.variables
        elif self.parent:
            return self.parent.search_scopes(var) 
        else:
            return None


    def compare_types(self, var, val, caller=None):
        t_var = var[-1]
        t_val = type(val)
        
        match t_var:
            case 'i':
                if t_val != int:
                    return False    # REPLACE WITH ACTUAL ERROR CALL
            case 's':
                if t_val != str:
                    return False    # REPLACE WITH ACTUAL ERROR CALL
            case 'o':
                if t_val != dict and val is not Nil:
                    return False    # REPLACE WITH ACTUAL ERROR CALL
            case 'f':
                from function import Function
                if not isinstance(val, Function) and val is not Nil:
                    return False    # REPLACE WITH ACTUAL ERROR CALL
            case 'b':
                if t_val != bool:
                    return False    # REPLACE WITH ACTUAL ERROR CALL
            case _:
                if t_var.isupper():
                    return self.check_interface_compatibility(variable=var, value=val, caller=caller)
                else:
                    return False        # REPLACE WITH ACTUAL ERROR CALL, INVALID VARIABLE TYPE

        return True
    

    def check_interface_compatibility(self, variable, value, caller):
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

    def retrieve_function(self, name, caller):
        match = None

        # Prolly need to add handling of segments for object nested function members
        for key, value in caller.function_defs.items():
            if key.startswith(name):
                match = value
                break
        
        if match == None:
            return ErrorType.NAME_ERROR
        else:
            return match
