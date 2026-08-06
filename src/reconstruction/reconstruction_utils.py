import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
import json



class ColmapCommandBuilder:
    """Construtor dinâmico para chamadas CLI do COLMAP."""

    def __init__(self, binario_base: str = "colmap"):
        self.binario = binario_base


    def build(self, modulo: str, parametros: Dict[str, Any]) -> str:
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


def setup_logger(caminho_projeto: Path) -> Path:
    arquivo_log = caminho_projeto / "fluxo_reconstrucao.log"

    for manipulador in logging.root.handlers[:]:
        logging.root.removeHandler(manipulador)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(arquivo_log, encoding='utf-8')]
    )
    return arquivo_log


def run_command(comando_shell: str, progress_callback=None, status_prefix: str = ""):
    """Executa um comando de sistema silenciosamente, guardando o output no log e repassando sub-etapas cruciais à UI."""
    processo = subprocess.Popen(
        comando_shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )

    for linha in iter(processo.stdout.readline, ""):
        conteudo = linha.strip()
        if conteudo:
            logging.info(conteudo)

            # Repassa sub-etapas cruciais e iterações pesadas em tempo real para a interface Flet
            if progress_callback and any(
                    k in conteudo for k in ["Registering", "Iter", "Bundle", "PatchMatch", "Fusion"]):
                resumo = conteudo if len(conteudo) < 60 else f"{conteudo[:57]}..."
                progress_callback(None, f"{status_prefix} ({resumo})")

    processo.wait()
    if processo.returncode != 0:
        raise subprocess.CalledProcessError(processo.returncode, comando_shell)


def setup_rig(caminho_arquivo_json: Path, baseline_metros: float):
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
