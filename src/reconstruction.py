import subprocess
import logging
from pathlib import Path
from tqdm import tqdm
from typing import Dict, Any, Optional


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
        (construtor.montar("exhaustive_matcher", {
            "database_path": db_path
        }), "Matcher Exaustivo"),

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

                executar_comando(comando)

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