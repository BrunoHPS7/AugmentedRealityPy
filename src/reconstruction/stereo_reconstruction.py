import time
from tqdm import tqdm
from src.reconstruction.reconstruction_utils import *



def run_stereo_reconstruction(pasta_frames: Path, pasta_projeto_saida: Path, baseline_metros: float, progress_callback=None) -> bool:
    """Pipeline COLMAP Estéreo atualizado para versões novas (substitui rig_bundle_adjuster) com suporte a feedback na UI."""

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = setup_logger(pasta_projeto_saida)

    # Definição de caminhos
    db_path = pasta_projeto_saida / "database.db"
    pasta_esparsa = pasta_projeto_saida / "sparse"

    # Caminhos específicos para o processo de RIG
    pasta_esparsa_rigged_init = pasta_esparsa / "0_rigged"
    pasta_esparsa_rig_final = pasta_esparsa / "rig"

    pasta_densa = pasta_projeto_saida / "dense"
    arquivo_rig = pasta_projeto_saida / "rig_config.json"

    pasta_esparsa.mkdir(exist_ok=True)
    pasta_esparsa_rigged_init.mkdir(exist_ok=True)
    pasta_esparsa_rig_final.mkdir(exist_ok=True)
    pasta_densa.mkdir(exist_ok=True)

    construtor = ColmapCommandBuilder()

    # Gera o arquivo JSON antes da execução
    setup_rig(arquivo_rig, baseline_metros)

    # --- DEFINIÇÃO DAS ETAPAS ATUALIZADAS ---
    etapas = [

        # Etapa 1: Feature Extractor
        (construtor.montar("feature_extractor", {
            "database_path": db_path,
            "image_path": pasta_frames,
            "ImageReader.single_camera_per_folder": True,
            "ImageReader.camera_model": "OPENCV"
        }), "Extração de Features (Estéreo)"),

        # Etapa 2: Matcher
        (construtor.montar("sequential_matcher", {
            "database_path": db_path
        }), "Matcher Sequencial"),

        # Etapa 3: Mapper
        (construtor.montar("mapper", {
            "database_path": db_path,
            "image_path": pasta_frames,
            "output_path": pasta_esparsa
        }), "Reconstrução Esparsa (Inicial)"),

        # Etapa 4a: Rig Configurator (NOVO: Vincula o JSON ao modelo esparso)
        (construtor.montar("rig_configurator", {
            "database_path": db_path,
            "input_path": pasta_esparsa / "0",
            "rig_config_path": arquivo_rig,
            "output_path": pasta_esparsa_rigged_init
        }), "Configuração do Rig"),

        # Etapa 4b: Bundle Adjuster (NOVO: Otimiza o rig em escala real)
        (construtor.montar("bundle_adjuster", {
            "input_path": pasta_esparsa_rigged_init,
            "output_path": pasta_esparsa_rig_final,
            "BundleAdjustment.refine_rig_from_world": False,
            "BundleAdjustment.refine_sensor_from_rig": False
        }), "Ajuste de Bundle (Escala Real)"),

        # Etapa 5: Undistorter (Usa o modelo final do Rig)
        (construtor.montar("image_undistorter", {
            "image_path": pasta_frames,
            "input_path": pasta_esparsa_rig_final,
            "output_path": pasta_densa,
            "output_type": "COLMAP"
        }), "Retificação de Imagens"),

        # Etapa 6: Patch Match
        (construtor.montar("patch_match_stereo", {
            "workspace_path": pasta_densa
        }), "Estéreo Patch Match"),

        # Etapa 7: Fusion
        (construtor.montar("stereo_fusion", {
            "workspace_path": pasta_densa,
            "output_path": pasta_densa / "modelo_fusionado.ply"
        }), "Fusão (Point Cloud)"),

        # Etapa 8: Poisson Mesher
        (construtor.montar("poisson_mesher", {
            "input_path": pasta_densa / "modelo_fusionado.ply",
            "output_path": pasta_densa / "malha_final.ply"
        }), "Geração de Malha (Poisson)")
    ]

    print(f"\n[RECONSTRUÇÃO ESTÉREO] Iniciando pipeline para: {pasta_projeto_saida.name}")
    print(f"[INFO] Baseline: {baseline_metros}m")

    total_etapas = len(etapas)
    try:
        with tqdm(total=len(etapas), desc="Progresso Estéreo", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)
                logging.info(f"--- EXECUTANDO: {comando} ---")

                if progress_callback:
                    progresso_calculado = (indice - 1) / total_etapas
                    progress_callback(progresso_calculado, f"Etapa {indice}/{total_etapas}: {descricao}")

                inicio_etapa = time.time()
                run_command(comando, progress_callback, f"Etapa {indice}/{total_etapas}: {descricao}")
                tempo_decorrido = time.time() - inicio_etapa

                tqdm.write(f"[TIMER] '{descricao}' concluída em {tempo_decorrido:.2f} segundos.")
                logging.info(f"--- TEMPO '{descricao}': {tempo_decorrido:.2f}s ---")

                # Verificações de segurança ajustadas aos novos índices
                if "Reconstrução Esparsa" in descricao and not (pasta_esparsa / "0").exists():
                    raise Exception("Falha no Mapper: Câmeras não conectaram.")

                if "Ajuste de Bundle" in descricao and not (pasta_esparsa_rig_final / "cameras.bin").exists():
                    raise Exception("Falha na otimização do Rig: Modelo final não gerado.")

                barra.update(1)

        if progress_callback:
            progress_callback(1.0, "Reconstrução Estéreo concluída!")
        print("\n[SUCESSO] Reconstrução Estéreo finalizada na escala real!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline estéreo falhou: {erro}")
        logging.error(f"Erro fatal no pipeline estéreo: {erro}")
        return False