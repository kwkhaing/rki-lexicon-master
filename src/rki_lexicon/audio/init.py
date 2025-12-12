"""
Audio module for Rakhine lexicon.
"""

from .recorder import AudioRecorder
from .processor import AudioProcessor
from .analyzer import AcousticAnalyzer
from .utils import (
    normalize_audio,
    trim_silence,
    extract_features,
    validate_audio_file
)

__all__ = [
    'AudioRecorder',
    'AudioProcessor',
    'AcousticAnalyzer',
    'normalize_audio',
    'trim_silence',
    'extract_features',
    'validate_audio_file'
]
