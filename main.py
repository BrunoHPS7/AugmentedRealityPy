import os
import sys
import yaml
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Módulos internos para execução do pipeline de Visão Computacional
from src.camera_calibration import executar_calibracao_mono, executar_calibracao_stereo
from src.acquisition import extrair_e_salvar_frames_por_segundo
from src.acquisition import normalize_images_clahe
from src.reconstruction import executar_pipeline_reconstrucao_3d, executar_pipeline_reconstrucao_3d_stereo
from src.visualization import renderizar_visualizacao_3d

# Tratamento do Tkinter para o CLI:
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Mock para evitar NameError no código
    tk = Any
    filedialog = Any
    print("[SISTEMA] Tkinter não detectado. Modo gráfico desativado automaticamente.")


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


def processar_calibracao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 1: Determinação dos parâmetros intrínsecos e métricos da câmera."""
    print("\n--- MODO: CALIBRAÇÃO DE CÂMERA ---")

    print("[1] Mono (Câmera Única)")
    print("[2] Stereo (Par de Câmeras)")
    tipo = input("\nEscolha o tipo de calibração: ").strip()

    if tipo not in ["1", "2"]:
        print("[ERRO] Opção inválida.")
        return False

    # Verificar modo de interação:
    is_remote = cfg.get("remote_mode", False)

    if is_remote:
        pasta_saida = Path(cfg["paths"]["calibration_output_folder_remote"])
    else:
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
        if is_remote:
            pasta_fotos = Path(cfg["paths"]["calibration_images_remote"])
            if not pasta_fotos: return False
            return executar_calibracao_mono(pasta_fotos, pasta_saida, dimensoes, tamanho_quadrado, nome_projeto)
        else:
            pasta_fotos = pedir_diretorio("Selecione a pasta com as fotos do tabuleiro", pasta_base_fotos)
            if not pasta_fotos: return False
            return executar_calibracao_mono(pasta_fotos, pasta_saida, dimensoes, tamanho_quadrado, nome_projeto)

    else:
        if is_remote:
            print("\nCarregando diretórios remotos:")
            pasta_A = Path(cfg["paths"]["calibration_images_remote_a"])
            pasta_B = Path(cfg["paths"]["calibration_images_remote_b"])
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

    # Verificar modo de interação:
    is_remote = cfg.get("remote_mode", False)

    if is_remote:
        print("[REMOTE] Pulando interface... usando caminhos do YAML.")
        caminho_video  = Path(cfg["paths"]["video_input_remote"])
        if not caminho_video: return False
    else:
        print("[LOCAL] Abrindo seletor de arquivos...")
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

    modo_reconstrucao = cfg.get("reconstruction_mode", "mono").lower()
    is_remote = cfg.get("remote_mode", False)

    # --- DEFINIÇÃO DOS CAMINHOS DE ORIGEM ---
    if modo_reconstrucao == "stereo":
        # Busca no YAML a nova pasta separada para estéreo
        caminho_local = cfg["paths"].get("colmap_input_stereo", "data/out/frames/stereo")
        # Se for remoto, tenta pegar a chave remota estéreo, senão usa a local como fallback
        caminho_remoto = cfg["paths"].get("colmap_input_remote_stereo", caminho_local)
    else:
        # Busca no YAML a pasta para mono
        caminho_local = cfg["paths"].get("colmap_input", "data/out/frames/mono")
        caminho_remoto = cfg["paths"].get("colmap_input_remote", caminho_local)

    # --- SELEÇÃO DO PROJETO ---
    if is_remote:
        pasta_frames = Path(caminho_remoto)
    else:
        pasta_base_frames = Path(caminho_local)

        # O texto do prompt muda para orientar o usuário
        if modo_reconstrucao == "stereo":
            titulo_janela = "Selecione o Projeto Estéreo (Contém subpastas)"
        else:
            titulo_janela = "Selecione o Projeto Mono (Contém frames)"

        pasta_frames = pedir_diretorio(titulo_janela, pasta_base_frames)

    if not pasta_frames or not pasta_frames.exists():
        print("[ERRO] Pasta do projeto inválida ou não encontrada.")
        return False

    # Sugere o nome do próprio projeto como nome da reconstrução
    nome_reconstrucao = input(f"Nome para esta reconstrução (Padrão: {pasta_frames.name}): ").strip()
    if not nome_reconstrucao:
        nome_reconstrucao = pasta_frames.name

    pasta_saida = Path(cfg["paths"]["colmap_output"]) / nome_reconstrucao
    if pasta_saida.exists():
        print("[ERRO] Nome já existente no diretório de saída.")
        return False

    # --- ROTEAMENTO E EXECUÇÃO ---
    if modo_reconstrucao == "stereo":
        print("\n[INFO] Roteamento: Pipeline Estéreo selecionada.")
        try:
            baseline = float(
                input("Digite a distância (baseline) entre as câmeras em metros (ex: 0.15): ").replace(",", "."))
        except ValueError:
            print("[ERRO] Entrada numérica inválida para o baseline.")
            return False

        return executar_pipeline_reconstrucao_3d_stereo(pasta_frames, pasta_saida, baseline)

    else:
        print("\n[INFO] Roteamento: Pipeline Mono selecionada.")
        return executar_pipeline_reconstrucao_3d(pasta_frames, pasta_saida)


def processar_visualizacao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 4: Renderização e inspeção visual da malha 3D."""
    print("\n--- MODO: VISUALIZAÇÃO 3D ---")
    pasta_base = Path(cfg["paths"]["colmap_output"])

    caminho_modelo = pedir_arquivo("Selecione o Modelo 3D", pasta_base, [("Modelos 3D", "*.ply *.obj")])
    if not caminho_modelo: return False

    renderizar_visualizacao_3d(caminho_modelo)
    return True


