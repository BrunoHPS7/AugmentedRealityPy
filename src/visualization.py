import pyvista as pv
import os
import subprocess
import platform


def selecionar_arquivo_linux():
    # Detecta a pasta onde o visualization.py está (src) e sobe um nível para a raiz
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_project = os.path.dirname(script_dir)
    diretorio_reconstructions = os.path.join(root_project, "data", "out", "reconstructions")

    # Garante que a pasta existe antes de abrir o Zenity
    if not os.path.exists(diretorio_reconstructions):
        os.makedirs(diretorio_reconstructions, exist_ok=True)

    try:
        comando = [
            "zenity", "--file-selection",
            "--title=Selecione o Modelo (Pasta arroz_3d)",
            f"--filename={diretorio_reconstructions}/",  # A barra final força abrir DENTRO da pasta
            "--file-filter=Modelos 3D (obj, ply) | *.obj *.ply"
        ]
        caminho = subprocess.check_output(comando, stderr=subprocess.DEVNULL).decode("utf-8").strip()
        return caminho
    except subprocess.CalledProcessError:
        return None


def run_3d_visualization(model_path=None):
    if not model_path:
        if platform.system() == "Linux":
            model_path = selecionar_arquivo_linux()
        else:
            # Fallback Tkinter para outros sistemas
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk();
            root.withdraw()
            model_path = filedialog.askopenfilename(title="Selecionar Modelo")
            root.destroy()

    if not model_path or not os.path.exists(model_path):
        print("Ação cancelada ou arquivo não encontrado.")
        return

    try:
        print(f"Lendo: {model_path}")
        mesh = pv.read(model_path)
        plotter = pv.Plotter(title=f"Visualizador - {os.path.basename(model_path)}")
        plotter.set_background("black")

        # COLMAP PLY costuma ter cores nos vértices, rgb=True habilita isso
        plotter.add_mesh(mesh, rgb=True, point_size=2)
        plotter.add_axes()
        plotter.show()
    except Exception as e:
        print(f"Erro ao renderizar: {e}")


if __name__ == "__main__":
    run_3d_visualization()