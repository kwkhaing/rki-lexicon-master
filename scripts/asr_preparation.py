#!/usr/bin/env python3
"""
Prepare data for ASR (Automatic Speech Recognition).
"""

import json
from pathlib import Path
from typing import List, Dict
import pandas as pd

def create_kaldi_structure():
    """Create Kaldi-style ASR directory structure."""
    kaldi_dir = Path("models/asr/kaldi")
    kaldi_dir.mkdir(parents=True, exist_ok=True)
    
    # Create standard Kaldi directories
    dirs = ['data/train', 'data/test', 'data/dev', 'exp', 'conf', 'local', 'utils']
    for dir_name in dirs:
        (kaldi_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Create necessary files
    with open(kaldi_dir / 'path.sh', 'w') as f:
        f.write('export KALDI_ROOT=/path/to/kaldi\n')
    
    with open(kaldi_dir / 'cmd.sh', 'w') as f:
        f.write('export train_cmd=run.pl\nexport decode_cmd=run.pl\n')
    
    print(f"Created Kaldi structure at {kaldi_dir}")

def prepare_espnet_data(audio_dir: str, output_dir: str):
    """Prepare data for ESPnet ASR."""
    import soundfile as sf
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ESPnet data structure
    data = {
        'utts': {},
        'output': []
    }
    
    # Find all audio files with transcripts
    audio_files = list(Path(audio_dir).glob('*.wav'))
    
    for audio_file in audio_files:
        # Check for corresponding transcript
        transcript_file = audio_file.with_suffix('.txt')
        if transcript_file.exists():
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            
            # Get audio info
            with sf.SoundFile(str(audio_file)) as af:
                duration = af.frames / af.samplerate
            
            utt_id = audio_file.stem
            data['utts'][utt_id] = {
                'input': [{
                    'feat': str(audio_file),
                    'name': 'input1',
                    'shape': [int(duration * 100), 83]  # Approximate
                }],
                'output': [{
                    'name': 'target1',
                    'shape': [len(transcript), len(set(transcript))],
                    'text': transcript,
                    'token': 'char',
                    'tokenid': ' '.join(str(ord(c)) for c in transcript)
                }]
            }
    
    # Save ESPnet data.json
    with open(output_dir / 'data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data

def create_whisper_training_data(audio_dir: str, output_dir: str):
    """Create training data for OpenAI Whisper fine-tuning."""
    import whisper
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    training_data = []
    audio_files = list(Path(audio_dir).glob('*.wav'))
    
    for audio_file in audio_files:
        transcript_file = audio_file.with_suffix('.txt')
        if transcript_file.exists():
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            
            # Whisper training format
            training_data.append({
                "audio_filepath": str(audio_file),
                "text": transcript,
                "duration": 0,  # Would need to calculate
                "language": "rki"
            })
    
    # Save as JSONL
    with open(output_dir / 'whisper_training.jsonl', 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    return training_data

def generate_ctc_labels(lexicon_file: str, output_file: str):
    """Generate CTC labels for ASR training."""
    with open(lexicon_file, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
    
    # Extract all unique characters
    all_chars = set()
    for entry in lexicon.get('lexicon', []):
        rakhine = entry.get('rakhine', '')
        all_chars.update(rakhine)
    
    # Add Burmese script characters
    burmese_chars = [chr(i) for i in range(0x1000, 0x109F)]  # Myanmar block
    all_chars.update(burmese_chars)
    
    # Create character map (CTC blank is index 0)
    char_list = ['<blank>', '<unk>', '<sos>', '<eos>'] + sorted(all_chars)
    char_to_idx = {char: idx for idx, char in enumerate(char_list)}
    
    # Save character map
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'char_to_idx': char_to_idx,
            'idx_to_char': {v: k for k, v in char_to_idx.items()},
            'num_classes': len(char_list)
        }, f, indent=2, ensure_ascii=False)
    
    return char_to_idx

def main():
    """Prepare ASR training data."""
    print("Preparing ASR training data...")
    
    # Create Kaldi structure
    create_kaldi_structure()
    
    # Generate CTC labels
    char_map = generate_ctc_labels(
        "data/lexicon.json",
        "models/asr/ctc_labels.json"
    )
    
    print(f"Generated {len(char_map)} CTC labels")
    
    # Prepare ESPnet data (if audio exists)
    audio_dir = "data/processed/audio/normalized/"
    if Path(audio_dir).exists():
        espnet_data = prepare_espnet_data(
            audio_dir,
            "models/asr/espnet/data/"
        )
        print(f"Prepared {len(espnet_data['utts'])} utterances for ESPnet")
    
    # Prepare Whisper data
    if Path(audio_dir).exists():
        whisper_data = create_whisper_training_data(
            audio_dir,
            "models/asr/whisper/"
        )
        print(f"Prepared {len(whisper_data)} samples for Whisper")

if __name__ == "__main__":
    main()
