from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.camera_calibration.mono_calibration_controller import handle_mono_calibration
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


def create_mono_calibration_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Calibração Monocular.
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

    # --- CAMPOS DE ENTRADA DO FORMULÁRIO ---
    tf_project_name = ft.TextField(label="Nome do Projeto (Subpasta)", value="meu_projeto_mono", expand=True)
    tf_grid_rows = ft.TextField(label="Linhas de Cantos Internos", value="6", expand=True)
    tf_grid_cols = ft.TextField(label="Colunas de Cantos Internos", value="9", expand=True)
    tf_square_size = ft.TextField(label="Tamanho do Quadrado (mm/m)", value="0.025", expand=True)

    txt_mono_in = ft.Text(
        "Nenhuma pasta selecionada...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    txt_mono_out = ft.Text(
        "Nenhum diretório de saída selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    def on_in_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["mono_in"] = Path(e.path)
            txt_mono_in.value = f".../{selected_paths['mono_in'].name}"
            txt_mono_in.color = COLOR_TEXT
            page.update()

    def on_out_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["mono_out"] = Path(e.path)
            txt_mono_out.value = f".../{selected_paths['mono_out'].name}"
            txt_mono_out.color = COLOR_TEXT
            page.update()

    picker_mono_in = ft.FilePicker(on_result=on_in_dir_result)
    picker_mono_out = ft.FilePicker(on_result=on_out_dir_result)
    page.overlay.extend([picker_mono_in, picker_mono_out])

    btn_run = ft.ElevatedButton(
        "Executar Calibração Monocular",
        on_click=lambda e: handle_mono_calibration(
            selected_paths=selected_paths,
            project_name_str=tf_project_name.value,
            rows_str=tf_grid_rows.value,
            cols_str=tf_grid_cols.value,
            square_size_str=tf_square_size.value,
            show_toast_callback=show_toast,
            update_progress_callback=update_progress,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_mono = ft.Column([
        # Nome do Projeto
        ft.Row([tf_project_name]),
        # Pasta de Entrada
        ft.Row([
            ft.ElevatedButton(
                "Pasta das Imagens",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: picker_mono_in.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_mono_in
        ]),
        # Pasta de Saída
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Destino",
                icon=ft.icons.CREATE_NEW_FOLDER,
                on_click=lambda _: picker_mono_out.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_mono_out
        ]),
        ft.Divider(),
        ft.Row([tf_grid_rows, tf_grid_cols]),
        ft.Row([tf_square_size]),
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
            ft.Icon(ft.icons.CAMERA_ALT, size=45, color=COLOR_ICON),
            ft.Text("Calibração Monocular", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_mono
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Teste Isolado da Página
def main(page: ft.Page):
    page.title = "Teste - Calibração Monocular"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 700
    page.window_center()

    selected_paths = {}
    page.add(create_mono_calibration_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)