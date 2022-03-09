"""
Copyright (c) 2008-2021 synodriver <synodriver@gmail.com>
"""
from dataclasses import dataclass


@dataclass
class Config:
    encoding: str = "utf-8"
    resp_version: int = 2
