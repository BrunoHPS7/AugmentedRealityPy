import sys
from cli.actions.acquisition.extract_frames import run_extract_frames_action
from cli.actions.visualization.visualization import run_visualization_action
from cli.menus.calibration_menu import run_calibration_menu
from cli.menus.post_processing_menu import run_post_processing_menu
from cli.menus.reconstruction_menu import run_reconstruction_menu
from cli.runner_utils import clear_screen, print_header


def run_cli():
    while True:
        clear_screen()
        print_header("AugmentedRealityPy — UFOP / ICEA")
        print("1. Extração de Frames de Vídeo")
        print("2. Calibração de Câmera")
        print("3. Pré-Processamento de Imagens")
        print("4. Reconstrução 3D (COLMAP)")
        print("5. Visualização de Modelo 3D")
        print("0. Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            run_extract_frames_action()
        elif opcao == "2":
            run_calibration_menu()
        elif opcao == "3":
            run_post_processing_menu()
        elif opcao == "4":
            run_reconstruction_menu()
        elif opcao == "5":
            run_visualization_action()
        elif opcao == "0":
            clear_screen()
            print("Encerrando o sistema. Até logo!\n")
            sys.exit(0)
        else:
            input("\n[ERRO] Opção inválida! Pressione ENTER para tentar novamente...")


if __name__ == "__main__":
    run_cli()