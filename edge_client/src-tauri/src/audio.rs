// 🎤 audio_sensor.rs: Native Audio Capture with Edge-VAD
// Pillar: Peripheral Senses (Ears)

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;

pub struct AudioSensor {
    tx: mpsc::UnboundedSender<Vec<u8>>,
    threshold: f32,
}

impl AudioSensor {
    pub fn new(tx: mpsc::UnboundedSender<Vec<u8>>) -> Self {
        Self {
            tx,
            threshold: 0.01, // Baseline VAD threshold (adjust based on noise floor)
        }
    }

    pub fn start_capture(&self) -> Result<cpal::Stream, String> {
        let host = cpal::default_host();
        let device = host.default_input_device().ok_or("No input device found")?;
        let config: cpal::StreamConfig = device
            .default_input_config()
            .map_err(|e| e.to_string())?
            .into();

        let tx_clone = self.tx.clone();
        let threshold = self.threshold;

        let stream = device
            .build_input_stream(
                &config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    // 1. Edge-VAD: Calculate Energy (RMS)
                    let energy =
                        (data.iter().map(|&x| x * x).sum::<f32>() / data.len() as f32).sqrt();

                    if energy > threshold {
                        // 2. Convert f32 PCM to i16 (Binary Contract)
                        let pcm_data: Vec<u8> = data
                            .iter()
                            .map(|&x| (x * i16::MAX as f32) as i16)
                            .flat_map(|x| x.to_le_bytes())
                            .collect();

                        let _ = tx_clone.send(pcm_data);
                    }
                },
                |err| eprintln!("Audio capture error: {}", err),
                None,
            )
            .map_err(|e| e.to_string())?;

        stream.play().map_err(|e| e.to_string())?;
        Ok(stream)
    }
}
