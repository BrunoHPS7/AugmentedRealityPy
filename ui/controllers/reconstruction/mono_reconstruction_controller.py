from pathlib import Path
from typing import Dict, Callable, Optional

from src.reconstruction.mono_reconstruction import run_mono_reconstruction
from ui.ui_utils import get_user_home_dir


def handle_mono_reconstruction(
    selected_paths: Dict[str, Path],
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para Reconstrução Monocular 3D (COLMAP SfM).
    Valida a pasta de imagens de entrada e aciona o pipeline.
    """
    images_dir: Optional[Path] = selected_paths.get("mono_rec_images")

    if not images_dir or not images_dir.exists():
        show_toast_callback("Selecione a pasta com as imagens de entrada!", is_error=True)
        return

    out_dir: Optional[Path] = selected_paths.get("mono_rec_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes" / f"{images_dir.name}_mono_3d"

    set_ui_state_callback(True, "Iniciando reconstrução monocular (COLMAP)...")

    try:
        success = run_mono_reconstruction(
            pasta_frames=images_dir,
            pasta_projeto_saida=out_dir,
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "Reconstrução Monocular concluída com sucesso!" if success else "Falha na reconstrução monocular.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")