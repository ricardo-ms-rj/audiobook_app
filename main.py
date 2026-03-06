import flet as ft
from interface import InterfaceApp
import motor_audio
import asyncio
import json
import inspect
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "manifest.json"

try:
    import flet_audio as fta
except Exception:
    fta = None


def main(page: ft.Page):
    page.title = "LPIC-1 Audiobook Factory"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1100
    page.window_height = 800

    ui = InterfaceApp()
    pdf_selecionado: str | None = None

    page.overlay.append(ui.file_picker)

    audio_player = None
    audio_is_playing = False
    current_duration_ms = 0

    def run_task(coro):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)

    def set_status(msg: str):
        ui.status_texto.value = msg
        page.update()

    def on_file_result(e):
        nonlocal pdf_selecionado
        if getattr(e, "files", None):
            pdf_selecionado = e.files[0].path
            ui.caminho_pdf_label.value = e.files[0].name
            if pdf_selecionado.lower().endswith(".docx"):
                set_status("DOCX carregado.")
            else:
                set_status("PDF carregado.")

    ui.file_picker.on_result = on_file_result

    def _duration_to_ms(d):
        if d is None:
            return 0
        if isinstance(d, (int, float)):
            return int(d)
        if hasattr(d, "milliseconds"):
            try:
                return int(d.milliseconds)
            except Exception:
                pass
        if hasattr(d, "in_milliseconds"):
            try:
                return int(d.in_milliseconds)
            except Exception:
                pass
        s = str(d)
        try:
            parts = s.split(":")
            if len(parts) == 3:
                h = int(parts[0])
                m = int(parts[1])
                sec = float(parts[2])
                return int(((h * 3600) + (m * 60) + sec) * 1000)
            if len(parts) == 2:
                m = int(parts[0])
                sec = float(parts[1])
                return int(((m * 60) + sec) * 1000)
        except Exception:
            return 0
        return 0

    def format_time(ms):
        ms = int(ms or 0)
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes:02d}:{seconds:02d}"

    async def _call_audio(method_name: str, *args):
        nonlocal audio_player
        if audio_player is None:
            return None
        m = getattr(audio_player, method_name, None)
        if m is None:
            return None
        r = m(*args)
        if inspect.isawaitable(r):
            return await r
        return r

    async def _seek_to(ms: int):
        ms = max(0, int(ms))
        try:
            if hasattr(ft, "Duration"):
                await _call_audio("seek", ft.Duration(milliseconds=ms))
            else:
                await _call_audio("seek", ms)
        except Exception:
            try:
                await _call_audio("seek", ms)
            except Exception:
                pass

    def _to_asset_src(mp3_abs: Path) -> str:
        try:
            rel = mp3_abs.resolve().relative_to(BASE_DIR).as_posix()
            return rel
        except Exception:
            tmp_dir = BASE_DIR / "audios" / "_tmp_play"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            dst = tmp_dir / mp3_abs.name
            if mp3_abs.exists():
                dst.write_bytes(mp3_abs.read_bytes())
            rel = dst.resolve().relative_to(BASE_DIR).as_posix()
            return rel

    def bind_audio_events():
        nonlocal current_duration_ms, audio_is_playing

        if audio_player is None:
            return

        def _on_duration_change(e):
            nonlocal current_duration_ms
            d = getattr(e, "duration", None)
            current_duration_ms = _duration_to_ms(d)
            ui.tempo_total.value = format_time(current_duration_ms)
            page.update()

        def _on_position_change(e):
            pos_ms = _duration_to_ms(getattr(e, "position", None))
            if current_duration_ms > 0:
                ui.slider_audio.value = (pos_ms / current_duration_ms) * 100
            ui.tempo_atual.value = format_time(pos_ms)
            page.update()

        def _on_state_change(e):
            nonlocal audio_is_playing
            st = str(getattr(e, "state", "")).lower()
            audio_is_playing = "playing" in st
            ui.btn_play_pause.icon = "pause_circle_filled" if audio_is_playing else "play_circle_filled"
            page.update()

        if hasattr(audio_player, "on_duration_changed"):
            audio_player.on_duration_changed = _on_duration_change
        if hasattr(audio_player, "on_position_changed"):
            audio_player.on_position_changed = _on_position_change
        if hasattr(audio_player, "on_state_changed"):
            audio_player.on_state_changed = _on_state_change

        if hasattr(audio_player, "on_duration_change"):
            audio_player.on_duration_change = _on_duration_change
        if hasattr(audio_player, "on_position_change"):
            audio_player.on_position_change = _on_position_change
        if hasattr(audio_player, "on_state_change"):
            audio_player.on_state_change = _on_state_change

    def ensure_audio_player(src_asset: str):
        nonlocal audio_player
        if fta is not None and hasattr(fta, "Audio"):
            if audio_player is None or audio_player.__class__.__module__ != "flet_audio":
                audio_player = fta.Audio(src=src_asset, autoplay=False, volume=1, balance=0)
                page.overlay.append(audio_player)
                bind_audio_events()
                page.update()
            else:
                audio_player.src = src_asset
            return True

        if hasattr(ft, "Audio"):
            if audio_player is None:
                audio_player = ft.Audio(src=src_asset, autoplay=False)
                page.overlay.append(audio_player)
                bind_audio_events()
                page.update()
            else:
                audio_player.src = src_asset
            return True

        set_status("Audio indisponível neste runtime.")
        return False

    async def tocar_audio_async(mp3_path_abs: str):
        nonlocal audio_is_playing
        try:
            p = Path(mp3_path_abs).resolve()
            if not p.exists():
                set_status("Arquivo não encontrado.")
                return

            src_asset = _to_asset_src(p)
            if not ensure_audio_player(src_asset):
                return

            try:
                await _call_audio("release")
            except Exception:
                pass

            try:
                await _call_audio("play")
            except TypeError:
                await _call_audio("play", None)

            audio_is_playing = True
            ui.btn_play_pause.icon = "pause_circle_filled"
            set_status(f"Tocando: {p.name}")
            page.update()
        except Exception as ex:
            set_status(f"Erro ao tocar áudio: {ex}")

    def tocar_audio(mp3_path_abs: str):
        run_task(tocar_audio_async(mp3_path_abs))

    def atualizar_lista_audios():
        ui.lista_audios.controls.clear()
        if not MANIFEST_PATH.exists():
            ui.lista_audios.controls.append(ft.Text("Nenhum manifest encontrado."))
            page.update()
            return

        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            for _, info in data.items():
                mp3_rel = info.get("mp3", "")
                mp3_abs = (BASE_DIR / mp3_rel).resolve()
                existe = mp3_abs.exists()

                ui.lista_audios.controls.append(
                    ft.ListTile(
                        leading=ft.Icon("audiotrack" if existe else "file_download_off"),
                        title=ft.Text(info.get("titulo", "Sem título")),
                        subtitle=ft.Text(f"Páginas: {info.get('inicio', '?')} a {info.get('fim', '?')}"),
                        trailing=ft.IconButton(
                            "play_arrow",
                            on_click=lambda e, p=str(mp3_abs): tocar_audio(p),
                        ) if existe else None,
                        disabled=not existe,
                    )
                )
        except Exception as ex:
            ui.lista_audios.controls.append(ft.Text(f"Erro ao ler manifest: {ex}"))

        page.update()

    async def iniciar_processamento(preview: bool = False, preview_alvo: str = "101_1"):
        nonlocal pdf_selecionado
        if not pdf_selecionado:
            set_status("Selecione um PDF ou DOCX!")
            return

        ui.progresso.visible = True
        set_status("Gerando...")
        try:
            # Modo DOCX (teste controlado): Preview gera apenas 101_1 e 102_1 (mais 101 e 102 mestres).
            if pdf_selecionado.lower().endswith(".docx"):
                pasta = Path(pdf_selecionado).resolve().parent
                set_status("Gerando (DOCX teste)...")
                await motor_audio.gerar_preview_docx(pasta, preview_alvo=preview_alvo, forcar=ui.cb_forcar.value)
                set_status("Concluído!")
                atualizar_lista_audios()
                return

            # Modo PDF (padrão)
            motor = motor_audio.MotorAudio(pdf_selecionado)

            itens_full = motor.obter_sumario()
            if preview:
                alvo_chave = preview_alvo.replace("_", ".")
                itens = [item for item in itens_full if alvo_chave in item[1]][:1]
                if not itens:
                    raise ValueError(f"Subtópico {preview_alvo} não encontrado no sumário.")
            else:
                itens = itens_full

            for idx, item in enumerate(itens):
                set_status(f"Processando {idx+1}/{len(itens)}")

                idx_real = itens_full.index(item)
                if (idx_real + 1) < len(itens_full):
                    prox_pag_0based = itens_full[idx_real + 1][2] - 1
                else:
                    prox_pag_0based = motor.doc.page_count

                await motor.extrair_e_converter(item, prox_pag_0based, forcar=ui.cb_forcar.value)

            motor_audio.gerar_manifest(pdf_selecionado)
            set_status("Concluído!")
            atualizar_lista_audios()
        except Exception as ex:
            set_status(f"Erro: {ex}")
        finally:
            ui.progresso.visible = False
            page.update()

    ui.btn_selecionar.on_click = lambda _: ui.file_picker.pick_files(allowed_extensions=["pdf","docx"])
    ui.btn_preview.on_click = lambda _: run_task(iniciar_processamento(preview=True, preview_alvo=ui.dd_preview_alvo.value or "101_1"))
    ui.btn_converter.on_click = lambda _: run_task(iniciar_processamento(preview=False))
    ui.btn_gerar_manifest.on_click = lambda _: (
        set_status("Selecione um PDF ou DOCX!") if not pdf_selecionado else (motor_audio.gerar_manifest(pdf_selecionado), atualizar_lista_audios())
    )

    async def _pause():
        await _call_audio("pause")

    async def _resume_or_play():
        if audio_player is None:
            return
        if hasattr(audio_player, "resume"):
            await _call_audio("resume")
        else:
            await _call_audio("play")

    def toggle_play(e):
        if audio_player is None or not getattr(audio_player, "src", None):
            return
        if ui.btn_play_pause.icon == "play_circle_filled":
            run_task(_resume_or_play())
            ui.btn_play_pause.icon = "pause_circle_filled"
        else:
            run_task(_pause())
            ui.btn_play_pause.icon = "play_circle_filled"
        page.update()

    def seek_relative(delta_ms: int):
        if audio_player is None or not getattr(audio_player, "src", None):
            return

        async def _do():
            pos_ms = 0
            if hasattr(audio_player, "get_current_position"):
                try:
                    pos_ms = _duration_to_ms(await _call_audio("get_current_position"))
                except Exception:
                    pos_ms = 0
            else:
                pos_ms = _duration_to_ms(getattr(audio_player, "position", 0))

            await _seek_to(pos_ms + int(delta_ms))

        run_task(_do())

    def stop_audio(e):
        async def _stop():
            await _pause()
            await _seek_to(0)

        run_task(_stop())
        ui.btn_play_pause.icon = "play_circle_filled"
        page.update()

    def slider_seek_end(e):
        if audio_player is None or not getattr(audio_player, "src", None):
            return
        if current_duration_ms <= 0:
            return
        try:
            pct = float(getattr(e, "control", ui.slider_audio).value or 0)
        except Exception:
            pct = float(ui.slider_audio.value or 0)
        run_task(_seek_to(int((pct / 100.0) * current_duration_ms)))

    if hasattr(ui.slider_audio, "on_change_end"):
        ui.slider_audio.on_change_end = slider_seek_end

    ui.btn_play_pause.on_click = toggle_play
    ui.btn_backward.on_click = lambda _: seek_relative(-10000)
    ui.btn_forward.on_click = lambda _: seek_relative(10000)
    ui.btn_stop.on_click = stop_audio

    page.add(ui.montar_layout())
    atualizar_lista_audios()


if __name__ == "__main__":
    try:
        ft.app(target=main, assets_dir=".")
    except TypeError:
        ft.app(target=main)
