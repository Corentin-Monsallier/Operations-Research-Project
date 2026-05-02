import argparse
import csv
import os
import random
import time

import matplotlib.pyplot as plt
import numpy as np

from north_west import north_west
from Balas_hammer import balas_hammer
from stepping_stone_utils import solve_stepping_stone

# Limit multithreading for reproducibility and fair timing
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# Configure Matplotlib cache locally (avoids permission issues)
mpl_cache_dir = os.path.join(os.path.dirname(__file__), ".matplotlib-cache")
os.makedirs(mpl_cache_dir, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", mpl_cache_dir)

# Default experiment parameters and directories for plots and raw data
DEFAULT_N_VALUES = [10, 40, 100, 400, 1000, 4000, 10000]
DEFAULT_NB_TEST = 100
PLOT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "complexity_plots")
RESULTS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "complexity_results")


# Generate a random transport problem of size n x n
def generate_transport_problem(n):
    """
    Generates a balanced random transport problem:
    - cost matrix
    - supply (provisions)
    - demand (orders)
    """
    costs = np.random.randint(1, 101, size=(n, n), dtype=np.int16)

    orders = np.zeros(n, dtype=np.int64)
    provisions = [0] * n
    # Chunking to avoid excessive memory usage for large n
    chunk_rows = max(1, min(256, 2_000_000 // max(n, 1)))

    for start in range(0, n, chunk_rows):
        stop = min(start + chunk_rows, n)
        temp_chunk = np.random.randint(1, 101, size=(stop - start, n), dtype=np.int16)

        # Compute row sums (supply)
        provisions[start:stop] = temp_chunk.sum(axis=1, dtype=np.int64).tolist()

        # Accumulate column sums (demand)
        orders += temp_chunk.sum(axis=0, dtype=np.int64)

    orders = orders.tolist()

    return {
        "n": n,
        "m": n,
        "costs": costs,
        "provisions": provisions,
        "orders": orders,
    }


# Measure CPU execution time of a function
def measure_time(func, *args):
    """Returns CPU time and function result."""
    start = time.process_time()
    result = func(*args)
    end = time.process_time()
    return end - start, result


# Initialize result storage structure
def _empty_results(n_values):
    """
    Creates a dictionary of lists for storing timings:
    - NO: North-West
    - BH: Balas-Hammer
    - tNO / tBH: Stepping-Stone improvements
    - *_total: combined times
    """
    return {
        "NO": {n: [] for n in n_values},
        "BH": {n: [] for n in n_values},
        "tNO": {n: [] for n in n_values},
        "tBH": {n: [] for n in n_values},
        "NO_total": {n: [] for n in n_values},
        "BH_total": {n: [] for n in n_values},
    }


# Format durations for logging
def _format_duration(seconds):
    """Readable duration formatting."""
def _format_duration(seconds):
    seconds = max(0.0, float(seconds))

    if seconds < 60:
        return f"{seconds:.4f}s"

    minutes, sec = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"

    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m{sec:02d}s"


# Save or display figures depending on backend
def _finalize_figure(filename):
    backend = plt.get_backend().lower()

    if "agg" in backend:
        os.makedirs(PLOT_OUTPUT_DIR, exist_ok=True)
        plt.savefig(os.path.join(PLOT_OUTPUT_DIR, filename), bbox_inches="tight")
        plt.close()
    else:
        plt.show()


# Save all raw timing results to CSV
def _save_results_csv(results, n_values):
    os.makedirs(RESULTS_OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_OUTPUT_DIR, "raw_results.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "n", "test_index", "time_seconds"])

        for metric in results:
            for n in n_values:
                for idx, value in enumerate(results[metric][n], start=1):
                    writer.writerow([metric, n, idx, value])


# Save worst-case values to CSV
def _save_worst_csv(worst, n_values):
    os.makedirs(RESULTS_OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_OUTPUT_DIR, "worst_case_results.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "n", "worst_time_seconds"])

        for metric in worst:
            for idx, n in enumerate(n_values):
                writer.writerow([metric, n, worst[metric][idx]])


# Compute worst-case (max) timings
def _worst_case(results, n_values):
    return {
        key: [max(results[key][n]) for n in n_values]
        for key in results
    }


# Scatter plots of all runs (with annotations)
def _plot_metric_panels(results, n_values, nb_test):
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    plot_mappings = [
        (axs[0, 0], "NO", "Scatter Plot - thetaNW(n)"),
        (axs[0, 1], "BH", "Scatter Plot - thetaBH(n)"),
        (axs[0, 2], "tNO", "Scatter Plot - tNW(n)"),
        (axs[1, 0], "tBH", "Scatter Plot - tBH(n)"),
        (axs[1, 1], "NO_total", "Scatter Plot - thetaNW(n) + tNW(n)"),
        (axs[1, 2], "BH_total", "Scatter Plot - thetaBH(n) + tBH(n)"),
    ]

    for ax, key, title in plot_mappings:
        for n in n_values:
            values = results[key][n]
            ax.scatter([n] * nb_test, values, label=f"n={n}", s=12)

            for i, val in enumerate(values):
                ax.text(n, val, f"{val:.4f}", fontsize=8)
        ax.set_title(title)
        ax.set_xlabel("n")
        ax.set_ylabel("Execution time (s)")
        ax.grid(True)
        ax.legend()

    plt.tight_layout()
    _finalize_figure("scatter_plots.png")


# Worst-case plots (max per n)
def _plot_worst_case_panels(worst, n_values):
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))
    plot_mappings = [
        (axs[0, 0], "NO", "Worst-case thetaNW(n)"),
        (axs[0, 1], "BH", "Worst-case thetaBH(n)"),
        (axs[0, 2], "tNO", "Worst-case tNW(n)"),
        (axs[1, 0], "tBH", "Worst-case tBH(n)"),
        (axs[1, 1], "NO_total", "Worst-case thetaNW(n) + tNW(n)"),
        (axs[1, 2], "BH_total", "Worst-case thetaBH(n) + tBH(n)"),
    ]

    for ax, key, title in plot_mappings:
        y_values = worst[key]
        ax.plot(n_values, y_values, marker="o")

        for x, y in zip(n_values, y_values):
            ax.text(x, y, f"{y:.4f}", fontsize=8, ha='center', va='bottom')

        ax.set_title(title)
        ax.set_xlabel("n")
        ax.set_ylabel("Time max (s)")
        ax.grid(True)

    plt.tight_layout()
    _finalize_figure("worst_case_plots.png")


# Plot ratio between NW and BH total times
def _plot_ratio(worst, n_values):
    ratios = [
        (worst["NO_total"][i] / worst["BH_total"][i])
        if worst["BH_total"][i] != 0 else 0
        for i in range(len(n_values))
    ]

    plt.figure(figsize=(8, 5))
    plt.plot(n_values, ratios, marker="o", color="purple")

    for x, y in zip(n_values, ratios):
        plt.text(x, y, f"{y:.4f}", fontsize=8, ha='center', va='bottom')

    plt.title("Worst-case comparison ratio: (thetaNW+tNW) / (thetaBH+tBH)")
    plt.xlabel("n")
    plt.ylabel("Ratio")
    plt.grid(True)

    _finalize_figure("worst_case_ratio.png")


# Main experiment loop
def complexity(n_values=None, nb_test=DEFAULT_NB_TEST):
    if n_values is None:
        n_values = DEFAULT_N_VALUES

    results = _empty_results(n_values)
    total_sizes = len(n_values)
    global_start = time.perf_counter()
    completed_runs = 0
    total_runs = total_sizes * nb_test

    for size_index, n in enumerate(n_values, start=1):
        print(f"[{size_index}/{total_sizes}] Test en cours pour n = {n}...", flush=True)
        size_start = time.perf_counter()

        for test_index in range(1, nb_test + 1):
            run_start = time.perf_counter()
            problem = generate_transport_problem(n)

            t_no, sol_no = measure_time(north_west, problem)
            results["NO"][n].append(t_no)

            t_tno, _ = measure_time(solve_stepping_stone, problem, sol_no, False)
            results["tNO"][n].append(t_tno)
            del sol_no

            t_bh, sol_bh = measure_time(balas_hammer, problem)
            results["BH"][n].append(t_bh)

            t_tbh, _ = measure_time(solve_stepping_stone, problem, sol_bh, False)
            results["tBH"][n].append(t_tbh)
            del sol_bh

            results["NO_total"][n].append(t_no + t_tno)
            results["BH_total"][n].append(t_bh + t_tbh)

            completed_runs += 1
            run_elapsed = time.perf_counter() - run_start
            size_elapsed = time.perf_counter() - size_start
            total_elapsed = time.perf_counter() - global_start
            avg_run_for_size = size_elapsed / test_index
            eta_size = avg_run_for_size * (nb_test - test_index)
            avg_run_global = total_elapsed / completed_runs
            eta_global = avg_run_global * (total_runs - completed_runs)

            print(
                (
                    f"  n={n} | test {test_index}/{nb_test}"
                    f" | last={_format_duration(run_elapsed)}"
                    f" | avg_n={_format_duration(avg_run_for_size)}"
                    f" | elapsed_n={_format_duration(size_elapsed)}"
                    f" | eta_n={_format_duration(eta_size)}"
                    f" | total_elapsed={_format_duration(total_elapsed)}"
                    f" | eta_total={_format_duration(eta_global)}"
                ),
                flush=True,
            )

        _save_results_csv(results, n_values)

    worst = _worst_case(results, n_values)
    _save_worst_csv(worst, n_values)

    _plot_metric_panels(results, n_values, nb_test)
    _plot_worst_case_panels(worst, n_values)
    _plot_ratio(worst, n_values)

    return results, worst


# CLI argument parsing
def _parse_args():
    parser = argparse.ArgumentParser(description="Complexity study for the transport project.")
    parser.add_argument(
        "--n-values",
        nargs="+",
        type=int,
        default=DEFAULT_N_VALUES,
        help="Problem sizes to test. Defaults to the values requested in the subject.",
    )
    parser.add_argument(
        "--nb-test",
        type=int,
        default=DEFAULT_NB_TEST,
        help="Number of random runs for each size.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    complexity(n_values=args.n_values, nb_test=args.nb_test)
