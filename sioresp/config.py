"""
Copyright (c) 2008-2021 synodriver <synodriver@gmail.com>
"""
from dataclasses import dataclass


@dataclass
class Config:
    encoding: str = "utf-8"
    errors: str = "strict"
    resp_version: int = 2
    dict_for_map = False  # True if you want to use dict for map type instead of List[Tuple[K, V]]
