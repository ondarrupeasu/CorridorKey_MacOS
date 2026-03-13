#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess, threading, os
from pathlib import Path

CK_PATH    = Path.home() / "CorridorKey"
PYTHON_BIN = CK_PATH / ".venv" / "bin" / "python"
UV         = Path.home() / ".local" / "bin" / "uv"

def is_installed():
    return (
        (CK_PATH / ".venv").exists() and
        (CK_PATH / "CorridorKeyModule" / "checkpoints" / "CorridorKey.pth").exists() and
        (CK_PATH / "corridorkey_cli.py").exists() and
        (CK_PATH / "corridorkey_gui.py").exists()
    )

def launch_main():
    gui = CK_PATH / "corridorkey_gui.py"
    os.execv(str(PYTHON_BIN), [str(PYTHON_BIN), str(gui)])

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CorridorKey")
        self.root.configure(bg="#141414")
        self.root.resizable(False, False)
        self._build_ui()
        self.root.update_idletasks()
        w, h = 560, 500
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        BG, ACC, FG, FGD = "#141414", "#F5C518", "#e8e8e8", "#777777"
        F = "Helvetica Neue"

        tk.Label(self.root, text="CorridorKey", bg=BG, fg="#ffffff",
                 font=(F,28,"bold")).pack(pady=(30,4))
        tk.Label(self.root, text="Neural green screen keying · Apple Silicon",
                 bg=BG, fg=FGD, font=(F,11)).pack()

        tk.Frame(self.root, bg="#2c2c2c", height=1).pack(fill=tk.X, pady=16)

        tk.Label(self.root,
                 text="CorridorKey needs to download and install\n"
                      "its components the first time (~400MB).",
                 bg=BG, fg=FG, font=(F,12), justify=tk.CENTER).pack()

        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=460)
        self.progress.pack(pady=(16,4))

        self.status_lbl = tk.Label(self.root, text="Ready to install.",
                                   bg=BG, fg=FGD, font=(F,10))
        self.status_lbl.pack()

        log_frame = tk.Frame(self.root, bg="#0d0d0d")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(8,0))
        self.log = tk.Text(log_frame, bg="#0d0d0d", fg=ACC,
                           font=("Menlo",9), height=7, bd=0,
                           padx=8, pady=6, state=tk.DISABLED,
                           relief=tk.FLAT, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.btn = tk.Button(self.root, text="Install Now",
            bg=ACC, fg="#000000", font=(F,13,"bold"), relief=tk.FLAT,
            padx=32, pady=10, cursor="hand2",
            activebackground="#e0b010", command=self._start)
        self.btn.pack(pady=14)

    def _log(self, msg):
        def _do():
            self.log.config(state=tk.NORMAL)
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.config(state=tk.DISABLED)
            self.status_lbl.config(text=msg[:70])
        self.root.after(0, _do)

    def _start(self):
        self.btn.config(state=tk.DISABLED, text="Installing...")
        self.progress.start(12)
        threading.Thread(target=self._install, daemon=True).start()

    def _run(self, cmd, label):
        self._log(f"→ {label}")
        env = os.environ.copy()
        env["PATH"] = str(UV.parent) + ":" + env.get("PATH", "")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True, env=env)
        for line in proc.stdout:
            line = line.strip()
            if line:
                self._log(f"  {line}")
        proc.wait()
        if proc.returncode != 0:
            raise Exception(f"Failed: {label}")

    def _install(self):
        try:
            env = os.environ.copy()
            env["PATH"] = str(UV.parent) + ":" + env.get("PATH", "")

            # 1. uv
            if not UV.exists():
                self._log("→ Installing uv...")
                subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh",
                               shell=True, env=env)
                self._log("✓ uv installed")

            # 2. Clonar
            if not CK_PATH.exists():
                self._run(["git", "clone",
                           "https://github.com/nikopueringer/CorridorKey",
                           str(CK_PATH)], "Cloning CorridorKey repository...")
            else:
                self._log("✓ Repository already exists")

            # 3. Dependencias
            self._run([str(UV), "sync", "--directory", str(CK_PATH)],
                      "Installing Python dependencies...")

            # 4. MLX
            self._run([str(UV), "pip", "install", "--directory", str(CK_PATH),
                       "corridorkey-mlx@git+https://github.com/nikopueringer/corridorkey-mlx.git"],
                      "Installing MLX backend...")

            # 5. imageio
            self._run([str(UV), "pip", "install", "--directory", str(CK_PATH), "imageio"],
                      "Installing extras...")

            # 6. Modelo
            model_dir  = CK_PATH / "CorridorKeyModule" / "checkpoints"
            model_file = model_dir / "CorridorKey.pth"
            model_dir.mkdir(parents=True, exist_ok=True)
            if not model_file.exists():
                self._log("→ Downloading AI model (~382MB)...")
                proc = subprocess.Popen(
                    ["curl", "-L", "--progress-bar",
                     "https://huggingface.co/nikopueringer/CorridorKey_v1.0/resolve/main/CorridorKey_v1.0.pth",
                     "-o", str(model_file)],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, env=env)
                for line in proc.stdout:
                    line = line.strip()
                    if line: self._log(f"  {line}")
                proc.wait()
                if proc.returncode != 0:
                    raise Exception("Failed to download model")
                self._log("✓ Model downloaded")
            else:
                self._log("✓ Model already exists")

            # 7. Copiar GUI
            import shutil
            gui_src = Path(__file__).parent / "corridorkey_gui.py"
            gui_dst = CK_PATH / "corridorkey_gui.py"
            if gui_src.exists() and gui_src.resolve() != gui_dst.resolve():
                shutil.copy2(gui_src, gui_dst)
                self._log("✓ GUI installed")

            self.root.after(0, self._done)

        except Exception as e:
            self.root.after(0, self._error, str(e))

    def _done(self):
        self.progress.stop()
        self.progress["value"] = 100
        self._log("✅ Installation complete!")
        self.btn.config(text="Launch CorridorKey →", state=tk.NORMAL,
                        bg="#F5C518", command=launch_main)

    def _error(self, msg):
        self.progress.stop()
        self._log(f"❌ Error: {msg}")
        self.btn.config(text="Retry", state=tk.NORMAL, command=self._start)

def main():
    if is_installed():
        launch_main()
        return
    root = tk.Tk()
    InstallerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
