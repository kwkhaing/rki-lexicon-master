#!/usr/bin/env python3
"""
Acoustic analysis of Rakhine audio recordings.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import librosa
import librosa.display
from sklearn.decomposition import PCA
import pandas as pd

class AcousticAnalyzer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def analyze_word(self, audio_file: str) -> Dict[str, any]:
        """Perform comprehensive acoustic analysis on a word recording."""
        # Load audio
        audio, sr = librosa.load(audio_file, sr=self.sample_rate)
        
        results = {
            'filename': Path(audio_file).name,
            'duration': librosa.get_duration(y=audio, sr=sr),
            'basic_features': {},
            'spectral_features': {},
            'temporal_features': {},
            'prosodic_features': {}
        }
        
        # Basic features
        results['basic_features']['rms'] = np.sqrt(np.mean(audio**2))
        results['basic_features']['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(y=audio)[0])
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        spectral_flatness = librosa.feature.spectral_flatness(y=audio)[0]
        
        results['spectral_features'].update({
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_centroid_std': np.std(spectral_centroid),
            'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
            'spectral_rolloff_mean': np.mean(spectral_rolloff),
            'spectral_flatness_mean': np.mean(spectral_flatness)
        })
        
        # MFCCs (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        for i in range(mfccs.shape[0]):
            results[f'mfcc_{i+1:02d}_mean'] = np.mean(mfccs[i])
            results[f'mfcc_{i+1:02d}_std'] = np.std(mfccs[i])
        
        # Pitch (F0) analysis
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        
        if np.any(~np.isnan(f0)):
            results['prosodic_features'].update({
                'f0_mean': np.nanmean(f0),
                'f0_std': np.nanstd(f0),
                'f0_min': np.nanmin(f0),
                'f0_max': np.nanmax(f0),
                'voiced_ratio': np.mean(voiced_flag)
            })
        
        # Formant estimation (simplified)
        # Note: Proper formant analysis requires LPC
        try:
            import crepe
            # Optional: Use CREPE for better pitch tracking
            pass
        except ImportError:
            pass
        
        return results
    
    def analyze_dialect_differences(self, audio_dir: str, metadata_file: str):
        """Analyze acoustic differences between dialects."""
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Analyze all audio files
        all_features = []
        dialects = []
        
        for speaker_data in metadata.get('speakers', []):
            dialect = speaker_data.get('dialect', 'unknown')
            speaker_id = speaker_data.get('speaker_id', '')
            
            # Find audio files for this speaker
            pattern = f"*{speaker_id}*.wav"
            audio_files = list(Path(audio_dir).glob(pattern))
            
            for audio_file in audio_files:
                features = self.analyze_word(str(audio_file))
                features['dialect'] = dialect
                features['speaker'] = speaker_id
                all_features.append(features)
                dialects.append(dialect)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        # Group by dialect
        dialect_stats = {}
        for dialect in set(dialects):
            dialect_df = df[df['dialect'] == dialect]
            dialect_stats[dialect] = {
                'count': len(dialect_df),
                'mean_f0': dialect_df['prosodic_features'].apply(lambda x: x.get('f0_mean', np.nan)).mean(),
                'mean_duration': dialect_df['duration'].mean(),
                'mean_spectral_centroid': dialect_df['spectral_features'].apply(lambda x: x.get('spectral_centroid_mean', np.nan)).mean()
            }
        
        return dialect_stats
    
    def create_visualizations(self, features_df: pd.DataFrame, output_dir: str):
        """Create acoustic visualization plots."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Dialect comparison box plots
        plt.figure(figsize=(12, 6))
        
        # F0 by dialect
        plt.subplot(1, 3, 1)
        f0_data = []
        dialects = []
        for _, row in features_df.iterrows():
            if 'prosodic_features' in row and 'f0_mean' in row['prosodic_features']:
                f0_data.append(row['prosodic_features']['f0_mean'])
                dialects.append(row['dialect'])
        
        if f0_data:
            import pandas as pd
            f0_df = pd.DataFrame({'dialect': dialects, 'f0_mean': f0_data})
            sns.boxplot(x='dialect', y='f0_mean', data=f0_df)
            plt.title('Fundamental Frequency by Dialect')
            plt.xticks(rotation=45)
        
        # Duration by dialect
        plt.subplot(1, 3, 2)
        sns.boxplot(x='dialect', y='duration', data=features_df)
        plt.title('Word Duration by Dialect')
        plt.xticks(rotation=45)
        
        # Spectral centroid by dialect
        plt.subplot(1, 3, 3)
        spectral_data = []
        dialects = []
        for _, row in features_df.iterrows():
            if 'spectral_features' in row and 'spectral_centroid_mean' in row['spectral_features']:
                spectral_data.append(row['spectral_features']['spectral_centroid_mean'])
                dialects.append(row['dialect'])
        
        if spectral_data:
            spectral_df = pd.DataFrame({'dialect': dialects, 'spectral_centroid': spectral_data})
            sns.boxplot(x='dialect', y='spectral_centroid', data=spectral_df)
            plt.title('Spectral Centroid by Dialect')
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/dialect_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Spectrogram examples
        audio_files = list(Path("data/processed/audio/normalized/").glob("*.wav"))[:5]
        
        fig, axes = plt.subplots(len(audio_files), 3, figsize=(15, 4*len(audio_files)))
        
        for i, audio_file in enumerate(audio_files):
            audio, sr = librosa.load(audio_file, sr=self.sample_rate)
            
            # Waveform
            axes[i, 0].plot(np.linspace(0, len(audio)/sr, len(audio)), audio)
            axes[i, 0].set_title(f"Waveform: {audio_file.stem}")
            axes[i, 0].set_xlabel("Time (s)")
            axes[i, 0].set_ylabel("Amplitude")
            
            # Spectrogram
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
            img = librosa.display.specshow(D, y_axis='log', x_axis='time', sr=sr, ax=axes[i, 1])
            axes[i, 1].set_title(f"Spectrogram: {audio_file.stem}")
            plt.colorbar(img, ax=axes[i, 1])
            
            # Mel spectrogram
            mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr)
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            img2 = librosa.display.specshow(mel_spec_db, x_axis='time', y_axis='mel', sr=sr, ax=axes[i, 2])
            axes[i, 2].set_title(f"Mel Spectrogram: {audio_file.stem}")
            plt.colorbar(img2, ax=axes[i, 2])
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/spectrogram_examples.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Feature correlation matrix
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            plt.figure(figsize=(12, 10))
            corr_matrix = features_df[numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/feature_correlation.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def export_analysis_results(self, features_df: pd.DataFrame, output_file: str):
        """Export analysis results to JSON."""
        # Convert DataFrame to dictionary
        results = {
            'summary': {
                'total_recordings': len(features_df),
                'dialects_analyzed': features_df['dialect'].nunique() if 'dialect' in features_df.columns else 0,
                'speakers_analyzed': features_df['speaker'].nunique() if 'speaker' in features_df.columns else 0
            },
            'features': features_df.to_dict(orient='records')
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        return results

def main():
    """Run acoustic analysis."""
    analyzer = AcousticAnalyzer()
    
    # Analyze individual word
    sample_file = "data/processed/audio/normalized/rki_0001_spk01_sittwe_m.wav"
    if Path(sample_file).exists():
        features = analyzer.analyze_word(sample_file)
        print(f"Features for {Path(sample_file).name}:")
        print(json.dumps(features, indent=2))
    
    # Analyze dialect differences
    if Path("data/audio_metadata.json").exists():
        dialect_stats = analyzer.analyze_dialect_differences(
            "data/processed/audio/normalized/",
            "data/audio_metadata.json"
        )
        
        print("\nDialect Statistics:")
        for dialect, stats in dialect_stats.items():
            print(f"{dialect}: {stats}")
    
    # Create visualizations
    # Note: This requires a features DataFrame
    # analyzer.create_visualizations(features_df, "data/analysis/plots/")

if __name__ == "__main__":
    main()
