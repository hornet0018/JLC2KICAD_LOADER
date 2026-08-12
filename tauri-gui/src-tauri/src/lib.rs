use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::Emitter;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;

#[derive(Serialize, Deserialize, Clone, Debug, Default)]
pub struct AppConfig {
    pub directories: Vec<String>,
    pub symbol_lib: String,
    pub footprint_lib: String,
    pub symbol_lib_dir: String,
    pub model_dir: String,
    pub model_base_variable: String,
    pub create_footprint: bool,
    pub create_symbol: bool,
    pub models: String,
    pub skip_existing: bool,
    pub add_to_all: bool,
}

fn app_config_dir() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| std::env::temp_dir())
        .join("JLC2KiCadLib")
}

fn config_file_path() -> PathBuf {
    app_config_dir().join("tauri-gui.json")
}

#[tauri::command]
fn load_config() -> Result<AppConfig, String> {
    let path = config_file_path();
    if !path.exists() {
        return Ok(AppConfig::default());
    }
    let content = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let config: AppConfig = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    Ok(config)
}

#[tauri::command]
fn save_config(config: AppConfig) -> Result<(), String> {
    let dir = app_config_dir();
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let path = config_file_path();
    let content = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    std::fs::write(&path, content).map_err(|e| e.to_string())?;
    Ok(())
}

/// Find the bundled sidecar executable.
/// In release builds Tauri renames it to `<name>.exe` next to the app binary.
/// In development we look in `src-tauri/binaries` using the target triple.
fn find_sidecar_path() -> Option<PathBuf> {
    #[cfg(debug_assertions)]
    {
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let dev_candidate = manifest_dir
            .join("binaries")
            .join("jlc2kicadlib-helper-x86_64-pc-windows-msvc.exe");
        if dev_candidate.exists() {
            return Some(dev_candidate);
        }
    }

    let exe_path = std::env::current_exe().ok()?;
    let exe_dir = exe_path.parent()?;
    let release_candidate = exe_dir.join(if cfg!(windows) {
        "jlc2kicadlib-helper.exe"
    } else {
        "jlc2kicadlib-helper"
    });
    if release_candidate.exists() {
        return Some(release_candidate);
    }
    None
}

/// Development fallback: find the repository root by walking up from the
/// executable location looking for `pyproject.toml`.
fn find_project_root() -> Option<PathBuf> {
    let exe_path = std::env::current_exe().ok()?;
    let mut dir = exe_path.parent()?;
    loop {
        if dir.join("pyproject.toml").exists() {
            return Some(dir.to_path_buf());
        }
        match dir.parent() {
            Some(parent) => dir = parent,
            None => break,
        }
    }
    None
}

async fn command_exists(name: &str) -> bool {
    Command::new(if cfg!(windows) { "where" } else { "which" })
        .arg(name)
        .output()
        .await
        .map(|output| output.status.success())
        .unwrap_or(false)
}

fn emit_log<R: tauri::Runtime>(window: &tauri::Window<R>, message: String) {
    let _ = window.emit("log-message", message);
}

fn emit_status<R: tauri::Runtime>(window: &tauri::Window<R>, message: String) {
    let _ = window.emit("status-message", message);
}

