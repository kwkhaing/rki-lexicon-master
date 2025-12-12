# Rakhine Language Lexicon (ISO 639-3: rki)

A comprehensive digital lexicon for the Rakhine language (Arakanese), an endangered Sino-Tibetan language spoken by approximately 3 to 5 million people, primarily in western Myanmar's Rakhine State, as well as in neighboring areas of Bangladesh and India.

## Features
- Machine-readable lexicon with rich linguistic annotations
- Audio recordings with native speaker pronunciations  
- Multiple representation formats (JSON, TSV, XML, SQL)
- Phonetic transcriptions (IPA)
- Part-of-speech tagging
- English and Burmese glosses
- Example sentences
- Morphological information
- Dialect variations

## Quick Start
```bash
# Clone and setup
git clone https://github.com/yourusername/rki-lexicon.git
cd rki-lexicon
./init_project.sh

# Add your first entry
python scripts/data_processing.py --add-entry

# Validate data
python scripts/validation.py

# Export to all formats
python scripts/export_formats.py
