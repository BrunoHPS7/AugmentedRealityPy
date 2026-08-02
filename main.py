import flet as ft
import yaml
from pathlib import Path
from typing import Dict, Any
import platform
import subprocess
import os

from src.camera_calibration import run_mono_calibration, run_stereo_calibration
from src.acquisition.extract_frames import extract_frames_from_video
from src.post_processing import run_clahe_enhancement, run_resize_images
from src.reconstruction import executar_pipeline_reconstrucao_mono, executar_pipeline_reconstrucao_3d_stereo
from src.visualization.visualization import render_3d_model


def load_config(config_path: Path = Path("config.yaml")) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main(page: ft.Page):
    # --- CONFIGURAÇÕES DA JANELA E TEMA ---
    page.title = "AugmentedRealityPy - UFOP/ICEA"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1150
    page.window_height = 850
    page.window_center()
    page.padding = 0

    # Paleta de Cores Padronizada
    COLOR_PRIMARY = ft.colors.BLUE_700
    COLOR_ICON = ft.colors.BLUE_400
    COLOR_TEXT = ft.colors.WHITE
    COLOR_SUBTEXT = ft.colors.WHITE54

    try:
        cfg = load_config()
        paths = cfg.get("paths", {})
    except Exception as e:
        page.add(ft.Text(f"Erro Crítico ao ler config.yaml: {e}", color="red"))
        return

    # --- FEEDBACK GLOBAL ---
    global_progress = ft.ProgressBar(width=600, value=0.0, visible=False, color=COLOR_PRIMARY)
    global_status = ft.Text("", italic=True, color=COLOR_SUBTEXT)

    def show_toast(message: str, is_error: bool = False):
        color = ft.colors.RED_700 if is_error else ft.colors.GREEN_700
        page.show_snack_bar(
            ft.SnackBar(ft.Text(message, weight="bold"), bgcolor=color)
        )

    def update_progress(value: float):
        global_progress.value = value
        page.update()

    # ==========================================
    # FILE PICKERS E UTILITÁRIOS DE DIRETÓRIO
    # ==========================================
    selected_paths = {}

    def get_out_dir() -> str:
        out_path = Path("data/out").resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        return f"{out_path}{os.sep}"

    def create_dir_picker(key: str, text_element: ft.Text):
        def on_result(e):
            if e.path:
                selected_paths[key] = Path(e.path)
                text_element.value = f".../{selected_paths[key].name}"
                page.update()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        return picker

    def create_file_picker(key: str, text_element: ft.Text):
        def on_result(e):
            if e.files:
                selected_paths[key] = Path(e.files[0].path)
                text_element.value = f".../{selected_paths[key].name}"
                page.update()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        return picker

    # ==========================================
    # TELA 1: CALIBRAÇÃO DE CÂMERA
    # ==========================================
    txt_calib_a = ft.Text("Nenhum diretório...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                          overflow=ft.TextOverflow.ELLIPSIS)
    txt_calib_b = ft.Text("Nenhum diretório...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                          overflow=ft.TextOverflow.ELLIPSIS)

    picker_calib_a = create_dir_picker("calib_a", txt_calib_a)
    picker_calib_b = create_dir_picker("calib_b", txt_calib_b)

    tf_calib_proj = ft.TextField(label="Nome do Projeto", expand=True)
    tf_calib_dim_x = ft.TextField(label="Quinas X (ex: 8)", value="8", expand=True)
    tf_calib_dim_y = ft.TextField(label="Quinas Y (ex: 6)", value="6", expand=True)
    tf_calib_square = ft.TextField(label="Quadrado (mm)", value="25.0", expand=True)

    def open_calib_a_picker(e):
        picker_calib_a.get_directory_path(initial_directory=f"{Path.home().resolve()}{os.sep}")

    def open_calib_b_picker(e):
        picker_calib_b.get_directory_path(initial_directory=f"{Path.home().resolve()}{os.sep}")

    btn_calib_b = ft.ElevatedButton("Selec. Câmera B", on_click=open_calib_b_picker, width=160)
    row_calib_b = ft.Row([btn_calib_b, txt_calib_b], visible=False)

    def toggle_calib_mode(e):
        row_calib_b.visible = (dd_calib_mode.value == "Stereo")
        page.update()

    dd_calib_mode = ft.Dropdown(
        label="Modo",
        options=[ft.dropdown.Option("Mono"), ft.dropdown.Option("Stereo")],
        value="Mono",
        width=150,
        on_change=toggle_calib_mode
    )

    def run_calibration_ui(e):
        try:
            dim_x, dim_y = int(tf_calib_dim_x.value), int(tf_calib_dim_y.value)
            sq_size = float(tf_calib_square.value.replace(",", "."))
        except ValueError:
            show_toast("Valores numéricos inválidos!", True)
            return

        proj_name = tf_calib_proj.value.strip()
        if not proj_name or not selected_paths.get("calib_a"):
            show_toast("Preencha o projeto e a Câmera A!", True)
            return

        out_dir = Path(paths.get("calibration_output_folder", "data/out/calibrations"))
        global_progress.visible = True
        global_status.value = "Calculando matrizes..."
        page.update()

        if dd_calib_mode.value == "Mono":
            success = run_mono_calibration(selected_paths["calib_a"], out_dir, (dim_x, dim_y), sq_size, proj_name,
                                           update_progress)
        else:
            if not selected_paths.get("calib_b"):
                show_toast("Selecione a Câmera B!", True)
                global_progress.visible = False
                page.update()
                return
            success = run_stereo_calibration(selected_paths["calib_a"], selected_paths["calib_b"], out_dir,
                                             (dim_x, dim_y), sq_size, proj_name, update_progress, update_progress)

        global_progress.visible, global_status.value = False, ""
        show_toast("✅ Calibração finalizada!" if success else "❌ Falha na calibração.", not success)
        page.update()

    form_calibration = ft.Column([
        ft.Row([dd_calib_mode, tf_calib_proj]),
        ft.Row([tf_calib_dim_x, tf_calib_dim_y, tf_calib_square]),
        ft.Row([ft.ElevatedButton("Selec. Câmera A", on_click=open_calib_a_picker, width=160), txt_calib_a]),
        row_calib_b,
        ft.Container(height=10),
        ft.ElevatedButton("Executar Calibração", on_click=run_calibration_ui, icon=ft.icons.PLAY_ARROW,
                          bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, height=45)
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_calibration = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.CAMERA, size=40, color=COLOR_ICON),
            ft.Text("Calibração de Câmera", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_calibration
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # TELA 2: EXTRAÇÃO DE FRAMES
    # ==========================================
    txt_video = ft.Text("Nenhum vídeo...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS)
    picker_video = create_file_picker("video", txt_video)

    tf_acq_proj = ft.TextField(label="Nome do Projeto (Pasta)", expand=True)
    tf_acq_fps = ft.TextField(label="FPS Desejado", value="5", width=150)

    def run_acquisition_ui(e):
        try:
            fps = int(tf_acq_fps.value)
        except ValueError:
            show_toast("O FPS deve ser um número inteiro!", True)
            return

        if not selected_paths.get("video") or not tf_acq_proj.value:
            show_toast("Selecione vídeo e projeto!", True)
            return

        out_dir = Path(paths.get("frames_output", "data/out/frames")) / tf_acq_proj.value.strip()
        global_progress.visible, global_status.value = True, "Extraindo frames..."
        page.update()

        success = extract_frames_from_video(selected_paths["video"], out_dir, fps, update_progress)
        global_progress.visible, global_status.value = False, ""
        show_toast("✅ Extração concluída!" if success else "❌ Falha na extração.", not success)
        page.update()

    form_acquisition = ft.Column([
        ft.Row([tf_acq_proj, tf_acq_fps]),
        ft.Row([ft.ElevatedButton("Selecionar Vídeo",
                                  on_click=lambda _: picker_video.pick_files(allowed_extensions=["mp4", "avi", "mov"],
                                                                             initial_directory=get_out_dir()),
                                  width=160), txt_video]),
        ft.Container(height=10),
        ft.ElevatedButton("Extrair Frames", on_click=run_acquisition_ui, icon=ft.icons.PLAY_ARROW,
                          bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, height=45)
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_acquisition = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.VIDEO_FILE, size=40, color=COLOR_ICON),
            ft.Text("Decomposição Temporal de Vídeo", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_acquisition
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # TELA 3: PRÉ-PROCESSAMENTO (RESIZE E CLAHE)
    # ==========================================
    txt_norm_in = ft.Text("Nenhuma pasta...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                          overflow=ft.TextOverflow.ELLIPSIS)
    picker_norm_in = create_dir_picker("norm_in", txt_norm_in)

    chk_resize = ft.Checkbox(label="Redimensionar Imagens", value=True)
    tf_resize_w = ft.TextField(label="Largura Alvo", value="4000", expand=True)
    tf_resize_h = ft.TextField(label="Altura Alvo", value="3000", expand=True)

    chk_clahe = ft.Checkbox(label="Aplicar CLAHE", value=True)
    tf_norm_clip = ft.TextField(label="Clip Limit", value="2.0", expand=True)
    tf_norm_tile = ft.TextField(label="Tile Size", value="8", expand=True)

    def open_norm_picker(e):
        picker_norm_in.get_directory_path(initial_directory=get_out_dir())

    def run_normalization_ui(e):
        if not selected_paths.get("norm_in"):
            show_toast("Selecione a pasta base de entrada!", True)
            return

        try:
            clip = float(tf_norm_clip.value.replace(",", "."))
            tile = (int(tf_norm_tile.value), int(tf_norm_tile.value))
            t_w = int(tf_resize_w.value)
            t_h = int(tf_resize_h.value)
        except ValueError:
            show_toast("Valores inválidos nos campos!", True)
            return

        in_dir = selected_paths["norm_in"]
        base_out_dir = Path(paths.get("frames_output_normalização", "data/out/normalizados"))

        run_res = chk_resize.value
        run_cla = chk_clahe.value

        if not run_res and not run_cla:
            show_toast("Selecione pelo menos uma etapa (Resize ou CLAHE)!", True)
            return

        current_input_dir = in_dir
        success = True

        # Etapa 1: Redimensionamento
        if run_res:
            out_resize = base_out_dir / f"{in_dir.name}_resized"
            global_progress.visible, global_status.value = True, "1/2: Redimensionando imagens..."
            page.update()

            success = run_resize_images(current_input_dir, out_resize, target_size=(t_h, t_w),
                                        progress_callback=update_progress)

            if not success:
                show_toast("❌ Falha no Redimensionamento.", True)
                global_progress.visible, global_status.value = False, ""
                page.update()
                return

            current_input_dir = out_resize

            # Etapa 2: CLAHE
        if run_cla:
            folder_sufix = f"{in_dir.name}_resized_clahe" if run_res else f"{in_dir.name}_clahe"
            out_clahe = base_out_dir / folder_sufix

            step_text = "2/2: Aplicando CLAHE..." if run_res else "Aplicando CLAHE..."
            global_progress.visible, global_status.value = True, step_text
            page.update()

            success = run_clahe_enhancement(current_input_dir, out_clahe, clip_limit=clip, tile_size=tile,
                                            progress_callback=update_progress)

            if not success:
                show_toast("❌ Falha na aplicação do CLAHE.", True)
                global_progress.visible, global_status.value = False, ""
                page.update()
                return

        global_progress.visible, global_status.value = False, ""
        show_toast("✅ Processamento em lote concluído com sucesso!")
        page.update()

    form_normalization = ft.Column([
        ft.Row([ft.ElevatedButton("Selecionar Pasta", on_click=open_norm_picker, width=160), txt_norm_in]),
        ft.Divider(),
        chk_resize,
        ft.Row([tf_resize_w, tf_resize_h]),
        ft.Divider(),
        chk_clahe,
        ft.Row([tf_norm_clip, tf_norm_tile]),
        ft.Container(height=10),
        ft.ElevatedButton("Processar Imagens", on_click=run_normalization_ui, icon=ft.icons.PLAY_ARROW,
                          bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, height=45)
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_normalization = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.IMAGE_SEARCH, size=40, color=COLOR_ICON),
            ft.Text("Pré-Processamento (Resize e Contraste)", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_normalization
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # TELA 4: RECONSTRUÇÃO 3D
    # ==========================================
    txt_recon_in = ft.Text("Nenhuma pasta...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                           overflow=ft.TextOverflow.ELLIPSIS)
    picker_recon_in = create_dir_picker("recon_in", txt_recon_in)

    tf_recon_proj = ft.TextField(label="Nome Reconstrução", expand=True)
    tf_recon_base = ft.TextField(label="Baseline (m)", value="0.15", expand=True, visible=False)

    def toggle_recon_mode(e):
        tf_recon_base.visible = (dd_recon_mode.value == "Stereo")
        page.update()

    dd_recon_mode = ft.Dropdown(
        label="Modo", options=[ft.dropdown.Option("Mono"), ft.dropdown.Option("Stereo")],
        value="Mono", width=150, on_change=toggle_recon_mode
    )

    def open_recon_picker(e):
        picker_recon_in.get_directory_path(initial_directory=get_out_dir())

    def run_reconstruction_ui(e):
        proj_name = tf_recon_proj.value.strip()
        if not selected_paths.get("recon_in") or not proj_name:
            show_toast("Faltam dados!", True)
            return

        out_dir = Path(paths.get("colmap_output", "data/out/reconstructions")) / proj_name

        global_progress.visible = True
        global_progress.value = 0.0
        global_status.value = "Iniciando estruturas de dados..."
        page.update()

        def colmap_ui_callback(val: float, texto: str):
            if val is not None:
                global_progress.value = val
            global_status.value = texto
            page.update()

        if dd_recon_mode.value == "Mono":
            success = executar_pipeline_reconstrucao_mono(
                selected_paths["recon_in"], out_dir, progress_callback=colmap_ui_callback
            )
        else:
            try:
                base = float(tf_recon_base.value.replace(",", "."))
            except ValueError:
                show_toast("Baseline inválido!", True)
                global_progress.visible = False
                page.update()
                return
            success = executar_pipeline_reconstrucao_3d_stereo(
                selected_paths["recon_in"], out_dir, base, progress_callback=colmap_ui_callback
            )

        global_progress.visible = False
        global_progress.value = 0.0
        global_status.value = ""
        page.update()

        show_toast("✅ Reconstrução finalizada!" if success else "❌ Falha no pipeline do COLMAP.", not success)

    form_reconstruction = ft.Column([
        ft.Row([dd_recon_mode, tf_recon_proj, tf_recon_base]),
        ft.Row([ft.ElevatedButton("Selecionar Projeto", on_click=open_recon_picker, width=160), txt_recon_in]),
        ft.Container(height=10),
        ft.ElevatedButton("Iniciar SfM e Dense MVS", on_click=run_reconstruction_ui, icon=ft.icons.PLAY_ARROW,
                          bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, height=45)
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_reconstruction = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.DOMAIN, size=40, color=COLOR_ICON),
            ft.Text("Structure-from-Motion (COLMAP)", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_reconstruction
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # TELA 5: VISUALIZAÇÃO
    # ==========================================
    txt_model = ft.Text("Nenhum modelo...", color=COLOR_SUBTEXT, expand=True, no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS)
    picker_model = create_file_picker("model", txt_model)

    def run_visualization_ui(e):
        if not selected_paths.get("model"):
            show_toast("Selecione uma malha!", True)
            return
        show_toast("Iniciando renderizador PyVista...")
        render_3d_model(selected_paths["model"])

    form_visualization = ft.Column([
        ft.Row([ft.ElevatedButton("Selecionar Malha",
                                  on_click=lambda _: picker_model.pick_files(allowed_extensions=["ply", "obj"],
                                                                             initial_directory=get_out_dir()),
                                  width=160), txt_model]),
        ft.Container(height=10),
        ft.ElevatedButton("Renderizar Modelo", on_click=run_visualization_ui, icon=ft.icons.PLAY_CIRCLE_FILL,
                          bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, height=45)
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_visualization = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.VIEW_IN_AR, size=40, color=COLOR_ICON),
            ft.Text("Inspeção Volumétrica 3D", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_visualization
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # TELA 6: DADOS
    # ==========================================
    def open_folder(target_path: Path):
        target_path = target_path.resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        try:
            if platform.system() == "Windows":
                os.startfile(target_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", target_path])
            else:
                subprocess.run(["xdg-open", target_path])
            show_toast(f"Pasta aberta: {target_path.name}")
        except Exception as e:
            show_toast(f"Erro: {e}", True)

    form_files = ft.Column([
        ft.Text("Acesse rapidamente os diretórios onde os dados estão salvos.", color=COLOR_SUBTEXT,
                text_align=ft.TextAlign.CENTER),
        ft.Container(height=15),
        ft.ElevatedButton("Abrir Pasta Raiz (data/out)", icon=ft.icons.FOLDER_SPECIAL, bgcolor=COLOR_PRIMARY,
                          color=COLOR_TEXT, height=45, on_click=lambda _: open_folder(Path("data/out"))),
        ft.Container(height=15),
        ft.Text("Acesso Direto aos Subdiretórios:", weight="bold", text_align=ft.TextAlign.CENTER),
        ft.Row([
            ft.ElevatedButton("Calibrações", icon=ft.icons.CAMERA, on_click=lambda _: open_folder(
                Path(paths.get("calibration_output_folder", "data/out/calibrations"))), expand=True),
            ft.ElevatedButton("Frames", icon=ft.icons.IMAGE,
                              on_click=lambda _: open_folder(Path(paths.get("frames_output", "data/out/frames"))),
                              expand=True),
            ft.ElevatedButton("Reconstruções", icon=ft.icons.DOMAIN, on_click=lambda _: open_folder(
                Path(paths.get("colmap_output", "data/out/reconstructions"))), expand=True),
        ])
    ], width=550, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    view_files = ft.Container(
        alignment=ft.alignment.center, padding=25,
        content=ft.Column([
            ft.Icon(ft.icons.FOLDER_OPEN, size=40, color=COLOR_ICON),
            ft.Text("Gerenciamento de Arquivos", size=24, weight="bold", color=COLOR_TEXT),
            ft.Container(height=10),
            form_files
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # ==========================================
    # LAYOUT PRINCIPAL E NAVEGAÇÃO CUSTOMIZADA
    # ==========================================
    views = [view_calibration, view_acquisition, view_normalization, view_reconstruction, view_visualization,
             view_files]
    main_content_container = ft.Container(content=views[0], expand=True)

    # MUDANÇA AQUI: Trocado de "Pré-Proc." para "Pré-Processamento"
    menu_labels = ["Calibração", "Aquisição", "Pré-Processamento", "Reconstrução", "Visualização", "Dados"]
    menu_items = []

    def change_route(index: int):
        for i, item in enumerate(menu_items):
            if i == index:
                item.content.color = COLOR_TEXT
                item.content.weight = "bold"
                item.bgcolor = ft.colors.WHITE10
            else:
                item.content.color = COLOR_SUBTEXT
                item.content.weight = "normal"
                item.bgcolor = ft.colors.TRANSPARENT

        main_content_container.content = views[index]
        page.update()

    # Construção dos botões de texto clicáveis
    for idx, label in enumerate(menu_labels):
        def make_click_callback(i=idx):
            return lambda _: change_route(i)

        menu_items.append(
            ft.Container(
                content=ft.Text(label, size=15, color=COLOR_TEXT if idx == 0 else COLOR_SUBTEXT,
                                weight="bold" if idx == 0 else "normal"),
                padding=ft.padding.only(top=15, bottom=15, left=25, right=10),
                border_radius=0,
                bgcolor=ft.colors.WHITE10 if idx == 0 else ft.colors.TRANSPARENT,
                on_click=make_click_callback(),
                ink=True,
            )
        )

    # BARRA LATERAL: Largura ajustada de 210 para 230 para caber o texto longo confortavelmente
    nav_sidebar = ft.Container(
        content=ft.Column(
            menu_items,
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        ),
        width=230,
        padding=ft.padding.only(top=20, left=15, right=0),
    )

    header = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.LAYERS, color=COLOR_ICON, size=35),
                    ft.Text("AugmentedRealityPy", size=26, weight="bold", color=COLOR_TEXT),
                ], alignment=ft.MainAxisAlignment.START, tight=True),
                expand=True,
            ),
            ft.Text("UFOP / ICEA", size=14, weight="bold", color=COLOR_SUBTEXT)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=25, vertical=20),
        bgcolor=ft.colors.BLACK54,
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.WHITE10))
    )

    footer = ft.Container(
        content=ft.Column([global_progress, global_status], alignment=ft.MainAxisAlignment.CENTER,
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(20),
        alignment=ft.alignment.center
    )

    content_area = ft.Column(
        controls=[
            main_content_container,
            footer
        ],
        expand=True
    )

    body = ft.Row([nav_sidebar, ft.VerticalDivider(width=1, color=ft.colors.WHITE10), content_area], expand=True)
    page.add(header, body)


if __name__ == "__main__":
    ft.app(target=main)