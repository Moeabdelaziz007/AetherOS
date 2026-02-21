// 🔌 The Optic Nerve: Rust-Python Synaptic Bridge
// Version: 0.1.0
// Pillar: HyperMind (Perception)

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{AppHandle, Manager};
use tokio::sync::mpsc;
use futures_util::{StreamExt, SinkExt};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct BrainCommand {
    cmd: String,
    pillar: Option<String>,
    action: Option<String>,
    params: Option<serde_json::Value>,
}

struct SynapticBridge {
    tx: mpsc::UnboundedSender<Message>,
}

#[tauri::command]
async fn stream_sensory_data(state: tauri::State<'_, SynapticBridge>, data: Vec<u8>) -> Result<(), String> {
    // Send binary sensory data (Optic/Aural)
    state.tx.send(Message::Binary(data)).map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let (tx, mut rx) = mpsc::unbounded_channel::<Message>();
            
            // Register Synaptic Bridge State
            app.manage(SynapticBridge { tx });

            let handle = app.handle().clone();

            // Spawn the Optic Nerve (Async WebSocket Task)
            tauri::async_runtime::spawn(async move {
                let addr = "ws://127.0.0.1:8000";
                println!("🛰️ AuraOS: Establishing Synaptic Bridge to {}...", addr);

                loop {
                    match connect_async(addr).await {
                        Ok((mut ws_stream, _)) => {
                            println!("✅ Synaptic Bridge: ONLINE.");
                            
                            loop {
                                tokio::select! {
                                    // Send messages from Rust to Python
                                    Some(msg) = rx.recv() => {
                                        if let Err(e) = ws_stream.send(msg).await {
                                            eprintln!("⚠️ Synaptic Error: {}", e);
                                            break;
                                        }
                                    }
                                    // Receive commands from Python Brain
                                    Some(Ok(msg)) = ws_stream.next() => {
                                        if let Message::Text(text) = msg {
                                            if let Ok(cmd) = serde_json::from_str::<BrainCommand>(&text) {
                                                println!("🧠 Brain Command: {:?}", cmd.cmd);
                                                // Handle commands (Veto, Action, etc.)
                                                handle.emit("brain-signal", cmd).unwrap();
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Err(e) => {
                            eprintln!("❌ Synaptic Bridge: OFFLINE ({}). Retrying in 5s...", e);
                            tokio::time::sleep(Duration::from_secs(5)).await;
                        }
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![stream_sensory_data])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
