from pathlib import Path
from typing import Dict, Callable
import flet as ft

# Home
from ui.pages.home_page import create_home_page

# Hubs
from ui.pages.camera_calibration.calibration_hub_page import create_calibration_hub_page
from ui.pages.reconstruction.reconstruction_hub_page import create_reconstruction_hub_page
from ui.pages.post_processing.post_processing_hub_page import create_post_processing_hub_page

# Páginas Direct - Acquisition
from ui.pages.acquisition.extract_frames_page import create_extract_frames_page

# Páginas Direct -  Visualization
from ui.pages.visualization.visualization_page import create_visualization_page

# Páginas Finais - Calibração
from ui.pages.camera_calibration.mono_calibration_page import create_mono_calibration_page
from ui.pages.camera_calibration.stereo_calibration_page import create_stereo_calibration_page

# Páginas Finais - Reconstrução
from ui.pages.reconstruction.mono_reconstruction_page import create_mono_reconstruction_page
from ui.pages.reconstruction.stereo_reconstruction_page import create_stereo_reconstruction_page

# Páginas Finais - Pós-Processamento
from ui.pages.post_processing.clahe_page import create_clahe_page
from ui.pages.post_processing.resize_page import create_resize_page

ROUTE_REGISTRY = {
    # Home Principal
    "home": {
        "title": "Início - Módulos Principais",
        "builder": create_home_page,
        "is_hub": True
    },

    # Hubs Sub-Modulares
    "calibration_hub": {
        "title": "Calibração de Câmeras",
        "builder": create_calibration_hub_page,
        "is_hub": True
    },
    "reconstruction_hub": {
        "title": "Reconstrução 3D",
        "builder": create_reconstruction_hub_page,
        "is_hub": True
    },
    "post_processing_hub": {
        "title": "Pós-Processamento de Imagens",
        "builder": create_post_processing_hub_page,
        "is_hub": True
    },

    # Calibração
    "mono_calibration": {
        "title": "Calibração Monocular",
        "builder": create_mono_calibration_page,
        "is_hub": False
    },
    "stereo_calibration": {
        "title": "Calibração Estéreo",
        "builder": create_stereo_calibration_page,
        "is_hub": False
    },

    # Reconstrução
    "mono_reconstruction": {
        "title": "Reconstrução Monocular",
        "builder": create_mono_reconstruction_page,
        "is_hub": False
    },
    "stereo_reconstruction": {
        "title": "Reconstrução Estéreo",
        "builder": create_stereo_reconstruction_page,
        "is_hub": False
    },

    # Pós-Processamento
    "clahe_processing": {
        "title": "Equalização CLAHE",
        "builder": create_clahe_page,
        "is_hub": False
    },
    "resize_processing": {
        "title": "Redimensionamento de Imagens",
        "builder": create_resize_page,
        "is_hub": False
    },

    "acquisition": {
        "title": "Aquisição de Imagens",
        "builder": create_extract_frames_page,
        "is_hub": False
    },
    "visualization": {
        "title": "Visualizador 3D",
        "builder": create_visualization_page,
        "is_hub": False
    },
}


def build_page_view(
        route_key: str,
        page: ft.Page,
        selected_paths: Dict[str, Path],
        on_navigate: Callable[[str], None]
) -> ft.Control:
    route_info = ROUTE_REGISTRY.get(route_key)
    if not route_info:
        return ft.Container(
            content=ft.Text(f"Rota '{route_key}' não encontrada!", color="red", size=18),
            alignment=ft.alignment.center
        )

    builder = route_info["builder"]

    if route_info.get("is_hub", False):
        return builder(page, selected_paths, on_navigate=on_navigate)

    return builder(page, selected_paths)