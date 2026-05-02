import random 
import time 
import matplotlib.pyplot as plt
from north_west import *
from Balas_hammer import *
from read_problem import *
from graph_utils import *
from stepping_stone_utils import *

# Valeurs de n demandées
n_values = [10, 1000] # 10, 40, 100, 400, 1000, 40000, 10000
nb_Test = 100

def generate_transport_problem(n):
    '''
    Génération d'un problème de transport carré aléatoire.
    '''
    costs = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]
    temp = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]
    
    provisions = [sum(row) for row in temp]
    orders = [sum(col) for col in zip(*temp)] 
    
    return {
        "n": n,
        "m": n,
        "costs": costs,
        "provisions": provisions,
        "orders": orders
    }

def measure_time(func, *args): 
    """ Retourne le temps CPU d'exécution précis """ 
    start = time.process_time()
    result = func(*args) 
    end = time.process_time() 
    return end - start, result

def stepping_stone(problem, proposal, display=False):
    """
    Paramètre display ajouté : par défaut à False pour ne pas polluer 
    la console et fausser les temps d'exécution lors du benchmark.
    """
    while True:
        cycle = detect_cycle(proposal)
        if cycle:
            if display: print("Graph contains a cycle.")
            transportation_maximization(proposal, cycle)
            update_proposal(proposal, cycle)
            continue

        test_connectivity(proposal)
        graph = build_graph(proposal)

        if len(find_connected_components(graph)) == 1:
            break

        proposal = connect_graph(problem, proposal)

    u, v = compute_potentials(problem, proposal)

    if display:
        print("u =", u)
        print("v =", v)
        display_potential_costs(problem, u, v)
        display_marginal_costs(problem, u, v)
        print("\n--- Checking optimality ---")

    cell, value = find_improving_cell(problem, u, v, proposal)

    if cell is None:
        if display: print("=> IT IS THE OPTIMAL SOLUTION")
        return proposal

    cycle = find_cycle(proposal, cell)

    if not cycle:
        if display: print("No cycle found => STOP")
        return proposal

    transportation_maximization(proposal, cycle)
    update_proposal(proposal, cycle)
   
def complexity():
    results = {
        "NO": {n: [] for n in n_values},
        "BH": {n: [] for n in n_values},
        "tNO": {n: [] for n in n_values},
        "tBH": {n: [] for n in n_values}
    }
    
    for n in n_values: 
        print(f"Test en cours pour n = {n}...") 
        for test in range(nb_Test): 
            problem = generate_transport_problem(n)

            t_no, sol_no = measure_time(north_west, problem)
            results["NO"][n].append(t_no)

            t_bh, sol_bh = measure_time(balas_hammer, problem)
            results["BH"][n].append(t_bh)

            t_tno, _ = measure_time(stepping_stone, problem, sol_no)
            results["tNO"][n].append(t_tno)

            t_tbh, _ = measure_time(stepping_stone, problem, sol_bh)
            results["tBH"][n].append(t_tbh)

    worst = {
        key: [max(results[key][n]) for n in n_values]
        for key in results
    }

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    plot_mappings = [
        (axs[0, 0], "NO", "North-West"),
        (axs[0, 1], "BH", "Balas-Hammer"),
        (axs[1, 0], "tNO", "Stepping stone North-West"),
        (axs[1, 1], "tBH", "Stepping stone Balas-Hammer")
    ]
    
    for ax, key, title in plot_mappings:
        for n in n_values:
            ax.scatter([n] * nb_Test, results[key][n], label=f"n={n}")
        ax.set_title(f"Scatter Plot - {title}")
        ax.set_xlabel("n")
        ax.set_ylabel("Execution time (s)")
        ax.grid(True)
        ax.legend()
        
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(8, 5)) 
    plt.plot(n_values, worst["NO"], marker='o', label="Worst θNO(n)") 
    plt.plot(n_values, worst["BH"], marker='o', label="Worst θBH(n)") 
    plt.title("Worst-case Complexity") 
    plt.xlabel("n") 
    plt.ylabel("Time max (s)") 
    plt.legend() 
    plt.grid(True) 
    plt.show()
    
    ratios = [
        (worst["NO"][i] + worst["tNO"][i]) / (worst["BH"][i] + worst["tBH"][i]) 
        if (worst["BH"][i] + worst["tBH"][i]) != 0 else 0 
        for i in range(len(n_values))
    ]
    
    plt.figure(figsize=(8, 5)) 
    plt.plot(n_values, ratios, marker='o', color='purple') 
    plt.title("Worst case comparison Ratio: (NO+tNO) / (BH+tBH)")
    plt.xlabel("n") 
    plt.ylabel("Ratio") 
    plt.grid(True) 
    plt.show() 

if __name__ == "__main__":
    complexity()