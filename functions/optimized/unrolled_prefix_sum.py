# optimized/prefix_sum.py: loop unrolled 4
class PrefixSum:
    def __init__(self, array: list[int]) -> None:
        len_array = len(array)
        self.prefix_sum = [0] * len_array
        if len_array == 0:
            return

        self.prefix_sum[0] = array[0]
        i = 1

        # Loop unrolling by 4
        while i + 3 < len_array:
            self.prefix_sum[i] = self.prefix_sum[i - 1] + array[i]
            self.prefix_sum[i + 1] = self.prefix_sum[i] + array[i + 1]
            self.prefix_sum[i + 2] = self.prefix_sum[i + 1] + array[i + 2]
            self.prefix_sum[i + 3] = self.prefix_sum[i + 2] + array[i + 3]
            i += 4

        # Handle remaining elements
        while i < len_array:
            self.prefix_sum[i] = self.prefix_sum[i - 1] + array[i]
            i += 1

    def get_sum(self, start: int, end: int) -> int:
        if not self.prefix_sum:
            raise ValueError("The array is empty.")
        if start < 0 or end >= len(self.prefix_sum) or start > end:
            raise ValueError("Invalid range specified.")
        if start == 0:
            return self.prefix_sum[end]
        return self.prefix_sum[end] - self.prefix_sum[start - 1]


if __name__ == "__main__":
    import random
    arr = [random.randint(1, 1000) for _ in range(10000)]
    ps = PrefixSum(arr)
    ps.get_sum(0, len(arr) - 1)
