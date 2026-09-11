class Money:
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def plus(self, other) -> 'Money':
        return Money(self.amount + other.amount)
