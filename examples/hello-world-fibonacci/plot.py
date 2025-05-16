import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import seaborn as sb
import sys
import os

exp_path = os.path.join("examples", "hello-world-fibonacci")

if __name__ == "__main__":
    if not os.path.exists(os.path.join(exp_path, "experiments", "new_runner_experiment")):
        print("Please run the example, so a valid 'experiments' directory exists")
        exit(1)
    
    results = pd.read_csv(os.path.join(exp_path, "experiments", "new_runner_experiment", "run_table.csv"))
    
    print(results)

    sb.stripplot(data=results,
                 x="fib_type", 
                 y="energy",
                 hue="problem_size",
                 palette="Paired",
                 order=["mem", "iter", "rec"],
                 jitter=True)

    plt.xlabel("Fibonacci Type")
    plt.ylabel("Energy Consumption (Joules)")
    plt.title("ER Demo Results")
    
    plt.savefig(os.path.join(exp_path, "fib_plot.png"))


    

    
