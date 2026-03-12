import subprocess
import logging
from pathlib import Path
from tqdm import tqdm
from typing import Optional


def configurar_logging(caminho_projeto: Path) -> Path:
    arquivo_log = caminho_projeto / "fluxo_reconstrucao.log"

    for manipulador in logging.root.handlers[:]:
        logging.root.removeHandler(manipulador)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(arquivo_log, encoding='utf-8')]
    )
    return arquivo_log


def executar_comando(comando_shell: str):
    """Executa um comando de sistema silenciosamente, guardando o output no log."""
    processo = subprocess.Popen(
        comando_shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )

    for linha in iter(processo.stdout.readline, ""):
        conteudo = linha.strip()
        if conteudo:
            logging.info(conteudo)

    processo.wait()
    if processo.returncode != 0:
        raise subprocess.CalledProcessError(processo.returncode, comando_shell)


def executar_pipeline_reconstrucao_3d(pasta_frames: Path, pasta_projeto_saida: Path, caminho_calib: Optional[Path] = None) -> bool:
    """Pipeline COLMAP em 7 etapas com log no arquivo e progresso no terminal."""

    CONFIG = {"threads": 6, "use_gpu": 0, "max_img_size": 4000}

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = configurar_logging(pasta_projeto_saida)

    # Conversão para string com aspas para evitar bugs com espaços no COLMAP
    dir_img = f'"{pasta_frames.resolve()}"'
    dir_out = f'"{pasta_projeto_saida.resolve()}"'

    db_path = f'"{pasta_projeto_saida.resolve() / "database.db"}"'
    pasta_esparsa = pasta_projeto_saida / "sparse"
    pasta_densa = pasta_projeto_saida / "dense"

    pasta_esparsa.mkdir(exist_ok=True)
    pasta_densa.mkdir(exist_ok=True)

    # --- LÓGICA DE CALIBRAÇÃO MANUAL ---
    flags_calib_extractor = ""
    flags_calib_mapper = ""

    if caminho_calib and caminho_calib.exists():
        params = caminho_calib.read_text().strip()
        flags_calib_extractor = (
            f" --ImageReader.single_camera 1"
            f" --ImageReader.camera_model OPENCV"
            f" --ImageReader.camera_params {params}"
        )
        flags_calib_mapper = " --Mapper.ba_refine_focal_length 0 --Mapper.ba_refine_extra_params 0"

    etapas = [
        (f"colmap feature_extractor --database_path {db_path} --image_path {dir_img} --SiftExtraction.use_gpu {CONFIG['use_gpu']}{flags_calib_extractor}",
         "Extração de Features"),
        (f"colmap exhaustive_matcher --database_path {db_path} --SiftMatching.use_gpu {CONFIG['use_gpu']}",
         "Matcher Exaustivo"),
        (f"colmap mapper --database_path {db_path} --image_path {dir_img} --output_path \"{pasta_esparsa.resolve()}\"{flags_calib_mapper}",
         "Reconstrução Esparsa"),
        (f"colmap image_undistorter --image_path {dir_img} --input_path \"{pasta_esparsa.resolve() / '0'}\" --output_path \"{pasta_densa.resolve()}\" --output_type COLMAP",
         "Retificação de Imagens"),
        (f"colmap patch_match_stereo --workspace_path \"{pasta_densa.resolve()}\"", "Estéreo Patch Match"),
        (f"colmap stereo_fusion --workspace_path \"{pasta_densa.resolve()}\" --output_path \"{pasta_densa.resolve() / 'modelo_fusionado.ply'}\"",
         "Fusão (Point Cloud)"),
        (f"colmap stereo_mesher --input_path \"{pasta_densa.resolve() / 'modelo_fusionado.ply'}\" --output_path \"{pasta_densa.resolve() / 'malha_final.ply'}\"",
         "Geração de Malha (Mesh)")
    ]

    print(f"\n[RECONSTRUÇÃO] Iniciando pipeline para o projeto: {pasta_projeto_saida.name}")
    print(f"[LOG] Acompanhe os detalhes técnicos em: {arquivo_log.name}\n")

    try:
        # TQDM cuidando da barra de etapas
        with tqdm(total=len(etapas), desc="Progresso COLMAP", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)

                executar_comando(comando)

                if indice == 3 and not (pasta_esparsa / "0").exists():
                    raise Exception("Modelo esparso não gerado. Verifique as fotos.")

                barra.update(1)

        print("\n[SUCESSO] Reconstrução finalizada com sucesso!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline falhou: {erro}")
        print(f"[INFO] Verifique o arquivo {arquivo_log} para mais detalhes.")
        return False