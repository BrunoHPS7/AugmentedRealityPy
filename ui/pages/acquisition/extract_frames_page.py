from pathlib import Path
from typing import Dict
import flet as ft

from ui.controllers.acquisition.extract_frames_controller import handle_extract_frames
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


def create_extract_frames_page(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Gera a View da Tela de Extração de Frames (Decomposição Temporal).
    """

    def show_toast(message: str, is_error: bool = False):
        color = COLOR_ERROR if is_error else COLOR_SUCCESS
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    # Elementos de Feedback Local
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

    # Campos do Formulário
    tf_acq_proj = ft.TextField(label="Nome do Projeto (Subpasta)", expand=True)
    tf_acq_fps = ft.TextField(label="FPS Desejado", value="5", width=130)

    # Label Vídeo de Entrada
    txt_video = ft.Text(
        "Nenhum vídeo selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    # Label Pasta de Saída
    txt_out_dir = ft.Text(
        "Nenhum diretório de saída selecionado...",
        color=COLOR_SUBTEXT,
        expand=True,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    # Pickers de Arquivo (Entrada) e Diretório (Saída)
    def on_video_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_paths["video"] = Path(e.files[0].path)
            txt_video.value = f".../{selected_paths['video'].name}"
            txt_video.color = COLOR_TEXT
            page.update()

    def on_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_paths["output_dir"] = Path(e.path)
            txt_out_dir.value = f".../{selected_paths['output_dir'].name}"
            txt_out_dir.color = COLOR_TEXT
            page.update()

    picker_video = ft.FilePicker(on_result=on_video_result)
    picker_out_dir = ft.FilePicker(on_result=on_dir_result)
    page.overlay.extend([picker_video, picker_out_dir])

    btn_run = ft.ElevatedButton(
        "Extrair Frames",
        on_click=lambda e: handle_extract_frames(
            selected_paths=selected_paths,
            project_name=tf_acq_proj.value,
            fps_str=tf_acq_fps.value,
            show_toast_callback=show_toast,
            update_progress_callback=update_progress,
            set_ui_state_callback=set_ui_state,
        ),
        icon=ft.icons.PLAY_ARROW,
        bgcolor=COLOR_PRIMARY,
        color=COLOR_TEXT,
        height=BUTTON_HEIGHT
    )

    form_acquisition = ft.Column([
        ft.Row([tf_acq_proj, tf_acq_fps]),
        ft.Container(height=5),

        # Seleção do Vídeo de Entrada
        ft.Row([
            ft.ElevatedButton(
                "Selecionar Vídeo",
                icon=ft.icons.VIDEO_FILE,
                on_click=lambda _: picker_video.pick_files(
                    allowed_extensions=["mp4", "avi", "mov", "mkv"],
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_video
        ]),

        # Seleção da Pasta de Saída
        ft.Row([
            ft.ElevatedButton(
                "Pasta de Destino",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: picker_out_dir.get_directory_path(
                    initial_directory=get_user_home_dir()
                ),
                width=180
            ),
            txt_out_dir
        ]),

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
            ft.Icon(ft.icons.VIDEO_FILE, size=45, color=COLOR_ICON),
            ft.Text("Decomposição Temporal de Vídeo", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_acquisition
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# Teste Isolado da Página
def main(page: ft.Page):
    page.title = "Teste - Extração de Frames"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 650
    page.window_center()

    selected_paths = {}
    page.add(create_extract_frames_page(page, selected_paths))


if __name__ == "__main__":
    ft.app(target=main)