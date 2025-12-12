#!/bin/bash
# Initialize Rakhine Lexicon Project

echo "Setting up Rakhine Lexicon Project..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Initialize data directory
mkdir -p data/{raw/{audio,text},processed,exports,analysis/plots,phonology/recordings}
mkdir -p corpus/{raw,processed/{tokenized,normalized,segmented},parallel,monolingual}
mkdir -p models/{asr/{kaldi,espnet,whisper},mt/{opennmt,fairseq,marian},llm,embeddings}

# Create initial data files
if [ ! -s "data/lexicon.json" ]; then
    echo '{"metadata": {"language": "Rakhine", "iso_code": "rki", "version": "1.0.0"}, "lexicon": []}' > data/lexicon.json
fi

# Create sample data
echo "ရခိုင်ဘာသာစကားသည် မြန်မာနိုင်ငံ၏ ရခိုင်ပြည်နယ်တွင် ပြောဆိုအသုံးပြုသော စကားဖြစ်သည်။" > corpus/raw/rakhine.txt
echo "Rakhine language is a language spoken in Rakhine State of Myanmar." > corpus/raw/english.txt

# Create audio metadata template
cat > data/audio_metadata_template.json << 'EOF'
[
  {
    "filename": "rki_0001_spk01_sittwe_m.wav",
    "entry_id": "rki_0001",
    "speaker_id": "spk01",
    "speaker_gender": "male",
    "speaker_age": 35,
    "dialect": "Sittwe",
    "recording_date": "2024-01-15",
    "recording_location": "Sittwe, Myanmar",
    "recording_device": "Zoom H5",
    "microphone": "Rode NT1-A",
    "recording_environment": "quiet room",
    "speaker_native": true,
    "speaker_other_languages": ["Burmese", "English"],
    "quality_rating": 5,
    "notes": "Clear pronunciation"
  }
]
EOF

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Add your first entries to data/lexicon.json"
echo "3. Run validation: python scripts/validation.py"
echo "4. Export data: python scripts/export_formats.py"
echo ""
echo "For audio features, install: pip install -r requirements_audio.txt"
echo "For NLP features, install: pip install -r requirements_nlp.txt"
echo "For LLM features, install: pip install -r requirements_llm.txt"