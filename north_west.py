from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost
import os

# ============================================================
# NORTH-WEST METHOD
#
# Builds an initial feasible solution by starting at (0,0)
# and allocating as much as possible at each step.
# ============================================================

def north_west(problem):
    n, m = problem["n"], problem["m"]

    # Copy supply and demand (we modify them)
    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

    # Initialize empty solution
    proposal = [[None] * m for _ in range(n)]

    i, j = 0, 0

    while i < n and j < m:
        qty = min(provisions[i], orders[j])
        proposal[i][j] = qty

        provisions[i] -= qty
        orders[j] -= qty

        # Move in the table
        if provisions[i] == 0 and orders[j] == 0:
            # Degenerate case: move diagonally
            i += 1
            j += 1
        elif provisions[i] == 0:
            i += 1
        else:
            j += 1

    return proposal


