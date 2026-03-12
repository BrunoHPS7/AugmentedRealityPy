import os
import sys
import yaml
import platform
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Dict, Any, Optional

# Módulos internos ordenados por fluxo lógico
from src.camera_calibration import executar_fluxo_calibracao_camera
from src.acquisition import extrair_e_salvar_frames_por_segundo
from src.reconstruction import executar_pipeline_reconstrucao_3d
from src.visualization import renderizar_visualizacao_3d


# --- UTILITÁRIOS DE INTERFACE ---

def inicializar_tkinter_oculto():
    """Inicializa uma instância do Tkinter sem exibir a janela principal."""
    raiz = tk.Tk()
    raiz.withdraw()
    # Em alguns ambientes Linux, o topmost pode travar o diálogo atrás da IDE
    # Se a janela não aparecer, comente a linha abaixo:
    raiz.attributes('-topmost', True)
    return raiz


def pedir_diretorio(titulo: str, caminho_inicial: Path) -> Optional[Path]:
    raiz = inicializar_tkinter_oculto()

    # Resolve para caminho absoluto
    caminho_abs = caminho_inicial.resolve()

    # Se a pasta do YAML não existir, avisa no terminal e usa o diretório atual
    if not caminho_abs.exists():
        print(f"[AVISO] Pasta não encontrada: {caminho_abs}")
        print(f"Verifique se o nome no config.yaml está idêntico ao da pasta no PyCharm.")
        diretorio_busca = os.getcwd()
    else:
        diretorio_busca = str(caminho_abs)

    escolha = filedialog.askdirectory(initialdir=diretorio_busca, title=titulo)
    raiz.destroy()
    return Path(escolha) if escolha else None


def pedir_arquivo(titulo: str, caminho_inicial: Path, tipos: list = None) -> Optional[Path]:
    raiz = inicializar_tkinter_oculto()

    caminho_abs = caminho_inicial.resolve()
    diretorio_busca = str(caminho_abs) if caminho_abs.exists() else os.getcwd()

    if not tipos:
        tipos = [("Vídeos", "*.mp4 *.avi *.mkv *.mov"), ("Todos os Arquivos", "*.*")]

    escolha = filedialog.askopenfilename(
        initialdir=diretorio_busca,
        title=titulo,
        filetypes=tipos
    )

    raiz.destroy()
    return Path(escolha) if escolha else None


def carregar_yaml(caminho: Path = Path("config.yaml")) -> Dict[str, Any]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de configuração '{caminho}' não encontrado.")
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def abrir_pasta_os(caminho: Path):
    caminho.mkdir(parents=True, exist_ok=True)
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(caminho)
        elif sistema == "Darwin":
            subprocess.run(["open", str(caminho)])
        else:
            # Comando padrão para a maioria das distros Linux
            subprocess.run(["xdg-open", str(caminho)], check=True)
    except Exception as e:
        print(f"[ERRO] Falha ao abrir pasta: {e}")


# --- PROCESSADORES (ORDEM LÓGICA DE EXECUÇÃO) ---

def processar_calibracao(cfg: Dict[str, Any]) -> bool:
    """1. Calibração: Gera os parâmetros intrínsecos da câmera."""
    print("\n--- MODO: CALIBRAÇÃO DE CÂMERA ---")

    pasta_base_fotos = Path(cfg["paths"]["calibration_images"])
    pasta_fotos = pedir_diretorio("Selecione a pasta com as fotos do tabuleiro", pasta_base_fotos)
    if not pasta_fotos: return False

    nome_arquivo = input("Digite um nome para o arquivo de saída (ex: camera_pro): ").strip()
    if not nome_arquivo: return False

    pasta_saida = Path(cfg["paths"]["calibration_output_folder"])
    caminho_final = pasta_saida / (nome_arquivo if nome_arquivo.endswith('.npz') else f"{nome_arquivo}.npz")

    if caminho_final.exists():
        if input(f"Arquivo '{caminho_final.name}' já existe. Sobrescrever? (s/n): ").lower() != 's':
            return False

    dimensoes = tuple(cfg["parameters"]["calibration"]["checkerboard_size"])
    tamanho_quadrado = float(cfg["parameters"]["calibration"]["square_size"])

    return executar_fluxo_calibracao_camera(pasta_fotos, pasta_saida, dimensoes, tamanho_quadrado, nome_arquivo)


