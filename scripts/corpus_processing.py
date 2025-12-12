#!/usr/bin/env python3
"""
Process Rakhine corpus for NLP tasks.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from sacremoses import MosesTokenizer, MosesDetokenizer

class RakhineCorpusProcessor:
    def __init__(self):
        self.rakhine_tokenizer = MosesTokenizer(lang='my')  # Burmese tokenizer for Rakhine
        self.english_tokenizer = MosesTokenizer(lang='en')
        
    def normalize_text(self, text: str, language: str = 'rakhine') -> str:
        """Normalize text for NLP processing."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Normalize Myanmar script
        if language in ['rakhine', 'burmese']:
            # Myanmar-specific normalization
            text = re.sub(r'[၀-၉]', lambda m: str(ord(m.group()) - 4112), text)  # Convert Myanmar digits
            
        # Common normalization
        text = text.replace('၊', ',')  # Myanmar comma
        text = text.replace('။', '.')  # Myanmar period
        
        return text
    
    def segment_sentences(self, text: str, language: str = 'rakhine') -> List[str]:
        """Segment text into sentences."""
        if language in ['rakhine', 'burmese']:
            # Myanmar sentence segmentation
            sentences = re.split(r'[။!?]+', text)
        else:
            # Western punctuation
            sentences = re.split(r'[.!?]+', text)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def tokenize(self, text: str, language: str = 'rakhine') -> List[str]:
        """Tokenize text."""
        if language == 'rakhine':
            return self.rakhine_tokenizer.tokenize(text)
        elif language == 'english':
            return self.english_tokenizer.tokenize(text)
        else:
            return text.split()
    
    def prepare_for_word_embeddings(self, corpus_file: str, output_file: str):
        """Prepare corpus for word2vec/fasttext training."""
        with open(corpus_file, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]
        
        # Tokenize all texts
        tokenized = []
        for text in texts:
            tokens = self.tokenize(self.normalize_text(text), 'rakhine')
            tokenized.append(' '.join(tokens))
        
        # Save tokenized corpus
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(tokenized))
    
    def create_parallel_corpus(self, rakhine_file: str, target_file: str, 
                              output_file: str, target_lang: str = 'burmese'):
        """Create sentence-aligned parallel corpus."""
        # Load and process both files
        with open(rakhine_file, 'r', encoding='utf-8') as f:
            rakhine_lines = [self.normalize_text(line.strip()) for line in f if line.strip()]
        
        with open(target_file, 'r', encoding='utf-8') as f:
            target_lines = [self.normalize_text(line.strip(), target_lang) for line in f if line.strip()]
        
        # Align (assuming same number of lines)
        aligned = []
        min_len = min(len(rakhine_lines), len(target_lines))
        
        for i in range(min_len):
            aligned.append(f"{rakhine_lines[i]} ||| {target_lines[i]}")
        
        # Save aligned corpus
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(aligned))
    
    def prepare_for_llm(self, output_dir: str):
        """Prepare data for LLM fine-tuning in multiple formats."""
        
        # 1. Instruction tuning format
        instructions = []
        lexicon = json.load(open('data/lexicon.json', 'r', encoding='utf-8'))
        
        for entry in lexicon['lexicon']:
            instruction = {
                "instruction": f"Translate the Rakhine word '{entry.get('rakhine')}' to English",
                "input": f"Rakhine: {entry.get('rakhine')}",
                "output": f"English: {entry.get('gloss_en', '')}",
                "pos": entry.get('pos', '')
            }
            instructions.append(instruction)
        
        with open(f"{output_dir}/instruction_tuning.jsonl", 'w', encoding='utf-8') as f:
            for inst in instructions:
                f.write(json.dumps(inst, ensure_ascii=False) + '\n')
        
        # 2. Chat format
        chat_data = []
        for entry in lexicon['lexicon'][:100]:  # First 100 entries as example
            chat = {
                "messages": [
                    {"role": "user", "content": f"What does '{entry.get('rakhine')}' mean in Rakhine?"},
                    {"role": "assistant", "content": f"It means '{entry.get('gloss_en', '')}'. It's a {entry.get('pos', '')}. Example: {entry.get('example', '')}"}
                ]
            }
            chat_data.append(chat)
        
        with open(f"{output_dir}/chat_format.jsonl", 'w', encoding='utf-8') as f:
            for chat in chat_data:
                f.write(json.dumps(chat, ensure_ascii=False) + '\n')
        
        # 3. Text completion (for continued pretraining)
        text_corpus = []
        for entry in lexicon['lexicon']:
            text = f"Rakhine word: {entry.get('rakhine')}\n"
            text += f"Romanization: {entry.get('romanization', '')}\n"
            text += f"Part of speech: {entry.get('pos', '')}\n"
            text += f"English: {entry.get('gloss_en', '')}\n"
            if entry.get('example'):
                text += f"Example: {entry.get('example')}\n"
            text_corpus.append(text)
        
        with open(f"{output_dir}/text_completion.txt", 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_corpus))

def main():
    processor = RakhineCorpusProcessor()
    
    # Example usage
    print("Processing corpus for NLP tasks...")
    
    # Prepare for word embeddings
    if Path("corpus/raw/rakhine.txt").exists():
        processor.prepare_for_word_embeddings(
            "corpus/raw/rakhine.txt",
            "corpus/processed/tokenized/rakhine_tokenized.txt"
        )
    
    # Create parallel corpus
    if Path("corpus/raw/rakhine.txt").exists() and Path("corpus/raw/burmese.txt").exists():
        processor.create_parallel_corpus(
            "corpus/raw/rakhine.txt",
            "corpus/raw/burmese.txt",
            "corpus/parallel/rakhine_burmese.aligned.txt"
        )
    
    # Prepare for LLM fine-tuning
    processor.prepare_for_llm("corpus/processed/llm/")

if __name__ == "__main__":
    main()
