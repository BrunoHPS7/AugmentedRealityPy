from typing import Callable, Dict
from pathlib import Path
import flet as ft

from ui.controllers.reconstruction.reconstruction_hub_controller import handle_reconstruction_hub_click
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_ICON,
    COLOR_TEXT,
    COLOR_SUBTEXT,
    COLOR_CARD_BG,
    COLOR_CARD_HOVER,
)


def create_reconstruction_hub_page(
    page: ft.Page,
    selected_paths: Dict[str, Path],
    on_navigate: Callable[[str], None]
) -> ft.Container:
    """
    View para o Hub de Reconstrução 3D.
    """

    def build_option_card(
        title: str,
        description: str,
        icon: str,
        route_key: str
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color=COLOR_PRIMARY),
                ft.Text(title, size=18, weight="bold", color=COLOR_TEXT),
                ft.Text(description, size=12, color=COLOR_SUBTEXT, text_align=ft.TextAlign.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=260,
            height=180,
            padding=20,
            bgcolor=COLOR_CARD_BG,
            border_radius=12,
            ink=True,
            on_click=lambda _: handle_reconstruction_hub_click(route_key, on_navigate),
            on_hover=lambda e: setattr(
                e.control,
                "bgcolor",
                COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG
            ) or e.control.update(),
        )

    return ft.Container(
        alignment=ft.alignment.center,
        padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.VIEW_IN_AR, size=50, color=COLOR_ICON),
            ft.Text("Reconstrução 3D", size=26, weight="bold", color=COLOR_TEXT),
            ft.Text("Selecione o pipeline de reconstrução que deseja executar", color=COLOR_SUBTEXT),
            ft.Container(height=20),
            ft.Row([
                build_option_card(
                    title="Reconstrução Monocular",
                    description="Gere um modelo 3D usando uma sequência de imagens de apenas uma câmera (COLMAP SfM).",
                    icon=ft.icons.IMAGE_SEARCH,
                    route_key="mono_reconstruction"
                ),
                build_option_card(
                    title="Reconstrução Estéreo",
                    description="Gere um modelo 3D denso e calibrado em escala real usando um par estéreo (Câmera Esq/Dir).",
                    icon=ft.icons.LAYERS,
                    route_key="stereo_reconstruction"
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


def main(page: ft.Page):
    page.title = "Teste - Hub de Reconstrução"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 600
    page.window_center()

    def dummy_navigate(route: str):
        page.show_snack_bar(
            ft.SnackBar(ft.Text(f"Navegando para: {route}"), bgcolor=COLOR_PRIMARY)
        )

    selected_paths = {}
    page.add(create_reconstruction_hub_page(page, selected_paths, on_navigate=dummy_navigate))


if __name__ == "__main__":
    ft.app(target=main)