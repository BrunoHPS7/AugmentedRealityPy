from typing import Callable, Dict
from pathlib import Path
import flet as ft

from ui.theme import (
    COLOR_PRIMARY,
    COLOR_ICON,
    COLOR_TEXT,
    COLOR_SUBTEXT,
    COLOR_CARD_BG,
    COLOR_CARD_HOVER,
)


def create_home_page(
        page: ft.Page,
        selected_paths: Dict[str, Path],
        on_navigate: Callable[[str], None]
) -> ft.Container:
    """
    Página Inicial (Dashboard/Home) com os 5 módulos principais da aplicação.
    """

    def build_module_card(
            title: str,
            description: str,
            icon: str,
            route_key: str
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=36, color=COLOR_PRIMARY),
                ft.Text(title, size=16, weight="bold", color=COLOR_TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text(description, size=11, color=COLOR_SUBTEXT, text_align=ft.TextAlign.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=200,
            height=160,
            padding=15,
            bgcolor=COLOR_CARD_BG,
            border_radius=12,
            ink=True,
            on_click=lambda _: on_navigate(route_key),
            on_hover=lambda e: setattr(
                e.control,
                "bgcolor",
                COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG
            ) or e.control.update(),
        )

    return ft.Container(
        alignment=ft.alignment.center,
        padding=20,
        content=ft.Column([
            ft.Icon(ft.icons.VIEW_IN_AR_ROUNDED, size=55, color=COLOR_ICON),
            ft.Text("Plataforma de Fotogrametria e Reconstrução 3D", size=24, weight="bold", color=COLOR_TEXT,
                    text_align=ft.TextAlign.CENTER),
            ft.Text("Selecione um dos módulos abaixo para iniciar", color=COLOR_SUBTEXT),
            ft.Container(height=15),

            # Grid de cards com os 5 módulos principais
            ft.Row([
                build_module_card(
                    title="Aquisição",
                    description="Captura e gerenciamento de conjuntos de imagens.",
                    icon=ft.icons.CAMERA_ENHANCE,
                    route_key="acquisition"
                ),
                build_module_card(
                    title="Calibração",
                    description="Calibração intrínseca e estéreo de câmeras.",
                    icon=ft.icons.CAMERA_ALT,
                    route_key="calibration_hub"
                ),
                build_module_card(
                    title="Reconstrução 3D",
                    description="Pipelines de reconstrução Monocular e Estéreo.",
                    icon=ft.icons.VIEW_IN_AR,  # <-- Ícone corrigido aqui!
                    route_key="reconstruction_hub"
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),

            ft.Row([
                build_module_card(
                    title="Pós-Processamento",
                    description="Filtros, CLAHE e redimensionamento em lote.",
                    icon=ft.icons.TUNE,
                    route_key="post_processing_hub"
                ),
                build_module_card(
                    title="Visualização 3D",
                    description="Visualizador de nuvens de pontos e malhas 3D.",
                    icon=ft.icons.PREVIEW,
                    route_key="visualization"
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),

        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )