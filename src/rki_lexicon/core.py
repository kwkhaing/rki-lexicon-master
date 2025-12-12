"""
Core module for Rakhine lexicon operations.
"""

import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re

@dataclass
class Etymology:
    """Etymology information for a word."""
    source: Optional[str] = None
    original: Optional[str] = None
    cognates: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class Sense:
    """A single sense/meaning of a word."""
    gloss_en: str
    gloss_my: Optional[str] = None
    definition_en: Optional[str] = None
    definition_my: Optional[str] = None
    example: Optional[str] = None
    example_translation: Optional[str] = None
    dialect: Optional[str] = None
    domain: Optional[str] = None  # e.g., 'anatomy', 'agriculture'

@dataclass
class LexiconEntry:
    """A single entry in the Rakhine lexicon."""
    id: str
    rakhine: str
    romanization: str
    pos: str
    senses: List[Sense] = field(default_factory=list)
    
    # Phonological information
    ipa: Optional[str] = None
    syllable_structure: Optional[str] = None
    tone: Optional[str] = None
    
    # Morphological information
    root: Optional[str] = None
    derivation: Optional[str] = None
    inflection: Optional[str] = None
    
    # Additional information
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    etymology: Optional[Etymology] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_sense(self, sense: Sense):
        """Add a new sense to the entry."""
        self.senses.append(sense)
        self.modified = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        result = asdict(self)
        
        # Handle nested dataclasses
        if self.etymology:
            result['etymology'] = asdict(self.etymology)
        
        result['senses'] = [asdict(sense) for sense in self.senses]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LexiconEntry':
        """Create entry from dictionary."""
        # Extract senses
        senses_data = data.pop('senses', [])
        senses = [Sense(**sense_data) for sense_data in senses_data]
        
        # Extract etymology
        etymology_data = data.pop('etymology', None)
        etymology = Etymology(**etymology_data) if etymology_data else None
        
        return cls(senses=senses, etymology=etymology, **data)

