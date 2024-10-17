def hourglassSum(arr):
    max_sum = float('-inf')
    
    # Iterate over each possible hourglass in arr
    for i in range(len(arr) - 3):
        for j in range(len(arr[0]) - 3):
            sub_array_sum = 0
            
            # Calculate the sum of the current hourglass
            for k in range(3):
                sub_array_sum += (arr[i+k][j] + arr[i+k][j+2]
                                 + arr[i+k+1][j+1])
            
            max_sum = max(max_sum, sub_array_sum)
    
    return max_sum

if __name__ == "__main__":
    with open('../../input/2d_array.txt', 'r') as file:
        arr = []
        for line in file:
            row = list(map(int, line.strip().split()))
            arr.append(row)
    
    result = hourglassSum(arr)
