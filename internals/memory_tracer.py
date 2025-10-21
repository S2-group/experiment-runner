import time
import os
import psutil


container_name = "test_container"

def find_container():
    pid = ""
    while pid == "" or pid == "0":
        pid = os.popen('docker inspect -f "{{.State.Pid}}" ' + container_name + " 2>/dev/null").read().strip()
    
    print("pid found ", pid)
    pid = int(pid)
    return pid



def total_memory_usage(pid):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    total_memory = parent.memory_info().rss
    for child in children:
        total_memory += child.memory_info().rss
    total_memory = total_memory 
    return total_memory

def monitor_memory_usage(pid):
    results = []
    while True:
        try:
            memory_usage = int(total_memory_usage(pid))
        except psutil.NoSuchProcess:
            results1, results2 = [], []
            max_memory1, max_memory2 = 0, 0
            cold_start_finish = float(os.popen('docker logs ' + container_name + " 2>/dev/null").read().strip())
            os.popen('docker rm ' + container_name + " 2>/dev/null")
            for r in results:
                if r[0] <= cold_start_finish:
                    results1.append(r)
                    max_memory1 = max(max_memory1, r[1])
                else:
                    results2.append(r)
                    max_memory2 = max(max_memory2, r[1])
            print("cold start max memory:", max_memory1)
            print("steady execution max memory:", max_memory2)
            print(cold_start_finish)
            print("-"*50)
            with open("/tmp/test_container.log", "w") as f:
                f.write(str(int(cold_start_finish * 1000)))
            with open("/tmp/test_container_memory_usage", "w") as f:
                f.write(str(max_memory1) + "\n" + str(max_memory2))
            return 0
        results.append((time.time(), memory_usage))


while(True):
    os.popen('docker rm ' + container_name + " 2>/dev/null")
    pid = find_container()
    monitor_memory_usage(pid)