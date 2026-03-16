import os
import sys
import yaml
import platform
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Dict, Any, Optional

# Módulos internos para execução do pipeline de Visão Computacional
from src.camera_calibration import executar_calibracao_mono, executar_calibracao_stereo
from src.acquisition import extrair_e_salvar_frames_por_segundo
from src.reconstruction import executar_pipeline_reconstrucao_3d
from src.visualization import renderizar_visualizacao_3d


# --- UTILITÁRIOS DE INTERFACE E SISTEMA ---

def inicializar_tkinter_oculto():
    """Inicializa o motor gráfico do Tkinter em segundo plano para diálogos nativos."""
    raiz = tk.Tk()
    raiz.withdraw()
    raiz.attributes('-topmost', True)
    return raiz


def pedir_diretorio(titulo: str, caminho_inicial: Path) -> Optional[Path]:
    """Exibe seletor de pastas com tratamento de caminhos absolutos e fallback."""
    raiz = inicializar_tkinter_oculto()
    caminho_abs = caminho_inicial.resolve()

    diretorio_busca = str(caminho_abs) if caminho_abs.exists() else os.getcwd()

    escolha = filedialog.askdirectory(initialdir=diretorio_busca, title=titulo)
    raiz.destroy()
    return Path(escolha) if escolha else None


def pedir_arquivo(titulo: str, caminho_inicial: Path, tipos: list = None) -> Optional[Path]:
    """Exibe seletor de arquivos com filtros de extensão específicos."""
    raiz = inicializar_tkinter_oculto()
    caminho_abs = caminho_inicial.resolve()

    diretorio_busca = str(caminho_abs) if caminho_abs.exists() else os.getcwd()

    if not tipos:
        tipos = [("Vídeos", "*.mp4 *.avi *.mkv *.mov"), ("Todos os Arquivos", "*.*")]

    escolha = filedialog.askopenfilename(initialdir=diretorio_busca, title=titulo, filetypes=tipos)
    raiz.destroy()
    return Path(escolha) if escolha else None


def carregar_yaml(caminho: Path = Path("config.yaml")) -> Dict[str, Any]:
    """Faz o parsing do arquivo de configuração para definição de parâmetros globais."""
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de configuração '{caminho}' não encontrado.")
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def abrir_pasta_os(caminho: Path):
    """Garante a abertura do gerenciador de arquivos nativo de acordo com o SO."""
    caminho.mkdir(parents=True, exist_ok=True)
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(caminho)
        elif sistema == "Darwin":
            subprocess.run(["open", str(caminho)])
        else:
            subprocess.run(["xdg-open", str(caminho)], check=True)
    except Exception as e:
        print(f"[ERRO] Falha ao acessar diretório: {e}")


# --- PROCESSADORES DE ETAPAS (PIPELINE) ---

