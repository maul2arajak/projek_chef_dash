"""
PILAR PBO 4: POLYMORPHISM (Polymorphic Entity Renderer)
Satu pemanggilan fungsi `entity.render(...)` akan mengeksekusi cara gambar yang berbeda
tergantung apakah objek tersebut adalah `WaitressCharacter`, `AIAssistantCharacter`,
`CustomerCharacter`, atau `ChefCharacter`.
"""

from pilar_pbo.abstraction.base_entity import AbstractAnimatedEntity


def render_entity_polymorphic(entity: AbstractAnimatedEntity, surface, asset_manager, **kwargs) -> int:
    """
    Memanggil method `render()` secara polimorfik pada objek turunan `AbstractAnimatedEntity`.
    """
    return entity.render(surface, asset_manager, **kwargs)
