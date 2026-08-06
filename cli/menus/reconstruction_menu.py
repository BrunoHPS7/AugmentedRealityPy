from cli.actions.reconstruction.mono_reconstruction import run_mono_reconstruction_action
from cli.actions.reconstruction.stereo_reconstruction import run_stereo_reconstruction_action
from cli.runner_utils import clear_screen, print_header


def run_reconstruction_menu():
    while True:
        clear_screen()
        print_header("Módulo de Reconstrução 3D (COLMAP)")
        print("1. Reconstrução Monocular")
        print("2. Reconstrução Estéreo")
        print("0. Voltar ao Menu Principal")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            run_mono_reconstruction_action()
        elif opcao == "2":
            run_stereo_reconstruction_action()
        elif opcao == "0":
            break
        else:
            input("\n[ERRO] Opção inválida! Pressione ENTER para tentar novamente...")