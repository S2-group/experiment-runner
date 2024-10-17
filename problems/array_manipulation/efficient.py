def arrayManipulation(n, queries):
    # Initialize an array of zeros with n+1 elements (0-indexed)
    arr = [0] * (n + 1)

    max_val = 0

    # Process each query and update the array accordingly
    for a, b, k in queries:
        # Calculate the delta value to add to arr[a-1] and subtract from arr[b]
        delta = k if a == 1 else k - (arr[a-2] if a > 1 else 0)
        
        # Add the delta value to arr[a-1]
        arr[a-1] += delta
        
        # If b < n, add the negated delta value to arr[b+1]
        if b < n:
            arr[b+1] -= delta

        # Update max_val on-the-fly
        max_val = max(max_val, arr[a-1])

    return max_val

if __name__ == "__main__":
    with open('../../input/array_manipulation.txt', 'r') as file:
        n, m = map(int, file.readline().strip().split())
        
        queries = []
        
        for _ in range(m):
            a, b, k = map(int, file.readline().strip().split())
            queries.append((a, b, k))
    
    arrayManipulation(n, queries)
