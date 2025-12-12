#!/usr/bin/env python3
"""
Validation utilities for Rakhine lexicon.
"""

import json
import re
from typing import Dict, List, Tuple, Set
import unicodedata

class RakhineLexiconValidator:
    def __init__(self):
        # Rakhine-specific validation patterns
        self.myanmar_pattern = re.compile(r'^[\u1000-\u109F\uAA60-\uAA7F\s\.၊။]+$')
        self.ipa_pattern = re.compile(r'^[/\[].*[/\]]$')  # Must start and end with / or []
        
        # ISO 15919 Romanization pattern (simplified)
        self.romanization_pattern = re.compile(r'^[a-zA-Zāīūṛṝḷḹēōṃḥṅñṭḍṇśṣḻ\s\.\-]+$')
        
        # Valid POS tags
        self.valid_pos = {
            'noun', 'verb', 'adjective', 'adverb', 
            'pronoun', 'particle', 'classifier', 
            'interjection', 'conjunction', 'numeral',
            'preposition', 'postposition', 'auxiliary'
        }
    
    def validate_entry(self, entry: Dict) -> Tuple[bool, List[str]]:
        """Validate a single lexicon entry."""
        errors = []
        
        # Check ID format
        if 'id' in entry:
            if not self._validate_id(entry['id']):
                errors.append(f"Invalid ID format: {entry['id']}")
        
        # Validate Rakhine script
        if 'rakhine' in entry:
            if not self._validate_myanmar(entry['rakhine']):
                errors.append(f"Invalid Myanmar script: {entry['rakhine']}")
        
        # Validate romanization
        if 'romanization' in entry:
            if not self._validate_romanization(entry['romanization']):
                errors.append(f"Invalid romanization: {entry['romanization']}")
        
        # Validate IPA
        if 'ipa' in entry and entry['ipa']:
            if not self._validate_ipa(entry['ipa']):
                errors.append(f"Invalid IPA: {entry['ipa']}")
        
        # Validate POS
        if 'pos' in entry:
            if not self._validate_pos(entry['pos']):
                errors.append(f"Invalid POS: {entry['pos']}. Valid: {sorted(self.valid_pos)}")
        
        # Validate gloss languages
        if 'gloss_en' in entry and not entry['gloss_en']:
            errors.append("Empty English gloss")
        
        # Check for duplicate fields
        if self._has_duplicate_meanings(entry):
            errors.append("Entry may have duplicate meanings")
        
        return len(errors) == 0, errors
    
    def _validate_id(self, entry_id: str) -> bool:
        """Validate entry ID format."""
        return bool(re.match(r'^rki_\d{4,}$', entry_id))
    
    def _validate_myanmar(self, text: str) -> bool:
        """Validate Myanmar script."""
        if not text or not isinstance(text, str):
            return False
        return bool(self.myanmar_pattern.match(text))
    
    def _validate_romanization(self, text: str) -> bool:
        """Validate romanization format."""
        if not text or not isinstance(text, str):
            return False
        return bool(self.romanization_pattern.match(text))
    
    def _validate_ipa(self, ipa: str) -> bool:
        """Validate IPA transcription."""
        if not ipa or not isinstance(ipa, str):
            return False
        
        # Check format
        if not self.ipa_pattern.match(ipa):
            return False
        
        # Basic IPA character check (simplified)
        ipa_content = ipa[1:-1]  # Remove slashes/brackets
        valid_ipa_chars = set("abcdefghijklmnopqrstuvwxyzɑæɐβɓʙçɕɖðɗəɘɛɜɝɞɟʄɡɠɢɣɤɥɦɧħɨɪʝɭɬɫɮʟɱɯɰɲŋɳɴøɵɸθœɶʘɺɻɽɾʀʁɹɻʃʂʈʊʋⱱʌʍɯʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘̩̥̤̪̬̰̺̼̻̹̜̟̠̩̥̬̰̺̼̻̹̜̟̠̊̈̽̈̽̚ˈˌːˑ")
        
        for char in ipa_content:
            if char not in valid_ipa_chars and char not in " .;,-":
                return False
        
        return True
    
    def _validate_pos(self, pos: str) -> bool:
        """Validate part of speech tag."""
        return pos.lower() in self.valid_pos
    
    def _has_duplicate_meanings(self, entry: Dict) -> bool:
        """Check for potentially duplicate meanings."""
        # Simple check for identical glosses in different languages
        if 'gloss_en' in entry and 'gloss_my' in entry:
            if entry['gloss_en'].lower() == entry['gloss_my'].lower():
                return True
        return False
    
    def validate_lexicon_file(self, filepath: str) -> Dict[str, Any]:
        """Validate entire lexicon file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = {
            'total_entries': 0,
            'valid_entries': 0,
            'invalid_entries': [],
            'summary': {}
        }
        
        if 'lexicon' not in data:
            return {'error': 'No lexicon data found'}
        
        results['total_entries'] = len(data['lexicon'])
        
        for idx, entry in enumerate(data['lexicon']):
            is_valid, errors = self.validate_entry(entry)
            
            if is_valid:
                results['valid_entries'] += 1
            else:
                results['invalid_entries'].append({
                    'index': idx,
                    'id': entry.get('id', f'entry_{idx}'),
                    'errors': errors
                })
        
        # Generate summary
        results['summary'] = {
            'validity_rate': f"{(results['valid_entries'] / results['total_entries']) * 100:.1f}%",
            'total_errors': sum(len(e['errors']) for e in results['invalid_entries'])
        }
        
        return results
    
    def generate_validation_report(self, validation_results: Dict, output_path: str = None):
        """Generate a validation report."""
        report = []
        report.append("=" * 60)
        report.append("RAKHINE LEXICON VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal entries: {validation_results['total_entries']}")
        report.append(f"Valid entries: {validation_results['valid_entries']}")
        report.append(f"Invalid entries: {len(validation_results['invalid_entries'])}")
        
        if 'summary' in validation_results:
            report.append(f"\nSummary: {validation_results['summary']}")
        
        if validation_results['invalid_entries']:
            report.append("\n" + "=" * 60)
            report.append("INVALID ENTRIES DETAIL")
            report.append("=" * 60)
            
            for invalid in validation_results['invalid_entries']:
                report.append(f"\nEntry {invalid['index']} (ID: {invalid['id']}):")
                for error in invalid['errors']:
                    report.append(f"  - {error}")
        
        report_text = "\n".join(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text

def main():
    """Run validation on lexicon."""
    validator = RakhineLexiconValidator()
    
    # Validate lexicon file
    results = validator.validate_lexicon_file("data/lexicon.json")
    
    # Generate report
    report = validator.generate_validation_report(results, "data/validation_report.txt")
    print(report)
    
    # Return exit code based on validation
    if len(results['invalid_entries']) > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
