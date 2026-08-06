from pathlib import Path
from typing import Dict, Callable, Optional

from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction
from ui.ui_utils import get_user_home_dir


def handle_stereo_reconstruction(
    selected_paths: Dict[str, Path],
    baseline_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para Reconstrução Estéreo 3D (COLMAP Rig Automático).
    Recebe uma pasta contendo subpastas por câmera e a distância de baseline.
    """
    images_dir: Optional[Path] = selected_paths.get("stereo_rec_images")

    if not images_dir or not images_dir.exists():
        show_toast_callback("Selecione a pasta de imagens estéreo!", is_error=True)
        return

    try:
        baseline = float(baseline_str.replace(",", "."))
        if baseline <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Insira um valor numérico positivo para a baseline (metros)!", is_error=True)
        return

    out_dir: Optional[Path] = selected_paths.get("stereo_rec_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes" / f"{images_dir.name}_stereo_3d"

    set_ui_state_callback(True, "Iniciando pipeline de reconstrução estéreo...")

    try:
        success = run_stereo_reconstruction(
            pasta_frames=images_dir,
            pasta_projeto_saida=out_dir,
            baseline_metros=baseline,
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "Reconstrução Estéreo concluída com sucesso!" if success else "Falha na reconstrução estéreo.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")