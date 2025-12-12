"""
Utility functions for Rakhine lexicon.
"""

import re
import unicodedata
from typing import Optional, Tuple, List, Dict, Any
import json
from pathlib import Path

def normalize_myanmar_text(text: str) -> str:
    """
    Normalize Myanmar Unicode text.
    
    Args:
        text: Input text in Myanmar script
        
    Returns:
        Normalized text
    """
    # Normalize to NFC form
    normalized = unicodedata.normalize('NFC', text)
    
    # Remove zero-width joiners/non-joiners if not needed
    normalized = normalized.replace('\u200c', '')  # ZWNJ
    normalized = normalized.replace('\u200d', '')  # ZWJ
    
    # Normalize spaces
    normalized = ' '.join(normalized.split())
    
    return normalized

def romanize_iso15919(text: str) -> str:
    """
    Convert Myanmar script to ISO 15919 romanization.
    This is a simplified version - would need actual mapping.
    
    Args:
        text: Myanmar script text
        
    Returns:
        Romanized text
    """
    # Basic mapping (incomplete - would need complete mapping)
    mapping = {
        'က': 'k', 'ခ': 'kh', 'ဂ': 'g', 'ဃ': 'gh',
        'င': 'ṅ', 'စ': 'c', 'ဆ': 'ch', 'ဇ': 'j',
        'ဈ': 'jh', 'ဉ': 'ñ', 'ည': 'ñ', 'ဋ': 'ṭ',
        'ဌ': 'ṭh', 'ဍ': 'ḍ', 'ဎ': 'ḍh', 'ဏ': 'ṇ',
        'တ': 't', 'ထ': 'th', 'ဒ': 'd', 'ဓ': 'dh',
        'န': 'n', 'ပ': 'p', 'ဖ': 'ph', 'ဗ': 'b',
        'ဘ': 'bh', 'မ': 'm', 'ယ': 'y', 'ရ': 'r',
        'လ': 'l', 'ဝ': 'w', 'သ': 's', 'ဟ': 'h',
        'ဠ': 'ḷ', 'အ': 'a', 'ဣ': 'i', 'ဤ': 'ī',
        'ဥ': 'u', 'ဦ': 'ū', 'ဧ': 'e', 'ဩ': 'o',
        'ဪ': 'au', 'ါ': 'ā', 'ာ': 'ā', 'ိ': 'i',
        'ီ': 'ī', 'ု': 'u', 'ူ': 'ū', 'ေ': 'e',
        'ဲ': 'ai', 'ံ': 'ṃ', '့': 'ʻ', 'း': 'ḥ',
        '်': '',  # virama
        'ျ': 'y', 'ြ': 'r', 'ွ': 'v', 'ှ': 'h',
    }
    
    romanized = []
    for char in text:
        romanized.append(mapping.get(char, char))
    
    return ''.join(romanized)

def split_syllables(text: str) -> List[str]:
    """
    Split Myanmar text into syllables.
    
    Args:
        text: Myanmar script text
        
    Returns:
        List of syllables
    """
    # Simplified syllable splitting for Myanmar
    # Based on consonant clusters and vowel signs
    pattern = re.compile(r'[\u1000-\u1021\u1023-\u1027\u1029-\u103A\u103C-\u103F\u1040-\u1049\u104C-\u104F]+[\u1031\u1032\u1036\u1037\u1038\u1039]*')
    
    syllables = pattern.findall(text)
    return syllables

def validate_ipa(ipa: str) -> Tuple[bool, Optional[str]]:
    """
    Validate IPA transcription.
    
    Args:
        ipa: IPA string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ipa:
        return True, None
    
    # Check for proper delimiters
    if not (ipa.startswith('/') and ipa.endswith('/')) and \
       not (ipa.startswith('[') and ipa.endswith(']')):
        return False, "IPA must be enclosed in /slashes/ or [brackets]"
    
    # Check for valid IPA characters (simplified)
    ipa_content = ipa[1:-1]
    valid_chars = set("abcdefghijklmnopqrstuvwxyzɑæɐβɓʙçɕɖðɗəɘɛɜɝɞɟʄɡɠɢɣɤɥɦɧħɨɪʝɭɬɫɮʟɱɯɰɲŋɳɴøɵɸθœɶʘɺɻɽɾʀʁɹɻʃʂʈʊʋⱱʌʍɯʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘̩̥̤̪̬̰̺̼̻̹̜̟̠̩̥̬̰̺̼̻̹̜̟̠̊̈̽̈̽̚ˈˌːˑ")
    
    for char in ipa_content:
        if char not in valid_chars and char not in " .;,-":
            return False, f"Invalid IPA character: '{char}'"
    
    return True, None

def extract_phonemes(ipa: str) -> List[str]:
    """
    Extract phonemes from IPA transcription.
    
    Args:
        ipa: IPA string
        
    Returns:
        List of phonemes
    """
    if not ipa:
        return []
    
    # Remove delimiters
    content = ipa[1:-1] if len(ipa) > 1 else ipa
    
    # Split by spaces and remove empty strings
    phonemes = [p.strip() for p in content.split() if p.strip()]
    
    return phonemes

def create_word_family(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group entries by word family (etymological relationships).
    
    Args:
        entries: List of lexicon entries
        
    Returns:
        Dictionary of word families
    """
    families = {}
    
    for entry in entries:
        root = entry.get('root')
        if not root:
            # Try to extract root from the word
            rakhine = entry.get('rakhine', '')
            # Simple heuristic: first consonant
            if rakhine:
                root = rakhine[0]
        
        if root not in families:
            families[root] = []
        
        families[root].append(entry)
    
    return families

