# Rakhine Orthography Rules

## Script and Encoding
- **Script**: Myanmar script (Burmese script)
- **Encoding**: Unicode UTF-8
- **Normalization**: NFC (Normalization Form C)

## Consonants
Rakhine uses the following consonants from the Myanmar script:

### Basic Consonants
က (ka) ခ (kha) ဂ (ga) ဃ (gha) င (ṅa)
စ (ca) ဆ (cha) ဇ (ja) ဈ (jha) ဉ/ည (ña)
ဋ (ṭa) ဌ (ṭha) ဍ (ḍa) ဎ (ḍha) ဏ (ṇa)
တ (ta) ထ (tha) ဒ (da) ဓ (dha) န (na)
ပ (pa) ဖ (pha) ဗ (ba) ဘ (bha) မ (ma)
ယ (ya) ရ (ra) လ (la) ဝ (wa) သ (sa)
ဟ (ha) ဠ (ḷa) အ (a)

## Vowels and Diacritics

### Independent Vowels

အ (a) ဣ (i) ဤ (ī) ဥ (u) ဦ (ū)
ဧ (e) ဩ (o) ဪ (au)

### Dependent Vowels (Diacritics)

ာ (ā) ါ (ā) ိ (i) ီ (ī) ု (u)
ူ (ū) ေ (e) ဲ (ai) ံ (ṃ) ့ (ʻ)
း (ḥ) ျ (ya) ြ (ra) ွ (va) ှ (ha)

## Special Characters

### Virama (Killer)
- `်` (Asat) - Used to kill the inherent vowel

### Stacked Consonants
Rakhine uses consonant stacking for certain clusters:
- `က္က` (kka)
- `ပ္ပ` (ppa)
- `မ္မ` (mma)

## Punctuation

။ (section delimiter)
၊ (phrase delimiter)


## Romanization (ISO 15919)

### Basic Principles
1. Each Myanmar character maps to a specific Latin character
2. Vowel diacritics modify the inherent vowel
3. Consonant clusters are represented directly

### Mapping Table
| Myanmar | ISO 15919 | Example |
|---------|-----------|---------|
| က | k | ကား → kā |
| ခ | kh | ခါ → khā |
| ဂ | g | ဂါ → gā |
| င | ṅ | ငါ → ṅā |
| ည | ñ | ညါ → ñā |
| အ | a | အံ → aṃ |
| ာ | ā | ကာ → kā |
| ိ | i | ကိ → ki |
| ေ | e | ကေ → ke |
| ံ | ṃ | ကံ → kaṃ |
| ့ | ʻ | က့ → kaʻ |

## IPA Transcription Guidelines

### Consonants
- က: /k/
- ခ: /kʰ/
- ဂ: /g/
- င: /ŋ/
- စ: /s/
- ဆ: /sʰ/
- ည: /ɲ/
- တ: /t/
- ထ: /tʰ/
- န: /n/
- ပ: /p/
- ဖ: /pʰ/
- မ: /m/
- ယ: /j/
- ရ: /r/ or /ɹ/
- လ: /l/
- ဝ: /w/
- သ: /θ/ or /ð/
- ဟ: /h/

### Vowels
- a: /a/
- i: /i/
- u: /u/
- e: /e/
- o: /o/
- ai: /ai/
- au: /au/

### Tone
Rakhine is a tonal language. Use diacritics:
- High tone: ◌́ (acute)
- Low tone: ◌̀ (grave)
- Creaky tone: ◌̰ (tilde below)

## Dialectal Variations

### Sittwe Dialect
- Preserves older phonology
- Clear tone distinctions

### Mrauk-U Dialect
- Some vowel shifts
- Influence of neighboring languages

### Northern Rakhine
- Different intonation patterns
- Lexical variations

## Data Entry Guidelines

### Required Format
1. Always use Unicode Myanmar text
2. Include tone marks when known
3. Use standard punctuation
4. Separate words with spaces
5. Normalize to NFC form

### Common Pitfalls to Avoid
1. Don't mix scripts
2. Don't use proprietary encodings
3. Don't omit tone marks if known
4. Don't use non-standard abbreviations

## References
1. Rakhine Language Commission. (1998). *Rakhine Dictionary*.
2. ISO 15919:2001. *Transliteration of Devanagari and related scripts*.
3. Unicode Consortium. (2023). *The Unicode Standard*.
   
