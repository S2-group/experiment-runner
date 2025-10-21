import os
import sys
import time
import subprocess
import json
from pathlib import Path


class BenchmarkRunner:
    def __init__(self):
        self.benchmarks = [
            'binary_trees', 'dac_mergesort', 'dijkstra', 'fannkuch',
            'insertionsort', 'mandlebrot', 'nbody', 'recur_matrix_multiplication',
            'richards', 'spectral_norm'
        ]
        self.variants = ['original', 'cython_variant', 'numba_variant']
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)

    def run_single_benchmark(self, benchmark, variant, args=None):
        benchmark_dir = Path('benchmarks') / benchmark
        
        if variant == 'original':
            script_path = benchmark_dir / 'original.py'
        elif variant == 'cython_variant':
            script_path = benchmark_dir / 'cython_variant.py'
        elif variant == 'numba_variant':
            script_path = benchmark_dir / 'numba_variant.py'
        
        if not script_path.exists():
            print(f"WARNING: {script_path} not found")
            return None

        cmd = ['python3.13', str(script_path)]
        if args:
            cmd.extend(args)

        print(f"running {benchmark}/{variant}...")
        
        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,
                cwd=os.getcwd()
            )
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            return {
                'benchmark': benchmark,
                'variant': variant,
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': time.time()
            }
            
        except subprocess.TimeoutExpired:
            print(f"timeout: {benchmark}/{variant}")
            return {
                'benchmark': benchmark,
                'variant': variant,
                'execution_time': 300,
                'return_code': -1,
                'stdout': '',
                'stderr': 'Timeout',
                'timestamp': time.time()
            }

    def run_all_benchmarks(self, repetitions=10):
        results = []
        
        for benchmark in self.benchmarks:
            for variant in self.variants:
                for rep in range(repetitions):
                    print(f"running {benchmark}/{variant} (repetition {rep+1}/{repetitions})")

                    result = self.run_single_benchmark(benchmark, variant, ['10'])
                    
                    if result:
                        result['repetition'] = rep
                        results.append(result)

                    time.sleep(2)

        results_file = self.results_dir / f'benchmark_results_{int(time.time())}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(results_file)
        return results

    def run_warm_benchmarks(self, repetitions=10):
        results = []
        
        for benchmark in self.benchmarks:
            for variant in self.variants:
                print(f"warm run: {benchmark}/{variant}")

                cold_result = self.run_single_benchmark(benchmark, variant, ['10'])
                if cold_result:
                    cold_result['phase'] = 'cold_start'
                    cold_result['repetition'] = 0
                    results.append(cold_result)

                for rep in range(1, repetitions + 1):
                    warm_result = self.run_single_benchmark(benchmark, variant, ['10'])
                    if warm_result:
                        warm_result['phase'] = 'steady_state'
                        warm_result['repetition'] = rep
                        results.append(warm_result)

                    time.sleep(0.5)
                time.sleep(5)

        results_file = self.results_dir / f'warm_benchmark_results_{int(time.time())}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(results_file)
        return results


if __name__ == "__main__":
    runner = BenchmarkRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "warm":
        runner.run_warm_benchmarks()
    else:
        runner.run_all_benchmarks()
