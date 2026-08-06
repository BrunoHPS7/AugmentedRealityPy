from cli.runner_utils import (
    ask_float,
    ask_int,
    ask_path,
    clear_screen,
    pause,
    print_header,
    progress_cli,
)
from src.camera_calibration.stereo_calibration import run_stereo_calibration


def run_stereo_calibration_action():
    clear_screen()
    print_header("Calibração Estéreo")

    proj_name = input("Nome do Projeto (ex: calib_stereo): ").strip()
    dim_x = ask_int("Número de quinas internas no eixo X (ex: 8): ", min_val=1)
    dim_y = ask_int("Número de quinas internas no eixo Y (ex: 6): ", min_val=1)
    sq_size = ask_float("Tamanho do quadrado do xadrez em mm (ex: 25.0): ", min_val=0.1)

    path_a = ask_path("Pasta com as imagens da Câmera A (Esquerda): ", is_file=False)
    path_b = ask_path("Pasta com as imagens da Câmera B (Direita): ", is_file=False)
    out_dir = ask_path(
        "Pasta de saída para salvar a calibração: ", is_file=False, must_exist=False
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n[INFO] Iniciando Calibração Estéreo...\n")
    success = run_stereo_calibration(
        path_a,
        path_b,
        out_dir,
        (dim_x, dim_y),
        sq_size,
        proj_name,
        progress_cli,
        progress_cli,
    )

    if success:
        print("\n[SUCESSO] Calibração Estéreo concluída!")
    else:
        print("\n[ERRO] Falha durante a calibração estéreo.")

    pause()