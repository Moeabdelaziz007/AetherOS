// 🖼️ vision_sensor.rs: Zero-Copy Native Screen Capture
// Pillar: Peripheral Senses (Eyes)
// OS: macOS (using scrap/CoreGraphics)

use scrap::{Display, Capturer};
use std::io::ErrorKind;
use std::time::Duration;
use tokio::time::sleep;
use image::{ImageBuffer, Rgba, codeck::jpeg::JpegEncoder};
use std::io::Cursor;

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

    pub async fn capture_frame_compressed(&mut self) -> Result<Vec<u8>, String> {
        loop {
            match self.capturer.frame() {
                Ok(frame) => {
                    // Vision: Zero-Copy Buffer Access
                    // frame is a Frame object wrapping the raw pixel data.
                    // On macOS, it's usually BGRA or RGBA.
                    
                    let mut buffer = Vec::new();
                    let mut encoder = JpegEncoder::new_with_quality(&mut buffer, 75);
                    
                    // Convert raw frame to ImageBuffer for compression
                    // Wrap existing slice without deep copy if possible, but JpegEncoder needs a slice.
                    // scrap's frame derefs to [u8].
                    
                    let img_buffer: ImageBuffer<Rgba<u8>, &[u8]> = 
                        ImageBuffer::from_raw(self.width as u32, self.height as u32, &*frame)
                        .ok_or("Failed to create image buffer")?;

                    encoder.encode_image(&img_buffer).map_err(|e| e.to_string())?;
                    
                    return Ok(buffer);
                }
                Err(ref e) if e.kind() == ErrorKind::WouldBlock => {
                    // Wait for the next VSync/Frame match
                    sleep(Duration::from_millis(16)).await;
                    continue;
                }
                Err(e) => return Err(e.to_string()),
            }
        }
    }
}
