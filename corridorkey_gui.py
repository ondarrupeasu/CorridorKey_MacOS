#!/usr/bin/env python3
import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, shutil, time
from pathlib import Path
HAS_DND = False

CK_PATH = Path.home() / "CorridorKey"
CLIPS_PATH = CK_PATH / "ClipsForInference"
PYTHON_BIN = CK_PATH / ".venv" / "bin" / "python"

THEMES = {
    "yellow": {"acc": "#F5C518", "name": "🟡"},
    "green":  {"acc": "#00e5b4", "name": "🟢"},
}

LANGS = {
    "EN": {
        "title": "CorridorKey",
        "subtitle": "Neural green screen keying · Apple Silicon",
        "sec1": "①  INPUT FILES",
        "sec2": "②  SETTINGS",
        "sec3": "③  PROGRESS",
        "lbl_input": "Green screen video:",
        "lbl_alpha": "Alpha Hint (mask):",
        "hint_text": "The Alpha Hint is a rough mask of your subject (video .mp4/.mov or image folder).",
        "lbl_gamma": "Color space:",
        "lbl_despill": "Despill  (0-10):",
        "lbl_despeckle": "Auto-despeckle:",
        "chk_despeckle": "Remove tracking dots and artifacts",
        "lbl_refiner": "Refiner:",
        "lbl_png": "Export PNG:",
        "chk_png": "Convert EXR to PNG after processing",
        "converting_png": "🖼  Converting EXR to PNG...",
        "btn_browse": "Browse",
        "lbl_output": "Output folder:",
        "btn_process": "▶   PROCESS",
        "btn_cancel": "■   CANCEL",
        "btn_results": "📁  View results",
        "processing": "⏳  Processing...",
        "ready": "Ready. Select your files and click Process.",
        "alpha_q_title": "Alpha Hint type",
        "alpha_q_msg": "Is your Alpha Hint a folder of images?\n\nYes → image folder\nNo → video file",
        "warn_no_input_t": "Missing file",
        "warn_no_input_m": "Please select the green screen video.",
        "warn_no_alpha_t": "Missing Alpha Hint",
        "warn_no_alpha_m": "Please select the Alpha Hint.",
        "err_not_found": "Not found",
        "preparing": "📂 Preparing clip:",
        "copied_video": "✓ Video copied",
        "copied_alpha": "✓ Alpha Hint copied",
        "copied_alpha_n": "✓ Alpha Hint copied ({n} images)",
        "launching": "🚀 Starting inference (Apple Silicon)",
        "done": "✅  Processing complete!\n📁  Results in:\n    {path}",
        "cancelled": "⛔  Processing cancelled.",
        "error": "❌  Error: {msg}",
        "proc_error": "Process finished with errors. Check the log.",
        "gamma_srgb": "sRGB  (normal)",
        "gamma_linear": "Linear",
        "lang_btn": "ES",
        "frame_progress": "Processing frame {current} of {total}  ({pct}%)",
    },
    "ES": {
        "title": "CorridorKey",
        "subtitle": "Neural green screen keying · Apple Silicon",
        "sec1": "①  ARCHIVOS DE ENTRADA",
        "sec2": "②  CONFIGURACIÓN",
        "sec3": "③  PROGRESO",
        "lbl_input": "Vídeo green screen:",
        "lbl_alpha": "Alpha Hint (máscara):",
        "hint_text": "El Alpha Hint es una máscara aproximada del sujeto (vídeo .mp4/.mov o carpeta de imágenes).",
        "lbl_gamma": "Espacio de color:",
        "lbl_despill": "Despill  (0-10):",
        "lbl_despeckle": "Auto-despeckle:",
        "chk_despeckle": "Eliminar puntos de tracking y artefactos",
        "lbl_refiner": "Refiner:",
        "lbl_png": "Export PNG:",
        "chk_png": "Convert EXR to PNG after processing",
        "converting_png": "🖼  Converting EXR to PNG...",
        "btn_browse": "Browse",
        "lbl_output": "Carpeta de salida:",
        "btn_process": "▶   PROCESAR",
        "btn_cancel": "■   CANCELAR",
        "btn_results": "📁  Ver resultados",
        "processing": "⏳  Procesando...",
        "ready": "Listo. Selecciona los archivos y pulsa Procesar.",
        "alpha_q_title": "Tipo de Alpha Hint",
        "alpha_q_msg": "¿El Alpha Hint es una carpeta con imágenes?\n\nSí → carpeta\nNo → archivo de vídeo",
        "warn_no_input_t": "Falta archivo",
        "warn_no_input_m": "Selecciona el vídeo de green screen.",
        "warn_no_alpha_t": "Falta Alpha Hint",
        "warn_no_alpha_m": "Selecciona el Alpha Hint.",
        "err_not_found": "No encontrado",
        "preparing": "📂 Preparando clip:",
        "copied_video": "✓ Vídeo copiado",
        "copied_alpha": "✓ Alpha Hint copiado",
        "copied_alpha_n": "✓ Alpha Hint copiado ({n} imágenes)",
        "launching": "🚀 Iniciando inferencia (Apple Silicon)",
        "done": "✅  ¡Procesado completado!\n📁  Resultados en:\n    {path}",
        "cancelled": "⛔  Procesado cancelado.",
        "error": "❌  Error: {msg}",
        "proc_error": "El proceso terminó con errores. Revisa el log.",
        "gamma_srgb": "sRGB  (normal)",
        "gamma_linear": "Linear",
        "lang_btn": "EN",
        "frame_progress": "Procesando frame {current} de {total}  ({pct}%)",
    },
}

