import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


def _extrair_pontos_tabuleiro(diretorio_fotos: Path, dimensoes: tuple, tamanho_quadrado_mm: float):
    """
    Localiza as quinas do tabuleiro de xadrez nas imagens e mapeia para coordenadas reais.
    """
    criterio_refinamento = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Inicialização das coordenadas 3D teóricas do tabuleiro (eixo Z em zero)
    pontos_objeto_3d = np.zeros((dimensoes[0] * dimensoes[1], 3), np.float32)
    pontos_objeto_3d[:, :2] = np.mgrid[0:dimensoes[0], 0:dimensoes[1]].T.reshape(-1, 2)

    # Aplicação da escala física para converter índices de grade em milímetros
    pontos_objeto_3d *= tamanho_quadrado_mm

    lista_pontos_3d = []
    lista_pontos_2d = []
    imagem_cinza_ref = None

    # Coleta e ordenação de arquivos de imagem suportados
    extensoes = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
    caminhos_fotos = []
    for ext in extensoes:
        caminhos_fotos.extend(diretorio_fotos.glob(ext))
        caminhos_fotos.extend(diretorio_fotos.glob(ext.upper()))

    caminhos_fotos = sorted(list(set(caminhos_fotos)))

    if not caminhos_fotos:
        return None, None, None

    # Iteração sobre as imagens para detecção e refinamento de subpixels
    for caminho in tqdm(caminhos_fotos, desc=f"Processando {diretorio_fotos.name}", unit="foto", leave=False):
        frame = cv2.imread(str(caminho))
        if frame is None: continue

        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if imagem_cinza_ref is None: imagem_cinza_ref = cinza

        # Busca inicial pelas quinas internas do tabuleiro
        achou, quinas = cv2.findChessboardCorners(cinza, dimensoes, None)
        if achou:
            lista_pontos_3d.append(pontos_objeto_3d)
            # Refinamento iterativo para precisão superior à do pixel
            refinadas = cv2.cornerSubPix(cinza, quinas, (11, 11), (-1, -1), criterio_refinamento)
            lista_pontos_2d.append(refinadas)

    return lista_pontos_3d, lista_pontos_2d, imagem_cinza_ref


def executar_calibracao_mono(
        diretorio_fotos: Path,
        diretorio_saida: Path,
        dimensoes: tuple,
        tamanho_quadrado_mm: float,
        nome_arquivo: str
) -> bool:
    """
    Calcula a distorção da lente e a matriz intrínseca para uma única câmera.
    """
    # Extração de correspondências entre o plano da imagem (2D) e o mundo real (3D)
    pts_3d, pts_2d, img_ref = _extrair_pontos_tabuleiro(diretorio_fotos, dimensoes, tamanho_quadrado_mm)

    if not pts_3d:
        print(f"\n[ERRO] Falha na detecção de quinas em: {diretorio_fotos}")
        return False

    # Resolução do sistema de projeção para obter focais e pontos principais
    print(f"[MATEMÁTICA] Calculando parâmetros para: {nome_arquivo}...")
    sucesso, mtx, dist, _, _ = cv2.calibrateCamera(
        pts_3d, pts_2d, img_ref.shape[::-1], None, None
    )

    if sucesso:
        # Estruturação do diretório de saída organizado por projeto
        pasta_projeto_mono = diretorio_saida / "mono" / nome_arquivo
        pasta_projeto_mono.mkdir(parents=True, exist_ok=True)

        # Decomposição da matriz intrínseca e vetores de distorção
        fx, fy = mtx[0, 0], mtx[1, 1]
        cx, cy = mtx[0, 2], mtx[1, 2]
        k1, k2, p1, p2 = dist.ravel()[:4]

        # Serialização dos parâmetros no padrão compatível com o COLMAP
        txt_content = f"{fx:.12f},{fy:.12f},{cx:.12f},{cy:.12f},{k1:.12f},{k2:.12f},{p1:.12f},{p2:.12f}"

        caminho_txt = pasta_projeto_mono / f"{nome_arquivo}.txt"
        caminho_txt.write_text(txt_content)

        print(f"\n[SUCESSO] Calibração MONO salva em: {pasta_projeto_mono}")
        return True

    return False


def executar_calibracao_stereo(
        pasta_A: Path,
        pasta_B: Path,
        diretorio_saida: Path,
        dimensoes: tuple,
        tamanho_quadrado_mm: float,
        nome_arquivo: str
) -> bool:
    """
    Calcula a relação espacial (rotação e translação) entre duas câmeras.
    """
    print(f"\n[STEREO] Analisando par de câmeras para: {nome_arquivo}")

    # Coleta de pontos de controle para ambos os sensores de forma independente
    obj_A, img_A, res_A = _extrair_pontos_tabuleiro(pasta_A, dimensoes, tamanho_quadrado_mm)
    obj_B, img_B, res_B = _extrair_pontos_tabuleiro(pasta_B, dimensoes, tamanho_quadrado_mm)

    if not img_A or not img_B or len(img_A) != len(img_B):
        print("\n[ERRO] Inconsistência nos pares de imagens detectados.")
        return False

    # Estimativa inicial dos intrínsecos de cada câmera separadamente
    _, mtxA, distA, _, _ = cv2.calibrateCamera(obj_A, img_A, res_A.shape[::-1], None, None)
    _, mtxB, distB, _, _ = cv2.calibrateCamera(obj_B, img_B, res_B.shape[::-1], None, None)

    # Determinação da geometria epipolar (Matriz de Rotação R e Vetor de Translação T)
    flags = cv2.CALIB_FIX_INTRINSIC
    criterio = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)

    ret, _, _, _, _, R, T, _, _ = cv2.stereoCalibrate(
        obj_A, img_A, img_B, mtxA, distA, mtxB, distB, res_A.shape[::-1],
        criteria=criterio, flags=flags
    )

    if ret:
        # Criação da estrutura de pastas para o projeto stereo
        pasta_projeto_stereo = diretorio_saida / "stereo" / nome_arquivo
        pasta_projeto_stereo.mkdir(parents=True, exist_ok=True)

        def formatar_colmap(m, d):
            return f"{m[0, 0]:.12f},{m[1, 1]:.12f},{m[0, 2]:.12f},{m[1, 2]:.12f},{d.ravel()[0]:.12f},{d.ravel()[1]:.12f},{d.ravel()[2]:.12f},{d.ravel()[3]:.12f}"

        # Persistência dos arquivos intrínsecos individuais
        (pasta_projeto_stereo / f"{nome_arquivo}_A.txt").write_text(formatar_colmap(mtxA, distA))
        (pasta_projeto_stereo / f"{nome_arquivo}_B.txt").write_text(formatar_colmap(mtxB, distB))

        # Cálculo da distância euclidiana entre as câmeras (Baseline métrica)
        baseline = np.linalg.norm(T)
        extrinsecos_content = (
            f"BASELINE_MM: {baseline:.12f}\n"
            f"T_VEC (X, Y, Z): {T.ravel().tolist()}\n"
            f"R_MAT:\n{np.array2string(R, precision=12, separator=',')}"
        )
        (pasta_projeto_stereo / f"{nome_arquivo}_RELACAO.txt").write_text(extrinsecos_content)

        print(f"\n[SUCESSO] Projeto STEREO salvo em: {pasta_projeto_stereo}")
        print(f"Distância entre câmeras (Baseline): {baseline:.4f} mm")
        return True

    return False