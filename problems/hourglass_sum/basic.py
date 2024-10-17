def hourglassSum(arr):
    max_sum = float('-inf')
    
    for i in range(len(arr) - 3):
        for j in range(len(arr[0]) - 3):
            sub_array = arr[i][j] + arr[i+1][j+1] + arr[i+2][j] + \
                        arr[i+3][j+1] + arr[i+2][j+2] + arr[i+1][j+3]
            
            max_sum = max(max_sum, sub_array)
    
    return max_sum

if __name__ == "__main__":
    with open('../../input/2d_array.txt', 'r') as file:
        arr = []
        for line in file:
            row = list(map(int, line.strip().split()))
            arr.append(row)
    
    result = hourglassSum(arr)
