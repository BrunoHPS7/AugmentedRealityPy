from cli.runner_utils import (
    ask_int,
    ask_path,
    clear_screen,
    pause,
    print_header,
    progress_cli,
)
from src.post_processing.resize import run_resize_images


def run_resize_action():
    clear_screen()
    print_header("Pré-Processamento: Redimensionamento (Resize)")

    in_dir = ask_path("Pasta com as imagens de entrada: ", is_file=False)
    out_dir = ask_path(
        "Pasta de saída para salvar as imagens: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    tw = ask_int("Largura alvo em pixels (ex: 4000): ", min_val=1)
    th = ask_int("Altura alvo em pixels (ex: 3000): ", min_val=1)

    print("\n[INFO] Redimensionando imagens...\n")
    success = run_resize_images(
        in_dir, out_dir, target_size=(th, tw), progress_callback=progress_cli
    )

    if success:
        print("\n[SUCESSO] Redimensionamento concluído!")
    else:
        print("\n[ERRO] Falha durante o redimensionamento das imagens.")

    pause()