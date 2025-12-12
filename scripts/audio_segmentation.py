#!/usr/bin/env python3
"""
Segment long audio recordings into individual word recordings.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
import soundfile as sf
import librosa
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr

class AudioSegmenter:
    def __init__(self, sample_rate: int = 44100, min_silence_len: int = 500):
        self.sample_rate = sample_rate
        self.min_silence_len = min_silence_len  # ms
        self.silence_thresh = -40  # dBFS
    
    def segment_by_silence(self, audio_file: str, output_dir: str) -> List[Dict]:
        """Segment audio based on silence detection."""
        # Load audio
        audio = AudioSegment.from_file(audio_file)
        
        # Normalize
        audio = audio.normalize()
        
        # Split on silence
        chunks = split_on_silence(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            keep_silence=100  # Keep 100ms of silence at boundaries
        )
        
        # Save chunks
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        segments_info = []
        for i, chunk in enumerate(chunks):
            # Filter very short chunks (likely noise)
            if len(chunk) < 200:  # Less than 200ms
                continue
            
            # Save chunk
            output_file = Path(output_dir) / f"segment_{i:03d}.wav"
            chunk.export(str(output_file), format="wav")
            
            # Get chunk info
            segments_info.append({
                'segment_id': i,
                'filename': output_file.name,
                'duration_ms': len(chunk),
                'start_ms': sum(c.duration_seconds * 1000 for c in chunks[:i]),
                'end_ms': sum(c.duration_seconds * 1000 for c in chunks[:i+1])
            })
        
        # Save segmentation info
        info_file = Path(output_dir) / "segmentation_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(segments_info, f, indent=2)
        
        return segments_info
    
    def segment_with_transcript(self, audio_file: str, transcript_file: str, 
                               output_dir: str) -> List[Dict]:
        """Segment audio using transcript with timestamps."""
        # Load audio
        audio, sr = librosa.load(audio_file, sr=self.sample_rate)
        
        # Load transcript (expected format: word, start_time, end_time)
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = json.load(f)
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        segments_info = []
        for i, entry in enumerate(transcript):
            word = entry.get('word', '')
            start_time = entry.get('start_time', 0)
            end_time = entry.get('end_time', 0)
            
            if not word or end_time <= start_time:
                continue
            
            # Convert times to samples
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Extract segment
            segment = audio[start_sample:end_sample]
            
            # Save segment
            output_file = Path(output_dir) / f"{word}_{i:03d}.wav"
            sf.write(str(output_file), segment, sr)
            
            segments_info.append({
                'word': word,
                'segment_id': i,
                'filename': output_file.name,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time
            })
        
        # Save segmentation info
        info_file = Path(output_dir) / "word_segments.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(segments_info, f, indent=2, ensure_ascii=False)
        
        return segments_info
    
    def align_with_lexicon(self, segments: List[Dict], lexicon_file: str) -> List[Dict]:
        """Align segmented words with lexicon entries."""
        # Load lexicon
        with open(lexicon_file, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        lexicon_words = {}
        for entry in lexicon.get('lexicon', []):
            rakhine_word = entry.get('rakhine', '')
            if rakhine_word:
                lexicon_words[rakhine_word] = entry
        
        aligned_segments = []
        for segment in segments:
            word = segment.get('word', '')
            
            if word in lexicon_words:
                segment['lexicon_entry'] = lexicon_words[word]['id']
                segment['matched'] = True
            else:
                # Try fuzzy matching or partial matching
                segment['matched'] = False
                segment['lexicon_entry'] = None
            
            aligned_segments.append(segment)
        
        # Statistics
        matched = sum(1 for s in aligned_segments if s['matched'])
        total = len(aligned_segments)
        
        print(f"Matched {matched}/{total} segments ({matched/total*100:.1f}%)")
        
        return aligned_segments
    
    def batch_segment_directory(self, input_dir: str, output_base_dir: str):
        """Segment all audio files in directory."""
        audio_files = list(Path(input_dir).glob('*.wav')) + \
                     list(Path(input_dir).glob('*.mp3'))
        
        all_segments = []
        
        for audio_file in audio_files:
            print(f"Segmenting {audio_file.name}...")
            
            # Check for transcript file
            transcript_file = audio_file.with_suffix('.json')
            if transcript_file.exists():
                # Segment with transcript
                output_dir = Path(output_base_dir) / audio_file.stem
                segments = self.segment_with_transcript(
                    str(audio_file),
                    str(transcript_file),
                    str(output_dir)
                )
            else:
                # Segment by silence
                output_dir = Path(output_base_dir) / audio_file.stem
                segments = self.segment_by_silence(
                    str(audio_file),
                    str(output_dir)
                )
            
            all_segments.extend(segments)
        
        # Save combined results
        combined_file = Path(output_base_dir) / "all_segments.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_segments, f, indent=2, ensure_ascii=False)
        
        return all_segments

def main():
    """Example segmentation workflow."""
    segmenter = AudioSegmenter()
    
    # Segment a single file with transcript
    if Path("data/raw/audio/sentences/sample.json").exists():
        segments = segmenter.segment_with_transcript(
            "data/raw/audio/sentences/sample.wav",
            "data/raw/audio/sentences/sample.json",
            "data/processed/audio/segmented/sample/"
        )
        
        # Align with lexicon
        aligned = segmenter.align_with_lexicon(
            segments,
            "data/lexicon.json"
        )
        
        # Save aligned segments
        with open("data/processed/audio/aligned_segments.json", 'w', encoding='utf-8') as f:
            json.dump(aligned, f, indent=2, ensure_ascii=False)
    
    # Batch process directory
    all_segments = segmenter.batch_segment_directory(
        "data/raw/audio/sentences/",
        "data/processed/audio/segmented/"
    )
    
    print(f"Total segments created: {len(all_segments)}")

if __name__ == "__main__":
    main()
