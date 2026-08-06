from src.camera_calibration.calibrations_utils import *


def run_mono_calibration(
        input_dir: Path,
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
    pts_3d, pts_2d, ref_img = run_extract_chessboard(input_dir, board_dimensions, square_size_mm, progress_callback)

    if not pts_3d:
        print(f"\n[ERROR] Failed to detect corners in: {input_dir}")
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