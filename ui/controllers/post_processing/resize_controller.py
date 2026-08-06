from pathlib import Path
from typing import Dict, Callable, Optional

from src.post_processing.resize import run_resize_images
from ui.ui_utils import get_user_home_dir


def handle_resize(
    selected_paths: Dict[str, Path],
    width_str: str,
    height_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para o redimensionamento de imagens.
    Valida as dimensões e caminhos de entrada/saída informados pela UI.
    """
    in_dir: Optional[Path] = selected_paths.get("resize_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    try:
        target_w = int(width_str)
        target_h = int(height_str)
        if target_w <= 0 or target_h <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de largura e altura devem ser inteiros positivos!", is_error=True)
        return

    # Definição do diretório de saída (Usuário escolhe ou fallback na HOME)
    out_dir: Optional[Path] = selected_paths.get("resize_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_resized"

    set_ui_state_callback(True, "Redimensionando imagens...")

    try:
        success = run_resize_images(
            input_dir=in_dir,
            output_dir=out_dir,
            target_size=(target_h, target_w),
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "✅ Redimensionamento concluído com sucesso!" if success else "❌ Falha no Redimensionamento.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")