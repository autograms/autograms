def fibonacci(n):

    if n<= 0:
        print("Incorrect input")
    # First Fibonacci number is 0
    elif n == 1:
        print(n)
        return 0
    # Second Fibonacci number is 1
    elif n == 2:
 
        return 1
    else:


        nm1=fibonacci(n-1)
        nm2=fibonacci(n-2)

        result = nm1+nm2

        return result