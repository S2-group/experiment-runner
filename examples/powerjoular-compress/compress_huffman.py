

import os
import struct

def compress(path):
    # list all files in the path
    files = os.listdir(path)
    for file in files:
        # get the absolute path of the file
        file_path = os.path.join(path, file)
        # if the file is a directory, continue to traverse
        if os.path.isdir(file_path):
            compress(file_path)
        else:
            # if the file is a file, compress it
            # run tcmpr -c file_path -alg huffman, only when the command is finished, the next command will be executed
            ret = os.system("tcmpr -c " + file_path + " -alg huffman")
            if ret != 0:
                print("compress error: " + file_path)
            else:
                continue
    return True

if __name__ == '__main__':
    # read the argument from the command line
    data_type = os.sys.argv[1]
    path = "./data/" + data_type
    ret = compress(path)
    # if ret is true, send signal the task is done
    if ret:
        print("compress done")
    else:
        print("compress error")


