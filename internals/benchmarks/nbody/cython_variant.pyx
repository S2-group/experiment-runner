# cython: language_level=3
import sys
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cdef list combinations_cython(list l):
    cdef list result = []
    cdef int x, y_idx
    cdef int l_len = len(l)
    
    for x in range(l_len - 1):
        ls = l[x+1:]
        for y in ls:
            result.append((l[x], y))
    return result

def combinations(l):
    return combinations_cython(l)

cdef double PI = 3.14159265358979323
cdef double SOLAR_MASS = 4 * PI * PI
cdef double DAYS_PER_YEAR = 365.24

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

@cython.boundscheck(False)
@cython.wraparound(False)
cdef void advance_cython(double dt, int n, list bodies, list pairs):
    cdef int i
    cdef double x1, y1, z1, x2, y2, z2
    cdef double dx, dy, dz, mag, b1m, b2m, m1, m2
    cdef list r1, v1, r2, v2, r
    cdef double vx, vy, vz, m

    for i in range(n):
        for pair in pairs:
            (r1, v1, m1), (r2, v2, m2) = pair
            x1, y1, z1 = r1
            x2, y2, z2 = r2
            dx = x1 - x2
            dy = y1 - y2
            dz = z1 - z2
            mag = dt * ((dx * dx + dy * dy + dz * dz) ** (-1.5))
            b1m = m1 * mag
            b2m = m2 * mag
            v1[0] -= dx * b2m
            v1[1] -= dy * b2m
            v1[2] -= dz * b2m
            v2[0] += dx * b1m
            v2[1] += dy * b1m
            v2[2] += dz * b1m
        for body in bodies:
            r, v, m = body
            vx, vy, vz = v
            r[0] += dt * vx
            r[1] += dt * vy
            r[2] += dt * vz

def advance(dt, n, bodies=SYSTEM, pairs=PAIRS):
    advance_cython(dt, n, bodies, pairs)

cdef double report_energy_cython(list bodies, list pairs):
    cdef double e = 0.0
    cdef double x1, y1, z1, x2, y2, z2
    cdef double dx, dy, dz, vx, vy, vz, m1, m2, m
    cdef list r1, v1, r2, v2, r, v

    for pair in pairs:
        (r1, v1, m1), (r2, v2, m2) = pair
        x1, y1, z1 = r1
        x2, y2, z2 = r2
        dx = x1 - x2
        dy = y1 - y2
        dz = z1 - z2
        e -= (m1 * m2) / ((dx * dx + dy * dy + dz * dz) ** 0.5)
    for body in bodies:
        r, v, m = body
        vx, vy, vz = v
        e += m * (vx * vx + vy * vy + vz * vz) / 2.0
    return e

def report_energy(bodies=SYSTEM, pairs=PAIRS, e=0.0):
    energy = report_energy_cython(bodies, pairs)
    print("%.9f" % energy)

def offset_momentum(ref, bodies=SYSTEM, px=0.0, py=0.0, pz=0.0):
    for (r, v, m) in bodies:
        vx, vy, vz = v
        px -= vx * m
        py -= vy * m
        pz -= vz * m
    r, v, m = ref
    v[0] = px / m
    v[1] = py / m
    v[2] = pz / m

def main(n, ref='sun'):
    offset_momentum(BODIES[ref])
    report_energy()
    advance(0.01, n)
    report_energy()

if __name__ == '__main__':
    main(int(sys.argv[1]))