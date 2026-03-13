# CorridorKey_MacOS
An executable App with GUI for MacOS (Silicons) using CorridorKey
CorridorKey GUI
Neural Green Screen Keying for Apple Silicon
User Guide, System Requirements & Developer Notes

1. What is CorridorKey?
CorridorKey is a neural network-based green screen keyer developed by Corridor Crew. Unlike traditional color-based keyers, it uses a deep learning model to physically reconstruct the real colors of the subject pixel by pixel, producing cleaner edges, accurate despill, and better handling of fine detail like hair.

This GUI was built as a companion application to make CorridorKey accessible without using the command line. It provides a dark-themed interface with drag-and-drop support, real-time progress tracking, bilingual support (English/Spanish), and automatic output management.

How it differs from traditional keyers
•	Traditional keyers (like those in DaVinci Resolve or Premiere) work by selecting a color range and making it transparent.
•	CorridorKey uses a trained neural network to understand the scene and reconstruct foreground colors as they would look without the green screen.
•	The result is more accurate color reconstruction, better edge detail, and physically correct despill.
•	The trade-off: it requires an Alpha Hint (rough mask) as input, and processing time is significantly longer than a real-time keyer.



2. System Requirements

Requirement	Details
Mac chip	Apple Silicon — M1, M2, M3, or M4 (Intel Macs are NOT supported)
RAM	Minimum 24 GB unified memory. 36 GB recommended for larger clips.
macOS	macOS 12 Monterey or later
Storage	At least 5 GB free space (for the Python environment, dependencies, and AI model)
Internet	Required for first-time installation (~400 MB download)
Git	Must be installed. On first run, macOS will prompt to install Xcode Command Line Tools if needed.

Note: The app uses the MPS (Metal Performance Shaders) backend on Apple Silicon, which is why Intel Macs are not supported. The neural network model requires approximately 22–30 GB of unified memory during inference.

3. Installation
First-time setup
The app includes an automatic installer. On first launch, a Terminal window will open and walk through the following steps automatically:

1.	Installs uv (a fast Python package manager)
2.	Clones the CorridorKey repository from GitHub
3.	Installs all Python dependencies (PyTorch, OpenCV, MLX, etc.)
4.	Installs the MLX backend for Apple Silicon
5.	Downloads the AI model checkpoint (~382 MB from Hugging Face)
6.	Copies the GUI into the installation directory

This process takes approximately 10–15 minutes depending on your internet connection. It only happens once. On subsequent launches, the app opens directly to the main interface.

Installation paths
Everything is installed under your home directory:
~/CorridorKey/                          ← Main repository
~/CorridorKey/.venv/                    ← Python virtual environment
~/CorridorKey/CorridorKeyModule/checkpoints/CorridorKey.pth  ← AI model
~/CorridorKey/corridorkey_gui.py         ← GUI script
~/.local/bin/uv                          ← uv package manager

4. Workflow
What you need before processing
CorridorKey requires two inputs for every clip:

•	Green screen video — your original footage shot in front of a green screen.
•	Alpha Hint — a rough, imprecise mask of your subject. It does not need to be clean; it just needs to indicate where the subject is in the frame.

The Alpha Hint is necessary because CorridorKey does not detect green — it reconstructs foreground colors. It needs to know where the subject is before it can do this reconstruction.

How to create an Alpha Hint
The easiest way is to do a quick, rough chroma key in DaVinci Resolve:
7.	Import your green screen clip into DaVinci Resolve.
8.	Apply a Qualifier (chroma key) — it does not need to be perfect.
9.	Export the result as a black-and-white video (subject white, background black).
10.	Use this exported video as the Alpha Hint in CorridorKey.

Other tools like CapCut, Final Cut Pro, or Premiere Pro can also work for this step. The key point is that the mask only needs to be approximate.

Step-by-step processing
11.	Launch CorridorKey.app from your Desktop.
12.	Section ① INPUT FILES: Click Browse next to “Green screen video” and select your footage.
13.	Click Browse next to “Alpha Hint”. When prompted, select whether it is a video file or a folder of image sequences.
14.	Click Browse next to “Output folder” and choose where the results should be saved.
15.	Section ② SETTINGS: Adjust parameters as needed (see Settings section below).
16.	Click ▶ PROCESS. The button turns red and shows ■ CANCEL.
17.	Section ③ PROGRESS: A progress bar and frame counter show real-time status.
18.	When complete, click 📁 View Results to open the output folder in Finder.

5. Settings

Color Space (Gamma)
sRGB (default) — use this for standard footage from most cameras.
Linear — use this if your footage is already in a linear color space (e.g., some BRAW or RAW formats).

Despill (0–10)
Controls how aggressively green contamination is removed from the edges and semi-transparent areas of the subject. A value of 5 is a good starting point. Increase for heavy green spill, decrease if the subject looks too desaturated.

Auto-despeckle
When enabled, removes small isolated artifacts (tracking markers, noise pixels) from the alpha channel. Recommended for most footage.

Refiner (0.5–2.0)
Controls the strength of the edge refinement pass. Higher values produce cleaner edges but may over-process fine detail like hair. The default value of 1.0 is suitable for most cases.

Export PNG
When enabled, after processing is complete the app will convert all EXR output files to PNG. The original EXR files are kept. PNG folders are created alongside the EXR folders with a _PNG suffix.

6. Output Files
CorridorKey generates four types of output, organized in subfolders:

Requirement	Details
Matte/	Alpha channel as EXR. White = opaque foreground, black = transparent background. Use this in Resolve as a matte/mask.
FG/	Foreground color reconstruction as EXR. The subject colors with green removed and physically reconstructed.
Processed/	RGBA premultiplied composite as EXR. Subject with alpha channel, ready for compositing.
Comp/	Preview composite as PNG. Subject composited over a checkerboard pattern for quick review.

