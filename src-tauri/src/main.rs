// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod data;
mod models;

use std::path::PathBuf;

use data::SqliteRepository;

fn get_database_path() -> PathBuf {
    // Dev override: allow pointing to a real data DB for testing
    if let Ok(custom) = std::env::var("ZYMEMO_DB_PATH") {
        println!("[zyMemo] Using custom DB path from ZYMEMO_DB_PATH: {}", custom);
        return PathBuf::from(custom);
    }

    // Robust discovery for real data (优先 zy_memo_real.db)
    // Tries several locations because Tauri dev can spawn the binary with different cwd/exe paths.
    let candidates = [
        // 1. Next to current working directory (most common for `pnpm tauri dev`)
        std::env::current_dir().unwrap_or_default().join("data").join("zy_memo_real.db"),
        // 2. Next to the executable (for built binaries + U盘便携)
        std::env::current_exe()
            .ok()
            .and_then(|exe| exe.parent().map(|p| p.to_path_buf()))
            .unwrap_or_default()
            .join("data")
            .join("zy_memo_real.db"),
        // 3. One level up from cwd (sometimes Tauri CLI changes dir)
        std::env::current_dir()
            .unwrap_or_default()
            .parent()
            .unwrap_or(&std::path::Path::new("."))
            .join("data")
            .join("zy_memo_real.db"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            println!("[zyMemo] Using real data DB: {}", candidate.display());
            return candidate.clone();
        }
    }

    // Final fallback: portable zy_memo.db next to exe (will be created/seeded if missing)
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|exe| exe.parent().map(|p| p.to_path_buf()))
        .unwrap_or_default();
    let data_dir = exe_dir.join("data");
    std::fs::create_dir_all(&data_dir).ok();
    let fallback = data_dir.join("zy_memo.db");
    println!("[zyMemo] Using fallback DB: {}", fallback.display());
    fallback
}

fn main() {
    let db_path = get_database_path();
    let sqlite_repo = SqliteRepository::new(db_path).expect("Failed to open SQLite database");

    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .manage(sqlite_repo)
        .invoke_handler(tauri::generate_handler![
            commands::get_slices,
            commands::get_messages_by_slice,
            commands::get_media_by_slice,
            commands::get_media_by_type,
            commands::get_annotations_for_slice,
            commands::save_annotation,
            commands::delete_annotation,
            commands::get_photo_contexts,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