def calculate_lexical_density(entries: List[Dict[str, Any]]) -> float:
    """
    Calculate lexical density (content words / total words).
    
    Args:
        entries: List of lexicon entries
        
    Returns:
        Lexical density ratio
    """
    content_pos = {'noun', 'verb', 'adjective', 'adverb'}
    
    content_words = 0
    total_words = 0
    
    for entry in entries:
        pos = entry.get('pos', '').lower()
        if pos in content_pos:
            content_words += 1
        total_words += 1
    
    return content_words / total_words if total_words > 0 else 0

def create_concordance(text: str, word: str, context_chars: int = 50) -> List[Dict[str, Any]]:
    """
    Create concordance for a word in example sentences.
    
    Args:
        text: Text to search in
        word: Word to find
        context_chars: Number of characters of context to show
        
    Returns:
        List of concordance entries
    """
    concordance = []
    
    # Find all occurrences
    pattern = re.compile(re.escape(word), re.IGNORECASE)
    
    for match in pattern.finditer(text):
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        
        left_context = text[start:match.start()]
        right_context = text[match.end():end]
        
        concordance.append({
            'left_context': left_context,
            'word': match.group(),
            'right_context': right_context,
            'position': match.start()
        })
    
    return concordance

def generate_wordlist(entries: List[Dict[str, Any]], 
                      sort_by: str = 'rakhine',
                      reverse: bool = False) -> List[Dict[str, Any]]:
    """
    Generate sorted wordlist from entries.
    
    Args:
        entries: List of lexicon entries
        sort_by: Field to sort by
        reverse: Sort in reverse order
        
    Returns:
        Sorted list of entries
    """
    if not entries:
        return []
    
    # Filter entries that have the sort field
    valid_entries = [e for e in entries if sort_by in e and e[sort_by]]
    
    # Sort
    sorted_entries = sorted(valid_entries, 
                           key=lambda x: x[sort_by].lower() if isinstance(x[sort_by], str) else x[sort_by],
                           reverse=reverse)
    
    return sorted_entries

def export_to_latex(entries: List[Dict[str, Any]], output_file: str):
    """
    Export entries to LaTeX format for linguistic publications.
    
    Args:
        entries: List of lexicon entries
        output_file: Output file path
    """
    latex_template = r"""
\documentclass{article}
\usepackage{fontspec}
\usepackage{multicol}
\usepackage[landscape]{geometry}
\usepackage{linguex}

\newfontfamily\myanmarfont{Padauk}[
  Path = fonts/,
  Extension = .ttf,
  UprightFont = *-Regular,
  BoldFont = *-Bold
]

\title{Rakhine Lexicon}
\author{}
\date{}

\begin{document}

\maketitle

\begin{multicols}{3}
\noindent
"""
    
    entries_text = []
    for entry in entries:
        entry_text = []
        
        if 'rakhine' in entry:
            entry_text.append(r"\textbf{\myanmarfont{" + entry['rakhine'] + r"}}")
        
        if 'romanization' in entry:
            entry_text.append(r"\textsc{" + entry['romanization'] + r"}")
        
        if 'pos' in entry:
            entry_text.append(r"\textit{" + entry['pos'] + r"}")
        
        if 'gloss_en' in entry:
            entry_text.append(r"`" + entry['gloss_en'] + r"'")
        
        if 'example' in entry:
            entry_text.append(r"\myanmarfont{" + entry['example'] + r"}")
        
        entries_text.append(r" \ ".join(entry_text) + r"\\")
    
    latex_template += "\n".join(entries_text)
    latex_template += r"""
\end{multicols}
\end{document}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_template)

def main():
    """Example usage of utility functions."""
    # Test normalization
    text = "ရခိုင်    ဘာသာ"
    normalized = normalize_myanmar_text(text)
    print(f"Normalized: {normalized}")
    
    # Test syllable splitting
    syllables = split_syllables("ရခိုင်ဘာသာ")
    print(f"Syllables: {syllables}")
    
    # Test IPA validation
    ipa = "/lăm/"
    is_valid, error = validate_ipa(ipa)
    print(f"IPA valid: {is_valid}, Error: {error}")
    
    # Test phoneme extraction
    phonemes = extract_phonemes("/lăm/")
    print(f"Phonemes: {phonemes}")

if __name__ == "__main__":
    main()
