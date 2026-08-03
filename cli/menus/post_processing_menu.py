from cli.actions.post_processing.clahe import run_clahe_action
from cli.actions.post_processing.resize import run_resize_action
from cli.runner_utils import clear_screen, print_header


def run_post_processing_menu():
    while True:
        clear_screen()
        print_header("Módulo de Pré-Processamento")
        print("1. Redimensionar Imagens (Resize)")
        print("2. Melhoria de Contraste (CLAHE)")
        print("0. Voltar ao Menu Principal")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            run_resize_action()
        elif opcao == "2":
            run_clahe_action()
        elif opcao == "0":
            break
        else:
            input("\n[ERRO] Opção inválida! Pressione ENTER para tentar novamente...")