def processar_extracao(cfg: Dict[str, Any]) -> bool:
    """2. Aquisição: Transforma vídeo em frames."""
    print("\n--- MODO: EXTRAÇÃO DE FRAMES (OpenCV) ---")

    # Garantir que a pasta de entrada exista no sistema de arquivos
    pasta_entrada = Path(cfg["paths"]["video_input"])

    caminho_video = pedir_arquivo("Selecione o Vídeo", pasta_entrada)
    if not caminho_video:
        print("[AVISO] Nenhum vídeo selecionado.")
        return False

    nome_projeto = input("Nome da pasta do projeto (ex: objeto_01): ").strip()
    if not nome_projeto: return False

    pasta_saida = Path(cfg["paths"]["frames_output"]) / nome_projeto
    if pasta_saida.exists():
        print("[AVISO] Pasta já existe. Os frames serão mesclados ou sobrescritos.")

    return extrair_e_salvar_frames_por_segundo(
        caminho_video, pasta_saida, cfg["parameters"]["acquisition"]["desired_fps"]
    )


def processar_reconstrucao(cfg: Dict[str, Any]) -> bool:
    """3. Reconstrução: Processa frames no COLMAP."""
    print("\n--- MODO: RECONSTRUÇÃO 3D (COLMAP) ---")
    pasta_base_frames = Path(cfg["paths"]["frames_output"])

    # 1. Seleciona os frames
    pasta_frames = pedir_diretorio("Selecione a pasta de frames", pasta_base_frames)
    if not pasta_frames: return False

    # 2. NOVO: Seleciona o arquivo de calibração .txt
    pasta_base_calib = Path(cfg["paths"]["calibration_output_folder"])
    caminho_calib = pedir_arquivo("Selecione a calibração (.txt)", pasta_base_calib,
                                  [("Arquivo de Calibração", "*.txt")])
    if not caminho_calib:
        print("[AVISO] Nenhuma calibração selecionada. O COLMAP tentará calibração automática.")
        # Você pode decidir se retorna False ou continua sem calibração manual

    nome_projeto = input("Nome para esta reconstrução (ex: modelo_final): ").strip()
    if not nome_projeto: return False

    pasta_saida = Path(cfg["paths"]["colmap_output"]) / nome_projeto
    if pasta_saida.exists():
        print("[ERRO] Este nome de reconstrução já foi usado.")
        return False

    # Passamos o caminho do txt para a pipeline
    return executar_pipeline_reconstrucao_3d(pasta_frames, pasta_saida, caminho_calib)


def processar_visualizacao(cfg: Dict[str, Any]) -> bool:
    """4. Visualização: Renderiza o resultado final (PLY/OBJ)."""
    print("\n--- MODO: VISUALIZAÇÃO 3D ---")
    pasta_base = Path(cfg["paths"]["colmap_output"])

    caminho_modelo = pedir_arquivo("Selecione o Modelo 3D", pasta_base, [("Modelos 3D", "*.ply *.obj")])
    if not caminho_modelo: return False

    renderizar_visualizacao_3d(caminho_modelo)
    return True


# --- FLUXO PRINCIPAL ---

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
            sucesso = mapeamento_modos[modo](config)
            if sucesso:
                print("\n[SUCESSO] Operação concluída.")
        elif modo == "History":
            abrir_pasta_os(Path(config["paths"]["colmap_output"]))
        else:
            print(f"\n[AVISO] Modo '{modo}' não reconhecido no config.yaml.")

    except KeyboardInterrupt:
        print("\n\n[SISTEMA] Interrompido pelo usuário. Saindo...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FALHA CRÍTICA] Ocorreu um erro inesperado: {e}")