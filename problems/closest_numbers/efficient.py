def closestNumbers(arr):
    """
    Given a list of unsorted integers, find all pairs of elements 
    with the smallest absolute difference between them.

    Args:
        arr (list): A list of unique integers.

    Returns:
        list: A list of integer pairs as described.
    """

    # First sort the array in ascending order
    arr.sort()

    # Initialize minimum difference and result lists
    min_diff = float('inf')
    result = []

    # Iterate over the sorted array to find all valid pairs
    for i in range(1, len(arr)):
        if arr[i] - arr[i-1] < min_diff:
            # Update minimum difference and reset result list
            min_diff = arr[i] - arr[i-1]
            result = [[arr[i-1], arr[i]]]
        elif arr[i] - arr[i-1] == min_diff:
            # If the current pair has the same minimum difference, 
            # add it to the result list
            result.append([arr[i-1], arr[i]])

    return [item for sublist in result for item in sublist]

if __name__ == "__main__":
    with open('../../input/closest_number.txt', 'r') as file:
        n = int(file.readline().strip())
        
        arr = list(map(int, file.readline().strip().split()))
    
    closestNumbers(arr)
