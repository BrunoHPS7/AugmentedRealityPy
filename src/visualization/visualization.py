import pyvista as pv
from pathlib import Path


def run_show_mesh(model_path: Path) -> bool:
    """
    Carrega e renderiza um modelo 3D (PLY ou OBJ) resultante da etapa de reconstrução.
    Permite a inspeção visual interativa da nuvem de pontos ou malha texturizada.
    """
    if not model_path or not model_path.exists():
        print(f"[ERROR] Model file not found: {model_path}")
        return False

    try:
        print(f"[VISUALIZATION] Loading 3D model: {model_path.name}...")

        # 1. Leitura estrutural dos dados volumétricos na memória
        mesh_geometry = pv.read(str(model_path))

        # 2. Configuração do ambiente de renderização (Plotter)
        plotter = pv.Plotter(title=f"Volumetric Analysis - {model_path.name}")
        plotter.set_background("black")

        # 3. Inserção da geometria na cena
        plotter.add_mesh(
            mesh_geometry,
            rgb=True,  # Habilita cores reais/textura
            point_size=2,  # Espessura ideal para nuvens de pontos
            render_points_as_spheres=True,
            label=model_path.name
        )

        # 4. Adição de guias espaciais
        plotter.add_axes()
        plotter.show_grid(color='gray', xtitle='X', ytitle='Y', ztitle='Z')

        print(f"[SUCCESS] Rendering started.")

        # 5. EXIBIÇÃO ÚNICA E FINAL
        plotter.show(full_screen=True)

        return True

    except Exception as error:
        print(f"[CRITICAL ERROR] Failed to render 3D model: {error}")
        return False