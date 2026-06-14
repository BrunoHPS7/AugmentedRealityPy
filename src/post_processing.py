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
    Aplica a técnica CLAHE (Contrast Limited Adaptive Histogram Equalization)
    em todas as imagens de um diretório para melhorar o contraste local
    sem distorcer as cores reais.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Garante que a pasta de destino exista
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Inicialização matemática do algoritmo CLAHE
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

    print(f"[POST-PROCESSING] Applying CLAHE enhancement...")

    # Coleta os arquivos válidos no diretório
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)]

    if not files:
        print("[WARNING] No images found to enhance.")
        return False

    total_files = len(files)

    # 2. Processamento iterativo de cada imagem
    for idx, filename in enumerate(tqdm(files, desc="Enhancing", unit="img", ncols=80, leave=False)):
        img_full_path = input_dir / filename
        img = cv2.imread(str(img_full_path))

        if img is None:
            continue

        # 3. Conversão para o espaço de cor LAB.
        # Motivo: No espaço RGB, alterar o contraste deforma as cores.
        # No LAB, o canal 'L' isola a luminosidade (brilho), preservando os canais 'a' e 'b' (cores originais).
        lab_image = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)

        # 4. Aplicação do algoritmo CLAHE estritamente no canal de Luminosidade
        l_enhanced = clahe.apply(l_channel)

        # 5. Recombinação dos canais e transformação matemática de volta para RGB (BGR no OpenCV)
        combined_lab = cv2.merge((l_enhanced, a_channel, b_channel))
        final_img = cv2.cvtColor(combined_lab, cv2.COLOR_LAB2BGR)

        # 6. Escrita do arquivo processado em disco
        cv2.imwrite(str(output_dir / filename), final_img)

        # Notifica a interface gráfica (Flet) sobre o avanço do processamento
        if progress_callback:
            progress_callback((idx + 1) / total_files)

    print(f"[SUCCESS] {total_files} images enhanced and saved in: {output_dir}")
    return True