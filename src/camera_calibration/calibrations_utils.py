import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from typing import Callable, Optional, Tuple



def run_extract_chessboard(
        images_dir: Path,
        board_dimensions: Tuple[int, int],
        square_size_mm: float,
        progress_callback: Optional[Callable[[float], None]] = None
):
    """
    Localiza as quinas internas do tabuleiro de calibração nas imagens
    e mapeia essas posições 2D para coordenadas 3D teóricas do mundo real.
    """
    # Critério de parada para o algoritmo de refinamento (precisão de subpixel)
    refinement_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # 1. Criação da grade 3D teórica (Eixos X e Y variam, Z é sempre 0 pois o alvo é plano)
    obj_points_3d = np.zeros((board_dimensions[0] * board_dimensions[1], 3), np.float32)
    obj_points_3d[:, :2] = np.mgrid[0:board_dimensions[0], 0:board_dimensions[1]].T.reshape(-1, 2)

    # Multiplica pelos milímetros reais para dar escala física ao modelo matemático
    obj_points_3d *= square_size_mm

    list_3d_points = []
    list_2d_points = []
    reference_gray_image = None

    # 2. Busca e ordenação de todas as imagens de calibração no diretório
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
    image_paths = []
    for ext in extensions:
        image_paths.extend(images_dir.glob(ext))
        image_paths.extend(images_dir.glob(ext.upper()))

    image_paths = sorted(list(set(image_paths)))

    if not image_paths:
        return None, None, None

    total_images = len(image_paths)

    # 3. Processamento imagem por imagem
    for idx, path in enumerate(tqdm(image_paths, desc=f"Processing {images_dir.name}", unit="img", leave=False)):
        frame = cv2.imread(str(path))
        if frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if reference_gray_image is None:
            reference_gray_image = gray

        # Tenta encontrar o padrão do xadrez na imagem atual
        found, corners = cv2.findChessboardCorners(gray, board_dimensions, None)

        if found:
            list_3d_points.append(obj_points_3d)
            # Refina as coordenadas encontradas para uma precisão maior que a de um pixel (subpixel)
            refined_corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), refinement_criteria)
            list_2d_points.append(refined_corners)

        # Notifica a interface gráfica (Flet) sobre o avanço, se o callback existir
        if progress_callback:
            progress_callback((idx + 1) / total_images)

    return list_3d_points, list_2d_points, reference_gray_image