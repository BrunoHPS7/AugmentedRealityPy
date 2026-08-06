from pathlib import Path

def get_user_home_dir() -> str:
    """
    Retorna o caminho absoluto do diretório HOME do usuário atual
    """
    return str(Path.home().resolve())