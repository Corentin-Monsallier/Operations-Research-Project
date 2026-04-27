import os

#------------------------------------------------------------------------------
# 1. TRANSPORT PROBLEM STRUCTURE
# A problem is stored as a dictionary with:
#   - n        : number of suppliers
#   - m        : number of customers
#   - costs    : cost matrix (n x m)
#   - provisions   : list of provisions
#   - orders   : list of orders
#------------------------------------------------------------------------------

def create_problem(n, m, costs, provisions, orders):
    return {
        "n": n,
        "m": m,
        "costs": costs,
        "provisions": provisions,
        "orders": orders
    }
#------------------------------------------------------------------------------
# READ PROBLEM FROM FILE
#------------------------------------------------------------------------------

def read_problem(filepath):
    with open(filepath, "r") as f:
        lines = [list(map(int, line.split())) for line in f if line.strip()]

    n, m = lines[0]

    costs = []
    provisions = []

    for i in range(1, n + 1):
        costs.append(lines[i][:m])
        provisions.append(lines[i][m])

    orders = lines[n + 1][:m]

    return {
        "n": n,
        "m": m,
        "costs": costs,
        "provisions": provisions,
        "orders": orders
    }

# ------------------------------------------------------------------------------
#  2. FUNCTIONS TO DISPLAY
# ------------------------------------------------------------------------------

def _col_width(values, header=""):
    """
    Compute the minimal width to display a column 
    (= max between length of the longest value in the column and length of the header column)
    default=0 avoid error if value NULL
    """
    max_val = max((len(str(v)) for v in values), default=0)
    return max(max_val, len(str(header)))

# ???????????????????????????????????????????????????????????????????????????
# NOTE SUR LE FORMATAGE DES CELLULES (f-strings)
# -----------------------------------------------
# Dans tout ce fichier, on utilise la syntaxe f"{valeur:>{largeur}}" pour
# aligner les cellules à droite dans une largeur fixe. Exemples :
#   f"{42:>6}"   → "    42"   (42 aligné à droite dans 6 caractères)
#   f"{'C1':>4}" → "  C1"    (texte aligné à droite dans 4 caractères)
#   f"{5:<5}"    → "5    "    (5 aligné à GAUCHE dans 5 caractères, utilisé pour les labels "Pi")
# Le :> signifie "aligner à droite", :< signifie "aligner à gauche".


def display_cost_matrix(problem):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]
    provisions = problem["provisions"]
    orders = problem["orders"]

    print("\n=== COST MATRIX ===")

    col_widths = []
    for j in range(m):
        col_vals = [costs[i][j] for i in range(n)] + [orders[j]]
        col_widths.append(max(len(str(v)) for v in col_vals))

    prov_width = max(len(str(v)) for v in provisions + ["Prov."])

    # Header
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for i in range(n):
        row = f"S{i+1:<5} " + "  ".join(f"{costs[i][j]:>{col_widths[j]}}" for j in range(m))
        row += f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Orders row
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_transport_proposal(problem, proposal):
    n, m = problem["n"], problem["m"]
    provisions = problem["provisions"]
    orders = problem["orders"]

    print("\n=== TRANSPORT PROPOSAL ===")

    col_widths = []
    for j in range(m):
        col_vals = [proposal[i][j] for i in range(n) if proposal[i][j] is not None]
        col_vals.append(orders[j])
        col_widths.append(max(len(str(v)) for v in col_vals))

    prov_width = max(len(str(v)) for v in provisions + ["Prov."])

    # Header
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    header += f"  {'Prov.':>{prov_width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for i in range(n):
        cells = []
        for j in range(m):
            val = proposal[i][j]
            cells.append(f"{val:>{col_widths[j]}}" if val is not None else f"{'·':>{col_widths[j]}}")

        row = f"S{i+1:<5} " + "  ".join(cells) + f"  {provisions[i]:>{prov_width}}"
        print(row)

    print("  " + "-" * (len(header) - 2))

    # Orders row
    orders_row = "Ord.   " + "  ".join(f"{orders[j]:>{col_widths[j]}}" for j in range(m))
    print(orders_row)


def display_potential_costs(problem, u, v):
    n, m = problem["n"], problem["m"]

    print("\n=== POTENTIAL COSTS (u[i] + v[j]) ===")

    pot_costs = [[u[i] + v[j] for j in range(m)] for i in range(n)]

    col_widths = []
    for j in range(m):
        col_vals = [pot_costs[i][j] for i in range(n)]
        col_widths.append(max(len(str(v)) for v in col_vals))

    # Header
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for i in range(n):
        row = f"S{i+1:<5} " + "  ".join(f"{pot_costs[i][j]:>{col_widths[j]}}" for j in range(m))
        print(row)


def display_marginal_costs(problem, u, v):
    n, m = problem["n"], problem["m"]
    costs = problem["costs"]

    print("\n=== MARGINAL COSTS (c[i][j] - u[i] - v[j]) ===")

    marginals = [[costs[i][j] - u[i] - v[j] for j in range(m)] for i in range(n)]

    col_widths = []
    for j in range(m):
        col_vals = [marginals[i][j] for i in range(n)]
        col_widths.append(max(len(str(v)) for v in col_vals))

    # Header
    header = "        " + "  ".join(f"{'C'+str(j+1):>{col_widths[j]}}" for j in range(m))
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for i in range(n):
        row = f"S{i+1:<5} " + "  ".join(f"{marginals[i][j]:>{col_widths[j]}}" for j in range(m))
        print(row)

# ------------------------------------------------------------------------------
#  3. Total cost calculation for a given transport proposal
# ------------------------------------------------------------------------------

def total_cost(problem, proposal):
    n, m = problem["n"], problem["m"]
    cost = 0
    for i in range(n):
        for j in range(m):
            if proposal[i][j] is not None and proposal[i][j] > 0:
                cost += problem["costs"][i][j] * proposal[i][j]
    return cost


# ------------------------------------------------------------------------------
#  4. TEST all the available files
# ------------------------------------------------------------------------------

def test_all_problems(folder):
    txt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

    if not txt_files:
        print(f"No .txt files found in: {folder}")
        return

    for filename in txt_files:
        filepath = os.path.join(folder, filename)

        print("\n" + "=" * 60)
        print(f"FILE: {filename}")
        print("=" * 60)

        try:
            problem = read_problem(filepath)
            print(f"Loaded: {problem['n']} suppliers, {problem['m']} customers")
            display_cost_matrix(problem)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    folder = input("Path to problem folder: ").strip()

    if not os.path.exists(folder):
        print(f"Folder not found: {folder}")
    else:
        test_all_problems(folder)
