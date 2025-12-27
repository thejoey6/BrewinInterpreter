# My Code

class NilClass:
    def __eq__(self, other):
        return isinstance(other, NilClass)
    
    def __str__(self):
        return "nil"

Nil = NilClass()