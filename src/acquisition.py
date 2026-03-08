import cv2
from pathlib import Path
from tqdm import tqdm


def obter_taxa_quadros_video(captura) -> float:
    """Extrai a taxa de quadros (FPS) de um objeto VideoCapture."""
    return captura.get(cv2.CAP_PROP_FPS)


def extrair_e_salvar_frames_por_segundo(caminho_video: Path, diretorio_saida: Path, fps_desejado: int) -> bool:
    """Extrai frames de um vídeo com base no FPS desejado, com barra de progresso no terminal."""

    captura_video = cv2.VideoCapture(str(caminho_video))
    if not captura_video.isOpened():
        print(f"[ERRO] Falha ao abrir o vídeo: {caminho_video}")
        return False

    fps_nativo = obter_taxa_quadros_video(captura_video)
    total_quadros = int(captura_video.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps_desejado <= 0 or total_quadros <= 0:
        captura_video.release()
        return False

    diretorio_saida.mkdir(parents=True, exist_ok=True)
    nome_projeto = diretorio_saida.name

    intervalo_pulo = max(1, int(fps_nativo / fps_desejado))
    contador_salvos = 1

    print(f"\n[EXTRAÇÃO] Iniciando processamento do vídeo (FPS Nativo: {fps_nativo:.2f} -> Desejado: {fps_desejado})")

    # tqdm cria uma barra de progresso linda direto no terminal
    for indice_frame in tqdm(range(total_quadros), desc="Extraindo Frames", unit="frame", ncols=80):
        sucesso, frame = captura_video.read()
        if not sucesso:
            break

        if indice_frame % intervalo_pulo == 0:
            nome_arquivo = f"{nome_projeto}_{contador_salvos:03d}.png"
            caminho_arquivo = diretorio_saida / nome_arquivo
            cv2.imwrite(str(caminho_arquivo), frame)
            contador_salvos += 1

    captura_video.release()
    print(f"[SUCESSO] Extração concluída! {contador_salvos - 1} imagens salvas em: {diretorio_saida}")
    return True