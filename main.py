import sys
from pathlib import Path
from typing import Dict
import flet as ft

from ui.app_layout import create_app_layout
from cli.runner import run_cli


def start_gui():
    """Inicia a Interface Gráfica com Flet."""
    def main_ui(page: ft.Page):
        page.title = "Plataforma de Fotogrametria e Reconstrução 3D"
        page.theme_mode = ft.ThemeMode.DARK
        page.window_width = 1024
        page.window_height = 768
        page.window_center()

        selected_paths: Dict[str, Path] = {}
        page.add(create_app_layout(page, selected_paths))

    ft.app(target=main_ui)


def start_cli():
    """Inicia a interface de Linha de Comando (CLI)."""
    print("=========================================")
    print(" Modo CLI - Reconstrução & Calibração 3D ")
    print("=========================================")
    run_cli()

if __name__ == "__main__":
    # Verifica se o parâmetro '--cli' foi passado no terminal
    if "--cli" in sys.argv:
        start_cli()
    else:
        start_gui()