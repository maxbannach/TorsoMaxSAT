from itertools import chain, combinations

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

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