class RakhineLexicon:
    """Main lexicon class."""
    
    def __init__(self, data_file: Optional[str] = None):
        self.entries: Dict[str, LexiconEntry] = {}
        self.metadata: Dict[str, Any] = {
            'language': 'Rakhine',
            'iso_code': 'rki',
            'script': 'Myanmar',
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'sources': [],
            'description': 'Digital lexicon for the Rakhine language'
        }
        
        if data_file:
            self.load(data_file)
    
    def load(self, filepath: str):
        """Load lexicon from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data.get('metadata', self.metadata)
        
        entries_data = data.get('lexicon', [])
        for entry_data in entries_data:
            entry = LexiconEntry.from_dict(entry_data)
            self.entries[entry.id] = entry
    
    def save(self, filepath: str):
        """Save lexicon to JSON file."""
        data = {
            'metadata': self.metadata,
            'lexicon': [entry.to_dict() for entry in self.entries.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.metadata['modified'] = datetime.now().isoformat()
    
    def add_entry(self, entry: LexiconEntry):
        """Add a new entry to the lexicon."""
        if entry.id in self.entries:
            raise ValueError(f"Entry with ID {entry.id} already exists")
        
        self.entries[entry.id] = entry
        self.metadata['modified'] = datetime.now().isoformat()
    
    def remove_entry(self, entry_id: str):
        """Remove an entry from the lexicon."""
        if entry_id not in self.entries:
            raise KeyError(f"Entry with ID {entry_id} not found")
        
        del self.entries[entry_id]
        self.metadata['modified'] = datetime.now().isoformat()
    
    def search(self, query: str, field: str = 'rakhine', 
               exact: bool = False) -> List[LexiconEntry]:
        """Search for entries."""
        results = []
        
        for entry in self.entries.values():
            search_value = getattr(entry, field, None)
            if not search_value:
                continue
            
            if isinstance(search_value, str):
                if exact:
                    if query == search_value:
                        results.append(entry)
                else:
                    if query.lower() in search_value.lower():
                        results.append(entry)
            elif isinstance(search_value, list):
                # Search in lists (like synonyms)
                for item in search_value:
                    if query.lower() in item.lower():
                        results.append(entry)
                        break
        
        return results
    
    def search_by_pos(self, pos: str) -> List[LexiconEntry]:
        """Search for entries by part of speech."""
        return [entry for entry in self.entries.values() if entry.pos == pos]
    
    def search_by_dialect(self, dialect: str) -> List[LexiconEntry]:
        """Search for entries by dialect."""
        results = []
        
        for entry in self.entries.values():
            for sense in entry.senses:
                if sense.dialect and dialect.lower() in sense.dialect.lower():
                    results.append(entry)
                    break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get lexicon statistics."""
        total_entries = len(self.entries)
        
        pos_counter = {}
        dialect_counter = {}
        senses_count = 0
        
        for entry in self.entries.values():
            pos_counter[entry.pos] = pos_counter.get(entry.pos, 0) + 1
            senses_count += len(entry.senses)
            
            for sense in entry.senses:
                if sense.dialect:
                    dialect_counter[sense.dialect] = dialect_counter.get(sense.dialect, 0) + 1
        
        return {
            'total_entries': total_entries,
            'total_senses': senses_count,
            'average_senses_per_entry': senses_count / total_entries if total_entries > 0 else 0,
            'pos_distribution': pos_counter,
            'dialect_distribution': dialect_counter,
            'entries_with_ipa': sum(1 for e in self.entries.values() if e.ipa),
            'entries_with_examples': sum(1 for e in self.entries.values() 
                                        if any(s.example for s in e.senses)),
            'entries_with_etymology': sum(1 for e in self.entries.values() if e.etymology),
        }
    
    def export_to_dataframe(self):
        """Export lexicon to pandas DataFrame."""
        import pandas as pd
        
        data = []
        for entry in self.entries.values():
            entry_dict = entry.to_dict()
            
            # Flatten senses
            if entry.senses:
                for i, sense in enumerate(entry.senses):
                    sense_dict = asdict(sense)
                    # Prefix sense fields
                    sense_dict = {f'sense_{i}_{k}': v for k, v in sense_dict.items()}
                    entry_dict.update(sense_dict)
            
            data.append(entry_dict)
        
        return pd.DataFrame(data)
    
    def validate(self) -> List[Dict[str, Any]]:
        """Validate all entries in the lexicon."""
        errors = []
        
        for entry_id, entry in self.entries.items():
            # Check required fields
            if not entry.rakhine:
                errors.append({
                    'entry_id': entry_id,
                    'type': 'missing_field',
                    'field': 'rakhine',
                    'message': 'Missing Rakhine word'
                })
            
            if not entry.romanization:
                errors.append({
                    'entry_id': entry_id,
                    'type': 'missing_field',
                    'field': 'romanization',
                    'message': 'Missing romanization'
                })
            
            if not entry.pos:
                errors.append({
                    'entry_id': entry_id,
                    'type': 'missing_field',
                    'field': 'pos',
                    'message': 'Missing part of speech'
                })
            
            if not entry.senses:
                errors.append({
                    'entry_id': entry_id,
                    'type': 'missing_field',
                    'field': 'senses',
                    'message': 'Entry has no senses'
                })
            else:
                for i, sense in enumerate(entry.senses):
                    if not sense.gloss_en:
                        errors.append({
                            'entry_id': entry_id,
                            'type': 'missing_field',
                            'field': f'sense_{i}_gloss_en',
                            'message': f'Sense {i} missing English gloss'
                        })
        
        return errors

# Example usage
def example_usage():
    """Example of how to use the lexicon."""
    lexicon = RakhineLexicon()
    
    # Create a new entry
    etymology = Etymology(
        source="Pali",
        original="လမ្ម",
        cognates=["Burmese: လမ်း"]
    )
    
    sense = Sense(
        gloss_en="road, path",
        gloss_my="လမ်း",
        definition_en="a way or track laid down for walking or traveling",
        example="လမ်ဒေါ့ရေ။",
        example_translation="Let's go on the road.",
        dialect="Sittwe"
    )
    
    entry = LexiconEntry(
        id="rki_0001",
        rakhine="လမ်",
        romanization="lam",
        pos="noun",
        ipa="/lăm/",
        senses=[sense],
        etymology=etymology,
        notes="Common in daily conversation"
    )
    
    lexicon.add_entry(entry)
    
    # Save to file
    lexicon.save("data/lexicon.json")
    
    # Search
    results = lexicon.search("လမ်")
    print(f"Found {len(results)} entries")
    
    # Get statistics
    stats = lexicon.get_statistics()
    print(f"Total entries: {stats['total_entries']}")

if __name__ == "__main__":
    example_usage()
