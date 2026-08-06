from typing import Callable


def handle_calibration_hub_click(
    route_key: str,
    on_navigate: Callable[[str], None]
) -> None:
    """
    Controller do Hub de Calibração.
    Processa a escolha do card e aciona a navegação para a rota selecionada.
    """
    # Ex: no futuro, se precisar salvar estado ou validar algo antes de trocar de tela, faz-se aqui.
    on_navigate(route_key)