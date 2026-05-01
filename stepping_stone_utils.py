from read_problem import *
from graph_utils import *
import os
from collections import deque


#------------------------------
# POTENTIALS
#------------------------------

def compute_potentials(problem, proposal):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    u = [None] * n
    v = [None] * m

    u[0] = 0

    changed = True
    while changed:
        changed = False

        for i in range(n):
            for j in range(m):
                if proposal[i][j] is not None:  # basic cell
                    if u[i] is not None and v[j] is None:
                        v[j] = costs[i][j] - u[i]
                        changed = True
                    elif v[j] is not None and u[i] is None:
                        u[i] = costs[i][j] - v[j]
                        changed = True

    return u, v

def potential_costs(problem, u, v):
    n, m = problem["n"], problem["m"]

    table = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    print("\n=== POTENTIAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table

#------------------------------
# MARGINAL COSTS
#------------------------------

def marginal_costs(problem, u, v):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    table = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    print("\n=== MARGINAL COSTS ===")
    for i in range(n):
        print(table[i])

    return table

#------------------------------
# DEGENERATE OR NOT
#------------------------------

def is_degenerate(problem, proposal):
    n, m = problem["n"], problem["m"]

    count = sum(
        1 for i in range(n) for j in range(m)
        if proposal[i][j] is not None
    )

    return count < (n + m - 1)

#-------------------------------
# CYCLE PART
#-------------------------------

def find_improving_cell(problem, u, v, proposal):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    best_value = 0
    best_cell = None

    for i in range(n):
        for j in range(m):
            if proposal[i][j] is None:  # non-basic cell
                delta = costs[i][j] - u[i] - v[j]

                if delta < best_value:
                    best_value = delta
                    best_cell = (i, j)

    return best_cell, best_value

def _node_to_index(node):
    return int(node[1:])


def _edge_to_cell(node_a, node_b):
    if node_a.startswith("S"):
        return (_node_to_index(node_a), _node_to_index(node_b))
    return (_node_to_index(node_b), _node_to_index(node_a))


def _node_path_to_cells(node_path):
    return [
        _edge_to_cell(node_path[k], node_path[k + 1])
        for k in range(len(node_path) - 1)
    ]


def _rotate_cycle(cycle, start_idx):
    cells = cycle[:-1]
    rotated = cells[start_idx:] + cells[:start_idx]
    return rotated + [rotated[0]]


def _prefer_zero_on_minus(proposal, cycle):
    """
    When we correct an already-basic cycle, we prefer an orientation that puts
    a zero-valued edge on a '-' position so the cycle can be broken without
    changing the transported quantities.
    """
    cells = cycle[:-1]

    for start_idx in range(len(cells)):
        rotated = _rotate_cycle(cycle, start_idx)
        minus_cells = [rotated[k] for k in range(1, len(rotated) - 1, 2)]
        if any(proposal[i][j] == 0 for i, j in minus_cells):
            return rotated

    return cycle


def _find_node_path(graph, start, goal):
    queue = deque([start])
    parents = {start: None}

    while queue:
        node = queue.popleft()

        if node == goal:
            break

        for neighbor in graph[node]:
            if neighbor not in parents:
                parents[neighbor] = node
                queue.append(neighbor)

    if goal not in parents:
        return None

    path = []
    node = goal

    while node is not None:
        path.append(node)
        node = parents[node]

    path.reverse()
    return path


def _find_cycle_node_path(graph):
    visited = set()
    stack = set()
    parents = {}

    def dfs(node, parent):
        visited.add(node)
        stack.add(node)
        parents[node] = parent

        for neighbor in graph[node]:
            if neighbor == parent:
                continue

            if neighbor not in visited:
                cycle = dfs(neighbor, node)
                if cycle is not None:
                    return cycle
            elif neighbor in stack:
                path = []
                current = node

                while current != neighbor:
                    path.append(current)
                    current = parents[current]

                path.reverse()
                return [neighbor] + path + [neighbor]

        stack.remove(node)
        return None

    for start in graph:
        if start not in visited:
            cycle = dfs(start, None)
            if cycle is not None:
                return cycle

    return None


# Test acyclic
def detect_cycle(proposal):
    graph = build_graph(proposal)
    node_cycle = _find_cycle_node_path(graph)

    if node_cycle is None:
        return None

    cycle_cells = _node_path_to_cells(node_cycle)
    cycle = cycle_cells + [cycle_cells[0]]
    cycle = _prefer_zero_on_minus(proposal, cycle)

    print("\nCycle found:")
    print(cycle)
    return cycle

def transportation_maximization(proposal, cycle):
    """
    Perform the 'transportation maximization' step once a cycle is detected.

    Steps:
    1. Assign alternating signs (+ / -) to the cells of the cycle
    2. Compute theta = minimum value among '-' cells
    3. Identify and display the edge(s) that will be removed (value becomes 0)

    Parameters:
        proposal : current transportation matrix (n x m)
        cycle    : list of (i, j) tuples representing the cycle
    """

    print("\n=== TRANSPORTATION MAXIMIZATION ===")

    # --------------------------------------------------------
    # Step 1: Display conditions (+ / -) for each box
    # --------------------------------------------------------
    print("\nConditions for each box:")

    minus_cells = []  # store cells with '-' sign

    for k, (i, j) in enumerate(cycle[:-1]):
        if k % 2 == 0:
            sign = "+"
        else:
            sign = "-"
            minus_cells.append((i, j))

        print(f"{sign} P{i+1}, C{j+1}")

    # --------------------------------------------------------
    # Step 2: Compute theta
    # Theta = minimum value among cells with '-' sign
    # --------------------------------------------------------
    theta = min(proposal[i][j] for i, j in minus_cells)

    print(f"\nTheta (maximum transport): {theta}")

    # --------------------------------------------------------
    # Step 3: Identify deleted edges
    # A deleted edge is a '-' cell that becomes 0 after subtraction
    # --------------------------------------------------------
    print("\nDeleted edge(s):")

    deleted_found = False

    for (i, j) in minus_cells:
        if proposal[i][j] == theta:
            print(f"P{i+1}, C{j+1}")
            deleted_found = True

    if not deleted_found:
        print("None")


#-------------------------------
# FIND CYCLE -> TO UPDATE THE SOLUTION
#-------------------------------

def find_cycle(proposal, start):
    graph = build_graph(proposal)
    start_row = f"S{start[0]}"
    start_col = f"C{start[1]}"
    node_path = _find_node_path(graph, start_row, start_col)

    if node_path is not None:
        cycle = [start] + _node_path_to_cells(node_path) + [start]

        print("\nCycle found:")
        print(cycle)

        return cycle

    print("\nNo valid cycle found.")
    return None

def update_proposal(proposal, cycle):
    minus_cells = []
    signs = []

    for k, (i, j) in enumerate(cycle[:-1]):
        if k % 2 == 0:
            signs.append((i, j, "+"))
        else:
            signs.append((i, j, "-"))
            minus_cells.append((i, j))

    theta = min(proposal[i][j] for (i, j) in minus_cells)

    print("\n=== APPLYING UPDATE ===")
    print(f"Theta = {theta}\n")

    print("Before update:")
    for (i, j, sign) in signs:
        val = proposal[i][j]
        print(f"{sign} S{i+1}, C{j+1} : {val}")

    # APPLY
    for (i, j, sign) in signs:
        if sign == "+":
            if proposal[i][j] is None:
                proposal[i][j] = 0
            proposal[i][j] += theta
        else:
            proposal[i][j] -= theta

    print("\nAfter update:")
    for (i, j, sign) in signs:
        val = proposal[i][j]
        print(f"{sign} S{i+1}, C{j+1} : {val}")

    print("\nRemoved edges:")
    removed = False

    for (i, j) in minus_cells:
        if proposal[i][j] == 0:
            proposal[i][j] = None
            print(f"S{i+1}, C{j+1}")
            removed = True

    if not removed:
        print("None")
