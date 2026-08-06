from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.reconstruction.mono_reconstruction_controller import handle_mono_reconstruction
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


def create_mono_reconstruction_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    View para a Reconstrução Monocular 3D (COLMAP SfM).
    """

    def show_toast(message: str, is_error: bool = False):
        color = COLOR_ERROR if is_error else COLOR_SUCCESS
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    progress_bar = ft.ProgressBar(width=FORM_WIDTH, value=0.0, visible=False, color=COLOR_PRIMARY)
    status_text = ft.Text("", italic=True, color=COLOR_SUBTEXT)

    def update_progress(val: float, msg: str = ""):
        progress_bar.value = val
        if msg:
            status_text.value = msg
        page.update()

    def set_ui_state(is_running: bool, status_msg: str):
        progress_bar.visible = is_running
        status_text.value = status_msg
        btn_run.disabled = is_running
        page.update()

    txt_images_in = ft.Text(
        "Nenhuma pasta de imagens selecionada...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    txt_out_dir = ft.Text(
        "Nenhum diretório de saída selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    def on_images_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["mono_rec_images"] = Path(e.path)
            txt_images_in.value = f".../{selected_paths['mono_rec_images'].name}"
            txt_images_in.color = COLOR_TEXT
            page.update()

    def on_out_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["mono_rec_out"] = Path(e.path)
            txt_out_dir.value = f".../{selected_paths['mono_rec_out'].name}"
            txt_out_dir.color = COLOR_TEXT
            page.update()

    picker_images_in = ft.FilePicker(on_result=on_images_dir_result)
    picker_out_dir = ft.FilePicker(on_result=on_out_dir_result)

    page.overlay.extend([picker_images_in, picker_out_dir])

    btn_run = ft.ElevatedButton(
        "Executar Reconstrução Monocular",
        on_click=lambda e: handle_mono_reconstruction(
            selected_paths=selected_paths,
            show_toast_callback=show_toast,
            update_progress_callback=update_progress,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_mono_rec = ft.Column([
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Imagens",
                icon=ft.icons.FOLDER,
                on_click=lambda _: picker_images_in.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_images_in
        ]),
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Destino",
                icon=ft.icons.CREATE_NEW_FOLDER,
                on_click=lambda _: picker_out_dir.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_out_dir
        ]),
        ft.Divider(),
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
            ft.Text("Reconstrução Monocular (3D)", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_mono_rec
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# --- Teste direto do arquivo ---
def main(page: ft.Page):
    page.title = "Teste - Reconstrução Monocular"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 600
    page.window_center()

    selected_paths = {}
    page.add(create_mono_reconstruction_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)