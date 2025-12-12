# Example Entries

## Complete Entry Example
```json
{
  "id": "rki_0423",
  "rakhine": "ဆာ",
  "romanization": "hsa",
  "ipa": "/sʰa/",
  "pos": "verb",
  "gloss_en": "eat",
  "gloss_my": "စား",
  "definition_en": "to put food in the mouth and swallow it",
  "definition_my": "အစာကိုပါးစပ်ထဲထည့်၍မျိုချသည်",
  "example": "ထမင်းဆာရေ။",
  "example_translation": "Let's eat rice.",
  "synonyms": ["အစာစား"],
  "dialect": "Mrauk-U",
  "etymology": {
    "source": "Proto-Sino-Tibetan",
    "original": "*dza",
    "cognates": ["Burmese: စား"]
  },
  "notes": "Basic vocabulary item",
  "source": "Rakhine Dictionary 1998"
}

Minimal Entry

{
  "id": "rki_1001",
  "rakhine": "ရေ",
  "romanization": "re",
  "pos": "noun",
  "gloss_en": "water"
}

Multiple Senses

{
  "id": "rki_0756",
  "rakhine": "မင်",
  "romanization": "mang",
  "pos": "noun",
  "senses": [
    {
      "gloss_en": "ink",
      "definition_en": "colored fluid for writing",
      "example": "မင်နှင့်ရေး။"
    },
    {
      "gloss_en": "tattoo",
      "definition_en": "permanent mark on skin",
      "example": "မင်ထိုး။",
      "dialect": "Northern Rakhine"
    }
  ]
}


## 3. **config/metadata.yaml**
```yaml
project:
  name: "Rakhine Language Lexicon"
  version: "1.0.0"
  description: "Digital lexicon for the Rakhine language (ISO 639-3: rki)"
  
language:
  name: "Rakhine"
  native_name: "ရခိုင်ဘာသာ"
  iso_639_3: "rki"
  family: "Sino-Tibetan"
  branch: "Lolo-Burmese"
  script: "Myanmar"
  country: "Myanmar"
  region: "Rakhine State"
  status: "Vulnerable"
  speakers: "~1,000,000"
  
authors:
  - name: "Your Name"
    affiliation: "Your Institution"
    role: "maintainer"
    orcid: ""

contributors: []

license:
  type: "CC BY-SA 4.0"
  url: "https://creativecommons.org/licenses/by-sa/4.0/"
  
citation:
  apa: "Author, A. (2024). Rakhine Language Lexicon [Data set]."
  bibtex: "@misc{rkilexicon2024,
    title={Rakhine Language Lexicon},
    author={Author, A.},
    year={2024},
    url={https://github.com/yourusername/rki-lexicon}
  }"

data_sources:
  - name: "Rakhine Dictionary"
    year: 1998
    publisher: "Rakhine Language Commission"
    type: "print"
    
  - name: "Fieldwork Data"
    year: "2020-2024"
    collector: "Research Team"
    type: "primary"

last_updated: "2024-01-01"
