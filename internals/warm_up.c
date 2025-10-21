//gcc stress_avx.c -o stress_avx -O2 -pthread -mavx2 -mfma
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <immintrin.h> 

#ifndef __AVX2__
#error "AVX2 instruction set not enabled. Please compile with -mavx2."
#endif
#ifndef __FMA__
#error "FMA instruction set not enabled. Please compile with -mfma."
#endif

volatile int keep_running = 1;
volatile int dummy_sink = 0;


void* stress_worker() {
    unsigned long long seed = 0x9E3779B97F4A7C15ULL
                            ^ (unsigned long long)(size_t)&seed
                            ^ (unsigned long long)(size_t)pthread_self()
                            ^ ((unsigned long long)getpid() << 32);
    const double inv2p53 = 1.0 / 9007199254740992.0;
    #define NEXT_RAND() (seed = seed * 6364136223846793005ULL + 1ULL)
    #define RAND01() ((double)(NEXT_RAND() >> 11) * inv2p53)

    double a1 = 0.5 + RAND01();
    double a2 = 0.5 + RAND01();
    double a3 = 0.5 + RAND01();
    double a4 = 0.5 + RAND01();
    double b1 = 0.5 + RAND01();
    double b2 = 0.5 + RAND01();
    double b3 = 0.5 + RAND01();
    double b4 = 0.5 + RAND01();
    double c1 = 0.5 + RAND01();
    double c2 = 0.5 + RAND01();
    double c3 = 0.5 + RAND01();
    double c4 = 0.5 + RAND01();
    double d1 = 0.5 + RAND01();
    double d2 = 0.5 + RAND01();
    double d3 = 0.5 + RAND01();
    double d4 = 0.5 + RAND01();

    __m256d r1 = _mm256_set_pd(a1, a2, a3, a4);
    __m256d r2 = _mm256_set_pd(b1, b2, b3, b4);
    __m256d r3 = _mm256_set_pd(c1, c2, c3, c4);
    __m256d r4 = _mm256_set_pd(d1, d2, d3, d4);

    #undef NEXT_RAND
    #undef RAND01

    while (keep_running) {
        for (int i = 0; i < 100000; ++i) {
            r1 = _mm256_fmadd_pd(r2, r3, r1);
            r2 = _mm256_fmadd_pd(r3, r4, r2);
            r3 = _mm256_fmadd_pd(r4, r1, r3);
            r4 = _mm256_fmadd_pd(r1, r2, r4);
        }
    }

    dummy_sink ^= ((int*)&r1)[0];
    dummy_sink ^= ((int*)&r2)[0];
    dummy_sink ^= ((int*)&r3)[0];
    dummy_sink ^= ((int*)&r4)[0];

    return NULL;
}


int get_num_processors() {
    return sysconf(_SC_NPROCESSORS_ONLN);
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        int num_cores = get_num_processors();
        fprintf(stderr, "Usage: %s [num_threads] [duration_seconds]\n", argv[0]);
        fprintf(stderr, "Your system has %d logical processor(s).\n", num_cores);
        return 1;
    }

    int num_threads = atoi(argv[1]);
    int duration_sec = atoi(argv[2]);

    if (num_threads <= 0 || duration_sec <= 0) {
        fprintf(stderr, "Error: Number of threads and duration must be positive integers.\n");
        return 1;
    }

    pthread_t* threads = malloc(num_threads * sizeof(pthread_t));
    if (!threads) {
        perror("Failed to allocate memory for threads");
        return 1;
    }

    for (int i = 0; i < num_threads; ++i) {
        int rc = pthread_create(&threads[i], NULL, stress_worker, NULL);
        if (rc) {
            fprintf(stderr, "Error creating thread %d; return code: %d\n", i, rc);
            free(threads);
            return 1;
        }
    }

    printf("Stress test running for %d seconds. Please wait...\n", duration_sec);

    sleep(duration_sec);
    keep_running = 0;
    for (int i = 0; i < num_threads; ++i) {
        pthread_join(threads[i], NULL);
    }

    free(threads);
    printf("All threads have terminated.\n");

    return 0;
}