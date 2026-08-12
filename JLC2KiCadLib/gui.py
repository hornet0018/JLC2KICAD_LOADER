import json
import logging
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from types import SimpleNamespace

from .JLC2KiCadLib import add_component

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".JLC2KiCadLib_gui.json")

MODEL_OPTIONS = {
    "STEP": ["STEP"],
    "WRL": ["WRL"],
    "Both": ["STEP", "WRL"],
    "None": [],
}


class QueueHandler(logging.Handler):
    """Logging handler that forwards records to a queue for thread-safe GUI display."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


class JLC2KiCadLibGUI:
    """Graphical interface for adding JLCPCB parts to registered KiCad libraries."""

    def __init__(self, root):
        self.root = root
        self.root.title("JLC2KiCadLib GUI")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        self.config = self.load_config()
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.build_ui()
        self.load_ui_from_config()
        self.poll_log_queue()

    def load_config(self):
        """Load saved GUI configuration or return defaults."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                logging.exception("Failed to load config")
        return {
            "directories": [],
            "symbol_lib": "",
            "footprint_lib": "footprint",
            "symbol_lib_dir": "symbol",
            "model_dir": "packages3d",
            "model_base_variable": "",
            "create_footprint": True,
            "create_symbol": True,
            "models": "STEP",
            "skip_existing": False,
            "add_to_all": False,
        }

    def save_config(self):
        """Persist current GUI settings to disk."""
        self.sync_config_from_ui()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            logging.exception("Failed to save config")

    def setup_logging(self):
        """Configure logging to write into the GUI log pane."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        handler = QueueHandler(self.log_queue)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(handler)

    def build_ui(self):
        """Build the Tkinter user interface."""
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            self.main_frame,
            text="JLC2KiCadLib - Add components to registered KiCad libraries",
            font=("Segoe UI", 12, "bold"),
        )
        title_label.pack(pady=(0, 10))

        paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # ---- Left panel: library settings ----
        left_frame = ttk.LabelFrame(paned, text="Library Settings", padding=10)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Registered Output Directories:").pack(
            anchor=tk.W, pady=(0, 5)
        )

        dir_list_frame = ttk.Frame(left_frame)
        dir_list_frame.pack(fill=tk.BOTH, expand=True)

        self.dir_listbox = tk.Listbox(dir_list_frame, selectmode=tk.EXTENDED)
        self.dir_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        dir_scroll = ttk.Scrollbar(
            dir_list_frame, orient=tk.VERTICAL, command=self.dir_listbox.yview
        )
        dir_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox.config(yscrollcommand=dir_scroll.set)

        dir_btn_frame = ttk.Frame(left_frame)
        dir_btn_frame.pack(fill=tk.X, pady=5)
        self.add_dir_btn = ttk.Button(
            dir_btn_frame, text="Add Directory", command=self.add_directory
        )
        self.add_dir_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.remove_dir_btn = ttk.Button(
            dir_btn_frame, text="Remove Selected", command=self.remove_directory
        )
        self.remove_dir_btn.pack(side=tk.LEFT)

        self.add_to_all_var = tk.BooleanVar(
            value=self.config.get("add_to_all", False)
        )
        ttk.Checkbutton(
            left_frame,
            text="Add to all registered directories",
            variable=self.add_to_all_var,
        ).pack(anchor=tk.W, pady=(0, 10))

        # Library names
        lib_frame = ttk.Frame(left_frame)
        lib_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lib_frame, text="Symbol Library:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.symbol_lib_var = tk.StringVar()
        ttk.Entry(lib_frame, textvariable=self.symbol_lib_var).grid(
            row=0, column=1, sticky=tk.EW, padx=5, pady=2
        )

        ttk.Label(lib_frame, text="Footprint Library:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.footprint_lib_var = tk.StringVar()
        ttk.Entry(lib_frame, textvariable=self.footprint_lib_var).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=2
        )

        ttk.Label(lib_frame, text="Symbol Dir:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.symbol_lib_dir_var = tk.StringVar()
        ttk.Entry(lib_frame, textvariable=self.symbol_lib_dir_var).grid(
            row=2, column=1, sticky=tk.EW, padx=5, pady=2
        )

        ttk.Label(lib_frame, text="Model Dir:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.model_dir_var = tk.StringVar()
        ttk.Entry(lib_frame, textvariable=self.model_dir_var).grid(
            row=3, column=1, sticky=tk.EW, padx=5, pady=2
        )

        ttk.Label(lib_frame, text="Model Base Var:").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.model_base_var_var = tk.StringVar()
        ttk.Entry(lib_frame, textvariable=self.model_base_var_var).grid(
            row=4, column=1, sticky=tk.EW, padx=5, pady=2
        )
        lib_frame.columnconfigure(1, weight=1)

        # Options
        options_frame = ttk.LabelFrame(left_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)

        self.create_footprint_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Create Footprint", variable=self.create_footprint_var
        ).pack(anchor=tk.W)
        self.create_symbol_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Create Symbol", variable=self.create_symbol_var
        ).pack(anchor=tk.W)
        self.skip_existing_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Skip Existing", variable=self.skip_existing_var
        ).pack(anchor=tk.W)

        ttk.Label(options_frame, text="3D Model:").pack(anchor=tk.W, pady=(5, 0))
        self.models_var = tk.StringVar()
        self.models_combo = ttk.Combobox(
            options_frame,
            textvariable=self.models_var,
            values=list(MODEL_OPTIONS.keys()),
            state="readonly",
        )
        self.models_combo.pack(fill=tk.X)

        # ---- Right panel: add components ----
        right_frame = ttk.LabelFrame(paned, text="Add Components", padding=10)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="JLCPCB Part Number(s):").pack(
            anchor=tk.W, pady=(0, 5)
        )
        self.part_entry = ttk.Entry(right_frame)
        self.part_entry.pack(fill=tk.X, pady=(0, 5))
        self.part_entry.bind("<Return>", lambda _event: self.on_add_components())

        self.add_btn = ttk.Button(
            right_frame, text="Add to Library", command=self.on_add_components
        )
        self.add_btn.pack(fill=tk.X, pady=(0, 10))

        self.progress = ttk.Progressbar(right_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # ---- Bottom: log pane ----
        log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, state="disabled", wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def load_ui_from_config(self):
        """Populate widgets from loaded configuration."""
        for directory in self.config.get("directories", []):
            self.dir_listbox.insert(tk.END, directory)
        self.symbol_lib_var.set(self.config.get("symbol_lib", ""))
        self.footprint_lib_var.set(self.config.get("footprint_lib", "footprint"))
        self.symbol_lib_dir_var.set(self.config.get("symbol_lib_dir", "symbol"))
        self.model_dir_var.set(self.config.get("model_dir", "packages3d"))
        self.model_base_var_var.set(self.config.get("model_base_variable", ""))
        self.create_footprint_var.set(self.config.get("create_footprint", True))
        self.create_symbol_var.set(self.config.get("create_symbol", True))
        self.skip_existing_var.set(self.config.get("skip_existing", False))
        models = self.config.get("models", "STEP")
        if models not in MODEL_OPTIONS:
            models = "STEP"
        self.models_var.set(models)

    def sync_config_from_ui(self):
        """Read widget values into the configuration dict."""
        self.config["directories"] = list(self.dir_listbox.get(0, tk.END))
        self.config["symbol_lib"] = self.symbol_lib_var.get()
        self.config["footprint_lib"] = self.footprint_lib_var.get()
        self.config["symbol_lib_dir"] = self.symbol_lib_dir_var.get()
        self.config["model_dir"] = self.model_dir_var.get()
        self.config["model_base_variable"] = self.model_base_var_var.get()
        self.config["create_footprint"] = self.create_footprint_var.get()
        self.config["create_symbol"] = self.create_symbol_var.get()
        self.config["skip_existing"] = self.skip_existing_var.get()
        self.config["models"] = self.models_var.get()
        self.config["add_to_all"] = self.add_to_all_var.get()

    def add_directory(self):
        """Register a new output directory via file dialog."""
        dir_path = filedialog.askdirectory()
        if not dir_path:
            return
        dir_path = os.path.normpath(dir_path)
        existing = self.dir_listbox.get(0, tk.END)
        if dir_path in existing:
            messagebox.showinfo("Info", "Directory is already registered.")
            return
        self.dir_listbox.insert(tk.END, dir_path)
        self.save_config()

    def remove_directory(self):
        """Remove selected directories from the registered list."""
        selection = self.dir_listbox.curselection()
        if not selection:
            return
        for index in reversed(selection):
            self.dir_listbox.delete(index)
        self.save_config()

    def get_target_directories(self):
        """Return the directories where components should be saved."""
        if self.add_to_all_var.get():
            return list(self.dir_listbox.get(0, tk.END))
        selection = self.dir_listbox.curselection()
        if selection:
            return [self.dir_listbox.get(i) for i in selection]
        dirs = self.dir_listbox.get(0, tk.END)
        if dirs:
            return [dirs[0]]
        return []

    def on_add_components(self):
        """Start adding the entered part number(s) to the target library(s)."""
        part_numbers = self.part_entry.get().strip()
        if not part_numbers:
            messagebox.showwarning("Warning", "Please enter part number(s).")
            return

        target_dirs = self.get_target_directories()
        if not target_dirs:
            messagebox.showwarning(
                "Warning", "Please register/select an output directory."
            )
            return

        parts = [
            p.strip() for p in part_numbers.replace(",", " ").split() if p.strip()
        ]
        self.sync_config_from_ui()
        self.save_config()

        self.add_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        options = SimpleNamespace(
            footprint_creation=self.create_footprint_var.get(),
            symbol_creation=self.create_symbol_var.get(),
            footprint_lib=self.footprint_lib_var.get() or "footprint",
            symbol_lib=self.symbol_lib_var.get() or None,
            symbol_lib_dir=self.symbol_lib_dir_var.get() or "symbol",
            model_dir=self.model_dir_var.get() or "packages3d",
            model_base_variable=self.model_base_var_var.get(),
            skip_existing=self.skip_existing_var.get(),
            models=MODEL_OPTIONS[self.models_var.get()],
        )

        def worker():
            try:
                for directory in target_dirs:
                    options.output_dir = directory
                    logging.info(f"Processing directory: {directory}")
                    for part in parts:
                        logging.info(f"Adding component {part} ...")
                        add_component(part, options)
            except Exception:
                logging.exception("Error while adding components")
            finally:
                self.root.after(0, self.on_add_finished)

        threading.Thread(target=worker, daemon=True).start()

    def on_add_finished(self):
        """Re-enable the UI after processing is complete."""
        self.add_btn.config(state=tk.NORMAL)
        self.progress.stop()

    def poll_log_queue(self):
        """Periodically drain the log queue into the on-screen log pane."""
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        self.root.after(100, self.poll_log_queue)

    def run(self):
        self.root.mainloop()


def main():
    root = tk.Tk()
    app = JLC2KiCadLibGUI(root)
    app.run()


if __name__ == "__main__":
    main()
