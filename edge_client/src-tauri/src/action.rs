// 🦾 action.rs: OS-level UI Controller
// Pillar: AlphaMind (Execution)

use enigo::{Enigo, KeyboardControllable, MouseControllable};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct UIAction {
    pub action: String, // "CLICK", "TYPE", "SCROLL"
    pub x: Option<i32>,
    pub y: Option<i32>,
    pub text: Option<String>,
}

pub struct ActionExecutor {
    // Enigo is not thread-safe in all platforms, so we instantiate it when needed
}

impl ActionExecutor {
    pub fn execute(command: &UIAction) {
        let mut enigo = Enigo::new();

        match command.action.as_str() {
            "CLICK" => {
                if let (Some(x), Some(y)) = (command.x, command.y) {
                    println!("🖱️ Executing CLICK at ({}, {})", x, y);
                    enigo.mouse_move_to(x, y);
                    std::thread::sleep(std::time::Duration::from_millis(50));
                    enigo.mouse_click(enigo::MouseButton::Left);
                } else {
                    eprintln!("⚠️ CLICK action missing coordinates");
                }
            }
            "TYPE" => {
                if let Some(text) = &command.text {
                    println!("⌨️ Executing TYPE: '{}'", text);
                    enigo.key_sequence(text);
                } else {
                    eprintln!("⚠️ TYPE action missing text");
                }
            }
            "PRESS_ENTER" => {
                println!("⌨️ Executing PRESS_ENTER");
                enigo.key_click(enigo::Key::Return);
            }
            _ => {
                eprintln!("⚠️ Unknown UIAction: {}", command.action);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deserialize_click_action() {
        let json_payload = r#"{"action": "CLICK", "x": 1024, "y": 768}"#;
        let action: UIAction = serde_json::from_str(json_payload).unwrap();

        assert_eq!(action.action, "CLICK");
        assert_eq!(action.x, Some(1024));
        assert_eq!(action.y, Some(768));
        assert_eq!(action.text, None);
    }

    #[test]
    fn test_deserialize_type_action() {
        let json_payload = r#"{"action": "TYPE", "text": "AuraOS Devpost"}"#;
        let action: UIAction = serde_json::from_str(json_payload).unwrap();

        assert_eq!(action.action, "TYPE");
        assert_eq!(action.text, Some("AuraOS Devpost".to_string()));
        assert_eq!(action.x, None);
        assert_eq!(action.y, None);
    }

    #[test]
    fn test_deserialize_press_enter_action() {
        let json_payload = r#"{"action": "PRESS_ENTER"}"#;
        let action: UIAction = serde_json::from_str(json_payload).unwrap();

        assert_eq!(action.action, "PRESS_ENTER");
        assert_eq!(action.x, None);
        assert_eq!(action.y, None);
        assert_eq!(action.text, None);
    }
}
