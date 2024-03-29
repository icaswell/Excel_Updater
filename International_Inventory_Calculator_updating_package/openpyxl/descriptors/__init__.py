# Copyright (c) 2010-2014 openpyxl


"""
Based on Python Cookbook 3rd Edition, 8.13
http://chimera.labs.oreilly.com/books/1230000000393/ch08.html#_discussion_130
"""

from openpyxl.compat import basestring, bytes
from numbers import Number

class Descriptor(object):

    def __init__(self, name=None, **kw):
        self.name = name
        for k, v in kw.items():
            setattr(self, k, v)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class Typed(Descriptor):
    """Values must of a particular type"""

    expected_type = type(None)
    allow_none = False

    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            if (not self.allow_none
                or (self.allow_none and value is not None)):
                raise TypeError('expected ' + str(self.expected_type))
        super(Typed, self).__set__(instance, value)


class Convertible(Typed):
    """Values must be convertible to a particular type"""

    def __set__(self, instance, value):
        if ((self.allow_none and value is not None)
            or not self.allow_none):
            try:
                value = self.expected_type(value)
            except:
                raise TypeError('expected ' + str(self.expected_type))
        super(Convertible, self).__set__(instance, value)


class Max(Typed):
    """Values must be less than a `max` value"""

    expected_type = float

    def __init__(self, name=None, **kw):
        if 'max' not in kw:
            raise TypeError('missing max value')
        super(Max, self).__init__(name, **kw)

    def __set__(self, instance, value):
        try:
            value = self.expected_type(value)
        except:
            raise TypeError('expected ' + str(self.expected_type))
        if value > self.max:
            raise ValueError('Max value is {0}'.format(self.max))
        super(Max, self).__set__(instance, value)


class Min(Typed):
    """Values must be greater than a `min` value"""

    expected_type = float

    def __init__(self, name=None, **kw):
        if 'min' not in kw:
            raise TypeError('missing min value')
        super(Min, self).__init__(name, **kw)

    def __set__(self, instance, value):
        try:
            value = self.expected_type(value)
        except:
            raise TypeError('expected ' + str(self.expected_type))
        if value < self.min:
            raise ValueError('Min value is {0}'.format(self.min))
        super(Min, self).__set__(instance, value)


class MinMax(Min, Max):
    """Values must be greater than `min` value and less than a `max` one"""
    pass


class Set(Descriptor):
    """Value can only be from a set of know values"""

    def __init__(self, name=None, **kw):
        if not 'values' in kw:
            raise TypeError("missing set of values")
        super(Set, self).__init__(name, **kw)

    def __set__(self, instance, value):
        if value not in self.values:
            raise ValueError("Value must be one of {0}".format(self.values))
        super(Set, self).__set__(instance, value)


class Integer(Convertible):

    expected_type = int


class Float(Convertible):

    expected_type = float


class Bool(Convertible):

    expected_type = bool

    def __set__(self, instance, value):
        if isinstance(value, str):
            if value in ('false', 'f', '0'):
                value = False
        super(Bool, self).__set__(instance, value)


class String(Typed):

    expected_type = basestring


class ASCII(Typed):

    expected_type = bytes


class Tuple(Typed):

    expected_type = tuple


class Sequence(Descriptor):
    """
    A sequence (list or tuple) that may only contain objects of the declared
    type
    """

    expected_type = type(None)

    def __set__(self, instance, seq):
        if not isinstance(seq, (list, tuple)):
            raise TypeError("Value must be a sequence")
        for idx, value in enumerate(seq):
            if not isinstance(value, self.expected_type):
                raise TypeError(
                    "[{0}] of sequence must be of type {1}".format(
                        idx, self.expected_type)
                )
        super(Sequence, self).__set__(instance, seq)


class Length(Descriptor):

    def __init__(self, name=None, **kw):
        if "length" not in kw:
            raise TypeError("value length must be supplied")
        super(Length, self).__init__(**kw)


    def __set__(self, instance, value):
        if len(value) != self.length:
            raise ValueError("Value must be length {0}".format(self.length))
        super(Length, self).__set__(instance, value)


class Default(Typed):
    """
    When called returns an instance of the expected type.
    Additional default values can be passed in to the descriptor
    """

    def __init__(self, name=None, **kw):
        if "defaults" not in kw:
            kw['defaults'] = {}
        super(Default, self).__init__(**kw)

    def __call__(self):
        return self.expected_type()


class Alias(Descriptor):
    """
    Aliases can be used when either the desired attribute name is not allowed
    or confusing in Python (eg. "type") or a more descriptve name is desired
    (eg. "underline" for "u")
    """

    def __init__(self, alias):
        self.alias = alias

    def __set__(self, instance, value):
        setattr(instance, self.alias, value)

    def __get__(self, instance, cls):
        return getattr(instance, self.alias)


class MetaStrict(type):

    def __new__(cls, clsname, bases, methods):
        for k, v in methods.items():
            if isinstance(v, Descriptor):
                v.name = k
        return type.__new__(cls, clsname, bases, methods)

Strict = MetaStrict('Strict', (object, ), {}
               )

del MetaStrict
