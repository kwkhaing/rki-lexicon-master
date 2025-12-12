# Data Format Specification

## Entry Structure

### Required Fields
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | string | Unique identifier | `rki_0001` |
| rakhine | string | Word in Myanmar script | `လမ်` |
| romanization | string | ISO 15919 transliteration | `lam` |
| pos | string | Part of speech | `noun` |
| gloss_en | string | English gloss | `road` |

### Optional Fields
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| ipa | string | IPA transcription | `/lăm/` |
| gloss_my | string | Burmese gloss | `လမ်း` |
| definition_en | string | English definition | `a way or track for walking` |
| definition_my | string | Burmese definition | `သွားလာရန်လမ်း` |
| example | string | Example sentence | `လမ်ဒေါ့ရေ။` |
| example_translation | string | Translation | `Let's go on the road.` |
| synonyms | array | List of synonyms | `["လမ်း", "ခရီးလမ်း"]` |
| antonyms | array | List of antonyms | `["ပိတ်လမ်း"]` |
| dialect | string | Regional variant | `Sittwe` |
| etymology | object | Word origin | `{"source": "Pali", "original": "လမ្ម"}` |
| notes | string | Additional notes | `Common in daily conversation` |
| source | string | Source reference | `U Tha Tun 2015` |

## IPA Guidelines
- Use slashes `/` for phonemic transcription
- Use brackets `[ ]` for phonetic transcription
- Follow IPA standards for Rakhine

## Validation Rules
1. All Myanmar script must be valid Unicode
2. Romanization follows ISO 15919
3. IPA uses standard symbols
4. Part of speech must be from approved list
