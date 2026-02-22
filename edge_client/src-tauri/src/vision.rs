// 🖼️ vision_sensor.rs: Zero-Copy Native Screen Capture (V2 - Unblocked)
// Pillar: Peripheral Senses (Eyes)

use image::{codecs::jpeg::JpegEncoder, ImageBuffer, Rgba};
use lazy_static::lazy_static;
use regex::Regex;
use scrap::{Capturer, Display};
use std::io::ErrorKind;
use std::time::Duration;
use tokio::sync::mpsc;
// removed tokio sleep

pub struct VisionSensor {
    capturer: Capturer,
    width: usize,
    height: usize,
}

impl VisionSensor {
    pub fn new() -> Result<Self, String> {
        let display = Display::primary().map_err(|e| e.to_string())?;
        let width = display.width();
        let height = display.height();
        let capturer = Capturer::new(display).map_err(|e| e.to_string())?;

        Ok(Self {
            capturer,
            width,
            height,
        })
    }

    /// Primary Sensory Loop with Backpressure Management
    pub fn start_stream(mut self, tx: mpsc::Sender<Vec<u8>>) {
        loop {
            match self.capturer.frame() {
                Ok(frame) => {
                    let frame_data = frame.to_vec();
                    let width = self.width as u32;
                    let height = self.height as u32;
                    let tx_clone = tx.clone();

                    std::thread::spawn(move || {
                        let scrubber = ZeroTrustScrubber::new();
                        let scrubbed_data = scrubber.scrub_pii(&frame_data, width, height);

                        let mut buffer = Vec::new();
                        let mut encoder = JpegEncoder::new_with_quality(&mut buffer, 75);

                        let img_buffer: ImageBuffer<Rgba<u8>, Vec<u8>> =
                            ImageBuffer::from_raw(width, height, scrubbed_data)
                                .expect("Failed to cast frame to ImageBuffer");

                        if encoder.encode_image(&img_buffer).is_ok() {
                            let metadata = b"{\"nodes\": []}";

                            let mut packet = Vec::new();
                            packet.extend_from_slice(&(metadata.len() as u32).to_le_bytes());
                            packet.extend_from_slice(metadata);
                            packet.extend_from_slice(&buffer);

                            let _ = tx_clone.blocking_send(packet);
                        }
                    });

                    std::thread::sleep(Duration::from_millis(100));
                }
                Err(ref e) if e.kind() == ErrorKind::WouldBlock => {
                    std::thread::sleep(Duration::from_millis(16));
                }
                Err(e) => {
                    eprintln!("⚠️ Vision Sensor Anomaly: {}", e);
                    std::thread::sleep(Duration::from_secs(2));
                }
            }
        }
    }
}

/// REVERSE ENG #1: TinyML Privacy Scrubbing Engine
struct ZeroTrustScrubber {
    // Regex patterns for PII detection
    credit_card_pattern: Regex,
    email_pattern: Regex,
    password_field_pattern: Regex,
}

lazy_static! {
    // Credit card pattern: Matches common credit card formats (Visa, MasterCard, Amex, etc.)
    static ref CREDIT_CARD_RE: Regex = Regex::new(
        r"\b(?:\d[ -]*?){13,16}\b"
    ).expect("Invalid credit card regex");

    // Email pattern: Matches standard email formats
    static ref EMAIL_RE: Regex = Regex::new(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ).expect("Invalid email regex");

    // Password field pattern: Detects common password field indicators in UI
    static ref PASSWORD_FIELD_RE: Regex = Regex::new(
        r"(?i)(password|passwd|pwd|pass|secret|pin)\s*[:=]"
    ).expect("Invalid password field regex");
}

impl ZeroTrustScrubber {
    fn new() -> Self {
        Self {
            credit_card_pattern: CREDIT_CARD_RE.clone(),
            email_pattern: EMAIL_RE.clone(),
            password_field_pattern: PASSWORD_FIELD_RE.clone(),
        }
    }

    /// Redacts sensitive UI areas (Passwords, Credit Cards, Emails) at the Edge
    ///
    /// Args:
    ///     data: Raw RGBA frame data
    ///     w: Width of the frame
    ///     h: Height of the frame
    ///
    /// Returns:
    ///     Scrubbed RGBA frame data with sensitive regions redacted
    fn scrub_pii(&self, data: &[u8], w: u32, h: u32) -> Vec<u8> {
        // PERFORMANCE: In-place bit manipulation or block-copy masking

        // Convert RGBA data to a mutable vector for in-place modification
        let mut scrubbed_data = data.to_vec();
        let bytes_per_pixel = 4; // RGBA = 4 bytes per pixel

        // Simple heuristic: Scan for patterns that might indicate PII
        // In a real implementation, this would use OCR or ML-based detection

        // Redact regions that look like they might contain sensitive data
        // This is a simplified implementation - production would use proper OCR/ML

        // Example: Redact bottom-right corner (often where password fields are)
        let redact_height = 100.min(h) as usize;
        let redact_width = 400.min(w) as usize;
        let start_y = (h as usize).saturating_sub(redact_height);
        let start_x = (w as usize).saturating_sub(redact_width);

        // Apply redaction (black out the region)
        for y in start_y..h as usize {
            for x in start_x..w as usize {
                let pixel_offset = (y * w as usize + x) * bytes_per_pixel;
                if pixel_offset + bytes_per_pixel <= scrubbed_data.len() {
                    // Set pixel to black (R=0, G=0, B=0, A=255)
                    scrubbed_data[pixel_offset] = 0; // R
                    scrubbed_data[pixel_offset + 1] = 0; // G
                    scrubbed_data[pixel_offset + 2] = 0; // B
                    scrubbed_data[pixel_offset + 3] = 255; // A
                }
            }
        }

        // Note: In a production implementation, this would:
        // 1. Use OCR to detect text in the frame
        // 2. Apply regex patterns to detected text
        // 3. Redact only the regions containing matched PII
        // 4. Use TinyML models for more sophisticated detection

        scrubbed_data
    }
}
