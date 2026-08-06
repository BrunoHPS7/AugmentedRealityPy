from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.post_processing.resize_controller import handle_resize
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


def create_resize_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Redimensionamento de Imagens.
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

    tf_resize_w = ft.TextField(label="Largura Alvo (px)", value="4000", expand=True)
    tf_resize_h = ft.TextField(label="Altura Alvo (px)", value="3000", expand=True)

    txt_resize_in = ft.Text(
        "Nenhuma pasta selecionada...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    txt_resize_out = ft.Text(
        "Nenhum diretório de saída selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    def on_in_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["resize_in"] = Path(e.path)
            txt_resize_in.value = f".../{selected_paths['resize_in'].name}"
            txt_resize_in.color = COLOR_TEXT
            page.update()

    def on_out_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["resize_out"] = Path(e.path)
            txt_resize_out.value = f".../{selected_paths['resize_out'].name}"
            txt_resize_out.color = COLOR_TEXT
            page.update()

    picker_resize_in = ft.FilePicker(on_result=on_in_dir_result)
    picker_resize_out = ft.FilePicker(on_result=on_out_dir_result)
    page.overlay.extend([picker_resize_in, picker_resize_out])

    btn_run = ft.ElevatedButton(
        "Redimensionar Imagens",
        on_click=lambda e: handle_resize(
            selected_paths=selected_paths,
            width_str=tf_resize_w.value,
            height_str=tf_resize_h.value,
            show_toast_callback=show_toast,
            update_progress_callback=update_progress,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_resize = ft.Column([
        # Entrada
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Entrada",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: picker_resize_in.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_resize_in
        ]),
        # Saída
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Destino",
                icon=ft.icons.CREATE_NEW_FOLDER,
                on_click=lambda _: picker_resize_out.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_resize_out
        ]),
        ft.Divider(),
        ft.Row([tf_resize_w, tf_resize_h]),
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
            ft.Icon(ft.icons.ASPECT_RATIO, size=45, color=COLOR_ICON),
            ft.Text("Redimensionamento de Imagens", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_resize
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Teste Isolado da Página
def main(page: ft.Page):
    page.title = "Teste - Redimensionamento"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 650
    page.window_center()

    selected_paths = {}
    page.add(create_resize_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)