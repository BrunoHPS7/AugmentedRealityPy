from typing import Callable


def handle_calibration_hub_click(
    route_key: str,
    on_navigate: Callable[[str], None]
) -> None:
    """
    Controller do Hub de Calibração.
    Processa a escolha do card e aciona a navegação para a rota selecionada.
    """
    on_navigate(route_key)