def processar_normalizacao(cfg: Dict[str, Any]) -> bool:
    """ETAPA 5: Normalização de contraste via CLAHE."""
    print("\n--- MODO: NORMALIZAÇÃO DE IMAGENS (CLAHE) ---")

    # 1. Define onde estão as pastas de frames e onde ficarão as normalizadas
    pasta_base_frames = Path(cfg["paths"]["frames_input_normalização"])
    pasta_base_saida = Path(cfg["paths"]["frames_output_normalização"])

    # 2. Pergunta ao usuário qual projeto ele quer normalizar
    print(f"[INFO] Procurando projetos em: {pasta_base_frames}")

    # Se quiser usar a interface gráfica que você já tem:
    pasta_projeto = pedir_diretorio("Selecione a pasta do projeto para normalizar", pasta_base_frames)

    if not pasta_projeto:
        return False

    # 3. Define o nome de saída como "nome_do_projeto_normalizado"
    nome_projeto = pasta_projeto.name
    pasta_saida = pasta_base_saida / f"{nome_projeto}_normalizado"

    print(f"\n[PROCESSO] Origem: {pasta_projeto}")
    print(f"[PROCESSO] Destino: {pasta_saida}")

    # 4. Chama a função técnica de processamento
    return normalize_images_clahe(pasta_projeto, pasta_saida)


if __name__ == "__main__":
    try:
        config = carregar_yaml()
        modo = config.get("execution_mode", "OpenCV")

        print("\n" + "=" * 45)
        print(f" SISTEMA DE RECONSTRUÇÃO 3D - UFOP/ICEA")
        print(f" SO: {platform.system()} | Modo Ativo: {modo}")
        print("=" * 45)

        # Mapeamento atualizado incluindo o novo modo
        mapeamento_modos = {
            "CameraCalibration": processar_calibracao,
            "OpenCV":            processar_extracao,
            "Normalize":         processar_normalizacao,
            "Reconstruction":    processar_reconstrucao,
            "Visualization":     processar_visualizacao,
        }

        if modo in mapeamento_modos:
            if mapeamento_modos[modo](config):
                print("\n[SUCESSO] Operação concluída.")
            else:
                print("\n[FALHA] A operação retornou um erro.")
        elif modo == "History":
            abrir_pasta_os(Path(config["paths"]["colmap_output"]))
        else:
            print(f"\n[AVISO] Modo '{modo}' não reconhecido.")

    except KeyboardInterrupt:
        print("\n\n[SISTEMA] Processo interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FALHA CRÍTICA] Erro: {e}")