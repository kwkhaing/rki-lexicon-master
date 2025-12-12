#!/usr/bin/env python3
"""
Prepare data for Machine Translation.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
import sentencepiece as spm
import subprocess

class MTDataPreparer:
    def __init__(self):
        pass
    
    def prepare_opennmt_data(self, parallel_corpus: str, output_dir: str, 
                            src_lang: str = 'rakhine', tgt_lang: str = 'burmese'):
        """Prepare data for OpenNMT-py."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read parallel corpus
        with open(parallel_corpus, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # Split into source and target
        src_lines = []
        tgt_lines = []
        
        for line in lines:
            if ' ||| ' in line:
                parts = line.split(' ||| ')
                if len(parts) >= 2:
                    src_lines.append(parts[0])
                    tgt_lines.append(parts[1])
        
        # Split into train/dev/test
        total = len(src_lines)
        train_end = int(total * 0.8)
        dev_end = int(total * 0.9)
        
        # Save splits
        splits = {
            'train': (src_lines[:train_end], tgt_lines[:train_end]),
            'valid': (src_lines[train_end:dev_end], tgt_lines[train_end:dev_end]),
            'test': (src_lines[dev_end:], tgt_lines[dev_end:])
        }
        
        for split_name, (src, tgt) in splits.items():
            with open(output_dir / f'{split_name}.{src_lang}', 'w', encoding='utf-8') as f:
                f.write('\n'.join(src))
            with open(output_dir / f'{split_name}.{tgt_lang}', 'w', encoding='utf-8') as f:
                f.write('\n'.join(tgt))
        
        # Create OpenNMT config
        config = {
            'data': {
                'corpus_1': {
                    'path_src': str(output_dir / 'train.rakhine'),
                    'path_tgt': str(output_dir / 'train.burmese'),
                },
                'valid': {
                    'path_src': str(output_dir / 'valid.rakhine'),
                    'path_tgt': str(output_dir / 'valid.burmese'),
                }
            },
            'src_vocab': str(output_dir / 'vocab.src'),
            'tgt_vocab': str(output_dir / 'vocab.tgt'),
            'save_model': str(output_dir / 'model'),
            'world_size': 1,
            'gpu_ranks': [0]
        }
        
        with open(output_dir / 'config.yaml', 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config, f)
        
        return splits
    
    def train_sentencepiece(self, corpus_file: str, model_prefix: str, 
                           vocab_size: int = 8000, language: str = 'rakhine'):
        """Train SentencePiece tokenizer."""
        # SentencePiece training command
        cmd = [
            'spm_train',
            f'--input={corpus_file}',
            f'--model_prefix={model_prefix}',
            f'--vocab_size={vocab_size}',
            '--character_coverage=1.0',
            '--model_type=unigram',
            '--input_sentence_size=1000000',
            '--shuffle_input_sentence=true',
            '--hard_vocab_limit=false'
        ]
        
        if language in ['rakhine', 'burmese']:
            cmd.append('--split_by_unicode_script=false')
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Trained SentencePiece model: {model_prefix}.model")
        except subprocess.CalledProcessError as e:
            print(f"Error training SentencePiece: {e}")
    
    def prepare_fairseq_data(self, parallel_corpus: str, output_dir: str):
        """Prepare data for Fairseq."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read and split corpus
        with open(parallel_corpus, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        src_lines = []
        tgt_lines = []
        
        for line in lines:
            if ' ||| ' in line:
                parts = line.split(' ||| ')
                src_lines.append(parts[0])
                tgt_lines.append(parts[1])
        
        # Save raw files
        with open(output_dir / 'raw.rakhine', 'w', encoding='utf-8') as f:
            f.write('\n'.join(src_lines))
        with open(output_dir / 'raw.burmese', 'w', encoding='utf-8') as f:
            f.write('\n'.join(tgt_lines))
        
        # Tokenize (using SentencePiece)
        for lang in ['rakhine', 'burmese']:
            spm.SentencePieceProcessor().EncodeAsPieces
        
        # Create Fairseq binary data
        fairseq_cmd = [
            'fairseq-preprocess',
            '--source-lang', 'rakhine',
            '--target-lang', 'burmese',
            '--trainpref', str(output_dir / 'train'),
            '--validpref', str(output_dir / 'valid'),
            '--testpref', str(output_dir / 'test'),
            '--destdir', str(output_dir / 'data-bin'),
            '--workers', '4'
        ]
        
        print("Run this command to preprocess for Fairseq:")
        print(' '.join(fairseq_cmd))
        
        return output_dir
    
    def create_translation_evaluation_set(self, lexicon_file: str, output_file: str):
        """Create evaluation set from lexicon."""
        with open(lexicon_file, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        evaluation_set = []
        
        for entry in lexicon.get('lexicon', []):
            rakhine = entry.get('rakhine', '')
            english = entry.get('gloss_en', '')
            burmese = entry.get('gloss_my', '')
            
            if rakhine and english:
                evaluation_set.append({
                    'rakhine': rakhine,
                    'english': english,
                    'burmese': burmese,
                    'pos': entry.get('pos', ''),
                    'example': entry.get('example', '')
                })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_set, f, indent=2, ensure_ascii=False)
        
        return evaluation_set
    
    def generate_marian_config(self, output_dir: str):
        """Generate Marian-NMT configuration."""
        config = {
            'type': 'amun',
            'dim-vocabs': [8000, 8000],
            'dim-emb': 512,
            'dim-rnn': 1024,
            'enc-type': 'bidirectional',
            'enc-cell': 'lstm',
            'enc-depth': 1,
            'dec-cell': 'lstm',
            'dec-depth': 2,
            'tied-embeddings': True,
            'layer-normalization': False,
            'right-left': False,
            'input-types': ['sequence', 'sequence'],
            'train-sets': ['train.rakhine', 'train.burmese'],
            'vocabs': ['vocab.rakhine.yml', 'vocab.burmese.yml'],
            'model': 'model.npz',
            'after-epochs': 10,
            'after-batches': 0,
            'early-stopping': 5,
            'valid-freq': 10000,
            'valid-sets': ['valid.rakhine', 'valid.burmese'],
            'valid-metrics': ['cross-entropy', 'perplexity'],
            'valid-log': 'valid.log',
            'beam-size': 12,
            'normalize': 1.0,
            'word-penalty': 0,
            'max-length': 100,
            'mini-batch': 64,
            'workspace': 9500,
            'log': 'train.log',
            'disp-freq': 1000,
            'save-freq': 10000,
            'dropout-rnn': 0.2,
            'dropout-src': 0.1,
            'dropout-trg': 0.1,
            'optimizer': 'adam',
            'learn-rate': 0.0003,
            'clip-norm': 1.0,
            'exponential-smoothing': 0.0001
        }
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'config.yml', 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config, f)
        
        return config

def main():
    preparer = MTDataPreparer()
    
    print("Preparing MT training data...")
    
    # Check for parallel corpus
    parallel_corpus = "corpus/parallel/rakhine_burmese.aligned.txt"
    
    if Path(parallel_corpus).exists():
        # Prepare OpenNMT data
        splits = preparer.prepare_opennmt_data(
            parallel_corpus,
            "models/mt/opennmt/"
        )
        print(f"OpenNMT data: {len(splits['train'][0])} train, {len(splits['valid'][0])} valid")
        
        # Prepare Fairseq data
        fairseq_dir = preparer.prepare_fairseq_data(
            parallel_corpus,
            "models/mt/fairseq/"
        )
        print(f"Fairseq data prepared in {fairseq_dir}")
        
        # Generate Marian config
        marian_config = preparer.generate_marian_config("models/mt/marian/")
        print(f"Marian config generated")
    
    # Create evaluation set from lexicon
    eval_set = preparer.create_translation_evaluation_set(
        "data/lexicon.json",
        "models/mt/evaluation_set.json"
    )
    print(f"Created evaluation set with {len(eval_set)} examples")
    
    # Train SentencePiece tokenizer
    if Path("corpus/processed/tokenized/rakhine_tokenized.txt").exists():
        preparer.train_sentencepiece(
            "corpus/processed/tokenized/rakhine_tokenized.txt",
            "models/mt/spm/rakhine",
            vocab_size=8000
        )

if __name__ == "__main__":
    main()
