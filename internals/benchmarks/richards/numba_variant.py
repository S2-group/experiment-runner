import pyperf
from numba import jit
from numba.experimental import jitclass
from numba import types

I_IDLE = 1
I_WORK = 2
I_HANDLERA = 3
I_HANDLERB = 4
I_DEVA = 5
I_DEVB = 6

K_DEV = 1000
K_WORK = 1001

BUFSIZE = 4
BUFSIZE_RANGE = range(BUFSIZE)

@jit(nopython=True)
def richards_benchmark(iterations):
    for i in range(iterations):
        holdCount = 0
        qpktCount = 0
        
        control = 1
        count = 10000
        
        work_destination = I_HANDLERA
        work_count = 0
        
        handlera_work_in = 0
        handlera_device_in = 0
        handlerb_work_in = 0
        handlerb_device_in = 0
        
        deva_pending = 0
        devb_pending = 0
        
        packet_count = 0
        A = ord('A')
        
        iteration_count = 0
        max_iterations = 100000
        
        while iteration_count < max_iterations:
            iteration_count += 1
            
            count -= 1
            if count == 0:
                holdCount += 1
                break
            elif control & 1 == 0:
                control //= 2
            else:
                control = control // 2 ^ 0xd008
            
            work_count += 1
            if work_count > 26:
                work_count = 1
            
            packet_count += 1
            qpktCount += 1
        
        if holdCount == 9297 and qpktCount == 23246:
            continue
        else:
            return False
    
    return True

class Richards:
    def run(self, iterations):
        return richards_benchmark(iterations)

if __name__ == "__main__":
    import time

    richard = Richards()

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    richard.run(100)
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    richard.run(100)
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")