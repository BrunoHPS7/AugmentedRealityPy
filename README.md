# AugmentedRealityPy

Uma plataforma modular e escalável em Python projetada para automatizar todo o pipeline de fotogrametria. O sistema permite transformar arquivos de vídeo e conjuntos de imagens em nuvens de pontos e malhas tridimensionais (3D), oferecendo tanto uma **Interface Gráfica (GUI em Flet)** quanto uma **Interface de Linha de Comando (CLI)**.

---

## 🌟 Principais Módulos

O software é estruturado em 5 módulos centrais de processamento:

1. **📷 Aquisição (`src/acquisition/`):** Extração e amostragem configurável de *frames* a partir de arquivos de vídeo.
2. **🎯 Calibração (`src/camera_calibration/`):** Estimativa e cálculo dos parâmetros intrínsecos e estéreo para correção de distorção de lentes.
3. **🔄 Pós-Processamento (`src/post_processing/`):** Pré-processamento de imagens em lote (redimensionamento e realce de contraste via CLAHE) para otimizar os dados de entrada.
4. **🏗️ Reconstrução 3D (`src/reconstruction/`):** Pipeline base do motor de reconstrução (**COLMAP**) suportando abordagens Monoculares e Estéreo.
5. **👁️ Visualização 3D (`src/visualization/`):** Inspeção interativa e renderização de nuvens de pontos e malhas 3D (formatos `.ply`, `.obj`).

---

## 📁 Estrutura do Projeto

```text
├── cli/                 # Interface de Linha de Comando (Ações e Menus)
├── resources/           # Arquivos de configuração (.ini) do motor COLMAP
├── src/                 # Motores de algoritmo e lógica de negócio
│   ├── acquisition/
│   ├── camera_calibration/
│   ├── post_processing/
│   ├── reconstruction/
│   └── visualization/
├── ui/                  # Interface Gráfica (Flet Framework)
│   ├── controllers/     # Controladores e ponte de eventos
│   ├── pages/           # Views e telas da aplicação
│   ├── app_layout.py    # Shell base de navegação
│   └── router.py        # Mapeamento de rotas e hubs
├── config.yaml          # Parâmetros globais de execução
├── main.py              # Ponto de entrada (GUI ou CLI)
└── requirements.txt     # Dependências Python
```

---

## 📦 Dependências do Sistema

O projeto depende dos seguintes componentes e bibliotecas chave:

* **Motor Base:** `colmap=3.12.6` (via Conda)
* **Visão Computacional & 3D:** `opencv-contrib-python`, `open3d`, `pyvista`, `numpy`, `tqdm`
* **Interface Gráfica:** `flet==0.21.2` *(versão fixa necessária para compatibilidade dos componentes de UI)*
* **Backend & Configurações:** `PyYAML`

---

## ⚙️ Preparação do Ambiente (Conda)

Recomenda-se o uso do **Conda** para gerenciamento de dependências nativas e suporte completo à aceleração via hardware (**GPU/CUDA**).

### 1. Criar e Ativar o Ambiente
No terminal, dentro da pasta raiz do projeto, execute:
```bash
# Criação do ambiente isolado Python 3.12
conda create -n condaVenv python=3.12 -y

# Ativação do ambiente (Obrigatório)
conda activate condaVenv
```

### 2. Instalar o Motor COLMAP
Instale o COLMAP via `conda-forge`:
```bash
conda install -c conda-forge colmap=3.12.6 -y
```

### 3. Instalar Dependências do Python
Com o ambiente `condaVenv` ativo, instale as bibliotecas contidas no `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

A execução é centralizada no script `main.py`.

### Modo Interface Gráfica (GUI) - *Padrão*
Para rodar a aplicação desktop interativa:
```bash
python main.py
```

### Modo Linha de Comando (CLI)
Para executar via terminal (ideal para servidores ou ambientes headless):
```bash
python main.py --cli
```

---

## 📝 Configurações e Logs

* **Parâmetros:** Arquivos de inicialização do COLMAP estão disponíveis em `resources`.
* **Resultados e Logs:** Os modelos exportados e relatórios de progresso são salvos em `data/out/reconstructions/` (ou no diretório definido pelo usuário durante a execução).
EOF
