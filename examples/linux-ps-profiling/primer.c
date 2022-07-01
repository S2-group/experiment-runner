
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>

/**
 * Simple C program that consumes CPU by repeatedly checking if large random 64-bit numbers
 * are prime or not.
 */

//in bytes
#define STATIC_ARRAY_SZ(arr)    (sizeof(arr))

//in elements
#define STATIC_ARRAY_ELEMS(arr) (sizeof(arr)/sizeof((arr)[0]))

// Returns 0 if not prime.
static int is_prime(unsigned long long p) {
    if(p==0 || p==1)
        return 0;

    for(unsigned long long i=2; i<=p/2; ++i) {
        if(p % i == 0)
            return 0;
    }
    return 1;
}


int main() {
    unsigned long long p;
    char random_data[sizeof(p)];
    
    int fd = open("/dev/urandom", O_RDONLY);
    if(fd == -1) {
        perror("open failed");
        exit(1);
    }

    while(1) {
        ssize_t nread     = 0;
        ssize_t remaining = STATIC_ARRAY_SZ(random_data);
        do {
            ssize_t nslice = read(fd, random_data+nread, remaining);
            if(nslice == -1) {
                perror("read");
                exit(1);
            }
            nread += nslice;
            remaining -= nslice;
        } while(remaining > 0);

        p = *(unsigned long long*)random_data;
        printf("Testing %llu\n", p);
        if(is_prime(p))
            printf(" [*] prime\n");
        else
            printf(" [*] not prime\n");
    }
    close(fd);
    return 0;
}
