import os
import struct

def is_prime(p):
    if p==0 or p==1:
        return False

    for i in range(2, (p//2)+1, 1):
        if p % i == 0:
            return False
    return True

if __name__ == '__main__':
    fd = os.open("/dev/urandom", os.O_RDONLY)

    while True:
        p = struct.unpack("@Q", os.read(fd, 8))[0]
        print("Testing %lu" % p)
        if is_prime(p):
            print(" [*] prime")
        else:
            print(" [*] not prime")
    os.close(fd)
