import os
import struct
import time


if __name__ == '__main__':
    timestamp_start = int(time.time()*1000)
    time.sleep(0.5)
    timestamp_end = int(time.time()*1000)
    time_stamp_mid = (timestamp_start + timestamp_end) // 2
    # with open("timestamp.txt", "w") as f:
    #     f.write(f"{time_stamp_mid}\n")
    print(f"{time_stamp_mid}")