"""
utils:filepath
==============

Provides helpers for PathLike objects
"""
import os
from typing import TypeVar, Union

PathLike = TypeVar("PathLike", bound=Union[str, bytes, os.PathLike])


def path(relative_path: PathLike) -> os.PathLike:
    return os.path.abspath(relative_path)


def directory(__file__) -> os.PathLike:
    return path(os.path.dirname(__file__))


def join(*args) -> os.PathLike:
    return path(os.path.join(*args))
