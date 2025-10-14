def unroll4_calculate_span(price: list[int]) -> list[int]:
    """
    Unrolled (4x) version of the Stock Span algorithm.
    Groups four outer-loop iterations at a time.
    Functionally identical to the baseline version.
    """
    n = len(price)
    if n == 0:
        return []

    s = [0] * n
    st = [0]  # stack holds indices
    s[0] = 1
    i = 1

    # Process 4 elements per iteration of the outer loop
    while i + 3 < n:
        for j in (i, i + 1, i + 2, i + 3):
            # Pop all smaller elements
            while len(st) > 0 and price[st[-1]] <= price[j]:
                st.pop()

            # Compute span for this element
            s[j] = j + 1 if len(st) == 0 else (j - st[-1])

            # Push index to stack
            st.append(j)
        i += 4

    # Handle remaining elements (less than 4 left)
    while i < n:
        while len(st) > 0 and price[st[-1]] <= price[i]:
            st.pop()
        s[i] = i + 1 if len(st) == 0 else (i - st[-1])
        st.append(i)
        i += 1

    return s
