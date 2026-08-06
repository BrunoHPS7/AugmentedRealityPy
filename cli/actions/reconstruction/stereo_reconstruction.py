from cli.runner_utils import (
    ask_float,
    ask_path,
    clear_screen,
    pause,
    print_header,
    progress_cli,
)
from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction


def run_stereo_reconstruction_action():
    clear_screen()
    print_header("Reconstrução 3D Estéreo (COLMAP)")

    in_dir = ask_path("Pasta com as imagens de entrada: ", is_file=False)
    out_dir = ask_path(
        "Pasta de saída para o projeto COLMAP: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline = ask_float(
        "Linha de base / Baseline entre câmeras em metros (ex: 0.15): ", min_val=0.001
    )

    def colmap_callback(val: float, texto: str):
        progress_cli(val, texto)

    print("\n[INFO] Iniciando Pipeline de Reconstrução Estéreo...\n")
    success = run_stereo_reconstruction(
        in_dir, out_dir, baseline, progress_callback=colmap_callback
    )

    if success:
        print("\n[SUCESSO] Reconstrução Estéreo concluída!")
    else:
        print("\n[ERRO] Falha durante o pipeline de reconstrução estéreo.")

    pause()