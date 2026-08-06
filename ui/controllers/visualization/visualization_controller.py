from pathlib import Path
from typing import Dict, Optional
from src.visualization.visualization import run_show_mesh


def handle_visualization(selected_paths: Dict[str, Path], show_toast_callback) -> None:
    """
    Controller para a tela de visualização 3D.
    Valida a seleção do modelo e invoca a renderização do PyVista.
    """
    model_path: Optional[Path] = selected_paths.get("model")

    if not model_path or not model_path.exists():
        show_toast_callback("Selecione uma malha 3D válida (.ply ou .obj)!", is_error=True)
        return

    show_toast_callback("Iniciando renderizador PyVista...", is_error=False)

    try:
        # Chamada para o novo nome da função no backend
        run_show_mesh(model_path)
    except Exception as e:
        show_toast_callback(f"Erro ao renderizar modelo: {e}", is_error=True)