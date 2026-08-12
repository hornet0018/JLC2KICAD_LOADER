# JLC2KiCadLib

<p style="text-align: center;">

[![PyPI version](https://badge.fury.io/py/JLC2KiCadLib.svg)](https://badge.fury.io/py/JLC2KiCadLib)
![Python versions](https://img.shields.io/pypi/pyversions/JLC2KiCadLib.svg)
[![Downloads](https://pepy.tech/badge/jlc2kicadlib)](https://pepy.tech/project/jlc2kicadlib)
[![Code style: ruff](https://img.shields.io/badge/Linter-Ruff-D7FF64?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![Code style: ruff](https://img.shields.io/badge/Formatter-Ruff-D7FF64?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</p>

JLC2KiCadLib is a python script that generate a component library (symbol, footprint and 3D model) for KiCad from the JLCPCB/easyEDA library.
This script requires **Python 3.8** or higher.

## Example 



easyEDA origin | KiCad result
---- | ----
![JLCSymbol](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/JLC_Symbol_1.png) | ![KiCadSymbol](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/KiCad_Symbol_1.png)
![JLCFootprint](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/JLC_Footprint_1.png) | ![KiCadFootprint](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/KiCad_Footprint_1.png)
![JLC3Dmodel](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/JLC_3Dmodel.png) | ![KiCad3Dmodel](https://raw.githubusercontent.com/TousstNicolas/JLC2KiCad_lib/master/images/KiCad_3Dmodel.png)

## Installation

### From PyPI (recommended)

Install using pip:

```
pip install JLC2KiCadLib
```

This installs both the CLI (`JLC2KiCadLib`) and the Tkinter GUI (`JLC2KiCadLib-gui`). A separate Tauri-based desktop GUI is also available; see [Tauri desktop GUI](#tauri-desktop-gui) below.

### From source

```
git clone https://github.com/TousstNicolas/JLC2KiCad_lib.git
cd JLC2KiCad_lib
pip install .
```

Or with [uv](https://docs.astral.sh/uv/):

```
git clone https://github.com/TousstNicolas/JLC2KiCad_lib.git
cd JLC2KiCad_lib
uv pip install .
```

### From a local wheel

After building the package (see [Building](#building) below), install the generated wheel:

```
pip install dist/jlc2kicadlib-1.2.3-py3-none-any.whl
```

## Building

To build a distributable wheel and source distribution locally:

```
uv build
```

or with `build`:

```
python -m build
```

The resulting `.whl` and `.tar.gz` files will be placed in the `dist/` directory.

## Usage 

```
usage: JLC2KiCadLib [-h] [-dir OUTPUT_DIR] [--no_footprint] [--no_symbol] [-symbol_lib SYMBOL_LIB] [-footprint_lib FOOTPRINT_LIB]
                    [-models [{STEP,WRL} ...]] [--skip_existing] [-model_base_variable MODEL_BASE_VARIABLE]
                    [-logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log_file] [--version]
                    JLCPCB_part_# [JLCPCB_part_# ...]

take a JLCPCB part # and create the according component's kicad's library

positional arguments:
  JLCPCB_part_#         list of JLCPCB part # from the components you want to create

options:
  -h, --help            show this help message and exit
  -dir OUTPUT_DIR       base directory for output library files
  --no_footprint        use --no_footprint if you do not want to create the footprint
  --no_symbol           use --no_symbol if you do not want to create the symbol
  -symbol_lib SYMBOL_LIB
                        set symbol library name, default is "default_lib"
  -symbol_lib_dir SYMBOL_LIB_DIR
                        Set symbol library path, default is "symbol" (relative to OUTPUT_DIR)
  -footprint_lib FOOTPRINT_LIB
                        set footprint library name, default is "footprint"
  -models [{STEP,WRL} ...]
                        Select the 3D model you want to use. Default is STEP. 
                        If both are selected, only the STEP model will be added to the footprint (the WRL model will still be generated alongside the STEP model). 
                        If you do not want any model to be generated, use the --models without arguments
  -model_dir MODEL_DIR  Set directory for storing 3d models, default is "packages3d" (relative to FOOTPRINT_LIB)
  --skip_existing       use --skip_existing if you want do not want to replace already existing footprints and symbols
  -model_base_variable MODEL_BASE_VARIABLE
                        use -model_base_variable if you want to specify the base path of the 3D model using a path variable
  -logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set logging level. If DEBUG is used, the debug logs are only written in the log file if the option --log_file is set
  --log_file            use --log_file if you want logs to be written in a file
  --version             Print versin number and exit

exemple use : 
        JLC2KiCadLib C1337258 C24112 -dir My_lib -symbol_lib My_Symbol_lib --no_footprint
```

The only required arguments are the JLCPCP_part number (e.g. Cxxxxx)

Example usage : 
```
JLC2KiCadLib C1337258 C24112 -dir My_lib                       \
                             -model_dir My_model_dir           \
                             -footprint_lib My_footprint_lib   \
                             -symbol_lib_dir My_symbol_lib_dir \
                             -symbol_lib My_symbol_lib
```

This example will create the symbol, footprint and 3D model for the two components specified and will output the symbol in the `./My_lib/symbol/My_symbol_lib.lib` file, the footprint and 3D model will be created in the `./My_lib/Footprint`. This will result in the following tree to be created : 

```
My_lib
├── My_footprint_lib
│   ├── My_model_dir
│   │   ├── QFN-24_L4.0-W4.0-P0.50-BL-EP2.7.step
│   │   └── VQFN-48_L7.0-W7.0-P0.50-BL-EP5.5.step
│   ├── QFN-24_L4.0-W4.0-P0.50-BL-EP2.7.kicad_mod
│   └── VQFN-48_L7.0-W7.0-P0.50-BL-EP5.5.kicad_mod
└── My_symbol_lib_dir
    └── My_symbol_lib.kicad_sym
```

Most of those arguments are optional. The only required argument is the JLCPCB part #.

The JLCPCB part # is found in the part info section of every component in the JLCPCB part library.

By default, the library folder will be created in the execution directory. You can specify an absolute path with the -dir option.

## Tkinter GUI

A graphical interface is also available and is designed to feel like a part-library manager: register one or more KiCad library directories once, then add new JLCPCB part numbers to them with a single click.

After installation, launch the GUI with:

```
JLC2KiCadLib-gui
```

If you use [uv](https://docs.astral.sh/uv/), you can run the GUI directly without installing it globally:

```
uv run JLC2KiCadLib-gui
```

`uv` will automatically create/manage the virtual environment and install the project dependencies.

### How to use

1. Register directories: click **Add Directory** to register the root directories where you want KiCad libraries to be created or updated.
2. Configure library names: set the **Symbol Library**, **Footprint Library**, and optional subdirectory names (defaults follow the CLI defaults).
   - **Tip**: If you leave **Symbol Library** empty, each component may be saved into a separate `.kicad_sym` file named after the component. To keep all symbols in one library, set **Symbol Library** to a fixed name such as `JLC_Symbols`.
3. Choose options: enable/disable footprint/symbol creation, pick the 3D model format (STEP, WRL, Both, or None), and choose whether to skip existing components.
4. Enter part number(s): type one or more JLCPCB part numbers (e.g. `C1337258 C24112`) in the input field.
5. Click **Add to Library**: the components are downloaded from EasyEDA and saved to the selected directory(ies). The GUI stores your registered directories and settings automatically.

If **Add to all registered directories** is checked, the component is saved to every directory in the list. Otherwise, it is saved to the currently selected directories (or the first directory if none is selected).

## Tauri desktop GUI

A modern desktop GUI built with [Tauri](https://tauri.app/) is available in the `tauri-gui/` directory. It provides the same library-manager workflow as the Tkinter GUI but as a native desktop application with a web-based UI.

The Tauri build can produce a **standalone installer** that bundles the Python backend as a sidecar, so end users do not need to install Python or uv separately.

### Prerequisites

- [Rust](https://www.rust-lang.org/tools/install)
- [Node.js](https://nodejs.org/) (for the Tauri CLI)
- [uv](https://docs.astral.sh/uv/) (only for development / building the sidecar)

### Development

From the `tauri-gui` directory:

```
cd tauri-gui
npm install
npm run tauri dev
```

In development mode the app first looks for the bundled sidecar; if it has not been built yet, it falls back to `uv run python -m JLC2KiCadLib`.

### Build a standalone installer

1. Build the Python backend sidecar:

   Windows:
   ```
   cd tauri-gui
   npm run build:sidecar
   ```

   Linux/macOS:
   ```
   cd tauri-gui
   bash scripts/build-sidecar.sh
   ```

2. Build the Tauri app and installer bundles:

   ```
   cd tauri-gui
   npm run tauri build
   ```

   Or run both steps at once on Windows:

   ```
   npm run build:all
   ```

The output installers are placed in `tauri-gui/src-tauri/target/release/bundle/` (e.g. `.msi` and `.exe` on Windows).

### How the standalone installer works

The Python backend (`JLC2KiCadLib` + its dependencies) is packaged into a single executable using [PyInstaller](https://pyinstaller.org/) and shipped as a Tauri [sidecar](https://tauri.app/develop/resources/). The Tauri frontend spawns this executable to run the actual part downloads and library generation, so the installed app works without a separate Python environment.

### How to use

1. Register directories: click **Add Directory** to register the root directories where you want KiCad libraries to be created or updated.
2. Configure library names: set the **Symbol Library**, **Footprint Library**, and optional subdirectory names (defaults follow the CLI defaults).
   - **Tip**: If you leave **Symbol Library** empty, each component may be saved into a separate `.kicad_sym` file named after the component. To keep all symbols in one library, set **Symbol Library** to a fixed name such as `JLC_Symbols`.
3. Choose options: enable/disable footprint/symbol creation, pick the 3D model format (STEP, WRL, Both, or None), and choose whether to skip existing components.
4. Enter part number(s): type one or more JLCPCB part numbers (e.g. `C1337258 C24112`) in the input field.
5. Click **Add to Library**: the components are downloaded from EasyEDA and saved to the selected directory(ies). Progress and logs are shown in the bottom pane.

If **Add to all registered directories** is checked, the component is saved to every directory in the list. Otherwise, it is saved to the currently selected directories (or the first directory if none is selected).

## Adding the generated libraries to KiCad

After a component is created, the following files/folders are generated inside your output directory:

```
My_lib/
├── My_footprint_lib/
│   ├── My_model_dir/
│   │   ├── QFN-24_L4.0-W4.0-P0.50-BL-EP2.7.step
│   │   └── ...
│   ├── QFN-24_L4.0-W4.0-P0.50-BL-EP2.7.kicad_mod
│   └── ...
└── My_symbol_lib_dir/
    └── My_symbol_lib.kicad_sym
```

### Symbol library

1. Open **KiCad** → **Symbol Editor** (or the main project window).
2. Go to **Preferences** → **Symbol Library Manager**.
3. Click **Add existing library to table** (the folder icon with a `+`).
4. Browse to your output directory and select the `.kicad_sym` file, for example:
   `My_lib/My_symbol_lib_dir/My_symbol_lib.kicad_sym`
5. Set a **Nickname** (e.g. `JLC_Symbols`) and choose the scope:
   - **Global**: available in every KiCad project.
   - **Project**: available only in the current project.
6. Click OK.

#### Multiple `.kicad_sym` files

If you did not set a fixed `symbol_lib` name, JLC2KiCadLib creates one `.kicad_sym` file per component title. In that case, you have two options:

1. **Register each file individually**: In the Symbol Library Manager, repeat the steps above for every `.kicad_sym` file you want to use.
2. **Use a single shared library (recommended)**: Go back to the GUI/CLI, set `symbol_lib` (e.g. `JLC_Symbols`), and re-add the components. They will all be appended to the same `JLC_Symbols.kicad_sym` file, so you only need to register one library in KiCad.

### Footprint library

1. Open **KiCad** → **Footprint Editor** (or the main project window).
2. Go to **Preferences** → **Footprint Library Manager**.
3. Click **Add existing library to table**.
4. Browse to your output directory and select the `.pretty` folder, for example:
   `My_lib/My_footprint_lib/`
5. Set a **Nickname** (e.g. `JLC_Footprints`) and choose the scope.
6. Click OK.

### 3D models

If the footprint was generated with a 3D model, the footprint file already references the model using the configured `model_dir` path.

- If you did **not** use `model_base_variable`, make sure the generated `packages3d` folder is kept next to the `.pretty` folder (this is the default layout).
- If you used a `model_base_variable` (e.g. `KICAD_3D_MODELS`), go to **Preferences** → **Configure Paths** in KiCad and create an environment variable pointing to the folder that contains `packages3d`. The 3D model path inside the footprint is relative to that variable.

Once the libraries are added, you can place symbols from the **Choose Symbol** dialog and footprints from the **Footprint Assignment** dialog.

### Footprint and 3D model misalignment

JLC2KiCadLib tries to place the 3D model at the same origin as the footprint, but depending on the EasyEDA source data the model can still be offset or rotated.

If the 3D model does not line up with the footprint, try the following:

1. **Open the footprint in the Footprint Editor** and switch to the 3D viewer (Alt+3).
2. **Edit the model placement**:
   - Select the 3D model in the footprint tree or click it in the 3D view.
   - Open the model properties and adjust the **Position (X, Y, Z)** and **Rotation (X, Y, Z)** values until the model aligns with the pads.
   - Save the footprint.
3. **Check the model path**: Make sure the `.step`/`.wrl` file actually exists in the configured `model_dir`. If the file is missing, KiCad may still show a placeholder or nothing at all.
4. **Try a different model format**: Some components look better in STEP, others in WRL. Generate both with `-models STEP WRL` (or select **Both** in the GUI) and compare.
5. **Regenerate the component**: Delete the existing footprint and 3D model, then run JLC2KiCadLib again. EasyEDA data sometimes changes and a newer version may produce a better result.

If the offset is consistent across many components, it may be a bug in JLC2KiCadLib. In that case, please open an issue with the JLCPCB part number and a screenshot of the misalignment.

## Dependencies

JLC2KiCadLib relies on the [KicadModTree](https://gitlab.com/kicad/libraries/kicad-footprint-generator) framework to generate the footprints. 

## Notes

* Even so I tested the script on a lot of components, be careful and always check the output footprint and symbol.
* I consider this project completed. I will continue to maintain it if a bug report is filed, but I will not develop new functionality in the near future. If you feel that an important feature is missing, please open an issue to discuss it, then you can fork this project with a new branch before submitting a PR. 

## License 

Copyright © 2021 TousstNicolas 

The code is released under the MIT license
