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
    Página Inicial com os 5 módulos em formato de lista (com ícone padronizado).
    """

    def build_module_card(
            title: str,
            description: str,
            icon: str,
            route_key: str
    ) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                # Lado Esquerdo: Ícone + Título
                ft.Row([
                    ft.Icon(icon, size=26, color=COLOR_PRIMARY),
                    ft.Text(title, size=15, weight="bold", color=COLOR_TEXT),
                ], spacing=12, alignment=ft.MainAxisAlignment.START),

                # Lado Direito: Descrição
                ft.Text(
                    description,
                    size=12,
                    color=COLOR_SUBTEXT,
                    text_align=ft.TextAlign.RIGHT,
                    expand=True
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=650,
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=COLOR_CARD_BG,
            border_radius=10,
            ink=True,
            on_click=lambda _: on_navigate(route_key),
            on_hover=lambda e: setattr(
                e.control,
                "bgcolor",
                COLOR_CARD_HOVER if e.data == "true" else COLOR_CARD_BG
            ) or e.control.update(),
        )

    modules = [
        {
            "title": "Aquisição",
            "description": "Captura e gerenciamento de conjuntos de imagens.",
            "icon": ft.icons.CAMERA_ENHANCE,
            "route_key": "acquisition"
        },
        {
            "title": "Calibração",
            "description": "Calibração intrínseca e estéreo de câmeras.",
            "icon": ft.icons.CAMERA_ALT,
            "route_key": "calibration_hub"
        },
        {
            "title": "Reconstrução 3D",
            "description": "Pipelines de reconstrução Monocular e Estéreo.",
            "icon": ft.icons.VIEW_IN_AR,
            "route_key": "reconstruction_hub"
        },
        {
            "title": "Pós-Processamento",
            "description": "Filtros, CLAHE e redimensionamento em lote.",
            "icon": ft.icons.TUNE,
            "route_key": "post_processing_hub"
        },
        {
            "title": "Visualização 3D",
            "description": "Visualizador de nuvens de pontos e malhas 3D.",
            "icon": ft.icons.VIEW_IN_AR,  # <-- Atualizado para usar exatamente ft.icons.VIEW_IN_AR
            "route_key": "visualization"
        },
    ]

    return ft.Container(
        alignment=ft.alignment.center,
        padding=20,
        content=ft.Column(
            controls=[
                build_module_card(
                    title=mod["title"],
                    description=mod["description"],
                    icon=mod["icon"],
                    route_key=mod["route_key"]
                ) for mod in modules
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )