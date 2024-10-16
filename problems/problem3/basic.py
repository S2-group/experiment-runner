def arrayManipulation(n, queries):
    # Initialize an array of zeros with n+1 elements (0-indexed)
    arr = [0] * (n + 1)

    # Process each query and update the array accordingly
    for a, b, k in queries:
        arr[a-1] += k
        if b < n:  # Only increment if b is less than n to avoid out-of-bounds access
            arr[b] -= k

    # Calculate the prefix sum of the array (i.e., cumsum)
    cum_sum = [0] * (n + 1)
    cum_sum[0] = arr[0]
    for i in range(1, n + 1):
        cum_sum[i] = cum_sum[i-1] + arr[i]

    # Find the maximum cumulative sum
    max_val = max(cum_sum)

    return max_val

if __name__ == "__main__":
    with open('../../input/array_manipulation.txt', 'r') as file:
        n, m = map(int, file.readline().strip().split())
        
        queries = []
        
        for _ in range(m):
            a, b, k = map(int, file.readline().strip().split())
            queries.append((a, b, k))
    
    arrayManipulation(n, queries)
