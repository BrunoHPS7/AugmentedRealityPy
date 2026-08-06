from pathlib import Path
from typing import Dict, Callable, Optional

from src.acquisition.extract_frames import run_extract_frames
from ui.ui_utils import get_user_home_dir


def handle_extract_frames(
    selected_paths: Dict[str, Path],
    project_name: str,
    fps_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para a extração de quadros a partir de vídeo.
    Valida as entradas da UI e executa o processamento do backend.
    """
    # 1. Validação do FPS
    try:
        fps = int(fps_str)
        if fps <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("O FPS deve ser um número inteiro positivo!", is_error=True)
        return

    # 2. Validação do Vídeo de Entrada
    video_path: Optional[Path] = selected_paths.get("video")
    if not video_path or not video_path.exists():
        show_toast_callback("Selecione um arquivo de vídeo válido!", is_error=True)
        return

    proj_name_clean = project_name.strip()
    if not proj_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 3. Definição do diretório de saída (Usuário escolhe ou fallback na HOME)
    base_out: Optional[Path] = selected_paths.get("output_dir")
    if not base_out:
        # Se não escolheu pasta, usa a HOME do SO como raiz
        base_out = Path(get_user_home_dir()) / "IC_Output"

    out_dir = base_out / proj_name_clean

    # 4. Início do processamento
    set_ui_state_callback(True, "Extraindo frames...")

    try:
        success = run_extract_frames(
            video_path=video_path,
            output_dir=out_dir,
            desired_fps=fps,
            progress_callback=update_progress_callback,
        )
        show_toast_callback(
            "✅ Extração concluída com sucesso!" if success else "❌ Falha na extração dos frames.",
            is_error=not success,
        )
    except Exception as e:
        show_toast_callback(f"Erro inesperado: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")