def fibonacciModified(t1, t2, n):
    """
    Compute and return the nth number in a modified Fibonacci sequence.

    Args:
        t1 (int): The first term of the sequence.
        t2 (int): The second term of the sequence.
        n (int): The iteration to report.

    Returns:
        int: The nth number in the sequence.
    """
    if n == 1:
        return t1
    elif n == 2:
        return t2

    fib_sequence = [t1, t2]
    for i in range(2, n):
        next_term = fib_sequence[i-2] + (fib_sequence[i-1]**2)
        fib_sequence.append(next_term)

    return fib_sequence[n-1]

if __name__ == "__main__":
    with open('../../input/fibonacci.txt', 'r') as file:
        t1, t2, n = map(int, file.readline().split())

    fibonacciModified(t1, t2, n)
