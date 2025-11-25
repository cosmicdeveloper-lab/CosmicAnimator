# src/cosmicanimator/adapters/transitions/__init__.py

from .blackhole import blackhole, hawking_radiation
from .stars import shooting_star, pulsar
from .reveal import reveal
from .visuals import spin, shine


__all__ = [
    "pulsar", "shooting_star",
    "blackhole", "hawking_radiation",
    "reveal"
    "spin", "shine"
]
