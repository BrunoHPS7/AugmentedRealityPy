import subprocess
import logging
import time
from pathlib import Path
from tqdm import tqdm
from typing import Dict, Any, Optional
import json


class ConstrutorColmap:
    """Construtor dinâmico para chamadas CLI do COLMAP."""

    def __init__(self, binario_base: str = "colmap"):
        self.binario = binario_base

    def montar(self, modulo: str, parametros: Dict[str, Any]) -> str:
        """
        Monta o comando shell final.
        Valores booleanos (True/False) são convertidos para 1/0 (padrão COLMAP).
        Objetos Path são resolvidos e envelopados em aspas duplas.
        """
        comando = [f"{self.binario} {modulo}"]

        for chave, valor in parametros.items():
            if valor is None:
                continue

            # Tratamento da formatação da flag (ex: camera_model -> --camera_model)
            flag = f"--{chave}"

            # Tratamento do valor
            if isinstance(valor, bool):
                str_valor = "1" if valor else "0"
            elif isinstance(valor, Path):
                # Resolve o caminho absoluto e protege contra espaços
                str_valor = f'"{valor.resolve()}"'
            else:
                str_valor = str(valor)

            comando.append(f"{flag} {str_valor}")

        return " ".join(comando)


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


def executar_pipeline_reconstrucao_3d(pasta_frames: Path, pasta_projeto_saida: Path) -> bool:
    """Pipeline COLMAP em 7 etapas com suporte automático para Mono e Stereo via pastas."""

    # Configurações globais que podem ser mescladas nos dicionários de parâmetros depois
    CONFIG = {"threads": -1, "use_gpu": 1, "max_img_size": 4000}

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = configurar_logging(pasta_projeto_saida)

    # Definição de caminhos usando Path puro
    db_path = pasta_projeto_saida / "database.db"
    pasta_esparsa = pasta_projeto_saida / "sparse"
    pasta_densa = pasta_projeto_saida / "dense"

    pasta_esparsa.mkdir(exist_ok=True)
    pasta_densa.mkdir(exist_ok=True)

    construtor = ConstrutorColmap()

    # --- DEFINIÇÃO DAS ETAPAS DO PIPELINE USANDO O CONSTRUTOR ---
    etapas = [
        # Etapa 1: Feature Extractor
        (construtor.montar("feature_extractor", {
            "database_path": db_path,
            "image_path": pasta_frames
        }), "Extração de Features"),

        # Etapa 2: Matcher
        (construtor.montar("sequential_matcher", {
            "database_path": db_path
        }), "Matcher Sequencial"),

        # Etapa 3: Mapper
        (construtor.montar("mapper", {
            "database_path": db_path,
            "image_path": pasta_frames,
            "output_path": pasta_esparsa
        }), "Reconstrução Esparsa"),

        # Etapa 4: Undistorter
        (construtor.montar("image_undistorter", {
            "image_path": pasta_frames,
            "input_path": pasta_esparsa / "0",
            "output_path": pasta_densa,
            "output_type": "COLMAP"
        }), "Retificação de Imagens"),

        # Etapa 5: Patch Match
        (construtor.montar("patch_match_stereo", {
            "workspace_path": pasta_densa
        }), "Estéreo Patch Match"),

        # Etapa 6: Fusion
        (construtor.montar("stereo_fusion", {
            "workspace_path": pasta_densa,
            "output_path": pasta_densa / "modelo_fusionado.ply"
        }), "Fusão (Point Cloud)"),

        # Etapa 7: Poisson Mesher
        (construtor.montar("poisson_mesher", {
            "input_path": pasta_densa / "modelo_fusionado.ply",
            "output_path": pasta_densa / "malha_final.ply"
        }), "Geração de Malha (Poisson)")
    ]

    print(f"\n[RECONSTRUÇÃO] Iniciando pipeline para o projeto: {pasta_projeto_saida.name}")
    print(f"[LOG] Acompanhe os detalhes técnicos em: {arquivo_log.name}\n")

    try:
        with tqdm(total=len(etapas), desc="Progresso COLMAP", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)

                # Log do comando gerado para fins de depuração
                logging.info(f"--- EXECUTANDO: {comando} ---")

                inicio_etapa = time.time()
                executar_comando(comando)
                tempo_decorrido = time.time() - inicio_etapa

                tqdm.write(f"[TIMER] '{descricao}' concluída em {tempo_decorrido:.2f} segundos.")
                logging.info(f"--- TEMPO '{descricao}': {tempo_decorrido:.2f}s ---")

                # Verificação crítica após o Mapper
                if indice == 3 and not (pasta_esparsa / "0").exists():
                    raise Exception("Modelo esparso não gerado. Verifique a qualidade das fotos ou a calibração.")

                barra.update(1)

        print("\n[SUCESSO] Reconstrução finalizada com sucesso!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline falhou: {erro}")
        print(f"[INFO] Verifique o arquivo {arquivo_log.name} para mais detalhes.")
        return False


def gerar_configuracao_rig(caminho_arquivo_json: Path, baseline_metros: float):
    """
    Gera o JSON com os prefixos de pasta corrigidos e a sintaxe de Rig atualizada para o COLMAP.
    """
    config_rig = [
        {
            "cameras": [
                {
                    "image_prefix": "direita/",
                    "ref_sensor": True
                },
                {
                    "image_prefix": "esquerda/",
                    "cam_from_rig_translation": [float(baseline_metros), 0.0, 0.0],
                    "cam_from_rig_rotation": [1.0, 0.0, 0.0, 0.0]
                }
            ]
        }
    ]

    caminho_arquivo_json.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(config_rig, f, indent=4)

    return caminho_arquivo_json


def executar_pipeline_reconstrucao_3d_stereo(pasta_frames: Path, pasta_projeto_saida: Path,
                                             baseline_metros: float) -> bool:
    """Pipeline COLMAP Estéreo atualizado para versões novas (substitui rig_bundle_adjuster)."""

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = configurar_logging(pasta_projeto_saida)

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

    construtor = ConstrutorColmap()

    # Gera o arquivo JSON antes da execução
    gerar_configuracao_rig(arquivo_rig, baseline_metros)

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

    try:
        with tqdm(total=len(etapas), desc="Progresso Estéreo", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)
                logging.info(f"--- EXECUTANDO: {comando} ---")

                inicio_etapa = time.time()
                executar_comando(comando)
                tempo_decorrido = time.time() - inicio_etapa

                tqdm.write(f"[TIMER] '{descricao}' concluída em {tempo_decorrido:.2f} segundos.")
                logging.info(f"--- TEMPO '{descricao}': {tempo_decorrido:.2f}s ---")

                # Verificações de segurança ajustadas aos novos índices
                if "Reconstrução Esparsa" in descricao and not (pasta_esparsa / "0").exists():
                    raise Exception("Falha no Mapper: Câmeras não conectaram.")

                if "Ajuste de Bundle" in descricao and not (pasta_esparsa_rig_final / "cameras.bin").exists():
                    raise Exception("Falha na otimização do Rig: Modelo final não gerado.")

                barra.update(1)

        print("\n[SUCESSO] Reconstrução Estéreo finalizada na escala real!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline estéreo falhou: {erro}")
        return False