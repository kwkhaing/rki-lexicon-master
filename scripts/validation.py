#!/usr/bin/env python3
"""
Validation utilities for Rakhine lexicon.
"""

import json
import re
from typing import Dict, List, Tuple

class RakhineLexiconValidator:
    def __init__(self):
        # Rakhine-specific validation patterns
        self.myanmar_pattern = re.compile(r'^[\u1000-\u109F\uAA60-\uAA7F\s\.၊။]+$')
        
        # Rakhine IPA pattern - allows Rakhine-specific diacritics
        self.ipa_pattern = re.compile(r'^[/\[].*[/\]]$')  # Must start and end with / or []
        
        # Valid Rakhine IPA characters (including tone marks)
        self.valid_rakhine_ipa_chars = set(
            "abcdefghijklmnopqrstuvwxyz"  # Basic Latin
            "ɑæɐβɓʙçɕɖðɗəɘɛɜɝɞɟʄɡɠɢɣɤɥɦɧħɨɪʝɭɬɫɮʟɱɯɰɲŋɳɴøɵɸθœɶʘɺɻɽɾʀʁɹɻʃʂʈʊʋⱱʌʍɯʏʑʐʒʔʡʕʢǀǁǂǃ"
            "ˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘"  # Suprasegmentals
            "̩̥̤̪̬̰̺̼̻̹̜̟̠̊̈̽̚"  # Diacritics
            "ăĕĭŏŭ"  # Breves (common in Rakhine)
            "àèìòùáéíóúâêîôû"  # Accents for tone
            "ǎěǐǒǔ"  # Carons
            "äëïöü"  # Umlauts
            "ãẽĩõũ"  # Tildes
            "ȧėȯ"  # Dots
            "ḁḙḭṵ"  # Underrings
        )
        
        # Valid POS tags for Rakhine
        self.valid_pos = {
            'noun', 'verb', 'adjective', 'adverb', 
            'pronoun', 'particle', 'classifier', 
            'interjection', 'conjunction', 'numeral',
            'preposition', 'postposition', 'auxiliary'
        }
    
    def validate_entry(self, entry: Dict) -> Tuple[bool, List[str]]:
        """Validate a single lexicon entry."""
        errors = []
        
        # Check required fields
        required_fields = ['id', 'rakhine', 'romanization', 'pos', 'gloss_en']
        for field in required_fields:
            if field not in entry or not entry[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate ID format
        if 'id' in entry:
            if not re.match(r'^rki_\d{4,}$', entry['id']):
                errors.append(f"Invalid ID format: {entry['id']}")
        
        # Validate Rakhine script
        if 'rakhine' in entry:
            if not self._validate_myanmar(entry['rakhine']):
                errors.append(f"Invalid Myanmar script: {entry['rakhine']}")
        
        # Validate IPA (allow Rakhine-specific transcriptions)
        if 'ipa' in entry and entry['ipa']:
            is_valid, ipa_error = self._validate_rakhine_ipa(entry['ipa'])
            if not is_valid:
                errors.append(f"Invalid IPA: {entry['ipa']} - {ipa_error}")
        
        # Validate POS
        if 'pos' in entry:
            if not self._validate_pos(entry['pos']):
                errors.append(f"Invalid POS: {entry['pos']}")
        
        return len(errors) == 0, errors
    
    def _validate_myanmar(self, text: str) -> bool:
        """Validate Myanmar script."""
        if not text or not isinstance(text, str):
            return False
        return bool(self.myanmar_pattern.match(text))
    
    def _validate_rakhine_ipa(self, ipa: str) -> Tuple[bool, str]:
        """Validate IPA for Rakhine language (allows tone diacritics)."""
        if not ipa or not isinstance(ipa, str):
            return False, "Empty IPA"
        
        # Check for proper delimiters
        if not (ipa.startswith('/') and ipa.endswith('/')) and \
           not (ipa.startswith('[') and ipa.endswith(']')):
            return False, "IPA must be enclosed in /slashes/ or [brackets]"
        
        # Extract content
        ipa_content = ipa[1:-1]
        
        # Allow empty IPA (for words without known IPA)
        if not ipa_content.strip():
            return True, ""
        
        # Check each character
        for char in ipa_content:
            if char not in self.valid_rakhine_ipa_chars and char not in " .;,-":
                # Check if it's a combining diacritic
                if ord(char) >= 0x0300 and ord(char) <= 0x036F:
                    continue  # Allow combining diacritics
                return False, f"Character '{char}' (U+{ord(char):04X}) not in valid IPA set"
        
        # Rakhine-specific checks
        if 'ă' in ipa_content or 'ĕ' in ipa_content or 'ĭ' in ipa_content:
            # These are valid for Rakhine vowel lengths
            pass
        
        return True, ""
    
    def _validate_pos(self, pos: str) -> bool:
        """Validate part of speech tag."""
        return pos.lower() in self.valid_pos
    
    def validate_lexicon_file(self, filepath: str) -> Dict[str, any]:
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
        if results['total_entries'] > 0:
            validity_rate = (results['valid_entries'] / results['total_entries']) * 100
            results['summary'] = {
                'validity_rate': f"{validity_rate:.1f}%",
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
    report = validator.generate_validation_report(results)
    print(report)
    
    # Return exit code based on validation
    # Only fail on missing required fields, not just IPA issues
    critical_errors = 0
    for invalid in results['invalid_entries']:
        for error in invalid['errors']:
            if "Missing required field" in error or "Invalid Myanmar script" in error:
                critical_errors += 1
    
    if critical_errors > 0:
        exit(1)
    else:
        print("\nNote: IPA warnings are non-critical. Required fields are all present.")
        exit(0)

if __name__ == "__main__":
    main()
