def multiply_a_b(a, b: int) -> int:
    """
    Multiplies 'a' by 'b' using a loop instead of the multiplication operator.
    
    Parameters:
    a (int/float): The number to be multiplied.
    b (int): The number of times 'a' is to be added to itself.
    
    Returns:
    int/float: The result of multiplying 'a' by 'b'.
    """
    result = 0
    # Adding 'a' to itself 'b' times
    for _ in range(abs(b)):
        result += a
    # Adjust result sign for negative 'b'
    return result if b >= 0 else -result