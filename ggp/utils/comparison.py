"""Comparison Utilities"""


class TypedEqualityMixin():
    """Equality based on type and members.

    Defines == such that other is equal if type and __dict__ are the same.
    """
    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__
