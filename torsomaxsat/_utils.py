from itertools import chain, combinations

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

#shift v by p positions to left
#def _shift(p):
    #return v << p
#    e = 0
#    print("shift ", p)
#    while p > 0:
#        e = e << 1
#        if p & 1:   #last bit set --> set bit here also
#            e = e | 1
#        p = p >> 1  #shift one back
#    print("shiftout ",  e)
#    return e 



class BiMap:
    def __init__(self):
        self.key_to_value = {}
        self.value_to_key = {}

    def insert(self, key, value):
        self.key_to_value[key]   = value
        self.value_to_key[value] = key

    def get_value(self, key):
        return self.key_to_value.get(key)

    def get_key(self, value):
        return self.value_to_key.get(value)

    def __str__(self):
        return f'key_to_value: {self.key_to_value}\nvalue_to_key: {self.value_to_key}'
