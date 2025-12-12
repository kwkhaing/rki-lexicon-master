#!/usr/bin/env python3
"""
Validate audio files for Rakhine lexicon.
"""

import json
import wave
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import soundfile as sf
import librosa

class AudioValidator:
    def __init__(self, min_duration: float = 0.5, max_duration: float = 3.0):
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.max_amplitude = 0.95  # Max allowed amplitude to avoid clipping
    
    def validate_file(self, filepath: str) -> Dict[str, any]:
        """Validate a single audio file."""
        results = {
            'filename': Path(filepath).name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Check file exists
            if not Path(filepath).exists():
                results['valid'] = False
                results['errors'].append('File does not exist')
                return results
            
            # Get file info
            with sf.SoundFile(filepath) as f:
                results['metadata'].update({
                    'samplerate': f.samplerate,
                    'channels': f.channels,
                    'duration': f.frames / f.samplerate,
                    'format': f.format,
                    'subtype': f.subtype
                })
            
            # Load audio for further checks
            audio, sr = librosa.load(filepath, sr=None, mono=False)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)
                results['warnings'].append('Converted stereo to mono')
            
            # Check duration
            duration = len(audio) / sr
            results['metadata']['duration_seconds'] = duration
            
            if duration < self.min_duration:
                results['valid'] = False
                results['errors'].append(f'Duration too short: {duration:.2f}s (min: {self.min_duration}s)')
            elif duration > self.max_duration:
                results['warnings'].append(f'Duration long: {duration:.2f}s (max: {self.max_duration}s)')
            
            # Check for clipping
            max_amp = np.max(np.abs(audio))
            if max_amp > self.max_amplitude:
                results['valid'] = False
                results['errors'].append(f'Clipping detected: max amplitude = {max_amp:.3f}')
            
            # Check for silence
            rms = np.sqrt(np.mean(audio**2))
            if rms < 0.001:  # Very low RMS
                results['valid'] = False
                results['errors'].append('Audio is too quiet (possible silence)')
            
            # Check sample rate
            if sr < 22050:
                results['valid'] = False
                results['errors'].append(f'Sample rate too low: {sr} Hz (min: 22050 Hz)')
            
            # Check for NaN/inf values
            if np.any(np.isnan(audio)):
                results['valid'] = False
                results['errors'].append('Audio contains NaN values')
            
            if np.any(np.isinf(audio)):
                results['valid'] = False
                results['errors'].append('Audio contains infinite values')
            
            # Calculate SNR (simple version)
            # Assuming first and last 0.1s are silence
            silence_samples = int(0.1 * sr)
            if len(audio) > 2 * silence_samples:
                leading_silence = audio[:silence_samples]
                trailing_silence = audio[-silence_samples:]
                noise_power = np.mean(np.concatenate([leading_silence, trailing_silence]) ** 2)
                signal_power = np.mean(audio[silence_samples:-silence_samples] ** 2)
                
                if noise_power > 0:
                    snr = 10 * np.log10(signal_power / noise_power)
                    results['metadata']['snr_db'] = snr
                    
                    if snr < 20:  # Low SNR
                        results['warnings'].append(f'Low SNR: {snr:.1f} dB')
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f'Error reading file: {str(e)}')
        
        return results
    
    def validate_directory(self, directory: str) -> Dict[str, any]:
        """Validate all audio files in a directory."""
        audio_files = list(Path(directory).glob('*.wav')) + \
                     list(Path(directory).glob('*.mp3')) + \
                     list(Path(directory).glob('*.flac'))
        
        results = {
            'total_files': len(audio_files),
            'valid_files': 0,
            'invalid_files': 0,
            'files_with_warnings': 0,
            'detailed_results': []
        }
        
        for audio_file in audio_files:
            file_results = self.validate_file(str(audio_file))
            results['detailed_results'].append(file_results)
            
            if file_results['valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
            
            if file_results['warnings']:
                results['files_with_warnings'] += 1
        
        # Calculate statistics
        results['valid_percentage'] = (results['valid_files'] / results['total_files'] * 100) if results['total_files'] > 0 else 0
        
        return results
    
    def generate_validation_report(self, validation_results: Dict, output_file: str = None) -> str:
        """Generate a validation report."""
        report = []
        report.append("=" * 60)
        report.append("AUDIO VALIDATION REPORT")
        report.append("=" * 60)
        
        report.append(f"\nSummary:")
        report.append(f"  Total files: {validation_results['total_files']}")
        report.append(f"  Valid files: {validation_results['valid_files']} ({validation_results['valid_percentage']:.1f}%)")
        report.append(f"  Invalid files: {validation_results['invalid_files']}")
        report.append(f"  Files with warnings: {validation_results['files_with_warnings']}")
        
        if validation_results['invalid_files'] > 0:
            report.append("\n" + "=" * 60)
            report.append("INVALID FILES DETAIL")
            report.append("=" * 60)
            
            for file_result in validation_results['detailed_results']:
                if not file_result['valid']:
                    report.append(f"\n{file_result['filename']}:")
                    for error in file_result['errors']:
                        report.append(f"  ERROR: {error}")
        
        if validation_results['files_with_warnings'] > 0:
            report.append("\n" + "=" * 60)
            report.append("FILES WITH WARNINGS")
            report.append("=" * 60)
            
            for file_result in validation_results['detailed_results']:
                if file_result['warnings']:
                    report.append(f"\n{file_result['filename']}:")
                    for warning in file_result['warnings']:
                        report.append(f"  WARNING: {warning}")
        
        # Format recommendations
        report.append("\n" + "=" * 60)
        report.append("RECOMMENDATIONS")
        report.append("=" * 60)
        
        if validation_results['invalid_files'] > 0:
            report.append("\nFor invalid files:")
            report.append("1. Re-record files with clipping or noise")
            report.append("2. Check microphone placement and gain settings")
            report.append("3. Use proper recording environment")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text

def main():
    """Validate audio files."""
    validator = AudioValidator()
    
    # Validate raw audio directory
    print("Validating raw audio files...")
    raw_results = validator.validate_directory("data/raw/audio/")
    raw_report = validator.generate_validation_report(raw_results, "data/audio_validation_raw.txt")
    print(raw_report)
    
    # Validate processed audio directory
    print("\nValidating processed audio files...")
    processed_results = validator.validate_directory("data/processed/audio/normalized/")
    processed_report = validator.generate_validation_report(processed_results, "data/audio_validation_processed.txt")
    print(processed_report)
    
    # Save results to JSON
    all_results = {
        'raw_audio': raw_results,
        'processed_audio': processed_results
    }
    
    with open("data/audio_validation_results.json", 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    return all_results

if __name__ == "__main__":
    main()
