from pathlib import Path
from typing import Dict, List
import flet as ft

from ui.router import ROUTE_REGISTRY, build_page_view
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_TEXT,
    COLOR_SUBTEXT,
    COLOR_CARD_BG,
)


def create_app_layout(page: ft.Page, selected_paths: Dict[str, Path]) -> ft.Container:
    """
    Cria a moldura principal do aplicativo contendo:
    - Cabeçalho (Header) fixo com botão voltar e título centralizado.
    - Área de conteúdo dinâmico (onde as páginas abrem).
    """
    # Pilha para guardar o histórico de navegação (ex: ["calibration_hub", "mono_calibration"])
    navigation_stack: List[str] = ["home"]

    # Componentes do Cabeçalho
    btn_back = ft.IconButton(
        icon=ft.icons.ARROW_BACK_IOS_NEW,
        icon_color=COLOR_PRIMARY,
        tooltip="Voltar",
        visible=False,  # Oculto na tela inicial/hub inicial
        on_click=lambda _: go_back()
    )

    lbl_page_title = ft.Text(
        value="",
        size=20,
        weight="bold",
        color=COLOR_TEXT,
        text_align=ft.TextAlign.CENTER
    )

    # Container central de conteúdo
    content_area = ft.Container(expand=True)

    def update_header_and_content():
        current_route = navigation_stack[-1]
        route_info = ROUTE_REGISTRY.get(current_route, {})

        # Atualiza título do cabeçalho
        lbl_page_title.value = route_info.get("title", "Visão Computacional 3D")

        # Exibe o botão de voltar se houver mais de uma página no histórico
        btn_back.visible = len(navigation_stack) > 1

        # Carrega a página atual no container de conteúdo
        content_area.content = build_page_view(
            route_key=current_route,
            page=page,
            selected_paths=selected_paths,
            on_navigate=navigate_to
        )

        page.update()

    def navigate_to(target_route: str):
        """Navega para uma nova rota empilhando no histórico."""
        navigation_stack.append(target_route)
        update_header_and_content()

    def go_back():
        """Volta para a tela anterior desempilhando o histórico."""
        if len(navigation_stack) > 1:
            navigation_stack.pop()
            update_header_and_content()

    # Estrutura do Cabeçalho Fixo (Topo)
    header_bar = ft.Container(
        height=60,
        padding=ft.padding.symmetric(horizontal=15),
        bgcolor=COLOR_CARD_BG,
        border_radius=8,
        content=ft.Row([
            ft.Container(content=btn_back, width=50, alignment=ft.alignment.center_left),
            ft.Container(content=lbl_page_title, expand=True, alignment=ft.alignment.center),
            ft.Container(width=50)  # Espaçador para manter o título perfeitamente centralizado
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # Inicializa o primeiro estado
    update_header_and_content()

    # Retorna o layout completo
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column([
            header_bar,
            ft.Container(height=10),
            content_area
        ], expand=True)
    )