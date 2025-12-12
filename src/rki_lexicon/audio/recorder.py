"""
Audio recording interface for Rakhine lexicon.
"""

import pyaudio
import wave
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import json

class AudioRecorder:
    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = 1024
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        
    def start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            return
        
        self.frames = []
        self.is_recording = True
        
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
        
    def _record(self):
        """Internal recording loop."""
        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)
    
    def stop_recording(self) -> bytes:
        """Stop recording and return audio data."""
        if not self.is_recording:
            return b''
        
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Combine all frames
        audio_data = b''.join(self.frames)
        return audio_data
    
    def save_recording(self, audio_data: bytes, output_path: str, metadata: dict = None):
        """Save recording to WAV file."""
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
        
        # Save metadata if provided
        if metadata:
            metadata_file = Path(output_path).with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def record_word(self, word: str, speaker_id: str, output_dir: str, 
                   repetitions: int = 3, pause_duration: float = 1.0) -> list:
        """Record a word with repetitions and carrier phrases."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        recordings = []
        
        print(f"Recording word: {word}")
        print("Instructions:")
        print("1. Say the word in isolation")
        print("2. Wait for the beep")
        print("3. Say the word in carrier phrase")
        print("4. Wait for the beep")
        print(f"5. Repeat {repetitions} times\n")
        
        for i in range(repetitions):
            print(f"Repetition {i+1}/{repetitions}")
            
            # Record isolated word
            input(f"Press Enter to record isolated word '{word}'...")
            print("Recording... (press Enter to stop)")
            self.start_recording()
            input()
            audio_data = self.stop_recording()
            
            # Save isolated word
            iso_filename = f"{word}_isolated_{i+1:02d}_{speaker_id}.wav"
            iso_path = output_dir / iso_filename
            self.save_recording(audio_data, str(iso_path))
            
            # Record in carrier phrase
            carrier_phrase = f"{word} လို့ခေါ်တယ်"  # "we call it ___"
            input(f"Press Enter to record in carrier phrase: '{carrier_phrase}'...")
            print("Recording... (press Enter to stop)")
            self.start_recording()
            input()
            audio_data = self.stop_recording()
            
            # Save carrier phrase
            carrier_filename = f"{word}_carrier_{i+1:02d}_{speaker_id}.wav"
            carrier_path = output_dir / carrier_filename
            self.save_recording(audio_data, str(carrier_path))
            
            recordings.append({
                'repetition': i + 1,
                'isolated_file': iso_filename,
                'carrier_file': carrier_filename,
                'timestamp': datetime.now().isoformat()
            })
            
            # Pause between repetitions
            if i < repetitions - 1:
                print(f"Pausing for {pause_duration} seconds...")
                time.sleep(pause_duration)
        
        # Save recording metadata
        metadata = {
            'word': word,
            'speaker_id': speaker_id,
            'recordings': recordings,
            'total_recordings': len(recordings) * 2,  # Isolated + carrier
            'recording_date': datetime.now().isoformat(),
            'sample_rate': self.sample_rate,
            'channels': self.channels
        }
        
        metadata_file = output_dir / f"{word}_{speaker_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return recordings
    
    def close(self):
        """Clean up resources."""
        if self.stream:
            self.stream.close()
        self.audio.terminate()

def record_word_cli():
    """Command-line interface for recording words."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Record Rakhine words')
    parser.add_argument('word', help='Word to record (in Myanmar script)')
    parser.add_argument('speaker_id', help='Speaker identifier')
    parser.add_argument('--output-dir', default='data/raw/audio',
                       help='Output directory for recordings')
    parser.add_argument('--repetitions', type=int, default=3,
                       help='Number of repetitions')
    parser.add_argument('--sample-rate', type=int, default=44100,
                       help='Sample rate for recording')
    
    args = parser.parse_args()
    
    recorder = AudioRecorder(sample_rate=args.sample_rate)
    
    try:
        recordings = recorder.record_word(
            word=args.word,
            speaker_id=args.speaker_id,
            output_dir=args.output_dir,
            repetitions=args.repetitions
        )
        
        print(f"\nRecording complete!")
        print(f"Recorded {len(recordings)} repetitions")
        print(f"Files saved to: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\nRecording interrupted")
    finally:
        recorder.close()

if __name__ == "__main__":
    record_word_cli()
