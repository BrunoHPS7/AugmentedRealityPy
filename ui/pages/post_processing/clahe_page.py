from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.post_processing.clahe_controller import handle_clahe
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
from ui.ui_utils import get_user_home_dir


def create_clahe_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Realce de Contraste CLAHE.
    """
    def show_toast(message: str, is_error: bool = False):
        color = COLOR_ERROR if is_error else COLOR_SUCCESS
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    progress_bar = ft.ProgressBar(width=FORM_WIDTH, value=0.0, visible=False, color=COLOR_PRIMARY)
    status_text = ft.Text("", italic=True, color=COLOR_SUBTEXT)

    def update_progress(val: float):
        progress_bar.value = val
        page.update()

    def set_ui_state(is_running: bool, status_msg: str):
        progress_bar.visible = is_running
        status_text.value = status_msg
        btn_run.disabled = is_running
        page.update()

    tf_norm_clip = ft.TextField(label="Clip Limit", value="2.0", expand=True)
    tf_norm_tile = ft.TextField(label="Tile Size", value="8", expand=True)

    txt_clahe_in = ft.Text(
        "Nenhuma pasta selecionada...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    txt_clahe_out = ft.Text(
        "Nenhum diretório de saída selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    def on_in_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["clahe_in"] = Path(e.path)
            txt_clahe_in.value = f".../{selected_paths['clahe_in'].name}"
            txt_clahe_in.color = COLOR_TEXT
            page.update()

    def on_out_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["clahe_out"] = Path(e.path)
            txt_clahe_out.value = f".../{selected_paths['clahe_out'].name}"
            txt_clahe_out.color = COLOR_TEXT
            page.update()

    picker_clahe_in = ft.FilePicker(on_result=on_in_dir_result)
    picker_clahe_out = ft.FilePicker(on_result=on_out_dir_result)
    page.overlay.extend([picker_clahe_in, picker_clahe_out])

    btn_run = ft.ElevatedButton(
        "Aplicar CLAHE",
        on_click=lambda e: handle_clahe(
            selected_paths=selected_paths,
            clip_limit_str=tf_norm_clip.value,
            tile_size_str=tf_norm_tile.value,
            show_toast_callback=show_toast,
            update_progress_callback=update_progress,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_clahe = ft.Column([
        # Entrada
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Entrada",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: picker_clahe_in.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_clahe_in
        ]),
        # Saída
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Destino",
                icon=ft.icons.CREATE_NEW_FOLDER,
                on_click=lambda _: picker_clahe_out.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_clahe_out
        ]),
        ft.Divider(),
        ft.Row([tf_norm_clip, tf_norm_tile]),
        ft.Container(height=10),
        progress_bar,
        status_text,
        ft.Container(height=5),
        btn_run
    ], width=FORM_WIDTH, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.IMAGE_SEARCH, size=45, color=COLOR_ICON),
            ft.Text("Realce Contraste (CLAHE)", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_clahe
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Teste Isolado da Página
def main(page: ft.Page):
    page.title = "Teste - CLAHE"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 650
    page.window_center()

    selected_paths = {}
    page.add(create_clahe_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)