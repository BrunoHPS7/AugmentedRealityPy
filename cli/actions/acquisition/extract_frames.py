from cli.runner_utils import ask_int, ask_path, clear_screen, pause, print_header, progress_cli
from src.acquisition.extract_frames import run_extract_frames


def run_extract_frames_action():
    clear_screen()
    print_header("Extração de Frames de Vídeo")

    video_path = ask_path("Caminho do arquivo de vídeo (.mp4, .avi): ", is_file=True)
    out_dir = ask_path(
        "Pasta de saída para salvar os frames: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    fps = ask_int("FPS desejado para extração (ex: 5): ", min_val=1)

    print("\n[INFO] Iniciando extração de frames...\n")
    success = run_extract_frames(video_path, out_dir, fps, progress_cli)

    if success:
        print("\n[SUCESSO] Frames extraídos com sucesso!")
    else:
        print("\n[ERRO] Falha durante a extração dos frames.")

    pause()