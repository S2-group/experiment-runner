

import os
import struct
def lzw_compress(data):
    dictionary = {bytes([i]): i for i in range(256)}  # Initialize the dictionary with byte values
    next_code = 256  # The next available code for dictionary entries
    result = bytearray()  # The compressed output

    current_sequence = b""  # Initialize an empty current sequence

    for symbol in data:
        current_sequence += bytes([symbol])
        if current_sequence not in dictionary:
            dictionary[current_sequence] = next_code
            next_code += 1
            result.extend(int.to_bytes(dictionary[current_sequence[:-1]], 2, 'big'))  # Append the code for the current sequence (excluding the last symbol) to the result
            current_sequence = bytes([symbol])  # Start a new current sequence with the current symbol

    if current_sequence in dictionary:
        result.extend(int.to_bytes(dictionary[current_sequence], 2, 'big'))

    return result

def compress_file(input_file):
    with open(input_file, 'rb') as f:
        data = f.read()
    compressed_data = lzw_compress(data)
    output_file = input_file + '.lzw'
    with open(output_file, 'wb') as f:
        f.write(compressed_data)

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
            if file_path.split('.')[-1] == 'huffman' or file_path.split('.')[-1] == 'lzw':
                continue
            compress_file(file_path)
    return True

if __name__ == '__main__':
    # read the argument from the command line
    data_type = os.sys.argv[1]
    # replace '-' with '/' in data_type
    data_type = data_type.replace('-', '/')
    path = "./data/" + data_type
    ret = compress(path)
    # if ret is true, send signal the task is done
    if ret:
        print("compress done")
    else:
        print("compress error")
