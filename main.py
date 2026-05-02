import os
import re
from read_problem import *
from north_west import *
from Balas_hammer import *
from graph_utils import *
from stepping_stone_utils import *

# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------
# This file links all the modules together and manages the user dialogue.
# Its role is:
# 1. ask in which folder the .txt problems are found
# 2. let the user choose a problem
# 3. read and display the cost matrix
# 4. build an initial solution (North-West or Balas-Hammer)
# 5. launch the stepping-stone to reach the optimum
# 6. display the final solution then suggest starting again
# --------------------------------------------------


def main():
    # We store the last valid folder so as not to ask for it again
    # at each new problem tested.
    folder = None

    # Main loop: one turn = complete resolution of one problem.
    while True:
        print("\n===============================================")
        print(" OPERATION RESEARCH PROJECT - TRANSPORT PROBLEM ")
        print("===============================================")

        # We ask for the folder only the first time, or if the memorized
        # path no longer exists.
        if folder is None or not os.path.exists(folder):
            folder = input("\nPath to problem folder: ").strip()

        # Basic verification of the entered path.
        if not os.path.exists(folder):
            print("Folder not found.")
            folder = None
            continue

        # We keep only the text files of the folder.
        files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")], key=lambda f: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', f)])

        if not files:
            print("No .txt files found.")
            continue

        # Display of the numbered list of available problems.
        print("\nAvailable problems:")
        for i, f in enumerate(files):
            print(f"{i+1}. {f}")

        try:
            # We convert the user choice into a list index.
            choice = int(input("\nChoose problem: ")) - 1

            # We then build the full path to this file.
            filepath = os.path.join(folder, files[choice])
        except:
            # Any failure here means that the input was not usable.
            print("Invalid choice.")
            continue

        # Reading of the chosen file, then display of the cost matrix.
        problem = read_problem(filepath)
        display_cost_matrix(problem)

        # Choice of the initial solution method.
        print("\nChoose initial solution method:")
        print("1. North-West")
        print("2. Balas-Hammer")

        algo = input("Choice: ")

        if algo == "1":
            # Simple method of the north-west corner.
            proposal = north_west(problem)
        elif algo == "2":
            # Balas-Hammer method with detailed trace.
            proposal = balas_hammer(problem, display=True)
        else:
            print("Invalid choice.")
            continue

        # Display of the initial solution before optimization.
        print("\n--- INITIAL PROPOSAL ---")

        # We display the table of proposed flows after the initial algorithm.
        display_transport_proposal(problem, proposal)

        # Then its representation as a bipartite graph.
        display_graph(proposal)

        # And finally the total cost associated with this first solution.
        print(f"Initial cost: {total_cost(problem, proposal)}")

        # Launch of the stepping-stone algorithm until the optimal solution.
        proposal = solve_stepping_stone(problem, proposal, verbose=True)

        # -----------------------------------
        # Final result
        # -----------------------------------
        print("\n===============")
        print(" FINAL SOLUTION ")
        print("===============")

        display_transport_proposal(problem, proposal)
        print(f"Final cost: {total_cost(problem, proposal)}")

        # Suggestion to restart a new test.
        cont = input("\nTest another problem? (y/n): ").lower()
        if cont != "y":
            print("Exiting")
            break


if __name__ == "__main__":
    # This block guarantees that main() starts only if this file
    # is executed directly, and not when it is imported elsewhere.
    main()
