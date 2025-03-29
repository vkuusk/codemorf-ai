def multiply_a_b(a, b: int) -> int:
    """
    Multiplies a by b using a loop instead of the multiplication operator.
    
    Parameters:
    a (float|int): The number to be multiplied.
    b (int): The number of times 'a' is to be added to itself.
    
    Returns:
    int|float: The product of 'a' and 'b'.
    """
    result = 0
    for _ in range(abs(b)):
        result += a
    return result if b >= 0 else -result

# Example usage
if __name__ == "__main__":
    print(multiply_a_b(2.5, 3))  # Should output 7.5
    print(multiply_a_b(10, 0))   # Should output 0
    print(multiply_a_b(-4, 2))   # Should output -8