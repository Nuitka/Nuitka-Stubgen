def sorter(arr):
    unused_var = None
    print("codeflash")
    for i in range(len(arr)):
        for j in range(len(arr) - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
    print(arr)
    return arr


def sorterv2(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp

    total_sum = sum(arr)

    max_value = max(arr)

    return arr, total_sum, max_value


if __name__ == "__main__":
    arr = [64, 34, 25, 12, 22, 11, 90]
    sorterv2(arr)
