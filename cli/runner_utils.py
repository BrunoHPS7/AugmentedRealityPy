import os
import sys
from pathlib import Path



def clear_screen():
    """Limpa o terminal de acordo com o sistema operacional."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    """Exibe um cabeçalho padronizado e limpo no terminal."""
    print("=" * 55)
    print(f"  {title.upper()}")
    print("=" * 55)


def progress_cli(value: float, message: str = ""):
    """
    Callback padronizado para exibir progresso em % no terminal.
    Compatível com os callbacks esperados pelas funções do src/.
    """
    if value is not None:
        pct = int(value * 100) if value <= 1.0 else int(value)
        print(f"\r[{pct:3d}%] {message}", end="", flush=True)
        if pct >= 100:
            print()  # Quebra de linha ao finalizar
    else:
        print(f"\r[AGUARDE] {message}", end="", flush=True)


def ask_path(prompt: str, is_file: bool = False, must_exist: bool = True) -> Path:
    """
    Solicita um caminho ao usuário, limpa aspas acidentais (comum ao arrastar pastas/arquivos)
    e valida a existência se necessário.
    """
    while True:
        path_str = input(prompt).strip().strip("'\"")

        if not path_str:
            print("[ERRO] O caminho não pode ser vazio. Tente novamente.\n")
            continue

        path = Path(path_str).resolve()

        if must_exist:
            if is_file and not path.is_file():
                print(f"[ERRO] O arquivo não foi encontrado: {path}\n")
                continue
            if not is_file and not path.is_dir():
                print(f"[ERRO] A pasta não foi encontrada: {path}\n")
                continue

        return path


def ask_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Solicita e valida um número inteiro do usuário."""
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val is not None and val < min_val:
                print(f"[ERRO] O valor deve ser no mínimo {min_val}.\n")
                continue
            if max_val is not None and val > max_val:
                print(f"[ERRO] O valor deve ser no máximo {max_val}.\n")
                continue
            return val
        except ValueError:
            print("[ERRO] Entrada inválida. Por favor, digite um número inteiro.\n")


def ask_float(prompt: str, min_val: float = None) -> float:
    """Solicita e valida um número decimal (float) do usuário."""
    while True:
        try:
            val = float(input(prompt).strip().replace(",", "."))
            if min_val is not None and val < min_val:
                print(f"[ERRO] O valor deve ser no mínimo {min_val}.\n")
                continue
            return val
        except ValueError:
            print("[ERRO] Entrada inválida. Por favor, digite um número válido.\n")


def pause():
    """Pausa a execução aguardando o usuário pressionar ENTER."""
    input("\n[Pressione ENTER para continuar...]")