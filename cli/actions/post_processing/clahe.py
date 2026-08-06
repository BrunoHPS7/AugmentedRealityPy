from cli.runner_utils import (
    ask_float,
    ask_int,
    ask_path,
    clear_screen,
    pause,
    print_header,
    progress_cli,
)
from src.post_processing.clahe import run_clahe_images


def run_clahe_action():
    clear_screen()
    print_header("Pré-Processamento: Melhoria de Contraste (CLAHE)")

    in_dir = ask_path("Pasta com as imagens de entrada: ", is_file=False)
    out_dir = ask_path(
        "Pasta de saída para salvar as imagens: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    clip = ask_float("Limite de corte do CLAHE / Clip Limit (ex: 2.0): ", min_val=0.1)
    tile = ask_int("Tamanho do bloco / Tile Size (ex: 8): ", min_val=1)

    print("\n[INFO] Aplicando CLAHE nas imagens...\n")
    success = run_clahe_images(
        in_dir,
        out_dir,
        clip_limit=clip,
        tile_size=(tile, tile),
        progress_callback=progress_cli,
    )

    if success:
        print("\n[SUCESSO] Processamento CLAHE concluído!")
    else:
        print("\n[ERRO] Falha durante a aplicação do CLAHE.")

    pause()