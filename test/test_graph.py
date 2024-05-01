import unittest
from translator.get_source_nodes  import get_roots

class TestGetRoots(unittest.TestCase):
    def test_get_roots(self):
        graph = {
            'A': ['B', 'C'],
            'B': ['D'],
            'C': [],
            'D': []
        }
        self.assertEqual(set(get_roots(graph)), set({'A'}))

        graph = {
            'A': ['B'],
            'B': ['A'],
            'C': ['D'],
            'D': []
        }
        self.assertEqual(set(get_roots(graph)), {'A','B', 'C'})

        graph ={
            'a':['b'],
            'b': ['a']
        }

        self.assertEqual(set(get_roots(graph)), {'a','b'})

        graph ={
            'a':[],
            'b': [],
            'c': []
        }
        self.assertEqual(set(get_roots(graph)), {'a','b','c'})

        graph ={
            'a':['b','c'],
            'b': ['d'],
            'c': ['d','f'],
            'd': ['e'],
            'e': [],
            'f': ['g','a'],
            'g': ['e'],

            'h': ['i'],
            'i': ['h'],

            'j': ['k'],
            'k': ['l'],
            'l': ['k']
        }

        self.assertEqual(set(get_roots(graph)), {'f','a','c','j','i',  'h'})



if __name__ == '__main__':
    unittest.main()