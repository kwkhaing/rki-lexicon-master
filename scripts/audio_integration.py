#!/usr/bin/env python3
"""
Integrate audio files with lexicon database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class AudioIntegrator:
    def __init__(self, db_path: str = "data/lexicon.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with audio tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audio files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT UNIQUE,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            entry_id TEXT,
            speaker_id TEXT,
            dialect TEXT,
            gender TEXT,
            duration REAL,
            sample_rate INTEGER,
            channels INTEGER,
            format TEXT,
            filesize INTEGER,
            recording_date TEXT,
            quality_score REAL,
            FOREIGN KEY (entry_id) REFERENCES lexicon (id)
        )
        ''')
        
        # Create audio features table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_features (
            audio_file_id INTEGER,
            feature_name TEXT,
            feature_value REAL,
            PRIMARY KEY (audio_file_id, feature_name),
            FOREIGN KEY (audio_file_id) REFERENCES audio_files (id)
        )
        ''')
        
        # Create speakers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS speakers (
            speaker_id TEXT PRIMARY KEY,
            gender TEXT,
            age INTEGER,
            dialect TEXT,
            native_speaker BOOLEAN,
            location TEXT,
            other_languages TEXT,
            notes TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of file."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    
    def import_audio_file(self, filepath: str, metadata: Dict) -> int:
        """Import a single audio file into database."""
        filepath = Path(filepath)
        
        # Calculate file hash
        file_hash = self.calculate_file_hash(filepath)
        
        # Get file info
        import soundfile as sf
        with sf.SoundFile(filepath) as f:
            duration = f.frames / f.samplerate
            sample_rate = f.samplerate
            channels = f.channels
            format_info = f"{f.format}-{f.subtype}"
        
        filesize = filepath.stat().st_size
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if file already exists
        cursor.execute('SELECT id FROM audio_files WHERE file_hash = ?', (file_hash,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"File already exists in database: {filepath.name}")
            conn.close()
            return existing[0]
        
        # Insert audio file record
        cursor.execute('''
        INSERT INTO audio_files (
            file_hash, filename, filepath, entry_id, speaker_id, dialect, gender,
            duration, sample_rate, channels, format, filesize, recording_date, quality_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_hash,
            filepath.name,
            str(filepath),
            metadata.get('entry_id'),
            metadata.get('speaker_id'),
            metadata.get('dialect'),
            metadata.get('gender'),
            duration,
            sample_rate,
            channels,
            format_info,
            filesize,
            metadata.get('recording_date'),
            metadata.get('quality_score', 1.0)
        ))
        
        audio_file_id = cursor.lastrowid
        
        # Insert or update speaker information
        if metadata.get('speaker_id'):
            cursor.execute('''
            INSERT OR REPLACE INTO speakers (
                speaker_id, gender, age, dialect, native_speaker, location, other_languages, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata['speaker_id'],
                metadata.get('speaker_gender'),
                metadata.get('speaker_age'),
                metadata.get('dialect'),
                metadata.get('native_speaker', True),
                metadata.get('recording_location'),
                json.dumps(metadata.get('other_languages', [])),
                metadata.get('speaker_notes', '')
            ))
        
        conn.commit()
        conn.close()
        
        return audio_file_id
    
    def link_audio_to_lexicon(self, audio_file_id: int, entry_id: str):
        """Link audio file to lexicon entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE audio_files SET entry_id = ? WHERE id = ?
        ''', (entry_id, audio_file_id))
        
        conn.commit()
        conn.close()
    
    def batch_import_directory(self, directory: str, metadata_file: Optional[str] = None):
        """Import all audio files from directory."""
        # Load metadata if provided
        metadata_map = {}
        if metadata_file and Path(metadata_file).exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
            for meta in metadata_list:
                filename = meta.get('filename')
                if filename:
                    metadata_map[filename] = meta
        
        # Find audio files
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.m4a']:
            audio_files.extend(Path(directory).glob(f'*{ext}'))
        
        results = []
        for audio_file in audio_files:
            print(f"Importing {audio_file.name}...")
            
            # Get metadata for this file
            metadata = metadata_map.get(audio_file.name, {})
            
            # Parse filename for metadata
            parts = audio_file.stem.split('_')
            if len(parts) >= 1 and not metadata.get('entry_id'):
                metadata['entry_id'] = parts[0]
            if len(parts) >= 2 and not metadata.get('speaker_id'):
                metadata['speaker_id'] = parts[1]
            if len(parts) >= 3 and not metadata.get('dialect'):
                metadata['dialect'] = parts[2]
            if len(parts) >= 4 and not metadata.get('gender'):
                metadata['gender'] = parts[3]
            
            try:
                audio_file_id = self.import_audio_file(str(audio_file), metadata)
                
                # Link to lexicon if entry_id is known
                if metadata.get('entry_id'):
                    self.link_audio_to_lexicon(audio_file_id, metadata['entry_id'])
                
                results.append({
                    'filename': audio_file.name,
                    'audio_file_id': audio_file_id,
                    'success': True,
                    'entry_linked': bool(metadata.get('entry_id'))
                })
                
            except Exception as e:
                results.append({
                    'filename': audio_file.name,
                    'success': False,
                    'error': str(e)
                })
        
        # Save import results
        results_file = Path(directory) / "import_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Generate statistics
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        linked = sum(1 for r in results if r.get('entry_linked', False))
        
        print(f"\nImport Summary:")
        print(f"  Total files: {total}")
        print(f"  Successful imports: {successful}")
        print(f"  Linked to lexicon: {linked}")
        
        return results
    
    def query_audio_by_entry(self, entry_id: str) -> List[Dict]:
        """Get all audio files for a lexicon entry."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT af.*, s.age as speaker_age, s.location as speaker_location
        FROM audio_files af
        LEFT JOIN speakers s ON af.speaker_id = s.speaker_id
        WHERE af.entry_id = ?
        ORDER BY af.dialect, af.speaker_id
        ''', (entry_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def query_audio_by_dialect(self, dialect: str) -> List[Dict]:
        """Get all audio files for a specific dialect."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT af.*, l.rakhine, l.romanization, l.gloss_en
        FROM audio_files af
        LEFT JOIN lexicon l ON af.entry_id = l.id
        WHERE af.dialect = ?
        ORDER BY af.entry_id, af.speaker_id
        ''', (dialect,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_database_stats(self) -> Dict:
        """Get statistics about audio database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count total audio files
        cursor.execute('SELECT COUNT(*) FROM audio_files')
        stats['total_audio_files'] = cursor.fetchone()[0]
        
        # Count entries with audio
        cursor.execute('SELECT COUNT(DISTINCT entry_id) FROM audio_files WHERE entry_id IS NOT NULL')
        stats['entries_with_audio'] = cursor.fetchone()[0]
        
        # Count by dialect
        cursor.execute('SELECT dialect, COUNT(*) FROM audio_files GROUP BY dialect')
        stats['files_by_dialect'] = dict(cursor.fetchall())
        
        # Count by speaker
        cursor.execute('SELECT speaker_id, COUNT(*) FROM audio_files GROUP BY speaker_id')
        stats['files_by_speaker'] = dict(cursor.fetchall())
        
        # Total duration
        cursor.execute('SELECT SUM(duration) FROM audio_files')
        total_duration = cursor.fetchone()[0] or 0
        stats['total_duration_hours'] = total_duration / 3600
        
        conn.close()
        
        return stats

def main():
    """Example integration workflow."""
    integrator = AudioIntegrator()
    
    # Import audio files
    print("Importing processed audio files...")
    results = integrator.batch_import_directory(
        "data/processed/audio/normalized/",
        "data/audio_metadata.json"
    )
    
    # Get database statistics
    stats = integrator.get_database_stats()
    print("\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Query example
    print("\nAudio files for entry rki_0001:")
    audio_files = integrator.query_audio_by_entry("rki_0001")
    for af in audio_files:
        print(f"  - {af['filename']} ({af['dialect']}, speaker: {af['speaker_id']})")
    
    # Export database to JSON
    conn = sqlite3.connect("data/lexicon.db")
    conn.row_factory = sqlite3.Row
    
    # Get all audio files with lexicon info
    cursor = conn.cursor()
    cursor.execute('''
    SELECT af.*, l.rakhine, l.romanization, l.pos, l.gloss_en
    FROM audio_files af
    LEFT JOIN lexicon l ON af.entry_id = l.id
    ORDER BY af.entry_id, af.dialect
    ''')
    
    rows = cursor.fetchall()
    audio_data = [dict(row) for row in rows]
    
    with open("data/audio_database_export.json", 'w', encoding='utf-8') as f:
        json.dump(audio_data, f, indent=2, ensure_ascii=False)
    
    conn.close()
    
    print(f"\nExported {len(audio_data)} audio records to JSON")

if __name__ == "__main__":
    main()
