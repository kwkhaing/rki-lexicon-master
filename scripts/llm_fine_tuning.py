#!/usr/bin/env python3
"""
Prepare data for LLM fine-tuning.
"""

import json
from pathlib import Path
from typing import List, Dict
import random
from datasets import Dataset, DatasetDict

class LLMDataPreparer:
    def __init__(self):
        pass
    
    def prepare_alpaca_format(self, lexicon_file: str, output_file: str):
        """Prepare data in Alpaca instruction-following format."""
        with open(lexicon_file, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        alpaca_data = []
        
        for entry in lexicon.get('lexicon', []):
            # Instruction
            instruction = f"What does the Rakhine word '{entry.get('rakhine')}' mean?"
            
            # Input
            input_text = f"Rakhine word: {entry.get('rakhine')}\n"
            if entry.get('romanization'):
                input_text += f"Romanization: {entry.get('romanization')}\n"
            if entry.get('pos'):
                input_text += f"Part of speech: {entry.get('pos')}"
            
            # Output
            output_text = f"The Rakhine word '{entry.get('rakhine')}' means '{entry.get('gloss_en', '')}' in English."
            if entry.get('gloss_my'):
                output_text += f" In Burmese, it's '{entry.get('gloss_my')}'."
            if entry.get('example'):
                output_text += f"\nExample: {entry.get('example')}"
                if entry.get('example_translation'):
                    output_text += f" ({entry.get('example_translation')})"
            
            alpaca_data.append({
                "instruction": instruction,
                "input": input_text,
                "output": output_text,
                "category": "lexicon"
            })
        
        # Save as JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in alpaca_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return alpaca_data
    
    def prepare_chat_format(self, lexicon_file: str, output_file: str):
        """Prepare data in chat format for models like Llama, Mistral."""
        with open(lexicon_file, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        chat_data = []
        
        for entry in lexicon.get('lexicon', []):
            # Multiple turns of conversation
            conversation = [
                {
                    "role": "user",
                    "content": f"Can you help me understand Rakhine language?"
                },
                {
                    "role": "assistant", 
                    "content": "Yes, I'd be happy to help you with Rakhine language!"
                },
                {
                    "role": "user",
                    "content": f"What does '{entry.get('rakhine')}' mean?"
                },
                {
                    "role": "assistant",
                    "content": f"The word '{entry.get('rakhine')}' means '{entry.get('gloss_en', '')}' in English."
                }
            ]
            
            # Add more details if available
            if entry.get('example'):
                conversation.append({
                    "role": "user",
                    "content": "Can you give me an example sentence?"
                })
                conversation.append({
                    "role": "assistant",
                    "content": f"Sure! Here's an example: {entry.get('example')}"
                })
                
                if entry.get('example_translation'):
                    conversation.append({
                        "role": "assistant",
                        "content": f"That means: {entry.get('example_translation')}"
                    })
            
            chat_data.append({
                "messages": conversation,
                "source": "rakhine_lexicon"
            })
        
        # Save as JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in chat_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return chat_data
    
    def prepare_continued_pretraining(self, corpus_files: List[str], output_file: str):
        """Prepare data for continued pretraining."""
        all_text = []
        
        for corpus_file in corpus_files:
            if Path(corpus_file).exists():
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                    all_text.append(text)
        
        # Also include lexicon as text
        with open('data/lexicon.json', 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        lexicon_text = "Rakhine Language Lexicon:\n\n"
        for entry in lexicon.get('lexicon', []):
            lexicon_text += f"Word: {entry.get('rakhine', '')}\n"
            lexicon_text += f"Meaning: {entry.get('gloss_en', '')}\n"
            if entry.get('example'):
                lexicon_text += f"Example: {entry.get('example')}\n"
            lexicon_text += "\n"
        
        all_text.append(lexicon_text)
        
        # Save as text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_text))
        
        return all_text
    
    def create_huggingface_dataset(self, data_format: str = "alpaca"):
        """Create HuggingFace Dataset for easy fine-tuning."""
        
        if data_format == "alpaca":
            data = self.prepare_alpaca_format(
                "data/lexicon.json",
                "temp_alpaca.jsonl"
            )
            
            # Convert to Dataset
            dataset = Dataset.from_list(data)
            
            # Split
            dataset = dataset.train_test_split(test_size=0.1, seed=42)
            
            # Save
            dataset.save_to_disk("models/llm/rakhine_alpaca_dataset")
            
            # Also push to hub (optional)
            # dataset.push_to_hub("your-username/rakhine-lexicon-alpaca")
            
            return dataset
        
        elif data_format == "chat":
            data = self.prepare_chat_format(
                "data/lexicon.json", 
                "temp_chat.jsonl"
            )
            
            dataset = Dataset.from_list(data)
            dataset = dataset.train_test_split(test_size=0.1, seed=42)
            dataset.save_to_disk("models/llm/rakhine_chat_dataset")
            
            return dataset
    
    def generate_finetuning_scripts(self, output_dir: str, model_name: str = "llama-2-7b"):
        """Generate fine-tuning scripts for different frameworks."""
        
        scripts = {
            "transformers": f"""#!/bin/bash
# Fine-tune with HuggingFace Transformers
export MODEL_NAME="meta-llama/{model_name}"
export DATASET_PATH="models/llm/rakhine_alpaca_dataset"

python -m transformers.finetuning_trainer \\
    --model_name_or_path $MODEL_NAME \\
    --dataset_path $DATASET_PATH \\
    --output_dir models/llm/finetuned \\
    --num_train_epochs 3 \\
    --per_device_train_batch_size 4 \\
    --gradient_accumulation_steps 4 \\
    --learning_rate 2e-5 \\
    --fp16
""",
            
            "axolotl": f"""#!/bin/bash
# Fine-tune with Axolotl
export MODEL_NAME="meta-llama/{model_name}"

accelerate launch -m axolotl.cli.train models/llm/axolotl_config.yml
""",
            
            "litgpt": f"""#!/bin/bash
# Fine-tune with LitGPT
export MODEL_NAME="{model_name}"

python finetune/lora.py \\
    --model_name $MODEL_NAME \\
    --data_path models/llm/rakhine_alpaca_dataset \\
    --out_dir models/llm/finetuned_litgpt
"""
        }
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, script in scripts.items():
            script_file = output_dir / f"finetune_{name}.sh"
            with open(script_file, 'w') as f:
                f.write(script)
            script_file.chmod(0o755)
        
        # Create Axolotl config
        axolotl_config = {
            "base_model": f"meta-llama/{model_name}",
            "model_type": "LlamaForCausalLM",
            "tokenizer_type": "LlamaTokenizer",
            "load_in_8bit": False,
            "load_in_4bit": True,
            "strict": False,
            "datasets": [{
                "path": "models/llm/rakhine_alpaca_dataset",
                "type": "alpaca"
            }],
            "dataset_prepared_path": "models/llm/dataset_prepared",
            "val_set_size": 0.1,
            "output_dir": "models/llm/axolotl_output",
            "adapter": "lora",
            "sequence_len": 2048,
            "sample_packing": True,
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "lora_target_modules": ["q_proj", "v_proj"],
            "gradient_accumulation_steps": 4,
            "micro_batch_size": 2,
            "num_epochs": 3,
            "optimizer": "adamw_bnb_8bit",
            "lr_scheduler": "cosine",
            "learning_rate": 0.0002,
            "train_on_inputs": False,
            "group_by_length": False,
            "bf16": True,
            "fp16": False,
            "tf32": False,
            "gradient_checkpointing": True,
            "logging_steps": 1,
            "flash_attention": True,
            "warmup_steps": 10,
            "weight_decay": 0.0,
            "special_tokens": {
                "bos_token": "<s>",
                "eos_token": "</s>",
                "unk_token": "<unk>"
            }
        }
        
        with open(output_dir / "axolotl_config.yml", 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(axolotl_config, f)
        
        print(f"Generated fine-tuning scripts in {output_dir}")

def main():
    preparer = LLMDataPreparer()
    
    print("Preparing LLM fine-tuning data...")
    
    # Prepare Alpaca format
    alpaca_data = preparer.prepare_alpaca_format(
        "data/lexicon.json",
        "models/llm/alpaca_format.jsonl"
    )
    print(f"Prepared {len(alpaca_data)} Alpaca format examples")
    
    # Prepare Chat format
    chat_data = preparer.prepare_chat_format(
        "data/lexicon.json",
        "models/llm/chat_format.jsonl"
    )
    print(f"Prepared {len(chat_data)} Chat format examples")
    
    # Prepare continued pretraining data
    corpus_files = [
        "corpus/raw/rakhine.txt",
        "corpus/processed/tokenized/rakhine_tokenized.txt"
    ]
    pretrain_data = preparer.prepare_continued_pretraining(
        corpus_files,
        "models/llm/pretraining_data.txt"
    )
    print(f"Prepared {len(pretrain_data)} text segments for continued pretraining")
    
    # Create HuggingFace Dataset
    try:
        dataset = preparer.create_huggingface_dataset("alpaca")
        print(f"Created HuggingFace dataset with {len(dataset['train'])} train, {len(dataset['test'])} test examples")
    except Exception as e:
        print(f"Could not create dataset: {e}")
    
    # Generate fine-tuning scripts
    preparer.generate_finetuning_scripts("models/llm/scripts/")

if __name__ == "__main__":
    main()
