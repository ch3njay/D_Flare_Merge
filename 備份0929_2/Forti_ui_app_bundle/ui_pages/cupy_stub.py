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


class ndarray:
    """最小化的 ndarray 存根類別。
    
    此類別僅提供最基本的 ndarray 介面，用於在 cupy 不可用時替代。
    """
    def __init__(self, *args, **kwargs):
        # 此存根類別僅用於類型檢查，不需要實際實現
        self.shape = ()
        self.dtype = None


__all__ = ["array", "asarray", "asnumpy", "ndarray"]

