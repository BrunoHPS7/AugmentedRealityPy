from src.camera_calibration.calibrations_utils import *


def run_stereo_calibration(
        input_dir_a: Path,
        input_dir_b: Path,
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
    obj_A, img_A, res_A = run_extract_chessboard(input_dir_a, board_dimensions, square_size_mm, progress_callback_a)

    print("[STEREO] Extracting corners for Camera B...")
    obj_B, img_B, res_B = run_extract_chessboard(input_dir_b, board_dimensions, square_size_mm, progress_callback_b)

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