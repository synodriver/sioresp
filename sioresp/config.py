"""
Copyright (c) 2008-2021 synodriver <synodriver@gmail.com>
"""
from dataclasses import dataclass


@dataclass
class Config:
    resp_version: int = 2
