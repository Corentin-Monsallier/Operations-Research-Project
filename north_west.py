from read_problem import read_problem, display_cost_matrix, display_transport_proposal, total_cost
import os

# ============================================================
# NORTH-WEST METHOD
# ============================================================
# General idea:
# we start in the north-west corner of the matrix, so at the top left.
# At each step, we transport the maximum possible in the current cell.
# Then:
# - if the supply of the row is exhausted, we go down
# - otherwise, if the demand of the column is satisfied, we go right
# This method produces a feasible solution, but not necessarily an optimal one.
# ============================================================


def north_west(problem):
    # Dimensions of the transport matrix.
    n, m = problem["n"], problem["m"]

    # We copy the supplies and demands because the algorithm modifies them
    # progressively until exhaustion.
    provisions = problem["provisions"][:]
    orders = problem["orders"][:]

    # The proposal is initially empty.
    # None means: "this cell does not belong to the current basis".
    proposal = [[None] * m for _ in range(n)]

    # We start at the top left.
    i, j = 0, 0

    # As long as we stay inside the matrix, we continue assigning quantities.
    while i < n and j < m:
        # The transported quantity is bounded at the same time:
        # - by what remains to be supplied on row i
        # - by what remains to be delivered in column j
        qty = min(provisions[i], orders[j])

        # The current cell therefore becomes a basic cell with this quantity.
        proposal[i][j] = qty

        # We update the remainders after assignment.
        provisions[i] -= qty
        orders[j] -= qty

        # We then decide the movement in the table.
        if provisions[i] == 0 and orders[j] == 0:
            # Delicate case: row and column are exhausted at the same time.
            # To keep a non-degenerate basis (n + m - 1 basic cells),
            # we add, if possible, a neighboring cell at 0.
            if i < n - 1 and j < m - 1 and proposal[i][j + 1] is None:
                # This cell at 0 does not change the cost,
                # but it stabilizes the basis structure.
                proposal[i][j + 1] = 0

            # Then we leave both the row and the column.
            i += 1
            j += 1
        elif provisions[i] == 0:
            # The supply of row i is finished: we go down.
            i += 1
        else:
            # Otherwise it is column j that is saturated: we go right.
            j += 1

    # The obtained proposal is a feasible initial solution.
    return proposal
