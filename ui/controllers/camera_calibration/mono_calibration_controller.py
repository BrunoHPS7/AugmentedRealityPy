from pathlib import Path
from typing import Dict, Callable, Optional

from src.camera_calibration.mono_calibration import run_mono_calibration
from ui.ui_utils import get_user_home_dir


def handle_mono_calibration(
    selected_paths: Dict[str, Path],
    project_name_str: str,
    rows_str: str,
    cols_str: str,
    square_size_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para a calibração monocular.
    Valida parâmetros do padrão de calibração, nome do projeto e caminhos de entrada/saída.
    """
    # 1. Validação do Nome do Projeto
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação do Diretório de Imagens
    in_dir: Optional[Path] = selected_paths.get("mono_in")
    if not in_dir or not in_dir.exists():
        show_toast_callback("Selecione uma pasta com os quadros de calibração!", is_error=True)
        return

    # 3. Validação dos Parâmetros Numéricos
    try:
        rows = int(rows_str)
        cols = int(cols_str)
        square_size = float(square_size_str.replace(",", "."))

        if rows <= 0 or cols <= 0 or square_size <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Número de cantos e tamanho do quadrado devem ser maiores que zero!", is_error=True)
        return

    # 4. Definição do diretório de saída (Usuário escolhe ou fallback na HOME)
    out_dir: Optional[Path] = selected_paths.get("mono_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    set_ui_state_callback(True, "Processando calibração monocular...")

    try:
        success = run_mono_calibration(
            input_dir=in_dir,
            output_dir=out_dir,
            board_dimensions=(rows, cols),
            square_size_mm=square_size,
            project_name=proj_name_clean,
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "✅ Calibração Monocular realizada com sucesso!" if success else "❌ Falha na calibração monocular.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")