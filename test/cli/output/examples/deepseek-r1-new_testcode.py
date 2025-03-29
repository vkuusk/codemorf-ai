def multiply_a_b(a, b):
    if b == 0:
        return 0
    result = 0
    for _ in range(b):
        result += a
    return result