.PHONY: help install test validate process export clean

help:
	@echo "Rakhine Lexicon Project Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  test        Run tests"
	@echo "  validate    Validate lexicon data"
	@echo "  process     Process and clean data"
	@echo "  export      Export to all formats"
	@echo "  analyze     Run frequency analysis"
	@echo "  clean       Clean generated files"
	@echo "  all         Run all processing steps"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m pytest tests/ -v

validate:
	python scripts/validation.py
	@echo "Validation complete. Check data/validation_report.txt"

process:
	python scripts/data_processing.py
	@echo "Data processing complete"

export:
	mkdir -p data/exports
	python scripts/export_formats.py
	@echo "Export complete. Files in data/exports/"

analyze:
	mkdir -p data/analysis/plots
	python scripts/analysis/frequency_analysis.py
	@echo "Analysis complete. Reports in data/analysis/"

clean:
	rm -rf data/exports/*
	rm -rf data/analysis/*
	rm -rf __pycache__ scripts/__pycache__ src/__pycache__ tests/__pycache__
	rm -rf src/*.egg-info
	rm -f data/validation_report.txt
	@echo "Clean complete"

all: install validate process export analyze
	@echo "All processing steps complete"

# Audio commands
audio-record:
	python -m rki_lexicon.audio.recorder

audio-process:
	python scripts/audio_processing.py

audio-validate:
	python scripts/audio_validation.py

audio-analyze:
	python scripts/audio_analysis.py

audio-segment:
	python scripts/audio_segmentation.py

audio-integrate:
	python scripts/audio_integration.py

audio-all: audio-process audio-validate audio-analyze audio-integrate

# NLP commands
nlp-process:
	python scripts/corpus_processing.py

nlp-asr:
	python scripts/asr_preparation.py

nlp-mt:
	python scripts/mt_preparation.py

nlp-llm:
	python scripts/llm_fine_tuning.py

nlp-all: nlp-process nlp-asr nlp-mt nlp-llm