def processar_calibracao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 1: Determinação dos parâmetros intrínsecos e métricos da câmera."""
    print("\n--- MODO: CALIBRAÇÃO DE CÂMERA ---")

    print("[1] Mono (Câmera Única)")
    print("[2] Stereo (Par de Câmeras)")
    tipo = input("\nEscolha o tipo de calibração: ").strip()

    if tipo not in ["1", "2"]:
        print("[ERRO] Opção inválida.")
        return False

    pasta_base_fotos = Path(cfg["paths"]["calibration_images"])
    pasta_saida = Path(cfg["paths"]["calibration_output_folder"])

    nome_projeto = input("Digite o nome para este projeto de calibração: ").strip()
    if not nome_projeto: return False

    try:
        # A escala métrica do modelo 3D depende desta entrada manual (Metrologia)
        tamanho_quadrado = float(input("Meça e digite o lado de um quadrado do tabuleiro (em mm): ").replace(",", "."))
    except ValueError:
        print("[ERRO] Entrada numérica inválida.")
        return False

    dimensoes = tuple(cfg["parameters"]["calibration"]["checkerboard_size"])

    if tipo == "1":
        pasta_fotos = pedir_diretorio("Selecione a pasta com as fotos do tabuleiro", pasta_base_fotos)
        if not pasta_fotos: return False
        return executar_calibracao_mono(pasta_fotos, pasta_saida, dimensoes, tamanho_quadrado, nome_projeto)

    else:
        print("\n[STEREO] Selecione a pasta da Câmera A (Esquerda/Referência)")
        pasta_A = pedir_diretorio("Selecionar Câmera A", pasta_base_fotos)
        if not pasta_A: return False

        print("\n[STEREO] Selecione a pasta da Câmera B (Direita)")
        pasta_B = pedir_diretorio("Selecionar Câmera B", pasta_base_fotos)
        if not pasta_B: return False

        return executar_calibracao_stereo(pasta_A, pasta_B, pasta_saida, dimensoes, tamanho_quadrado, nome_projeto)


def processar_extracao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 2: Decomposição temporal de vídeo em frames sequenciais."""
    print("\n--- MODO: EXTRAÇÃO DE FRAMES (OpenCV) ---")

    pasta_entrada = Path(cfg["paths"]["video_input"])
    caminho_video = pedir_arquivo("Selecione o Vídeo", pasta_entrada)
    if not caminho_video: return False

    nome_projeto = input("Nome da pasta do projeto (ex: objeto_01): ").strip()
    if not nome_projeto: return False

    pasta_saida = Path(cfg["paths"]["frames_output"]) / nome_projeto

    return extrair_e_salvar_frames_por_segundo(
        caminho_video, pasta_saida, cfg["parameters"]["acquisition"]["desired_fps"]
    )


def processar_reconstrucao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 3: Pipeline Structure-from-Motion (SfM) via COLMAP."""
    print("\n--- MODO: RECONSTRUÇÃO 3D (COLMAP) ---")

    pasta_base_frames = Path(cfg["paths"]["frames_output"])
    pasta_frames = pedir_diretorio("Selecione a pasta de frames", pasta_base_frames)
    if not pasta_frames: return False

    pasta_base_calib = Path(cfg["paths"]["calibration_output_folder"])
    caminho_calib = pedir_diretorio("Selecione a PASTA de calibração (Mono ou Stereo)", pasta_base_calib)

    nome_reconstrucao = input("Nome para esta reconstrução (ex: modelo_final): ").strip()
    if not nome_reconstrucao: return False

    pasta_saida = Path(cfg["paths"]["colmap_output"]) / nome_reconstrucao
    if pasta_saida.exists():
        print("[ERRO] Nome já existente no diretório de saída.")
        return False

    return executar_pipeline_reconstrucao_3d(pasta_frames, pasta_saida, caminho_calib)


def processar_visualizacao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 4: Renderização e inspeção visual da malha 3D."""
    print("\n--- MODO: VISUALIZAÇÃO 3D ---")
    pasta_base = Path(cfg["paths"]["colmap_output"])

    caminho_modelo = pedir_arquivo("Selecione o Modelo 3D", pasta_base, [("Modelos 3D", "*.ply *.obj")])
    if not caminho_modelo: return False

    renderizar_visualizacao_3d(caminho_modelo)
    return True


# --- ENTRY POINT ---

if __name__ == "__main__":
    try:
        config = carregar_yaml()
        modo = config.get("execution_mode", "OpenCV")

        print("\n" + "=" * 45)
        print(f" SISTEMA DE RECONSTRUÇÃO 3D - UFOP/ICEA")
        print(f" SO: {platform.system()} | Modo Ativo: {modo}")
        print("=" * 45)

        mapeamento_modos = {
            "CameraCalibration": processar_calibracao,
            "OpenCV": processar_extracao,
            "Reconstruction": processar_reconstrucao,
            "Visualization": processar_visualizacao,
        }

        if modo in mapeamento_modos:
            if mapeamento_modos[modo](config):
                print("\n[SUCESSO] Operação concluída.")
        elif modo == "History":
            abrir_pasta_os(Path(config["paths"]["colmap_output"]))
        else:
            print(f"\n[AVISO] Modo '{modo}' não reconhecido.")

    except KeyboardInterrupt:
        print("\n\n[SISTEMA] Processo interrompido.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FALHA CRÍTICA] Erro: {e}")