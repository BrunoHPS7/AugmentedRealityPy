from pathlib import Path
from tqdm import tqdm
from typing import Callable, Optional
from src.acquisition.acquisition_utils import *



def extract_frames_from_video(
    video_path: Path,
    output_dir: Path,
    desired_fps: int,
    progress_callback: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Extrai quadros sequenciais de um vídeo com base em uma taxa alvo (Target FPS).
    Essencial para reduzir redundância de dados em pipelines de fotogrametria.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print(f"[ERROR] Failed to open video: {video_path}")
        return False

    native_fps = get_video_fps(capture)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if desired_fps <= 0 or total_frames <= 0:
        capture.release()
        return False

    output_dir.mkdir(parents=True, exist_ok=True)
    project_name = output_dir.name

    # 1. Cálculo do intervalo de amostragem temporal (Downsampling)
    # Exemplo matemático: Vídeo a 60 FPS nativo -> Desejo 2 FPS = Salva 1 a cada 30 frames.
    skip_interval = max(1, int(native_fps / desired_fps))
    saved_counter = 1

    print(f"\n[ACQUISITION] Starting video processing (Native FPS: {native_fps:.2f} -> Target: {desired_fps})")

    # 2. Loop de extração sequencial
    for frame_idx in tqdm(range(total_frames), desc="Extracting Frames", unit="frame", ncols=80, leave=False):
        success, frame = capture.read()
        if not success:
            break

        # Apenas converte e salva a imagem se ela cair no intervalo de amostragem correto
        if frame_idx % skip_interval == 0:
            # Formatação do nome com zeros à esquerda (ex: projeto_001.png) para ordenação alfanumérica correta no COLMAP
            file_name = f"{project_name}_{saved_counter:03d}.png"
            file_path = output_dir / file_name
            cv2.imwrite(str(file_path), frame)
            saved_counter += 1

        # Notifica a interface gráfica (Flet) sobre o avanço
        if progress_callback:
            progress_callback((frame_idx + 1) / total_frames)

    capture.release()
    print(f"[SUCCESS] Extraction complete! {saved_counter - 1} images saved to: {output_dir}")
    return True