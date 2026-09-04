"""Bounded MCTS search with a distinct solved-route early-stop target."""
import time


def search(finder, solved_target=0, progress=None):
    from aizynthfinder.chem import hash_reactions
    start = time.monotonic()
    seen_nodes, solved_routes = set(), set()
    stats = {"iterations": 0, "returned_first": False}
    reason = "iteration_limit"
    for iteration in range(finder.config.search.iteration_limit):
        if time.monotonic() - start >= finder.config.search.time_limit:
            reason = "search_time_limit"
            break
        stats["iterations"] = iteration + 1
        try:
            finder.tree.one_iteration()
        except StopIteration:
            reason = "search_exhausted"
            break
        for node in finder.tree.graph(recreate=True):
            if node.state.is_solved and node not in seen_nodes:
                solved_routes.add(hash_reactions(node.actions_to()))
                seen_nodes.add(node)
        if solved_routes and "first_solution_time" not in stats:
            stats.update(first_solution_time=time.monotonic() - start,
                         first_solution_iteration=iteration + 1)
        if progress:
            progress(len(solved_routes))
        if solved_target and len(solved_routes) >= solved_target:
            reason = "solved_route_target"
            break
    stats.update(time=time.monotonic() - start, solved_routes_found=len(solved_routes),
                 stop_reason=reason)
    finder.search_stats = stats
    return stats
