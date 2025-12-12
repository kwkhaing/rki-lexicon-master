#!/usr/bin/env python3
"""
Data processing utilities for Rakhine lexicon.
"""

import json
import pandas as pd
import yaml
from pathlib import Path

def load_lexicon(filepath: str):
    """Load lexicon from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_lexicon(data, filepath: str):
    """Save lexicon to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """Main processing function."""
    print("Processing Rakhine lexicon...")
    
    # Load lexicon
    lexicon = load_lexicon("data/lexicon.json")
    
    # Process entries
    print(f"Loaded {len(lexicon.get('lexicon', []))} entries")
    
    # Export to TSV
    df = pd.DataFrame(lexicon.get('lexicon', []))
    if not df.empty:
        df.to_csv("data/lexicon.tsv", sep='\t', index=False, encoding='utf-8')
        print("Exported to data/lexicon.tsv")
    
    print("Processing complete!")

if __name__ == "__main__":
    main()
