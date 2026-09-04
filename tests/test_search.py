from types import SimpleNamespace as NS
import pytest

from explorer.search import search
from explorer.server import SearchRequest


class Node:
    state = NS(is_solved=True)

    def __init__(self, key):
        self.key = key

    def actions_to(self):
        return self.key


class Tree:
    def __init__(self):
        self.items = []

    def one_iteration(self):
        # Two occurrences of the same route must count once.
        self.items.extend([Node(len(self.items)), Node(len(self.items))])

    def graph(self, recreate=False):
        assert recreate, "MCTS caches its graph; request a fresh view each iteration"
        return self.items


def test_candidate_target_and_budget(monkeypatch):
    monkeypatch.setattr('aizynthfinder.chem.hash_reactions', lambda key: key)
    finder = NS(tree=Tree(), config=NS(search=NS(iteration_limit=10, time_limit=60)))
    stats = search(finder, 3)
    assert stats['solved_routes_found'] == 3
    assert stats['iterations'] == 3
    assert stats['stop_reason'] == 'solved_route_target'
    finder.tree = Tree()
    finder.config.search.iteration_limit = 2
    stats = search(finder, 3)
    assert stats['stop_reason'] == 'iteration_limit'
    assert stats['solved_routes_found'] == 2


def test_candidate_validation():
    for field, value in [('solved_route_target', -1), ('return_routes', 0), ('return_routes', 101)]:
        with pytest.raises(ValueError):
            SearchRequest(smiles='CCO', **{field: value})
