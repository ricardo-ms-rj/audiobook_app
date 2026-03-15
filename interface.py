import flet as ft

class InterfaceApp:
    def __init__(self):
        # FilePicker instanciado aqui
        self.file_picker = ft.FilePicker()
        
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=70,
            destinations=[
                ft.NavigationRailDestination(icon="home_outlined", selected_icon="home", label="Home"),
                ft.NavigationRailDestination(icon="settings_outlined", selected_icon="settings", label="Config"),
            ],
        )

        self.btn_selecionar = ft.ElevatedButton("Selecionar PDF", icon="folder_open")
        self.btn_preview = ft.ElevatedButton("Preview", icon="speed")
        self.btn_converter = ft.ElevatedButton("Gerar Completo", icon="play_arrow")
        self.btn_gerar_manifest = ft.ElevatedButton("Gerar Manifest", icon="assignment")
        self.dd_preview_alvo = ft.Dropdown(
            label="Preview",
            value="101_1",
            options=[
                ft.dropdown.Option("101_1"),
                ft.dropdown.Option("102_1"),
            ],
            width=180,
        )

        self.status_texto = ft.Text("Pronto.", weight="bold")
        self.progresso = ft.ProgressBar(visible=False)
        self.caminho_pdf_label = ft.Text("Nenhum arquivo selecionado.", italic=True)
        self.cb_forcar = ft.Checkbox(label="Forçar Regeneração", value=False)

        self.slider_audio = ft.Slider(min=0, max=100, value=0, expand=True)
        self.tempo_atual = ft.Text("00:00")
        self.tempo_total = ft.Text("00:00")
        
        self.btn_backward = ft.IconButton(icon="replay_10", icon_size=30)
        self.btn_play_pause = ft.IconButton(icon="play_circle_filled", icon_size=40)
        self.btn_forward = ft.IconButton(icon="forward_10", icon_size=30)
        self.btn_stop = ft.IconButton(icon="stop_circle_outlined", icon_size=30)
        
        self.lista_audios = ft.ListView(expand=True, spacing=10, padding=10)
        self.conteudo_variavel = ft.Container(expand=True)

    def _build_player(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.tempo_atual, self.slider_audio, self.tempo_total], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.btn_stop, self.btn_backward, self.btn_play_pause, self.btn_forward], alignment=ft.MainAxisAlignment.CENTER),
                ]
            ),
            padding=20,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

    def build_home_tab(self):
        sidebar = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Comandos", weight="bold", size=18),
                    self.btn_selecionar,
                    self.caminho_pdf_label,
                    self.cb_forcar,
                    self.dd_preview_alvo,
                    ft.Divider(),
                    ft.Row([self.btn_preview, self.btn_converter, self.btn_gerar_manifest], wrap=True),
                    self.progresso,
                    self.status_texto,
                ],
                tight=True,
            ),
            width=320,
            padding=10,
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

        biblioteca = ft.Container(
            content=ft.Column([ft.Text("Sua Biblioteca", weight="bold", size=18), self.lista_audios], expand=True),
            padding=10, expand=True,
        )

        return ft.Row([sidebar, biblioteca], expand=True)

    def montar_layout(self):
        self.conteudo_variavel.content = self.build_home_tab()
        area_principal = ft.Container(
            content=ft.Column([self.conteudo_variavel, self._build_player()], expand=True),
            expand=True, padding=0,
        )
        return ft.Row([self.nav_rail, ft.VerticalDivider(width=1), area_principal], expand=True)
