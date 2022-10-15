import numpy


def chunks(lst, n):
    return numpy.array_split(numpy.array(lst), n)
