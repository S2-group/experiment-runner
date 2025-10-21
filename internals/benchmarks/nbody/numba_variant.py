import sys
from numba import jit
import numpy as np

@jit(nopython=True)
def combinations_numba(bodies):
    n = len(bodies)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((i, j))
    return pairs

def combinations(l):
    return [(l[i], l[j]) for i, j in combinations_numba(list(range(len(l))))]

PI = 3.14159265358979323
SOLAR_MASS = 4 * PI * PI
DAYS_PER_YEAR = 365.24

BODIES = {
    'sun': ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], SOLAR_MASS),

    'jupiter': ([4.84143144246472090e+00,
                 -1.16032004402742839e+00,
                 -1.03622044471123109e-01],
                [1.66007664274403694e-03 * DAYS_PER_YEAR,
                 7.69901118419740425e-03 * DAYS_PER_YEAR,
                 -6.90460016972063023e-05 * DAYS_PER_YEAR],
                9.54791938424326609e-04 * SOLAR_MASS),

    'saturn': ([8.34336671824457987e+00,
                4.12479856412430479e+00,
                -4.03523417114321381e-01],
               [-2.76742510726862411e-03 * DAYS_PER_YEAR,
                4.99852801234917238e-03 * DAYS_PER_YEAR,
                2.30417297573763929e-05 * DAYS_PER_YEAR],
               2.85885980666130812e-04 * SOLAR_MASS),

    'uranus': ([1.28943695621391310e+01,
                -1.51111514016986312e+01,
                -2.23307578892655734e-01],
               [2.96460137564761618e-03 * DAYS_PER_YEAR,
                2.37847173959480950e-03 * DAYS_PER_YEAR,
                -2.96589568540237556e-05 * DAYS_PER_YEAR],
               4.36624404335156298e-05 * SOLAR_MASS),

    'neptune': ([1.53796971148509165e+01,
                 -2.59193146099879641e+01,
                 1.79258772950371181e-01],
                [2.68067772490389322e-03 * DAYS_PER_YEAR,
                 1.62824170038242295e-03 * DAYS_PER_YEAR,
                 -9.51592254519715870e-05 * DAYS_PER_YEAR],
                5.15138902046611451e-05 * SOLAR_MASS) }

SYSTEM = list(BODIES.values())
PAIRS = combinations(SYSTEM)

@jit(nopython=True)
def advance_numba(dt, n, positions, velocities, masses, pair_indices):
    for _ in range(n):
        for pair_idx in range(len(pair_indices)):
            i, j = pair_indices[pair_idx]
            
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            dz = positions[i][2] - positions[j][2]
            
            mag = dt * ((dx * dx + dy * dy + dz * dz) ** (-1.5))
            b1m = masses[i] * mag
            b2m = masses[j] * mag
            
            velocities[i][0] -= dx * b2m
            velocities[i][1] -= dy * b2m
            velocities[i][2] -= dz * b2m
            velocities[j][0] += dx * b1m
            velocities[j][1] += dy * b1m
            velocities[j][2] += dz * b1m
        
        for i in range(len(positions)):
            positions[i][0] += dt * velocities[i][0]
            positions[i][1] += dt * velocities[i][1]
            positions[i][2] += dt * velocities[i][2]

def advance(dt, n, bodies=SYSTEM, pairs=PAIRS):
    positions = np.array([body[0] for body in bodies], dtype=np.float64)
    velocities = np.array([body[1] for body in bodies], dtype=np.float64)
    masses = np.array([body[2] for body in bodies], dtype=np.float64)
    pair_indices = np.array([(i, j) for i, j in combinations_numba(list(range(len(bodies))))], dtype=np.int32)
    
    advance_numba(dt, n, positions, velocities, masses, pair_indices)
    
    for i, body in enumerate(bodies):
        body[0][:] = positions[i]
        body[1][:] = velocities[i]

@jit(nopython=True)
def report_energy_numba(positions, velocities, masses, pair_indices):
    e = 0.0
    
    for pair_idx in range(len(pair_indices)):
        i, j = pair_indices[pair_idx]
        dx = positions[i][0] - positions[j][0]
        dy = positions[i][1] - positions[j][1]
        dz = positions[i][2] - positions[j][2]
        e -= (masses[i] * masses[j]) / ((dx * dx + dy * dy + dz * dz) ** 0.5)
    
    for i in range(len(positions)):
        vx, vy, vz = velocities[i][0], velocities[i][1], velocities[i][2]
        e += masses[i] * (vx * vx + vy * vy + vz * vz) / 2.0
    
    return e

def report_energy(bodies=SYSTEM, pairs=PAIRS, e=0.0):
    positions = np.array([body[0] for body in bodies], dtype=np.float64)
    velocities = np.array([body[1] for body in bodies], dtype=np.float64)
    masses = np.array([body[2] for body in bodies], dtype=np.float64)
    pair_indices = np.array([(i, j) for i, j in combinations_numba(list(range(len(bodies))))], dtype=np.int32)
    
    energy = report_energy_numba(positions, velocities, masses, pair_indices)
    print("%.9f" % energy)

def offset_momentum(ref, bodies=SYSTEM, px=0.0, py=0.0, pz=0.0):
    for (r, [vx, vy, vz], m) in bodies:
        px -= vx * m
        py -= vy * m
        pz -= vz * m
    (r, v, m) = ref
    v[0] = px / m
    v[1] = py / m
    v[2] = pz / m

def main(n, ref='sun'):
    offset_momentum(BODIES[ref])
    advance(0.01, n)

if __name__ == '__main__':
    import time

    n = 500000

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    main(n)
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    main(n)
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")