#[tauri::command]
async fn add_components(
    window: tauri::Window,
    config: AppConfig,
    parts: Vec<String>,
    target_dirs: Vec<String>,
) -> Result<(), String> {
    if parts.is_empty() {
        return Err("No part numbers provided".to_string());
    }
    if target_dirs.is_empty() {
        return Err("No target directories provided".to_string());
    }

    // Prefer the bundled sidecar; fall back to system Python/uv in development.
    let sidecar_path = find_sidecar_path();
    let project_root = find_project_root();
    let has_uv = command_exists("uv").await;

    for directory in target_dirs {
        emit_status(&window, format!("Processing directory: {}", directory));
        emit_log(&window, format!("Processing directory: {}", directory));

        let (program, mut cmd, work_dir): (String, Command, PathBuf) =
            if let Some(ref sidecar) = sidecar_path {
                let mut c = Command::new(sidecar);
                c.current_dir(&directory);
                (sidecar.display().to_string(), c, PathBuf::from(&directory))
            } else if has_uv {
                let root = project_root.clone().ok_or_else(|| {
                    "Could not locate project root (pyproject.toml) and no bundled sidecar was found.".to_string()
                })?;
                let mut c = Command::new("uv");
                c.arg("run");
                c.arg("--");
                c.arg("python");
                c.arg("-m");
                c.arg("JLC2KiCadLib");
                c.current_dir(&root);
                ("uv".to_string(), c, root)
            } else {
                let mut c = Command::new("JLC2KiCadLib");
                c.current_dir(&directory);
                ("JLC2KiCadLib".to_string(), c, PathBuf::from(&directory))
            };

        for part in &parts {
            cmd.arg(part);
        }

        cmd.arg("-dir").arg(&directory);

        if !config.symbol_lib.is_empty() {
            cmd.arg("-symbol_lib").arg(&config.symbol_lib);
        }

        cmd.arg("-footprint_lib").arg(
            config
                .footprint_lib
                .clone()
                .is_empty()
                .then(|| "footprint".to_string())
                .unwrap_or_else(|| config.footprint_lib.clone()),
        );
        cmd.arg("-symbol_lib_dir").arg(
            config
                .symbol_lib_dir
                .clone()
                .is_empty()
                .then(|| "symbol".to_string())
                .unwrap_or_else(|| config.symbol_lib_dir.clone()),
        );
        cmd.arg("-model_dir").arg(
            config
                .model_dir
                .clone()
                .is_empty()
                .then(|| "packages3d".to_string())
                .unwrap_or_else(|| config.model_dir.clone()),
        );

        if !config.model_base_variable.is_empty() {
            cmd.arg("-model_base_variable").arg(&config.model_base_variable);
        }

        if config.skip_existing {
            cmd.arg("--skip_existing");
        }

        if !config.create_footprint {
            cmd.arg("--no_footprint");
        }

        if !config.create_symbol {
            cmd.arg("--no_symbol");
        }

        match config.models.as_str() {
            "STEP" => {
                cmd.arg("-models").arg("STEP");
            }
            "WRL" => {
                cmd.arg("-models").arg("WRL");
            }
            "Both" => {
                cmd.arg("-models").arg("STEP").arg("WRL");
            }
            "None" => {
                cmd.arg("--models");
            }
            _ => {}
        }

        let args: Vec<String> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_string_lossy().to_string())
            .collect();
        emit_log(
            &window,
            format!(
                "Running in {}: {} {}",
                work_dir.display(),
                program,
                args.join(" ")
            ),
        );

        let mut child = cmd
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start JLC2KiCadLib: {}", e))?;

        let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
        let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;

        let stdout_reader = BufReader::new(stdout);
        let stderr_reader = BufReader::new(stderr);

        let window_stdout = window.clone();
        let stdout_handle = tokio::spawn(async move {
            let mut lines = stdout_reader.lines();
            while let Ok(Some(line)) = lines.next_line().await {
                emit_log(&window_stdout, line);
            }
        });

        let window_stderr = window.clone();
        let stderr_handle = tokio::spawn(async move {
            let mut lines = stderr_reader.lines();
            while let Ok(Some(line)) = lines.next_line().await {
                emit_log(&window_stderr, line);
            }
        });

        let status = child
            .wait()
            .await
            .map_err(|e| format!("Failed to wait for JLC2KiCadLib: {}", e))?;

        let _ = stdout_handle.await;
        let _ = stderr_handle.await;

        if !status.success() {
            return Err(format!(
                "JLC2KiCadLib exited with status {} for directory {}",
                status
                    .code()
                    .map(|c| c.to_string())
                    .unwrap_or_else(|| "unknown".to_string()),
                directory
            ));
        }
    }

    emit_status(&window, "Finished".to_string());
    emit_log(&window, "All components processed successfully.".to_string());
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            load_config,
            save_config,
            add_components
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
