"""Lane J (IEEG033): restricted unpickler for the Du-IN release pickles.

Only the globals the release actually uses are allowed (utils.DotDict -> plain dict subclass, numpy array
reconstruction). Anything else raises, so a pickle cannot execute arbitrary code here.
"""
import pickle

import numpy as np

try:
    from numpy._core import multiarray as _ma
except ImportError:  # numpy < 2
    from numpy.core import multiarray as _ma


class DotDict(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e


ALLOWED = {
    ('utils.DotDict', 'DotDict'): DotDict,
    ('numpy.core.multiarray', '_reconstruct'): _ma._reconstruct,
    ('numpy._core.multiarray', '_reconstruct'): _ma._reconstruct,
    ('numpy', 'ndarray'): np.ndarray,
    ('numpy', 'dtype'): np.dtype,
    ('numpy.core.multiarray', 'scalar'): _ma.scalar,
    ('numpy._core.multiarray', 'scalar'): _ma.scalar,
}
SEEN = set()


class Restricted(pickle.Unpickler):
    def find_class(self, module, name):
        SEEN.add((module, name))
        if (module, name) in ALLOWED:
            return ALLOWED[(module, name)]
        raise pickle.UnpicklingError(f'global {module}.{name} not allowed')


def load(path):
    with open(path, 'rb') as f:
        return Restricted(f).load()
