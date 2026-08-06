from pathlib import Path
from typing import Dict, Callable, Optional

from src.post_processing.clahe import run_clahe_images
from ui.ui_utils import get_user_home_dir


def handle_clahe(
    selected_paths: Dict[str, Path],
    clip_limit_str: str,
    tile_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para o realce de contraste adaptativo CLAHE.
    Valida parâmetros e caminhos de entrada/saída informados pela UI.
    """
    in_dir: Optional[Path] = selected_paths.get("clahe_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta de entrada válida!", is_error=True)
        return

    try:
        clip_limit = float(clip_limit_str.replace(",", "."))
        tile_val = int(tile_size_str)
        tile_size = (tile_val, tile_val)

        if clip_limit <= 0 or tile_val <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Valores de Clip Limit e Tile Size devem ser positivos!", is_error=True)
        return

    # Definição do diretório de saída (Usuário escolhe ou fallback na HOME)
    out_dir: Optional[Path] = selected_paths.get("clahe_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / f"{in_dir.name}_clahe"

    set_ui_state_callback(True, "Aplicando realce CLAHE...")

    try:
        success = run_clahe_images(
            input_dir=in_dir,
            output_dir=out_dir,
            clip_limit=clip_limit,
            tile_size=tile_size,
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "✅ CLAHE aplicado com sucesso!" if success else "❌ Falha no processamento CLAHE.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")