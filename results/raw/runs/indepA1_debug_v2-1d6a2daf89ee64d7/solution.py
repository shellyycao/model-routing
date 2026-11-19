def dependency_order(deps):
    """
    Return a deterministic topological ordering of all nodes appearing as keys
    or as dependencies in ``deps``.  Among nodes that are ready (i.e. all of
    their dependencies have already been emitted) the alphabetically smallest
    name is chosen first.  If the graph contains a cycle a ``ValueError`` is
    raised.
    """
    # Gather every node that is either a key or appears in a dependency list.
    all_nodes = set(deps) | {node for targets in deps.values() for node in targets}
    remaining = set(all_nodes)
    order = []

    while remaining:
        # Nodes whose dependencies are all already removed from ``remaining``.
        ready = sorted(
            n for n in remaining if not (set(deps.get(n, [])) & remaining)
        )
        if not ready:
            # No node can be emitted → a cycle exists.
            raise ValueError("Cyclic dependency detected")
        order.extend(ready)
        remaining.difference_update(ready)

    return order