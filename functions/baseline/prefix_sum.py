# prefix_sum_nonopt.py
class PrefixSum:
    def __init__(self, array: list[int]) -> None:
        len_array = len(array)
        self.prefix_sum = [0] * len_array
        if len_array > 0:
            self.prefix_sum[0] = array[0]
        for i in range(1, len_array):
            self.prefix_sum[i] = self.prefix_sum[i - 1] + array[i]

    def get_sum(self, start: int, end: int) -> int:
        if not self.prefix_sum:
            raise ValueError("The array is empty.")
        if start < 0 or end >= len(self.prefix_sum) or start > end:
            raise ValueError("Invalid range specified.")
        if start == 0:
            return self.prefix_sum[end]
        return self.prefix_sum[end] - self.prefix_sum[start - 1]


if __name__ == "__main__":
    import random, time
    arr = [random.randint(1, 1000) for _ in range(10000)]
    start = time.time()
    ps = PrefixSum(arr)
    result = ps.get_sum(0, len(arr) - 1)
    end = time.time()
    print(f"Execution time: {end - start:.5f} seconds")
