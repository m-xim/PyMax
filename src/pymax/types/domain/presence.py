from .base import CamelModel


class Presence(CamelModel):
    """Состояние присутствия пользователя.

    :ivar seen: Время последней активности в формате Unix time, если оно
        передано сервером.
    :vartype seen: int | None
    :ivar status: Код статуса присутствия Max.
    :vartype status: int
    """

    seen: int | None = None
    status: int