EXR files are 32-bit floating point and preserve full dynamic range. They are the recommended format for compositing in DaVinci Resolve. If you need PNG files for other applications, enable the Export PNG option in Settings.

Importing into DaVinci Resolve
19.	Import the Processed/ folder (or Matte/ folder) into your media pool.
20.	Resolve will recognize the EXR sequence automatically.
21.	Place the sequence on your timeline above the background plate.
22.	The alpha channel is embedded in the Processed/ EXR files — no additional keying needed.


7. Developer Notes
This section documents the development process, technical decisions, and issues encountered while building the GUI. It may be useful for anyone contributing to or extending this project.

Architecture
The GUI is a single-file Python tkinter application (corridorkey_gui.py). It was chosen over frameworks like PyQt or wxPython because tkinter is included with Python and requires no additional dependencies, keeping the installation footprint small.

•	Language: Python 3.14
•	UI framework: tkinter with ttk widgets
•	Theme: Custom dark theme (#141414 background, #F5C518 accent)
•	Process management: subprocess.Popen with start_new_session=True
•	Progress tracking: background thread counting EXR files in Output/Matte/
•	File operations: symlinks instead of file copies to avoid duplicating large video files

Key technical decisions
Backend: torch instead of MLX
The repository ships with two inference backends: torch (PyTorch) and mlx (Apple MLX framework). The MLX backend requires the model in .safetensors format, but the publicly available model checkpoint is .pth (PyTorch format). The GUI uses the torch backend, which loads the .pth file correctly and still uses MPS (Metal) acceleration on Apple Silicon.
Symlinks instead of file copies
CorridorKey requires its input files to be placed in a specific folder structure inside ClipsForInference/. The original implementation copied files there, which duplicated large video files on disk. The GUI now creates symlinks pointing to the original files, saving storage space.
Frame count mismatch handling
CorridorKey strictly requires that the input video and Alpha Hint have exactly the same number of frames. A mismatch of even one frame causes the clip to be rejected. The GUI automatically detects the frame count of both files and passes --max-frames with the minimum of the two, preventing this error.
Progress tracking via file counting
The CorridorKey CLI does not emit per-frame progress to stdout when called with flags. Instead, the GUI monitors the Output/Matte/ folder in a background thread and counts the number of .exr files created. This provides an accurate real-time frame counter and percentage bar.
Process termination
When the user clicks Cancel, the GUI uses os.killpg() to send SIGKILL to the entire process group (not just the parent process). This is necessary because CorridorKey spawns child processes that hold the GPU memory. Without killing the process group, Python would continue consuming 22-30 GB of RAM even after the parent was terminated.

Known issues and workarounds
AVFFrameReceiver warnings
Two harmless warnings appear in the terminal when the app runs: “Class AVFFrameReceiver is implemented in both...”. This is caused by a conflict between cv2 and PyAV both bundling their own version of libavdevice. It does not affect functionality and can be ignored.
tkinterdnd2 incompatibility
The tkinterdnd2 library (which enables drag-and-drop file support) is not compatible with Python 3.14 / Tcl 9. The library installs without errors but crashes when creating the window. The GUI falls back gracefully to standard Browse dialogs when drag-and-drop is unavailable.
OpenCV cannot read EXR files
The OpenCV build bundled with the Python package has the OpenEXR codec disabled. Reading EXR files via cv2.imread() returns None silently. The solution is to use imageio instead, which reads EXR files correctly via OpenEXR bindings. The OPENCV_IO_ENABLE_OPENEXR environment variable is set at startup but has no effect on this build.
Memory release after inference
PyTorch holds onto GPU memory even after inference is complete. The GUI explicitly calls torch.mps.empty_cache() after processing finishes, which releases the memory back to the system without requiring the user to close the app.

8. Troubleshooting

Requirement	Details
App does not open on first launch	Make sure Git is installed. Open Terminal and run: git --version. If not installed, macOS will prompt you to install Xcode Command Line Tools.
Invalid or Skipped Clips error	The most common cause is a frame count mismatch between the video and Alpha Hint. Make sure both files have the same duration. The GUI handles this automatically from version 1.0.
Process hangs at 0%	Check Activity Monitor for a python3.14 process using CPU. If the process exists but does not make progress, click Cancel and try again. If it does not exist, check that your output folder path is valid.
No EXR files generated	The app needs write permission to the output folder. Try choosing a folder inside your home directory (e.g., ~/Movies/CorridorKey).
Mac slows down during processing	Normal. The model uses 22–30 GB of unified memory during inference. Avoid running other memory-intensive apps simultaneously.
PNG conversion fails	Make sure imageio is installed. Run in Terminal: cd ~/CorridorKey && uv pip install imageio
Stale processes after force-quit	If the app was force-quit, run: pkill -f corridorkey_cli.py

9. Contributing
This GUI was developed as a community contribution to the CorridorKey project. If you want to contribute improvements:

23.	Fork the CorridorKey repository on GitHub: https://github.com/nikopueringer/CorridorKey
24.	Add corridorkey_gui.py and corridorkey_installer.py to the root of the repository.
25.	Open a Pull Request with a description of what the GUI does and how to use it.

The GUI files are self-contained and do not modify any existing CorridorKey files. They can be added to the repository without breaking the existing CLI workflow.

10. Credits

•	CorridorKey neural network model and CLI: Niko Pueringer / Corridor Digital
•	GUI application: developed with the assistance of Claude (Anthropic)
•	MLX backend for Apple Silicon: nikopueringer/corridorkey-mlx
•	AI model weights: hosted on Hugging Face (nikopueringer/CorridorKey_v1.0)


CorridorKey GUI v1.0 — March 2026
