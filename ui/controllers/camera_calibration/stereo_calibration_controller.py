from pathlib import Path
from typing import Dict, Callable, Optional

from src.camera_calibration.stereo_calibration import run_stereo_calibration
from ui.ui_utils import get_user_home_dir


def handle_stereo_calibration(
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
    Controller para a calibração estéreo.
    Valida parâmetros do padrão de calibração, nome do projeto e caminhos de entrada/saída.
    """
    # 1. Validação do Nome do Projeto
    proj_name_clean = project_name_str.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 2. Validação dos Diretórios de Imagens
    left_dir: Optional[Path] = selected_paths.get("stereo_left_in")
    right_dir: Optional[Path] = selected_paths.get("stereo_right_in")

    if not left_dir or not left_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Esquerda!", is_error=True)
        return

    if not right_dir or not right_dir.exists():
        show_toast_callback("Selecione a pasta de imagens da Câmera Direita!", is_error=True)
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
    out_dir: Optional[Path] = selected_paths.get("stereo_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / "calibracoes"

    set_ui_state_callback(True, "Processando calibração estéreo...")

    try:
        # Passa project_name e divide o progresso: 0%-50% para Câmera A e 50%-100% para Câmera B
        success = run_stereo_calibration(
            input_dir_a=left_dir,
            input_dir_b=right_dir,
            output_dir=out_dir,
            board_dimensions=(rows, cols),
            square_size_mm=square_size,
            project_name=proj_name_clean,
            progress_callback_a=lambda v: update_progress_callback(v * 0.5),
            progress_callback_b=lambda v: update_progress_callback(0.5 + v * 0.5)
        )
        show_toast_callback(
            "✅ Calibração Estéreo realizada com sucesso!" if success else "❌ Falha na calibração estéreo.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")