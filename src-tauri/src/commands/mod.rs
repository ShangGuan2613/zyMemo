use tauri::State;

use crate::data::{Repository, SqliteRepository};
use crate::models::{Annotation, MediaItem, Message, PhotoContext, Slice};

/// All Tauri commands the frontend can call.
/// These should stay very thin — they just delegate to the repository.

#[tauri::command]
pub fn get_slices(repo: State<SqliteRepository>) -> Vec<Slice> {
    repo.get_slices()
}

#[tauri::command]
pub fn get_messages_by_slice(repo: State<SqliteRepository>, slice_id: String) -> Vec<Message> {
    repo.get_messages_by_slice(&slice_id)
}

#[tauri::command]
pub fn get_media_by_slice(repo: State<SqliteRepository>, slice_id: String) -> Vec<MediaItem> {
    repo.get_media_by_slice(&slice_id)
}

#[tauri::command]
pub fn get_media_by_type(repo: State<SqliteRepository>, media_type: String) -> Vec<MediaItem> {
    repo.get_media_by_type(&media_type)
}

#[tauri::command]
pub fn get_annotations_for_slice(repo: State<SqliteRepository>, slice_id: String) -> Vec<Annotation> {
    repo.get_annotations_for_slice(&slice_id)
}

#[tauri::command]
pub fn save_annotation(repo: State<SqliteRepository>, annotation: Annotation) {
    repo.save_annotation(annotation);
}

#[tauri::command]
pub fn delete_annotation(repo: State<SqliteRepository>, id: String) {
    repo.delete_annotation(&id);
}

#[tauri::command]
pub fn get_photo_contexts(repo: State<SqliteRepository>, emotion: Option<String>) -> Vec<PhotoContext> {
    repo.get_photo_contexts(emotion.as_deref())
}
