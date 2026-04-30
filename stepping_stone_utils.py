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

# Test acyclic
def detect_cycle(graph):
    visited = set()

    for start in graph:
        if start not in visited:
            queue = deque([(start, None)])
            parent_map = {start: None}

            while queue:
                node, parent = queue.popleft()

                if node in visited:
                    # reconstruct cycle
                    cycle = [node]
                    p = parent
                    while p and p not in cycle:
                        cycle.append(p)
                        p = parent_map[p]
                    cycle.append(node)

                    print("Cycle found:", cycle)
                    return True

                visited.add(node)

                for neighbor in graph[node]:
                    if neighbor != parent:
                        parent_map[neighbor] = node
                        queue.append((neighbor, node))

    return False

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

    for k, (i, j) in enumerate(cycle):
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

    n = len(proposal)
    m = len(proposal[0])

    # Get all basic cells
    def is_basic(i, j):
        return proposal[i][j] is not None or (i, j) == start

    for i1 in range(n):
        for j1 in range(m):
            if (i1, j1) == start:
                continue
            if not is_basic(i1, j1):
                continue

            # same row as start
            if i1 == start[0]:

                for i2 in range(n):
                    if i2 == i1:
                        continue

                    if not is_basic(i2, j1):
                        continue

                    j2 = start[1]

                    # check last corner
                    if i2 != start[0] and j2 != j1:
                        if is_basic(i2, j2):

                            cycle = [
                                start,
                                (i1, j1),
                                (i2, j1),
                                (i2, j2),
                                start
                            ]

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