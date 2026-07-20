from helpers import double


class Calculator:
    def total(self, value):
        return double(value)


def run(value):
    return Calculator().total(value)
