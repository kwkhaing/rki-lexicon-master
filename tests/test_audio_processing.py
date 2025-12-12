"""
Tests for audio processing module.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from scripts.audio_processing import AudioProcessor, AudioMetadata, create_audio_index
from scripts.audio_validation import AudioValidator

class TestAudioProcessor:
    @pytest.fixture
    def processor(self):
        return AudioProcessor(sample_rate=22050)
    
    @pytest.fixture
    def test_audio(self):
        # Create synthetic audio signal (1 second of 440 Hz sine wave)
        sample_rate = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        return audio, sample_rate
    
    def test_normalize_audio(self, processor, test_audio):
        audio, sr = test_audio
        normalized = processor.normalize_audio(audio, target_dbfs=-20.0)
        
        # Check shape preserved
        assert normalized.shape == audio.shape
        
        # Check not all zeros (unless input was zeros)
        if np.any(audio != 0):
            assert np.any(normalized != 0)
    
    def test_trim_silence(self, processor, test_audio):
        audio, sr = test_audio
        
        # Add silence to beginning and end
        silence = np.zeros(int(0.1 * sr))  # 0.1 seconds of silence
        audio_with_silence = np.concatenate([silence, audio, silence])
        
        trimmed = processor.trim_silence(audio_with_silence, top_db=40)
        
        # Should be shorter than original with silence
        assert len(trimmed) < len(audio_with_silence)
        
        # Should be approximately original length
        assert abs(len(trimmed) - len(audio)) < 100  # Within 100 samples
    
    def test_extract_features(self, processor, test_audio):
        audio, sr = test_audio
        features = processor.extract_features(audio)
        
        # Check required features exist
        required_features = ['duration', 'mean_f0', 'std_f0', 'mean_rms']
        for feature in required_features:
            assert feature in features
        
        # Check duration is correct
        expected_duration = len(audio) / sr
        assert abs(features['duration'] - expected_duration) < 0.01
    
    def test_segment_word(self, processor, test_audio):
        audio, sr = test_audio
        
        # Create test boundaries (0.2-0.4 seconds and 0.6-0.8 seconds)
        boundaries = [(0.2, 0.4), (0.6, 0.8)]
        
        segments = processor.segment_word(audio, boundaries)
        
        # Should get 2 segments
        assert len(segments) == 2
        
        # Each segment should be correct length
        for (start, end), segment in zip(boundaries, segments):
            expected_length = int((end - start) * sr)
            assert abs(len(segment) - expected_length) < 2
    
    @pytest.mark.skipif(not Path("test.wav").exists(), reason="Test audio file not found")
    def test_save_load(self, processor, test_audio, tmp_path):
        audio, sr = test_audio
        
        # Save audio
        test_file = tmp_path / "test.wav"
        processor.save_audio(audio, str(test_file))
        
        # Check file exists
        assert test_file.exists()
        
        # Load it back
        loaded_audio, loaded_sr = processor.load_audio(str(test_file))
        
        # Should be same length (within tolerance)
        assert abs(len(loaded_audio) - len(audio)) < 10
        
        # Sample rate should match processor's sample rate
        assert loaded_sr == processor.sample_rate

class TestAudioValidator:
    @pytest.fixture
    def validator(self):
        return AudioValidator(min_duration=0.1, max_duration=5.0)
    
    @pytest.fixture
    def valid_audio_file(self, tmp_path):
        """Create a valid test audio file."""
        import soundfile as sf
        
        # Create synthetic audio
        sr = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        audio = 0.8 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Save to file
        test_file = tmp_path / "valid_audio.wav"
        sf.write(test_file, audio, sr)
        
        return str(test_file)
    
    @pytest.fixture
    def silent_audio_file(self, tmp_path):
        """Create a silent audio file."""
        import soundfile as sf
        
        sr = 44100
        duration = 1.0
        audio = np.zeros(int(sr * duration))
        
        test_file = tmp_path / "silent_audio.wav"
        sf.write(test_file, audio, sr)
        
        return str(test_file)
    
    def test_validate_valid_file(self, validator, valid_audio_file):
        results = validator.validate_file(valid_audio_file)
        
        assert results['valid'] == True
        assert len(results['errors']) == 0
        assert 'duration_seconds' in results['metadata']
    
    def test_validate_silent_file(self, validator, silent_audio_file):
        results = validator.validate_file(silent_audio_file)
        
        # Silent file should fail validation
        assert results['valid'] == False
        assert any('too quiet' in error.lower() for error in results['errors'])
    
    def test_validate_nonexistent_file(self, validator):
        results = validator.validate_file("/nonexistent/file.wav")
        
        assert results['valid'] == False
        assert any('does not exist' in error.lower() for error in results['errors'])
    
    def test_validate_directory(self, validator, tmp_path):
        # Create multiple test files
        import soundfile as sf
        
        # Create one valid and one invalid file
        sr = 44100
        
        # Valid file
        audio1 = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))
        sf.write(tmp_path / "valid.wav", audio1, sr)
        
        # Invalid (clipped) file
        audio2 = 2.0 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr))  # Will clip
        sf.write(tmp_path / "clipped.wav", audio2, sr)
        
        # Validate directory
        results = validator.validate_directory(str(tmp_path))
        
        assert results['total_files'] == 2
        assert results['valid_files'] == 1
        assert results['invalid_files'] == 1

class TestAudioIntegration:
    def test_create_audio_index(self, tmp_path):
        # Create test lexicon
        lexicon = {
            "metadata": {"language": "Rakhine"},
            "lexicon": [
                {"id": "rki_0001", "rakhine": "လမ်", "gloss_en": "road"},
                {"id": "rki_0002", "rakhine": "ရေ", "gloss_en": "water"}
            ]
        }
        
        lexicon_file = tmp_path / "lexicon.json"
        with open(lexicon_file, 'w', encoding='utf-8') as f:
            json.dump(lexicon, f, ensure_ascii=False)
        
        # Create test audio directory with some files
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        
        # Create dummy audio files
        for filename in ["rki_0001_spk01.wav", "rki_0001_spk02.wav", "rki_0002_spk01.wav"]:
            (audio_dir / filename).touch()
        
        # Create audio index
        output_file = tmp_path / "lexicon_with_audio.json"
        index = create_audio_index(
            str(lexicon_file),
            str(audio_dir),
            str(output_file)
        )
        
        # Check results
        assert index['total_recordings'] == 3
        assert index['entries_with_audio'] == 2
        
        # Check lexicon was updated
        with open(output_file, 'r', encoding='utf-8') as f:
            updated_lexicon = json.load(f)
        
        # Entry 1 should have 2 audio files
        entry1 = next(e for e in updated_lexicon['lexicon'] if e['id'] == 'rki_0001')
        assert 'audio' in entry1
        assert len(entry1['audio']) == 2
        
        # Entry 2 should have 1 audio file
        entry2 = next(e for e in updated_lexicon['lexicon'] if e['id'] == 'rki_0002')
        assert len(entry2['audio']) == 1

def test_audio_metadata():
    """Test AudioMetadata dataclass."""
    metadata = AudioMetadata(
        speaker_id="spk01",
        speaker_gender="male",
        speaker_age=35,
        dialect="Sittwe",
        recording_date="2024-01-15",
        recording_location="Sittwe, Myanmar",
        recording_device="Zoom H5",
        microphone="Rode NT1-A",
        sample_rate=44100,
        channels=1,
        duration=1.5,
        rms_level=0.5,
        peak_level=0.8,
        snr=45.0
    )
    
    assert metadata.speaker_id == "spk01"
    assert metadata.dialect == "Sittwe"
    assert metadata.sample_rate == 44100
    assert isinstance(metadata.duration, float)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
