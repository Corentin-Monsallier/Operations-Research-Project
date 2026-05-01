import random 
import time 
import matplotlib.pyplot as plt
from north_west import *
from Balas_hammer import *
from read_problem import *
from graph_utils import *
from stepping_stone_utils import *

#Asked value of n (after add 100, 400, 1000)
n_values = [10,40]
#Total number of test
nb_Test = 100

def generate_transport_problem(n):
    '''
    The idea is to create random square transport problem depending of the size of n to test the complexity
    '''
    costs = [ [random.randint(1, 100) for _ in range(n)] for _ in range(n) ]
    temp = [ [random.randint(1, 100) for _ in range(n)] for _ in range(n) ]
    provisions = [sum(temp[i]) for i in range(n)]
    orders = [ sum(temp[i][j] for i in range(n)) for j in range(n) ]
    return {
        "n": n,
        "m": n,
        "costs": costs,
        "provisions": provisions,
        "orders": orders
    }

def measure_time(func, *args): 
    """ Return the time of execution """ 
    start = time.time() 
    result = func(*args) 
    end = time.time() 
    return end - start, result

def stepping_stone(problem,proposal):
    while True:
        cycle = detect_cycle(proposal)
        if cycle:
            print("Graph contains a cycle.")
            transportation_maximization(proposal, cycle)
            update_proposal(proposal, cycle)
            continue

        test_connectivity(proposal)
        graph = build_graph(proposal)

        if len(find_connected_components(graph)) == 1:
            break

        proposal = connect_graph(problem, proposal)

    # Potentials
    u, v = compute_potentials(problem, proposal)

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
        return proposal

    # Find cycle
    cycle = find_cycle(proposal, cell)

    if not cycle:
        print("No cycle found => STOP")
        return proposal

    # Transportation maximization
    transportation_maximization(proposal, cycle)

    # Apply update
    update_proposal(proposal, cycle)
   
def complexity():
    #Stock for result
    times_NO = {} # θNO(n) 
    times_BH = {} # θBH(n) 
    times_tNO = {} # tNO(n) 
    times_tBH = {} # tBH(n) 
    for n in n_values: 
        print(f"Test of n = {n}") 
        times_NO[n] = [] 
        times_BH[n] = [] 
        times_tNO[n] = [] 
        times_tBH[n] = [] 
        for test in range(nb_Test): 
            problem = generate_transport_problem(n)

            #North-west
            t_no, sol_no = measure_time(north_west,problem)
            times_NO[n].append(t_no)

            #Balas-Hammer
            t_bh, sol_bh = measure_time(balas_hammer,problem)
            times_BH[n].append(t_bh)

            #Stepping-stone North-west
            t_tno, sol_tno = measure_time(stepping_stone,problem,sol_no)
            times_tNO[n].append(t_tno)

            #Stepping-stone Balas-Hammer
            t_tbh, sol_tbh = measure_time(stepping_stone,problem,sol_bh)
            times_tBH[n].append(t_tbh)

    # Worst case = max of the Total nb of test
    worst_NO = [] 
    worst_BH = [] 
    worst_tNO = [] 
    worst_tBH = [] 
    for n in n_values: 
        worst_NO.append(max(times_NO[n])) 
        worst_BH.append(max(times_BH[n])) 
        worst_tNO.append(max(times_tNO[n])) 
        worst_tBH.append(max(times_tBH[n]))

    #Plot test North-west and have visual
    plt.figure(figsize=(10, 6)) 
    for n in n_values: 
        plt.scatter( 
            [n] * nb_Test, 
            times_NO[n], 
            label=f"n={n}" if n == n_values[0] else "" ) 
    plt.title("Scatter Plot - North-West") 
    plt.xlabel("n") 
    plt.ylabel("Execution time") 
    plt.grid() 
    plt.show()

    #Plot test Balas-Hammer and have visual
    plt.figure(figsize=(10, 6)) 
    for n in n_values: 
        plt.scatter( 
            [n] * nb_Test, 
            times_BH[n], 
            label=f"n={n}" if n == n_values[0] else "" ) 
    plt.title("Scatter Plot - Balas-Hammer") 
    plt.xlabel("n") 
    plt.ylabel("Execution time") 
    plt.grid() 
    plt.show()

    #Plot test stepping-stone North-west and have visual
    plt.figure(figsize=(10, 6)) 
    for n in n_values: 
        plt.scatter( 
            [n] * nb_Test, 
            times_tNO[n], 
            label=f"n={n}" if n == n_values[0] else "" ) 
    plt.title("Scatter Plot - Stepping stone North-West") 
    plt.xlabel("n") 
    plt.ylabel("Execution time") 
    plt.grid() 
    plt.show()

    #Plot test stepping-stone Balas-Hammer and have visual
    plt.figure(figsize=(10, 6)) 
    for n in n_values: 
        plt.scatter( 
            [n] * nb_Test, 
            times_tBH[n], 
            label=f"n={n}" if n == n_values[0] else "" ) 
    plt.title("Scatter Plot - Stepping stone Balas-Hammer") 
    plt.xlabel("n") 
    plt.ylabel("Execution time") 
    plt.grid() 
    plt.show()


    #Plot worst case and have visual
    plt.figure(figsize=(10, 6)) 
    plt.plot(n_values, worst_NO, marker='o', label="Worst θNO(n)") 
    plt.plot(n_values, worst_BH, marker='o', label="Worst θBH(n)") 
    plt.title("Worst-case Complexity") 
    plt.xlabel("n") 
    plt.ylabel("Time max") 
    plt.legend() 
    plt.grid() 
    plt.show()

    
    #Final ratio for comparison
    ratio = [] 
    for i in range(len(n_values)): 
        num = worst_NO[i] + worst_tNO[i] 
        den = worst_BH[i] + worst_tBH[i] 
        if den != 0: ratio.append(num / den) 
        else: 
            ratio.append(0) 
    plt.figure(figsize=(10, 6)) 
    plt.plot(n_values, ratio, marker='o') 
    plt.title("Worst case comparison")
    plt.xlabel("n") 
    plt.ylabel("Ratio") 
    plt.grid() 
    plt.show() 
    

if __name__ == "__main__":
    complexity()