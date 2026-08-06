import time
from tqdm import tqdm
from src.reconstruction.reconstruction_utils import *



def run_mono_reconstruction(pasta_frames: Path, pasta_projeto_saida: Path, progress_callback=None) -> bool:
    """Pipeline COLMAP em 7 etapas com suporte automático para Mono e Stereo via pastas e integração de logs na UI."""

    # Configurações globais que podem ser mescladas nos dicionários de parâmetros depois
    CONFIG = {"threads": -1, "use_gpu": 1, "max_img_size": 4000}

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = setup_logger(pasta_projeto_saida)

    # Definição de caminhos usando Path puro
    db_path = pasta_projeto_saida / "database.db"
    pasta_esparsa = pasta_projeto_saida / "sparse"
    pasta_densa = pasta_projeto_saida / "dense"

    pasta_esparsa.mkdir(exist_ok=True)
    pasta_densa.mkdir(exist_ok=True)

    constructor = ColmapCommandBuilder()

    # --- DEFINIÇÃO DAS ETAPAS DO PIPELINE USANDO O CONSTRUTOR ---
    etapas = [
        # Etapa 1: Feature Extractor
        (constructor.build("feature_extractor", {
            "database_path": db_path,
            "image_path": pasta_frames
        }), "Extração de Features"),

        # Etapa 2: Matcher
        (constructor.build("sequential_matcher", {
            "database_path": db_path
        }), "Matcher Sequencial"),

        # Etapa 3: Mapper
        (constructor.build("mapper", {
            "database_path": db_path,
            "image_path": pasta_frames,
            "output_path": pasta_esparsa
        }), "Reconstrução Esparsa"),

        # Etapa 4: Undistorter
        (constructor.build("image_undistorter", {
            "image_path": pasta_frames,
            "input_path": pasta_esparsa / "0",
            "output_path": pasta_densa,
            "output_type": "COLMAP"
        }), "Retificação de Imagens"),

        # Etapa 5: Patch Match
        (constructor.build("patch_match_stereo", {
            "workspace_path": pasta_densa
        }), "Estéreo Patch Match"),

        # Etapa 6: Fusion
        (constructor.build("stereo_fusion", {
            "workspace_path": pasta_densa,
            "output_path": pasta_densa / "modelo_fusionado.ply"
        }), "Fusão (Point Cloud)"),

        # Etapa 7: Poisson Mesher
        (constructor.build("poisson_mesher", {
            "input_path": pasta_densa / "modelo_fusionado.ply",
            "output_path": pasta_densa / "malha_final.ply"
        }), "Geração de Malha (Poisson)")
    ]

    print(f"\n[RECONSTRUÇÃO] Iniciando pipeline para o projeto: {pasta_projeto_saida.name}")
    print(f"[LOG] Acompanhe os detalhes técnicos em: {arquivo_log.name}\n")

    total_etapas = len(etapas)
    try:
        with tqdm(total=len(etapas), desc="Progresso COLMAP", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)

                # Log do comando gerado para fins de depuração
                logging.info(f"--- EXECUTANDO: {comando} ---")

                # Atualiza a interface gráfica com a porcentagem exata da nova etapa
                if progress_callback:
                    progresso_calculado = (indice - 1) / total_etapas
                    progress_callback(progresso_calculado, f"Etapa {indice}/{total_etapas}: {descricao}")

                inicio_etapa = time.time()
                run_command(comando, progress_callback, f"Etapa {indice}/{total_etapas}: {descricao}")
                tempo_decorrido = time.time() - inicio_etapa

                tqdm.write(f"[TIMER] '{descricao}' concluída em {tempo_decorrido:.2f} segundos.")
                logging.info(f"--- TEMPO '{descricao}': {tempo_decorrido:.2f}s ---")

                # Verificação crítica após o Mapper
                if indice == 3 and not (pasta_esparsa / "0").exists():
                    raise Exception("Modelo esparso não gerado. Verifique a qualidade das fotos ou a calibração.")

                barra.update(1)

        if progress_callback:
            progress_callback(1.0, "Reconstrução finalizada com sucesso!")
        print("\n[SUCESSO] Reconstrução finalizada com sucesso!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline falhou: {erro}")
        print(f"[INFO] Verifique o arquivo {arquivo_log.name} para mais detalhes.")
        logging.error(f"Erro fatal no pipeline mono: {erro}")
        return False
