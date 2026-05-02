import os

# ------------------------------------------------------------------------------
# 1. REPRESENTATION OF A TRANSPORT PROBLEM
# ------------------------------------------------------------------------------
# In the whole project, a problem is stored in a Python dictionary.
# This structure is deliberately simple:
# - n: number of suppliers (rows)
# - m: number of customers (columns)
# - costs: unit cost matrix
# - provisions: quantities available at each supplier
# - orders: quantities requested by each customer
# ------------------------------------------------------------------------------


def create_problem(n, m, costs, provisions, orders):
    # This helper simply builds the standard dictionary of the project.
    # It avoids rewriting the same keys everywhere.
    return {
        # Number of suppliers.
        "n": n,
        # Number of customers.
        "m": m,
        # Unit cost matrix.
        "costs": costs,
        # Supply of each supplier.
        "provisions": provisions,
        # Demand of each customer.
        "orders": orders,
    }


# ------------------------------------------------------------------------------
# 2. READING A PROBLEM FROM A TEXT FILE
# ------------------------------------------------------------------------------


def read_problem(filepath):
    # We open the problem file in read-only mode.
    with open(filepath, "r") as f:
        # Each non-empty line is transformed into a list of integers.
        # Example:
        # "30 20 20 450" -> [30, 20, 20, 450]
        lines = [list(map(int, line.split())) for line in f if line.strip()]

    # The first line contains the size of the problem: n rows, m columns.
    n, m = lines[0]

    # We prepare two lists:
    # - costs will receive each row of the cost matrix
    # - provisions will receive the last value of each supplier row
    costs = []
    provisions = []

    # The next n lines contain:
    # [cost_1, cost_2, ..., cost_m, provision_of_the_row]
    for i in range(1, n + 1):
        # We first keep the first m integers as costs.
        costs.append(lines[i][:m])
        # Then we take the last value as the provision of supplier i.
        provisions.append(lines[i][m])

    # The last useful line contains the demands of the customers.
    orders = lines[n + 1][:m]

    # We return the problem in the common format of the project.
    return {
        "n": n,
        "m": m,
        "costs": costs,
        "provisions": provisions,
        "orders": orders,
    }


# ------------------------------------------------------------------------------
# 3. DISPLAY FUNCTIONS
# ------------------------------------------------------------------------------


def _col_width(values, header=""):
    """
    Computes the minimum width of a column.

    The idea is simple:
    - we measure the maximum length of the values to display
    - we compare it with the length of the column title
    - we keep the larger of the two

    default=0 avoids an error if the column is empty.
    """
    # We convert each value to text to measure its width on screen.
    max_val = max((len(str(v)) for v in values), default=0)

    # We compare with the width of the column title to avoid
    # a larger header breaking the alignment.
    return max(max_val, len(str(header)))


def display_cost_matrix(problem):
    # We extract the different parts of the problem to lighten accesses.
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]
    provisions = problem["provisions"]
    orders = problem["orders"]

    print("\n=== COST MATRIX ===")

    # We compute the width of each customer column.
    # We must take into account both:
    # - the costs displayed in the matrix
    # - the demand displayed at the bottom of the column
    col_widths = []
    for j in range(m):
        # For column j, we gather:
        # - the costs of each row
        # - the demand at the bottom of the column
        col_vals = [costs[i][j] for i in range(n)] + [orders[j]]
        col_widths.append(max(len(str(v)) for v in col_vals))

    # Same principle for the right column "Prov.".
    prov_width = max(len(str(v)) for v in provisions + ["Prov."])

    # Header construction with right alignment.
    # "C1", "C2", etc. are right-aligned in their computed width.
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Display row by row of the suppliers.
    for i in range(n):
        # We build the whole row of one supplier before displaying it.
        row = f"S{i+1:<5} " + "  ".join(f"{costs[i][j]:>{col_widths[j]}}" for j in range(m))
        row += f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Last row: the orders of the customers.
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_transport_proposal(problem, proposal):
    # Here we no longer display the costs, but the transported quantity in
    # each cell of the transport plan.
    n, m = problem["n"], problem["m"]
    provisions = problem["provisions"]
    orders = problem["orders"]

    print("\n-----------------TRANSPORT PROPOSAL------------------")

    # Each column must be wide enough to display:
    # - all the quantities currently present in the proposal
    # - the demand at the bottom of the column
    col_widths = []
    for j in range(m):
        # We ignore None cells for the width because they will be displayed
        # with a simple replacement symbol.
        col_vals = [proposal[i][j] for i in range(n) if proposal[i][j] is not None]
        col_vals.append(orders[j])
        col_widths.append(max(len(str(v)) for v in col_vals))

    # Width of the provisions column.
    prov_width = max(len(str(v)) for v in provisions + ["Prov."])

    # Header of the customer columns.
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # We display each cell:
    # - its value if it exists in the basis
    # - a simple ASCII dot if the cell is empty
    #   to avoid encoding problems in the Windows console
    for i in range(n):
        cells = []
        for j in range(m):
            val = proposal[i][j]
            # If the cell is basic, we display its value.
            # Otherwise we put a dot to visualize an empty cell.
            cells.append(f"{val:>{col_widths[j]}}" if val is not None else f"{'.':>{col_widths[j]}}")

        row = f"S{i+1:<5} " + "  ".join(cells) + f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Final row of the orders.
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_potential_costs(problem, u, v):
    # Potential costs are the values u[i] + v[j].
    # They are used to compare the current structure with the real costs.
    n, m = problem["n"], problem["m"]

    print("\n------------POTENTIAL COSTS------------")

    # Explicit construction of the table for display.
    # Each cell of the table is simply worth u[i] + v[j].
    pot_costs = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    # We adjust the width of each column on the observed values.
    col_widths = []
    for j in range(m):
        col_vals = [pot_costs[i][j] for i in range(n)]
        col_widths.append(max(len(str(v)) for v in col_vals))

    # Column header.
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    # One row per supplier.
    for i in range(n):
        row = f"S{i+1:<5} " + "  ".join(f"{pot_costs[i][j]:>{col_widths[j]}}" for j in range(m))
        print(row)


def display_marginal_costs(problem, u, v):
    # The marginal cost of a cell is worth:
    # real cost - row potential - column potential
    # A negative value signals a possible improvement.
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    print("\n------------MARGINAL COSTS------------")

    # Construction of the table of marginal costs.
    # Each marginal cell indicates the interest of adding the cell to the basis.
    marginals = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    # Here we also make sure that the title "Cj" fits in the column.
    col_widths = []
    for j in range(m):
        col_vals = [marginals[i][j] for i in range(n)]
        max_val_width = max(len(str(v)) for v in col_vals)
        header_width = len(f"C{j+1}")
        col_widths.append(max(max_val_width, header_width))

    # Header.
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Display of the rows.
    for i in range(n):
        row = f"S{i+1:<5} " + "  ".join(f"{marginals[i][j]:>{col_widths[j]}}" for j in range(m))
        print(row)


# ------------------------------------------------------------------------------
# 4. TOTAL COST CALCULATION OF A PROPOSAL
# ------------------------------------------------------------------------------


def total_cost(problem, proposal):
    # We go through the whole transport matrix.
    n, m = problem["n"], problem["m"]
    cost = 0

    for i in range(n):
        for j in range(m):
            # An empty cell (None) does not count.
            # A cell at 0 does not change the cost either, so we ignore it too.
            if proposal[i][j] is not None and proposal[i][j] > 0:
                # Unit cost * transported quantity.
                cost += int(problem["costs"][i][j]) * proposal[i][j]

    return cost
