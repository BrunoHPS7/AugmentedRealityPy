import os
import cv2
from pathlib import Path
from tqdm import tqdm
from typing import Callable, Optional, Tuple


def run_clahe_enhancement(
        input_dir: Path,
        output_dir: Path,
        clip_limit: float = 2.0,
        tile_size: Tuple[int, int] = (8, 8),
        progress_callback: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Aplica a técnica CLAHE em todas as imagens (de forma recursiva, mantendo subpastas)
    para melhorar o contraste local sem distorcer as cores reais (via espaço LAB).
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # 1. Inicialização do algoritmo CLAHE
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

    print(f"[POST-PROCESSING] Applying CLAHE enhancement recursively...")

    # Coleta recursiva de arquivos (entra em pastas como 'esquerda' e 'direita')
    files = [p for p in input_dir.rglob('*') if p.suffix.lower() in valid_extensions]

    if not files:
        print("[WARNING] No images found to enhance.")
        return False

    total_files = len(files)

    # 2. Processamento iterativo de cada imagem
    for idx, img_path in enumerate(tqdm(files, desc="Enhancing", unit="img", ncols=80, leave=False)):
        img = cv2.imread(str(img_path))

        if img is None:
            continue

        # Conversão para LAB e aplicação do CLAHE
        lab_image = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        l_enhanced = clahe.apply(l_channel)

        combined_lab = cv2.merge((l_enhanced, a_channel, b_channel))
        final_img = cv2.cvtColor(combined_lab, cv2.COLOR_LAB2BGR)

        # Reconstrução da árvore de diretórios na pasta de saída
        relative_path = img_path.relative_to(input_dir)
        img_output_path = output_dir / relative_path
        img_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Escrita do arquivo processado
        cv2.imwrite(str(img_output_path), final_img)

        # Notifica a interface gráfica (Flet)
        if progress_callback:
            progress_callback((idx + 1) / total_files)

    print(f"[SUCCESS] {total_files} images enhanced and saved in: {output_dir}")
    return True


def run_resize_images(
        input_dir: Path,
        output_dir: Path,
        target_size: Tuple[int, int] = (3000, 4000),  # (Height, Width)
        progress_callback: Optional[Callable[[float], None]] = None
) -> bool:
    """
    Padroniza a resolução de todas as imagens de forma recursiva.
    Usa redimensionamento proporcional seguido de corte central (crop)
    para não alterar o Aspect Ratio da lente da câmera.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    target_h, target_w = target_size
    target_aspect = target_w / target_h

    print(f"[POST-PROCESSING] Resizing images to {target_w}x{target_h} recursively...")

    files = [p for p in input_dir.rglob('*') if p.suffix.lower() in valid_extensions]

    if not files:
        print("[WARNING] No images found to resize.")
        return False

    total_files = len(files)

    for idx, img_path in enumerate(tqdm(files, desc="Resizing", unit="img", ncols=80, leave=False)):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        orig_h, orig_w = img.shape[:2]
        orig_aspect = orig_w / orig_h

        # 1. Resize proporcional
        if orig_aspect > target_aspect:
            new_h = target_h
            new_w = int(orig_w * (target_h / orig_h))
        else:
            new_w = target_w
            new_h = int(orig_h * (target_w / orig_w))

        resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 2. Crop central exato
        start_x = (new_w - target_w) // 2
        start_y = (new_h - target_h) // 2
        final_img = resized_img[start_y:start_y + target_h, start_x:start_x + target_w]

        # Reconstrução da árvore de diretórios na pasta de saída
        relative_path = img_path.relative_to(input_dir)
        img_output_path = output_dir / relative_path
        img_output_path.parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(img_output_path), final_img)

        # Notifica a interface gráfica (Flet)
        if progress_callback:
            progress_callback((idx + 1) / total_files)

    print(f"[SUCCESS] {total_files} images resized and saved in: {output_dir}")
    return True