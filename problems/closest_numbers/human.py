
#Closest Numbers
def main():
   #N = int(input())
    #ar = sorted(list(map(int, str(input()).split())))
    input_file_path = "closestNumber/input/input.txt"  # Path to your input file
    
    with open(input_file_path, 'r') as file:
        # Read all lines from the input file
        lines = file.readlines()
    
    N = int(lines[0].strip())  # The first line contains the number of elements
    ar = sorted(list(map(int, lines[1].split())))  # The second line contains the array values
    
    prs = ''
    mini = pow(10, 7) + 1
    for i in range(1, N):
        diff = abs(ar[i-1] - ar[i])
        if (diff <= mini):
            if (diff < mini):
                prs = ''
            mini = diff
            prs += str(ar[i-1]) + ' ' + str(ar[i]) + ' '
    return prs

if __name__ == '__main__':
    output_file_path = "closestNumber/output/output.txt"  # path
    fptr = open(output_file_path, 'w')
    result = main()
    #fptr.write(' '.join(map(str, result)))
    fptr.write(result)
    fptr.write('\n')
    fptr.close()

