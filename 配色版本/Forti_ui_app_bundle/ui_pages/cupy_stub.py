"""Minimal Cupy stub used when the real library is unavailable.

The real project only relies on a tiny subset of the Cupy API.  When Cupy
isn't installed we provide drop-in functions that simply return the original
Python objects so the rest of the code can fall back to CPU execution without
raising attribute errors.
"""

def array(obj):
    return obj


# Alias asarray to array for compatibility with the real Cupy API.
def asarray(obj):
    return obj


def asnumpy(obj):
    return obj


__all__ = ["array", "asarray", "asnumpy"]

