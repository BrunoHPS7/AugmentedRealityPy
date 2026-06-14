import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from typing import Callable, Optional, Tuple


def _extract_chessboard_corners(
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


def run_mono_calibration(
        images_dir: Path,
        output_dir: Path,
        board_dimensions: Tuple[int, int],
        square_size_mm: float,
        project_name: str,
        progress_callback: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Calcula os parâmetros intrínsecos (distâncias focais e ponto principal)
    e os coeficientes de distorção da lente de uma única câmera.
    """
    # Coleta as correspondências entre o mundo 3D (teórico) e o plano 2D (foto real)
    pts_3d, pts_2d, ref_img = _extract_chessboard_corners(
        images_dir, board_dimensions, square_size_mm, progress_callback
    )

    if not pts_3d:
        print(f"\n[ERROR] Failed to detect corners in: {images_dir}")
        return False

    print(f"[MATH] Calculating parameters for: {project_name}...")

    # Otimização matemática: resolve o sistema de equações para encontrar a matriz intrínseca
    success, mtx, dist, _, _ = cv2.calibrateCamera(
        pts_3d, pts_2d, ref_img.shape[::-1], None, None
    )

    if success:
        mono_project_folder = output_dir / "mono" / project_name
        mono_project_folder.mkdir(parents=True, exist_ok=True)

        # Extrai os valores individuais da matriz intrínseca (mtx) e de distorção radial/tangencial (dist)
        # fx, fy = Distâncias Focais | cx, cy = Centro Ótico | k1, k2, p1, p2 = Coeficientes de Distorção
        fx, fy = mtx[0, 0], mtx[1, 1]
        cx, cy = mtx[0, 2], mtx[1, 2]
        k1, k2, p1, p2 = dist.ravel()[:4]

        # Formata os dados no padrão exato exigido pelo COLMAP (SIMPLE_RADIAL ou OPENCV model)
        txt_content = f"{fx:.12f},{fy:.12f},{cx:.12f},{cy:.12f},{k1:.12f},{k2:.12f},{p1:.12f},{p2:.12f}"

        out_file = mono_project_folder / f"{project_name}.txt"
        out_file.write_text(txt_content)

        print(f"\n[SUCCESS] MONO calibration saved in: {mono_project_folder}")
        return True

    return False


def run_stereo_calibration(
        folder_a: Path,
        folder_b: Path,
        output_dir: Path,
        board_dimensions: Tuple[int, int],
        square_size_mm: float,
        project_name: str,
        progress_callback_a: Optional[Callable[[float], None]] = None,
        progress_callback_b: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Calcula a relação espacial geométrica (Matriz de Rotação e Vetor de Translação)
    entre duas câmeras fixas usando imagens pareadas e sincronizadas.
    """
    print(f"\n[STEREO] Analyzing camera pair for: {project_name}")

    # 1. Extração de pontos de controle (quinas) de forma independente para cada câmera
    print("[STEREO] Extracting corners for Camera A...")
    obj_A, img_A, res_A = _extract_chessboard_corners(folder_a, board_dimensions, square_size_mm, progress_callback_a)

    print("[STEREO] Extracting corners for Camera B...")
    obj_B, img_B, res_B = _extract_chessboard_corners(folder_b, board_dimensions, square_size_mm, progress_callback_b)

    # Garante que ambas as câmeras capturaram os alvos perfeitamente pareados
    if not img_A or not img_B or len(img_A) != len(img_B):
        print("\n[ERROR] Inconsistency in detected image pairs.")
        return False

    # 2. Estima os intrínsecos de cada câmera separadamente (Bootstrapping)
    _, mtxA, distA, _, _ = cv2.calibrateCamera(obj_A, img_A, res_A.shape[::-1], None, None)
    _, mtxB, distB, _, _ = cv2.calibrateCamera(obj_B, img_B, res_B.shape[::-1], None, None)

    # Fixa os intrínsecos (CALIB_FIX_INTRINSIC) para forçar o algoritmo a descobrir apenas a posição relativa
    flags = cv2.CALIB_FIX_INTRINSIC
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)

    # 3. Resolve a geometria epipolar para encontrar a Rotação (R) e Translação (T)
    ret, _, _, _, _, R, T, _, _ = cv2.stereoCalibrate(
        obj_A, img_A, img_B, mtxA, distA, mtxB, distB, res_A.shape[::-1],
        criteria=criteria, flags=flags
    )

    if ret:
        stereo_project_folder = output_dir / "stereo" / project_name
        stereo_project_folder.mkdir(parents=True, exist_ok=True)

        def format_colmap(m, d):
            return f"{m[0, 0]:.12f},{m[1, 1]:.12f},{m[0, 2]:.12f},{m[1, 2]:.12f},{d.ravel()[0]:.12f},{d.ravel()[1]:.12f},{d.ravel()[2]:.12f},{d.ravel()[3]:.12f}"

        # Salva os arquivos de configuração individuais para posterior uso no pipeline do COLMAP
        (stereo_project_folder / f"{project_name}_A.txt").write_text(format_colmap(mtxA, distA))
        (stereo_project_folder / f"{project_name}_B.txt").write_text(format_colmap(mtxB, distB))

        # 4. Cálculo da Baseline Métrica (Magnitude exata do vetor de translação 3D)
        baseline = np.linalg.norm(T)

        # Persistência da relação extrínseca completa no disco
        extrinsics_content = (
            f"BASELINE_MM: {baseline:.12f}\n"
            f"T_VEC (X, Y, Z): {T.ravel().tolist()}\n"
            f"R_MAT:\n{np.array2string(R, precision=12, separator=',')}"
        )
        (stereo_project_folder / f"{project_name}_RELATION.txt").write_text(extrinsics_content)

        print(f"\n[SUCCESS] STEREO project saved in: {stereo_project_folder}")
        print(f"Distance between cameras (Baseline): {baseline:.4f} mm")
        return True

    return False