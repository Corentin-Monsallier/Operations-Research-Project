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


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    folder = input("Path to problem folder: ").strip()

    if not os.path.exists(folder):
        print(f"Folder not found: {folder}")
    else:
        txt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

        for filename in txt_files:
            filepath = os.path.join(folder, filename)

            print("\n" + "=" * 60)
            print(f"FILE: {filename}")
            print("=" * 60)

            try:
                problem = read_problem(filepath)

                # Display input data
                display_cost_matrix(problem)

                # Run North-West method
                print("\n--- North-West solution ---")
                proposal = north_west(problem)

                display_transport_proposal(problem, proposal)

                # Compute total cost
                cost = total_cost(problem, proposal)
                print(f"\nTotal cost (North-West): {cost}")

            except Exception as e:
                print(f"ERROR: {e}")