from cli.runner_utils import ask_path, clear_screen, pause, print_header, progress_cli
from src.reconstruction.mono_reconstruction import run_mono_reconstruction


def run_mono_reconstruction_action():
    clear_screen()
    print_header("Reconstrução 3D Monocular (COLMAP)")

    in_dir = ask_path("Pasta com as imagens de entrada: ", is_file=False)
    out_dir = ask_path(
        "Pasta de saída para o projeto COLMAP: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    def colmap_callback(val: float, texto: str):
        progress_cli(val, texto)

    print("\n[INFO] Iniciando Pipeline de Reconstrução Monocular...\n")
    success = run_mono_reconstruction(
        in_dir, out_dir, progress_callback=colmap_callback
    )

    if success:
        print("\n[SUCESSO] Reconstrução Monocular concluída!")
    else:
        print("\n[ERRO] Falha durante o pipeline de reconstrução monocular.")

    pause()