from typing import Any # Importante para o mock
from pathlib import Path

try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except Exception:
    PYVISTA_AVAILABLE = False
    pv = None # Ou Any, apenas para o interpretador não dar NameError
    # Não precisa de print aqui para não sujar o CLI do SSH toda vez que importar


def renderizar_visualizacao_3d(caminho_modelo: Path):
    """Carrega e renderiza um modelo 3D (PLY ou OBJ) usando PyVista."""

    if not caminho_modelo or not caminho_modelo.exists():
        print(f"[ERRO] Arquivo não encontrado: {caminho_modelo}")
        return

    try:
        print(f"[VISUALIZAÇÃO] Carregando modelo: {caminho_modelo.name}...")

        geometria_3d = pv.read(str(caminho_modelo))

        visualizador = pv.Plotter(title=f"Análise Volumétrica - {caminho_modelo.name}")
        visualizador.set_background("black")

        visualizador.add_mesh(
            geometria_3d,
            rgb=True,
            point_size=2,
            render_points_as_spheres=True,
            label=caminho_modelo.name
        )

        visualizador.add_axes()
        visualizador.show_grid(color='gray', xtitle='X', ytitle='Y', ztitle='Z')

        print(f"[OK] Renderização iniciada.")
        visualizador.show()

    except Exception as erro:
        print(f"[ERRO CRÍTICO] Falha ao renderizar modelo 3D: {erro}")