class App:
    def __init__(self, root):
        self.root = root
        self.lang  = "EN"
        self.theme = "yellow"
        self.input_video   = tk.StringVar()
        self.alpha_hint    = tk.StringVar()
        self.output_folder = tk.StringVar(value=str(Path.home() / "Movies" / "CorridorKey"))
        self.gamma_var     = tk.StringVar(value="srgb")
        self.despill_var   = tk.IntVar(value=5)
        self.despeckle_var = tk.BooleanVar(value=True)
        self.refiner_var   = tk.DoubleVar(value=1.0)
        self.png_var       = tk.BooleanVar(value=False)
        self.is_processing = False
        self.output_dir    = None
        self.proc          = None
        self.total_frames  = 0
        self.clip_dir      = None
        self._build_ui()

    def t(self, key, **kw):
        s = LANGS[self.lang][key]
        return s.format(**kw) if kw else s

    def acc(self):
        return THEMES[self.theme]["acc"]

    def _switch_lang(self):
        self.lang = "ES" if self.lang == "EN" else "EN"
        self._rebuild()

    def _switch_theme(self):
        self.theme = "green" if self.theme == "yellow" else "yellow"
        self._rebuild()

    def _rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()

    def _build_ui(self):
        BG, BG3, FG, FGD = "#141414", "#2a2a2a", "#e8e8e8", "#777777"
        ACC = self.acc()
        F = "Helvetica Neue"

        self.root.title(self.t("title"))
        self.root.geometry("680x960")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")
        for w in ("TFrame","TLabel","TCheckbutton","TRadiobutton","TScale","TScrollbar"):
            style.configure(w, background=BG, foreground=FG)
        style.configure("TScale", troughcolor=BG3, sliderthickness=14)
        style.configure("TScrollbar", troughcolor="#1e1e1e", arrowcolor=FGD, background=BG3)
        style.configure("TProgressbar", troughcolor=BG3, background=ACC, thickness=6)

        # Header
        hdr = tk.Frame(self.root, bg=BG, height=80)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)
        tk.Label(hdr, text=self.t("title"), bg=BG, fg="#ffffff", font=(F,26,"bold")).place(x=28,y=16)
        tk.Label(hdr, text=self.t("subtitle"), bg=BG, fg=FGD, font=(F,11)).place(x=30,y=52)

        other = THEMES["green"]["name"] if self.theme == "yellow" else THEMES["yellow"]["name"]
        lbl_theme = tk.Label(hdr, text=other, bg=BG, fg=ACC, font=(F,13), cursor="hand2")
        lbl_theme.place(x=588, y=32)
        lbl_theme.bind("<Button-1>", lambda e: self._switch_theme())

        lbl_lang = tk.Label(hdr, text=self.t("lang_btn"), bg=BG, fg=ACC, font=(F,11,"bold"), cursor="hand2")
        lbl_lang.place(x=625, y=34)
        lbl_lang.bind("<Button-1>", lambda e: self._switch_lang())

        tk.Frame(self.root, bg="#2c2c2c", height=1).pack(fill=tk.X)
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        def section(txt):
            f = tk.Frame(main, bg=BG)
            f.pack(fill=tk.X, padx=28, pady=(22,8))
            tk.Label(f, text=txt, bg=BG, fg=ACC, font=(F,10,"bold")).pack(anchor="w")
            tk.Frame(main, bg="#2c2c2c", height=1).pack(fill=tk.X, padx=28)

        def setup_drop(widget, var):
            if not HAS_DND: return
            widget.drop_target_register(DND_FILES)
            def on_drop(e):
                p = e.data.strip().strip("{}")
                var.set(p)
            widget.dnd_bind("<<Drop>>", on_drop)

        def file_row(lbl, var, cmd):
            row = tk.Frame(main, bg=BG)
            row.pack(fill=tk.X, padx=28, pady=(10,2))
            tk.Label(row, text=lbl, bg=BG, fg=FGD, font=(F,10), width=20, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=var, bg=BG3, fg=FG, insertbackground=FG,
                     relief=tk.FLAT, font=("Menlo",10), width=36)
            entry.pack(side=tk.LEFT, ipady=5, padx=(0,8))
            setup_drop(entry, var)
            tk.Button(row, text=self.t("btn_browse"), command=cmd,
                      bg=BG, fg="#000000" if self.theme=="yellow" else FGD,
                      relief=tk.FLAT, font=(F,10), bd=0, highlightthickness=0,
                      cursor="hand2", activebackground=BG).pack(side=tk.LEFT, padx=(4,0))

        section(self.t("sec1"))
        file_row(self.t("lbl_input"), self.input_video, self._browse_input)
        file_row(self.t("lbl_alpha"), self.alpha_hint,  self._browse_alpha)
        tk.Label(main, text=self.t("hint_text"), bg=BG, fg=FGD, font=(F,10),
                 justify=tk.LEFT).pack(anchor="w", padx=28, pady=(6,0))
        file_row(self.t("lbl_output"), self.output_folder, self._browse_output)

        section(self.t("sec2"))

        def lrow(lbl, builder):
            row = tk.Frame(main, bg=BG)
            row.pack(fill=tk.X, padx=28, pady=6)
            tk.Label(row, text=lbl, bg=BG, fg=FG, font=(F,11), width=20, anchor="w").pack(side=tk.LEFT)
            builder(row)

        def build_gamma(row):
            for val, key in (("srgb","gamma_srgb"),("linear","gamma_linear")):
                tk.Radiobutton(row, text=self.t(key), variable=self.gamma_var, value=val,
                               bg=BG, fg=FG, selectcolor=BG3, activebackground=BG,
                               font=(F,11)).pack(side=tk.LEFT, padx=(0,16))
        lrow(self.t("lbl_gamma"), build_gamma)

        def build_despill(row):
            ttk.Scale(row, from_=0, to=10, variable=self.despill_var,
                      orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT)
            lbl = tk.Label(row, text=str(int(self.despill_var.get())), bg=BG, fg=ACC, font=(F,11,"bold"), width=3)
            lbl.pack(side=tk.LEFT, padx=(8,0))
            self.despill_var.trace_add("write", lambda *_: lbl.config(text=str(int(self.despill_var.get()))))
        lrow(self.t("lbl_despill"), build_despill)

        def build_despeckle(row):
            tk.Checkbutton(row, text=self.t("chk_despeckle"), variable=self.despeckle_var,
                           bg=BG, fg=FG, selectcolor=BG3, activebackground=BG,
                           font=(F,11)).pack(side=tk.LEFT)
        lrow(self.t("lbl_despeckle"), build_despeckle)

        def build_refiner(row):
            ttk.Scale(row, from_=0.5, to=2.0, variable=self.refiner_var,
                      orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT)
            lbl = tk.Label(row, text=f"{self.refiner_var.get():.1f}", bg=BG, fg=ACC, font=(F,11,"bold"), width=4)
            lbl.pack(side=tk.LEFT, padx=(8,0))
            self.refiner_var.trace_add("write", lambda *_: lbl.config(text=f"{self.refiner_var.get():.1f}"))
        lrow(self.t("lbl_refiner"), build_refiner)

        def build_png(row):
            tk.Checkbutton(row, text=self.t("chk_png"), variable=self.png_var,
                           bg=BG, fg=FG, selectcolor=BG3, activebackground=BG,
                           font=(F,11)).pack(side=tk.LEFT)
        lrow(self.t("lbl_png"), build_png)

        section(self.t("sec3"))

        # Barra de progreso
        prog_frame = tk.Frame(main, bg=BG)
        prog_frame.pack(fill=tk.X, padx=28, pady=(10,4))
        self.progress_bar = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL,
                                             mode="determinate", style="TProgressbar")
        self.progress_bar.pack(fill=tk.X)
        self.progress_lbl = tk.Label(main, text="", bg=BG, fg=FGD, font=(F,9))
        self.progress_lbl.pack(anchor="w", padx=28)

        # Log
        log_outer = tk.Frame(main, bg="#0d0d0d")
        log_outer.pack(fill=tk.BOTH, expand=True, padx=28, pady=(6,0))
        self.log_text = tk.Text(log_outer, bg="#0d0d0d", fg=ACC, font=("Menlo",10), height=9,
                                wrap=tk.WORD, bd=0, padx=10, pady=8, state=tk.DISABLED, relief=tk.FLAT)
        vsb = ttk.Scrollbar(log_outer, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log(self.t("ready"))

        tk.Frame(self.root, bg="#2c2c2c", height=1).pack(fill=tk.X)
        bar = tk.Frame(self.root, bg="#1a1a1a", height=68)
        bar.pack(fill=tk.X); bar.pack_propagate(False)

        self.process_btn = tk.Button(bar, text=self.t("btn_process"), command=self._toggle,
            bg=ACC, fg="#000000", font=(F,13,"bold"), relief=tk.FLAT,
            padx=28, pady=10, cursor="hand2", activebackground=ACC)
        self.process_btn.place(x=28, y=14)

        self.open_btn = tk.Button(bar, text=self.t("btn_results"), command=self._open,
            bg="#2a2a2a", fg="#000000", font=(F,12,"bold"), relief=tk.FLAT, padx=20, pady=10,
            cursor="hand2", state=tk.NORMAL, activebackground="#3a3a3a")
        self.open_btn.place(x=210, y=14)

    def _browse_input(self):
        p = filedialog.askopenfilename(title=self.t("lbl_input"),
            filetypes=[("Videos","*.mp4 *.mov *.mxf *.avi *.mkv *.r3d"),("All","*.*")])
        if p: self.input_video.set(p)

    def _browse_output(self):
        p = filedialog.askdirectory(title=self.t("lbl_output"))
        if p: self.output_folder.set(p)

    def _browse_alpha(self):
        ans = messagebox.askquestion(self.t("alpha_q_title"), self.t("alpha_q_msg"))
        if ans == "yes":
            p = filedialog.askdirectory(title=self.t("lbl_alpha"))
        else:
            p = filedialog.askopenfilename(title=self.t("lbl_alpha"),
                filetypes=[("Videos","*.mp4 *.mov *.mxf *.avi *.mkv"),("All","*.*")])
        if p: self.alpha_hint.set(p)

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg+"\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _toggle(self):
        if self.is_processing:
            self._cancel()
        else:
            self._start()

    def _cancel(self):
        if self.proc:
            try:
                import signal, os
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except:
                self.proc.kill()
        self.proc = None
        self.is_processing = False
        self.process_btn.config(text=self.t("btn_process"), bg=self.acc(), activebackground=self.acc())
        self.progress_bar["value"] = 0
        self.progress_lbl.config(text="")
        self._log(self.t("cancelled"))

    def _start(self):
        inp = self.input_video.get().strip()
        alp = self.alpha_hint.get().strip()
        if not inp: return messagebox.showwarning(self.t("warn_no_input_t"), self.t("warn_no_input_m"))
        if not alp: return messagebox.showwarning(self.t("warn_no_alpha_t"), self.t("warn_no_alpha_m"))
        if not os.path.exists(inp): return messagebox.showerror(self.t("err_not_found"), f"Not found:\n{inp}")
        if not os.path.exists(alp): return messagebox.showerror(self.t("err_not_found"), f"Not found:\n{alp}")

        # Calcular total frames
        try:
            import cv2
            cap = cv2.VideoCapture(inp)
            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
        except:
            self.total_frames = 0

        self.is_processing = True
        self.process_btn.config(text=self.t("btn_cancel"), bg="#cc3333", activebackground="#aa2222")
        self.progress_bar["value"] = 0
        self.progress_lbl.config(text="")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        threading.Thread(target=self._run, args=(inp,alp), daemon=True).start()

    def _run(self, inp, alp):
        try:
            name = Path(inp).stem.replace(" ","_")
            self.clip_dir = CLIPS_PATH / name
            alpha_dir = self.clip_dir / "AlphaHint"
            self.root.after(0, self._log, f"{self.t('preparing')} {name}")
            if self.clip_dir.exists(): shutil.rmtree(self.clip_dir)
            self.clip_dir.mkdir(parents=True)
            alpha_dir.mkdir(parents=True)
            input_link = self.clip_dir / f"Input{Path(inp).suffix}"
            if input_link.exists() or input_link.is_symlink(): input_link.unlink()
            input_link.symlink_to(Path(inp).resolve())
            self.root.after(0, self._log, self.t("copied_video"))
            if os.path.isdir(alp):
                files = [f for f in os.listdir(alp) if not f.startswith(".")]
                for f in files:
                    link = alpha_dir / f
                    if link.exists() or link.is_symlink(): link.unlink()
                    link.symlink_to(Path(os.path.join(alp,f)).resolve())
                self.root.after(0, self._log, self.t("copied_alpha_n", n=len(files)))
            else:
                alpha_link = alpha_dir / f"AlphaHint{Path(alp).suffix}"
                if alpha_link.exists() or alpha_link.is_symlink(): alpha_link.unlink()
                alpha_link.symlink_to(Path(alp).resolve())
                self.root.after(0, self._log, self.t("copied_alpha"))

            gamma = "--linear" if self.gamma_var.get()=="linear" else "--srgb"
            desp  = int(self.despill_var.get())
            dspkl = "--despeckle" if self.despeckle_var.get() else "--no-despeckle"
            ref   = round(self.refiner_var.get(), 1)
            cmd = [str(PYTHON_BIN), str(CK_PATH/"corridorkey_cli.py"), "run-inference",
                   "--backend","torch", gamma, "--despill",str(desp), dspkl, "--refiner",str(ref)]
            self.root.after(0, self._log,
                f"\n{self.t('launching')}\n"
                f"   Gamma: {self.gamma_var.get()}  |  Despill: {desp}  |  Refiner: {ref}\n")
            env = os.environ.copy()
            env["CORRIDORKEY_BACKEND"] = "torch"
            env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

            self.proc = subprocess.Popen(cmd, cwd=str(CK_PATH),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=env, bufsize=1, start_new_session=True)

            # Monitorear progreso en hilo separado
            self.root.after(0, self._log, f"📊 Monitoring: {self.clip_dir / 'Output' / 'Matte'}")
            threading.Thread(target=self._monitor_progress, daemon=True).start()

            for line in self.proc.stdout:
                line = line.rstrip()
                if line: self.root.after(0, self._log, line)

            self.proc.wait()

            if not self.is_processing:
                return  # cancelado

            if self.proc.returncode == 0:
                import shutil as _shutil
                out_folder = Path(self.output_folder.get())
                out_base = out_folder / name
                output_src = self.clip_dir / "Output"
                self.root.after(0, self._log, f"📁 Copying results to: {out_base}")
                try:
                    out_folder.mkdir(parents=True, exist_ok=True)
                    if out_base.exists(): _shutil.rmtree(out_base)
                    if output_src.exists():
                        _shutil.copytree(output_src, out_base)
                        self.root.after(0, self._log, f"✓ Results copied")
                        # Borrar carpeta temporal de ClipsForInference
                        try:
                            _shutil.rmtree(self.clip_dir)
                        except Exception:
                            pass
                    else:
                        self.root.after(0, self._log, f"✗ Output folder not found: {output_src}")
                except Exception as copy_err:
                    self.root.after(0, self._log, f"✗ Copy error: {copy_err}")
                self.output_dir = str(out_base)
                if self.png_var.get():
                    self.root.after(0, self._log, self.t("converting_png"))
                    self._convert_to_png(out_base)
                self.root.after(0, self._on_ok)
            else:
                self.root.after(0, self._on_err, self.t("proc_error"))
        except Exception as e:
            self.root.after(0, self._on_err, str(e))

    def _convert_to_png(self, out_base):
        import imageio.v3 as iio
        import numpy as np
        folders = ["Matte", "FG", "Processed", "Comp"]
        for folder in folders:
            exr_dir = Path(out_base) / folder
            if not exr_dir.exists():
                continue
            png_dir = Path(out_base) / f"{folder}_PNG"
            png_dir.mkdir(exist_ok=True)
            exr_files = sorted(exr_dir.glob("*.exr"))
            converted = 0
            for exr_file in exr_files:
                try:
                    img = iio.imread(str(exr_file))
                    if img.dtype != np.uint8:
                        img = np.clip(img * 255, 0, 255).astype(np.uint8)
                    png_path = png_dir / (exr_file.stem + ".png")
                    iio.imwrite(str(png_path), img)
                    converted += 1
                except Exception as e:
                    self.root.after(0, self._log, f"  ✗ {exr_file.name}: {e}")
            self.root.after(0, self._log, f"  ✓ {folder}_PNG — {converted} frames")

    def _monitor_progress(self):
        """Cuenta los EXR generados en Output/Matte para mostrar progreso."""
        if self.total_frames == 0 or self.clip_dir is None:
            return
        matte_dir = self.clip_dir / "Output" / "Matte"
        while self.is_processing:
            try:
                if matte_dir.exists():
                    done = len([f for f in os.listdir(matte_dir) if f.endswith(".exr")])
                    if done > 0 and self.total_frames > 0:
                        pct = min(int(done / self.total_frames * 100), 100)
                        self.root.after(0, self._update_progress, done, self.total_frames, pct)
            except:
                pass
            time.sleep(1)

    def _update_progress(self, current, total, pct):
        self.progress_bar["value"] = pct
        self.progress_lbl.config(text=self.t("frame_progress", current=current, total=total, pct=pct))

    def _on_ok(self):
        self._log(self.t("done", path=self.output_dir))
        self.progress_bar["value"] = 100
        self.progress_lbl.config(text=self.t("frame_progress",
            current=self.total_frames, total=self.total_frames, pct=100))
        self.is_processing = False
        self.proc = None
        self.process_btn.config(text=self.t("btn_process"), bg=self.acc(), activebackground=self.acc())
        self.open_btn.config(state=tk.NORMAL)
        # Liberar memoria MPS
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

    def _on_err(self, msg):
        self._log(self.t("error", msg=msg))
        self.is_processing = False
        self.process_btn.config(text=self.t("btn_process"), bg=self.acc(), activebackground=self.acc())

    def _open(self):
        target = self.output_dir if (self.output_dir and os.path.exists(self.output_dir)) else str(CLIPS_PATH)
        subprocess.run(["open", target])

root = tk.Tk()
app = App(root)
root.update_idletasks()
w = root.winfo_width()
h = root.winfo_height()
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x = (sw - w) // 2
y = (sh - h) // 2
root.geometry(f"{w}x{h}+{x}+{y}")
root.mainloop()