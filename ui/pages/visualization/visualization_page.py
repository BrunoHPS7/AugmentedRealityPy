from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.visualization.visualization_controller import handle_visualization
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_ICON,
    COLOR_TEXT,
    COLOR_SUBTEXT,
    COLOR_SUCCESS,
    COLOR_ERROR,
    FORM_WIDTH,
    BUTTON_HEIGHT,
)
# Utilitário para pegar o diretório home do SO do usuário
from ui.ui_utils import get_user_home_dir


def create_visualization_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Visualização 3D.
    """
    def show_toast(message: str, is_error: bool = False):
        color = COLOR_ERROR if is_error else COLOR_SUCCESS
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    txt_model = ft.Text(
        "Nenhum modelo selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_paths["model"] = Path(e.files[0].path)
            txt_model.value = f".../{selected_paths['model'].name}"
            txt_model.color = COLOR_TEXT
            page.update()

    picker_model = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(picker_model)

    form_visualization = ft.Column([
        ft.Row([
            ft.ElevatedButton(
                "Selecionar Malha",
                icon=ft.icons.FILE_OPEN,
                on_click=lambda _: picker_model.pick_files(
                    allowed_extensions=["ply", "obj"],
                    initial_directory=get_user_home_dir()  # <--- Abre na HOME do usuário
                ),
                width=180
            ),
            txt_model
        ]),
        ft.Container(height=15),
        ft.ElevatedButton(
            "Renderizar Modelo 3D",
            on_click=lambda e: handle_visualization(selected_paths, show_toast),
            icon=ft.icons.PLAY_CIRCLE_FILL,
            bgcolor=COLOR_PRIMARY,
            color=COLOR_TEXT,
            height=BUTTON_HEIGHT
        )
    ], width=FORM_WIDTH, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.VIEW_IN_AR, size=45, color=COLOR_ICON),
            ft.Text("Inspeção Volumétrica 3D", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_visualization
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Bloqueio de Teste Direto do Arquivo
def main(page: ft.Page):
    page.title = "Teste - Visualização 3D"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 600
    page.window_center()

    selected_paths = {}
    page.add(create_visualization_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)