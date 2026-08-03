from cli.runner_utils import ask_path, clear_screen, pause, print_header
from src.visualization import render_3d_model


def run_visualization_action():
    clear_screen()
    print_header("Visualização de Modelo 3D")

    model_path = ask_path("Caminho do arquivo 3D (.ply, .obj): ", is_file=True)

    print("\n[INFO] Abrindo janela de renderização 3D...\n")
    try:
        render_3d_model(model_path)
        print("[SUCESSO] Visualização concluída.")
    except Exception as e:
        print(f"[ERRO] Falha ao renderizar o modelo 3D: {e}")

    pause()