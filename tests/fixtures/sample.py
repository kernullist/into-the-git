def complex_function(x: int, y: int) -> int:
    result = 0
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                result += i
            elif i % 3 == 0:
                result += i * 2
            else:
                result -= 1
    elif x < 0:
        while y > 0:
            y -= 1
            if y % 5 == 0:
                result += 10
    return result


class Calculator:
    def __init__(self, initial: float = 0.0):
        self.value = initial

    def add(self, n: float) -> float:
        self.value += n
        return self.value

    def multiply(self, n: float) -> float:
        if n == 0:
            return 0.0
        self.value *= n
        return self.value

    def dangerous_divide(self, n: float) -> float:
        return self.value / n


def unused_function():
    message = "This function is defined but never called anywhere"
    return message
