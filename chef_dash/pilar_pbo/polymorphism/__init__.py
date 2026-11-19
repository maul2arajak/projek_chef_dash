"""
Pilar 4: POLYMORPHISM
Satu nama method (`search()` atau `render()`) dapat melakukan aksi yang berbeda-beda
tergantung class objek yang memanggilnya (Method Overriding & Polymorphic Dispatch).
"""
from pilar_pbo.polymorphism.search_polymorphism import (
    BFSSearchStrategy,
    DFSSearchStrategy,
    run_polymorphic_search,
)
from pilar_pbo.polymorphism.render_polymorphism import render_entity_polymorphic

__all__ = [
    "BFSSearchStrategy",
    "DFSSearchStrategy",
    "run_polymorphic_search",
    "render_entity_polymorphic",
]
