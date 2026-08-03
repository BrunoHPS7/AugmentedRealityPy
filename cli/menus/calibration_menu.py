from cli.actions.camera_calibration.mono_calibration import run_mono_calibration_action
from cli.actions.camera_calibration.stereo_calibration import run_stereo_calibration_action
from cli.runner_utils import clear_screen, print_header


def run_calibration_menu():
    while True:
        clear_screen()
        print_header("Módulo de Calibração de Câmera")
        print("1. Calibração Monocular")
        print("2. Calibração Estéreo")
        print("0. Voltar ao Menu Principal")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            run_mono_calibration_action()
        elif opcao == "2":
            run_stereo_calibration_action()
        elif opcao == "0":
            break
        else:
            input("\n[ERRO] Opção inválida! Pressione ENTER para tentar novamente...")