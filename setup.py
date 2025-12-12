from setuptools import setup, find_packages

setup(
    name="rki-lexicon",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.3.0",
        "pyyaml>=5.4.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        'audio': [
            'librosa>=0.10.0',
            'soundfile>=0.12.0',
            'pydub>=0.25.1',
            'pyaudio>=0.2.12',
        ],
        'nlp': [
            'transformers>=4.35.0',
            'sentencepiece>=0.1.99',
            'gensim>=4.3.0',
        ],
        'full': [
            'librosa>=0.10.0',
            'soundfile>=0.12.0',
            'transformers>=4.35.0',
            'torch>=2.0.0',
            'scikit-learn>=1.3.0',
            'matplotlib>=3.7.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'rki-record=rki_lexicon.audio.recorder:record_word_cli',
            'rki-process=scripts.data_processing:main',
            'rki-validate=scripts.validation:main',
        ],
    },
)