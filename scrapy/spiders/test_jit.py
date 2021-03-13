import numpy as np
from numba import jit
import time
import pdb
pdb.set_trace()
import torch
print(torch.cuda.is_available())

@jit
def sum_jit(arr):
    s_time = time.time()
    m = arr.shape[0]
    result = 0.0
    for i in range(m):
        result += arr[i]
    e_time = time.time()
    return (e_time - s_time)


def sum(arr):
    s_time = time.time()
    m = arr.shape[0]
    result = 0.0
    for i in range(m):
        result += arr[i]
    e_time = time.time()
    return (e_time-s_time)


def main():
    n = int(10.0*1e6)
    array = np.random.random(n)
    t1 = sum_jit(array)
    t2 = sum(array)
    print("Time with JIT:", t1)
    print("Time without JIT:", t2)


if __name__ == '__main__':
    main()
