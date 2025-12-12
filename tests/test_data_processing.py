"""
Tests for data processing module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from scripts.data_processing import RakhineLexiconProcessor
from src.rki_lexicon.core import RakhineLexicon, LexiconEntry, Sense, Etymology

class TestRakhineLexiconProcessor:
    @pytest.fixture
    def processor(self):
        return RakhineLexiconProcessor()
    
    @pytest.fixture
    def sample_entry(self):
        return {
            "id": "rki_0001",
            "rakhine": "လမ်",
            "romanization": "lam",
            "pos": "noun",
            "gloss_en": "road",
            "ipa": "/lăm/",
            "example": "လမ်ဒေါ့ရေ။"
        }
    
    @pytest.fixture
    def sample_lexicon(self):
        return {
            "metadata": {
                "language": "Rakhine",
                "iso_code": "rki"
            },
            "lexicon": [
                {
                    "id": "rki_0001",
                    "rakhine": "လမ်",
                    "romanization": "lam",
                    "pos": "noun",
                    "gloss_en": "road"
                },
                {
                    "id": "rki_0002",
                    "rakhine": "ရေ",
                    "romanization": "re",
                    "pos": "noun",
                    "gloss_en": "water"
                }
            ]
        }
    
    def test_validate_entry_valid(self, processor, sample_entry):
        errors = processor.validate_entry(sample_entry)
        assert len(errors) == 0
    
    def test_validate_entry_missing_required(self, processor):
        entry = {"id": "rki_0001", "rakhine": "လမ်"}
        errors = processor.validate_entry(entry)
        assert "Missing required field" in errors[0]
    
    def test_validate_entry_invalid_pos(self, processor):
        entry = {
            "id": "rki_0001",
            "rakhine": "လမ်",
            "romanization": "lam",
            "pos": "invalid_pos",
            "gloss_en": "road"
        }
        errors = processor.validate_entry(entry)
        assert "Invalid POS tag" in errors[0]
    
    def test_validate_entry_invalid_myanmar(self, processor):
        entry = {
            "id": "rki_0001",
            "rakhine": "invalid123",
            "romanization": "lam",
            "pos": "noun",
            "gloss_en": "road"
        }
        errors = processor.validate_entry(entry)
        assert "Invalid Myanmar script" in errors[0]
    
    def test_validate_entry_invalid_ipa(self, processor):
        entry = {
            "id": "rki_0001",
            "rakhine": "လမ်",
            "romanization": "lam",
            "pos": "noun",
            "gloss_en": "road",
            "ipa": "invalid-ipa"
        }
        errors = processor.validate_entry(entry)
        assert "Invalid IPA format" in errors[0]
    
    def test_load_save_lexicon(self, processor, sample_lexicon, tmp_path):
        # Save sample lexicon
        test_file = tmp_path / "test_lexicon.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(sample_lexicon, f, ensure_ascii=False)
        
        # Load it back
        loaded = processor.load_lexicon(str(test_file))
        assert loaded["metadata"]["language"] == "Rakhine"
        assert len(loaded["lexicon"]) == 2
    
    def test_add_entry(self, processor, sample_lexicon):
        new_entry = {
            "rakhine": "ဆာ",
            "romanization": "hsa",
            "pos": "verb",
            "gloss_en": "eat"
        }
        
        updated = processor.add_entry(sample_lexicon, new_entry)
        assert len(updated["lexicon"]) == 3
        assert updated["lexicon"][2]["id"] == "rki_0003"
    
    def test_normalize_romanization(self, processor):
        assert processor.normalize_romanization("nga") == "ṅa"
        assert processor.normalize_romanization("nya") == "ña"
        assert processor.normalize_romanization("shwe") == "śwe"

class TestCoreLexicon:
    @pytest.fixture
    def lexicon(self):
        return RakhineLexicon()
    
    @pytest.fixture
    def sample_entry(self):
        sense = Sense(
            gloss_en="road, path",
            gloss_my="လမ်း",
            definition_en="a way or track for walking"
        )
        
        etymology = Etymology(
            source="Pali",
            original="လမ្ម",
            cognates=["Burmese: လမ်း"]
        )
        
        return LexiconEntry(
            id="rki_0001",
            rakhine="လမ်",
            romanization="lam",
            pos="noun",
            ipa="/lăm/",
            senses=[sense],
            etymology=etymology
        )
    
    def test_add_entry(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        assert len(lexicon.entries) == 1
        assert "rki_0001" in lexicon.entries
    
    def test_add_duplicate_entry(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        with pytest.raises(ValueError):
            lexicon.add_entry(sample_entry)
    
    def test_remove_entry(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        lexicon.remove_entry("rki_0001")
        assert len(lexicon.entries) == 0
    
    def test_remove_nonexistent_entry(self, lexicon):
        with pytest.raises(KeyError):
            lexicon.remove_entry("nonexistent")
    
    def test_search(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        
        results = lexicon.search("လမ်")
        assert len(results) == 1
        
        results = lexicon.search("road", field="gloss_en")
        assert len(results) == 1
        
        results = lexicon.search("nonexistent")
        assert len(results) == 0
    
    def test_search_by_pos(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        
        results = lexicon.search_by_pos("noun")
        assert len(results) == 1
        
        results = lexicon.search_by_pos("verb")
        assert len(results) == 0
    
    def test_get_statistics(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        stats = lexicon.get_statistics()
        
        assert stats["total_entries"] == 1
        assert stats["total_senses"] == 1
        assert "noun" in stats["pos_distribution"]
        assert stats["pos_distribution"]["noun"] == 1
    
    def test_validate(self, lexicon, sample_entry):
        lexicon.add_entry(sample_entry)
        errors = lexicon.validate()
        assert len(errors) == 0
    
    def test_validate_incomplete(self, lexicon):
        # Entry without senses
        entry = LexiconEntry(
            id="rki_0001",
            rakhine="လမ်",
            romanization="lam",
            pos="noun",
            senses=[]
        )
        lexicon.add_entry(entry)
        
        errors = lexicon.validate()
        assert len(errors) > 0
        assert "has no senses" in errors[0]["message"]
    
    def test_save_load(self, lexicon, sample_entry, tmp_path):
        lexicon.add_entry(sample_entry)
        
        test_file = tmp_path / "test_lexicon.json"
        lexicon.save(str(test_file))
        
        # Load into new lexicon
        new_lexicon = RakhineLexicon(str(test_file))
        assert len(new_lexicon.entries) == 1
        assert "rki_0001" in new_lexicon.entries

class TestUtils:
    def test_normalize_myanmar_text(self):
        from src.rki_lexicon.utils import normalize_myanmar_text
        
        text = "ရခိုင်    ဘာသာ"
        normalized = normalize_myanmar_text(text)
        assert "  " not in normalized  # No double spaces
    
    def test_split_syllables(self):
        from src.rki_lexicon.utils import split_syllables
        
        syllables = split_syllables("ရခိုင်ဘာသာ")
        assert len(syllables) > 0
        assert all(isinstance(s, str) for s in syllables)
    
    def test_validate_ipa(self):
        from src.rki_lexicon.utils import validate_ipa
        
        # Valid IPA
        is_valid, error = validate_ipa("/lăm/")
        assert is_valid
        assert error is None
        
        is_valid, error = validate_ipa("[lăm]")
        assert is_valid
        assert error is None
        
        # Invalid IPA
        is_valid, error = validate_ipa("lăm")
        assert not is_valid
        assert "enclosed" in error
    
    def test_extract_phonemes(self):
        from src.rki_lexicon.utils import extract_phonemes
        
        phonemes = extract_phonemes("/l ă m/")
        assert len(phonemes) == 3
        assert "l" in phonemes
        assert "ă" in phonemes
        assert "m" in phonemes
    
    def test_calculate_lexical_density(self):
        from src.rki_lexicon.utils import calculate_lexical_density
        
        entries = [
            {"pos": "noun", "gloss_en": "road"},
            {"pos": "verb", "gloss_en": "go"},
            {"pos": "particle", "gloss_en": "topic"},
            {"pos": "adjective", "gloss_en": "big"}
        ]
        
        density = calculate_lexical_density(entries)
        assert 0 <= density <= 1
        assert density == 0.75  # 3 content words out of 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
