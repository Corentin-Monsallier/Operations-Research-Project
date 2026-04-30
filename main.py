import os
from read_problem import *
from north_west import *
from Balas_hammer import *
from graph_utils import *
from stepping_stone_utils import *

# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------
def main():

    while True:
        print("\n===============================================")
        print(" OPERATION RESEARCH PROJECT - TRANSPORT PROBLEM ")
        print("===============================================")

        # Choose folder
        folder = input("\nPath to problem folder: ").strip()

        if not os.path.exists(folder):
            print("Folder not found.")
            continue

        files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])

        if not files:
            print("No .txt files found.")
            continue

        # Choice of the problem number to be processed
        print("\nAvailable problems:")
        for i, f in enumerate(files):
            print(f"{i+1}. {f}")

        try:
            choice = int(input("\nChoose problem: ")) - 1
            filepath = os.path.join(folder, files[choice])
        except:
            print("Invalid choice.")
            continue

        # Read + display
        problem = read_problem(filepath)
        display_cost_matrix(problem)

        # Initial proposal => 2 algorithms
        print("\nChoose initial solution method:")
        print("1. North-West")
        print("2. Balas-Hammer")

        algo = input("Choice: ")

        if algo == "1":
            proposal = north_west(problem)
        elif algo == "2":
            proposal = balas_hammer(problem)
        else:
            print("Invalid choice.")
            continue

        print("\n--- INITIAL PROPOSAL ---")
        display_transport_proposal(problem, proposal)
        display_graph(proposal)
        print(f"Initial cost: {total_cost(problem, proposal)}")

        # STEPPING-STONE
        iteration = 0

        while True:
            iteration += 1

            print("\n-----------")
            print(f" ITERATION {iteration}")
            print("-----------")

            # Display current solution
            display_transport_proposal(problem, proposal)
            display_graph(proposal)
            print(f"Current cost: {total_cost(problem, proposal)}")

            if is_degenerate(problem, proposal):
                print("The proposal is degenerate")

            # Connectivity
            test_connectivity(proposal)

            # Fix if not connected
            proposal = connect_graph(problem, proposal)

            graph = build_graph(proposal)
            if detect_cycle(graph):
                print("Graph contains a cycle.")

            # Potentials
            u, v = compute_potentials(problem, proposal)

            print("\nPotentials:")
            print("u =", u)
            print("v =", v)

            # Tables costs
            display_potential_costs(problem, u, v)
            display_marginal_costs(problem, u, v)

            # Optimality check
            print("\n--- Checking optimality ---")

            cell, value = find_improving_cell(problem, u, v, proposal)

            if cell is None:
                print("=> IT IS THE OPTIMAL SOLUTION")
                break

            print(f"Improving edge: S{cell[0]+1}, C{cell[1]+1} (delta = {value})")

            # Find cycle
            cycle = find_cycle(proposal, cell)

            if not cycle:
                print("No cycle found => STOP")
                break

            # Transportation maximization
            transportation_maximization(proposal, cycle)

            # Apply update
            update_proposal(proposal, cycle)

        # -----------------------------------
        # Final result
        # -----------------------------------
        print("\n===============")
        print(" FINAL SOLUTION ")
        print("===============")

        display_transport_proposal(problem, proposal)
        print(f"Final cost: {total_cost(problem, proposal)}")

        # Ask the user to test another problem
        cont = input("\nTest another problem? (y/n): ").lower()
        if cont != "y":
            print("Exiting")
            break


if __name__ == "__main__":
    main()