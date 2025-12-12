
### 2. **scripts/audio_processing.py**
```python
#!/usr/bin/env python3
"""
Audio processing utilities for Rakhine lexicon recordings.
"""

import os
import json
import wave
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import soundfile as sf
from pydub import AudioSegment
import librosa
import pyloudnorm as pyln

@dataclass
class AudioMetadata:
    """Metadata for audio recordings."""
    speaker_id: str
    speaker_gender: str
    speaker_age: int
    dialect: str
    recording_date: str
    recording_location: str
    recording_device: str
    microphone: str
    sample_rate: int
    channels: int
    duration: float
    rms_level: float
    peak_level: float
    snr: float

class AudioProcessor:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load audio file."""
        audio, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
        return audio, sr
    
    def normalize_audio(self, audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
        """Normalize audio to target dBFS level."""
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio**2))
        if current_rms == 0:
            return audio
        
        # Calculate gain needed
        current_dbfs = 20 * np.log10(current_rms)
        gain_db = target_dbfs - current_dbfs
        gain_linear = 10 ** (gain_db / 20)
        
        return audio * gain_linear
    
    def trim_silence(self, audio: np.ndarray, top_db: float = 40) -> np.ndarray:
        """Trim silence from beginning and end."""
        return librosa.effects.trim(audio, top_db=top_db)[0]
    
    def extract_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract acoustic features."""
        # Fundamental frequency (pitch)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, 
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sample_rate
        )
        
        # Formants (first 3)
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)[0]
        
        # Duration
        duration = librosa.get_duration(y=audio, sr=self.sample_rate)
        
        # Intensity
        rms = librosa.feature.rms(y=audio)[0]
        
        # Spectral features
        spectral_flatness = librosa.feature.spectral_flatness(y=audio)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate)[0]
        
        return {
            'duration': duration,
            'mean_f0': np.nanmean(f0) if np.any(~np.isnan(f0)) else 0,
            'std_f0': np.nanstd(f0) if np.any(~np.isnan(f0)) else 0,
            'mean_spectral_centroid': np.mean(spectral_centroids),
            'mean_rms': np.mean(rms),
            'max_rms': np.max(rms),
            'mean_spectral_flatness': np.mean(spectral_flatness),
            'mean_spectral_bandwidth': np.mean(spectral_bandwidth)
        }
    
    def segment_word(self, audio: np.ndarray, word_boundaries: List[Tuple[float, float]]) -> List[np.ndarray]:
        """Segment audio into words based on boundaries."""
        segments = []
        for start, end in word_boundaries:
            start_sample = int(start * self.sample_rate)
            end_sample = int(end * self.sample_rate)
            segment = audio[start_sample:end_sample]
            segments.append(segment)
        return segments
    
    def save_audio(self, audio: np.ndarray, filepath: str, format: str = 'wav'):
        """Save audio to file."""
        sf.write(filepath, audio, self.sample_rate, format=format)
    
    def batch_process(self, input_dir: str, output_dir: str):
        """Process all audio files in directory."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        audio_files = list(Path(input_dir).glob('*.wav')) + \
                     list(Path(input_dir).glob('*.mp3')) + \
                     list(Path(input_dir).glob('*.flac'))
        
        results = []
        for audio_file in audio_files:
            print(f"Processing {audio_file.name}...")
            
            # Load and process
            audio, sr = self.load_audio(str(audio_file))
            audio = self.trim_silence(audio)
            audio = self.normalize_audio(audio)
            
            # Extract features
            features = self.extract_features(audio)
            
            # Save processed audio
            output_file = Path(output_dir) / f"processed_{audio_file.name}"
            self.save_audio(audio, str(output_file))
            
            # Save features
            features_file = Path(output_dir) / f"{audio_file.stem}_features.json"
            with open(features_file, 'w', encoding='utf-8') as f:
                json.dump(features, f, indent=2)
            
            results.append({
                'filename': audio_file.name,
                'processed_file': output_file.name,
                'features': features
            })
        
        # Save batch results
        results_file = Path(output_dir) / 'batch_processing_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results

def create_audio_index(lexicon_file: str, audio_dir: str, output_file: str):
    """Create index linking lexicon entries to audio files."""
    # Load lexicon
    with open(lexicon_file, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
    
    # Scan audio directory
    audio_files = {}
    for ext in ['.wav', '.mp3', '.flac']:
        for audio_file in Path(audio_dir).glob(f'*{ext}'):
            # Parse filename for entry ID
            filename = audio_file.stem
            parts = filename.split('_')
            
            if len(parts) >= 1:
                entry_id = parts[0]  # First part should be entry ID
                
                if entry_id not in audio_files:
                    audio_files[entry_id] = []
                
                audio_files[entry_id].append({
                    'filename': audio_file.name,
                    'path': str(audio_file.relative_to(audio_dir)),
                    'size': audio_file.stat().st_size,
                    'speaker': parts[1] if len(parts) > 1 else 'unknown',
                    'dialect': parts[2] if len(parts) > 2 else 'unknown',
                    'gender': parts[3] if len(parts) > 3 else 'unknown'
                })
    
    # Update lexicon entries with audio references
    for entry in lexicon.get('lexicon', []):
        entry_id = entry.get('id')
        if entry_id in audio_files:
            if 'audio' not in entry:
                entry['audio'] = []
            entry['audio'].extend(audio_files[entry_id])
    
    # Save updated lexicon
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)
    
    # Also save separate audio index
    audio_index = {
        'total_recordings': sum(len(files) for files in audio_files.values()),
        'entries_with_audio': len(audio_files),
        'audio_by_entry': audio_files
    }
    
    with open('data/audio_index.json', 'w', encoding='utf-8') as f:
        json.dump(audio_index, f, indent=2, ensure_ascii=False)
    
    return audio_index

def main():
    """Example usage."""
    # Process audio files
    processor = AudioProcessor()
    results = processor.batch_process(
        "data/raw/audio/",
        "data/processed/audio/normalized/"
    )
    
    # Create audio index
    index = create_audio_index(
        "data/lexicon.json",
        "data/processed/audio/normalized/",
        "data/lexicon_with_audio.json"
    )
    
    print(f"Processed {len(results)} audio files")
    print(f"Entries with audio: {index['entries_with_audio']}")
    print(f"Total recordings: {index['total_recordings']}")

if __name__ == "__main__":
    main()
