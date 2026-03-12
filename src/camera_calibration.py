import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


def executar_fluxo_calibracao_camera(
        diretorio_fotos: Path,
        diretorio_saida: Path,
        dimensoes_tabuleiro: tuple,
        tamanho_quadrado_mm: float,
        nome_arquivo_saida: str
) -> bool:
    """Calcula a matriz intrínseca e os coeficientes de distorção a partir de fotos."""

    criterio_refinamento = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # 1. Preparação dos pontos reais (3D) no espaço físico
    pontos_objeto_3d = np.zeros((dimensoes_tabuleiro[0] * dimensoes_tabuleiro[1], 3), np.float32)
    pontos_objeto_3d[:, :2] = np.mgrid[0:dimensoes_tabuleiro[0], 0:dimensoes_tabuleiro[1]].T.reshape(-1, 2)
    pontos_objeto_3d *= tamanho_quadrado_mm

    lista_pontos_3d = []  # Pontos no mundo real
    lista_pontos_2d = []  # Pontos projetados na foto

    # 2. Busca pelas imagens usando pathlib
    extensoes = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
    caminhos_fotos = []

    for ext in extensoes:
        caminhos_fotos.extend(diretorio_fotos.glob(ext))
        caminhos_fotos.extend(diretorio_fotos.glob(ext.upper()))

    caminhos_fotos = sorted(list(set(caminhos_fotos)))

    if not caminhos_fotos:
        print(f"\n[ERRO] Nenhuma imagem válida encontrada na pasta: {diretorio_fotos}")
        return False

    print(f"\n[CALIBRAÇÃO] Iniciando análise de {len(caminhos_fotos)} imagens...")

    imagem_cinza_ref = None
    sucessos = 0

    # 3. Processamento das imagens com barra de progresso
    for caminho in tqdm(caminhos_fotos, desc="Extraindo Quinas", unit="foto", ncols=80):
        frame = cv2.imread(str(caminho))
        if frame is None:
            continue

        imagem_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if imagem_cinza_ref is None:
            imagem_cinza_ref = imagem_cinza

        achou, quinas = cv2.findChessboardCorners(imagem_cinza, dimensoes_tabuleiro, None)

        if achou:
            lista_pontos_3d.append(pontos_objeto_3d)
            quinas_refinadas = cv2.cornerSubPix(imagem_cinza, quinas, (11, 11), (-1, -1), criterio_refinamento)
            lista_pontos_2d.append(quinas_refinadas)
            sucessos += 1

    if not lista_pontos_3d:
        print("\n[ERRO] O padrão de xadrez não foi detectado com sucesso em NENHUMA foto.")
        return False

    # 4. Cálculo Matemático da Câmera
    print(f"\n[MATEMÁTICA] Calculando parâmetros com {sucessos} amostras válidas...")
    sucesso_calib, matriz_camera, distorcao, _, _ = cv2.calibrateCamera(
        lista_pontos_3d, lista_pontos_2d, imagem_cinza_ref.shape[::-1], None, None
    )

    if sucesso_calib:
        diretorio_saida.mkdir(parents=True, exist_ok=True)

        # 1. Extrair os parâmetros na ordem: fx, fy, cx, cy, k1, k2, p1, p2
        fx = matriz_camera[0, 0]
        fy = matriz_camera[1, 1]
        cx = matriz_camera[0, 2]
        cy = matriz_camera[1, 2]
        k1, k2, p1, p2 = distorcao.ravel()[:4]

        # 2. Formatar a string (usando 12 casas decimais para garantir precisão)
        params_colmap = f"{fx:.12f},{fy:.12f},{cx:.12f},{cy:.12f},{k1:.12f},{k2:.12f},{p1:.12f},{p2:.12f}"

        # 3. Escrita do arquivo
        caminho_final = (diretorio_saida / nome_arquivo_saida).with_suffix('.txt')
        caminho_final.write_text(params_colmap)

        print(f"\n[SUCESSO] Parâmetros salvos para COLMAP: {caminho_final.name}")
        print(f"Valores: {params_colmap}")

        return True