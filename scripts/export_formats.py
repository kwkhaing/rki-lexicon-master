#!/usr/bin/env python3
"""
Export Rakhine lexicon to various formats.
"""

import json
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Any
import csv

class LexiconExporter:
    def __init__(self, lexicon_data: Dict[str, Any]):
        self.lexicon_data = lexicon_data
        self.entries = lexicon_data.get('lexicon', [])
        self.metadata = lexicon_data.get('metadata', {})
    
    def to_json(self, filepath: str, pretty: bool = True):
        """Export to JSON format."""
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(self.lexicon_data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(self.lexicon_data, f, ensure_ascii=False)
    
    def to_tsv(self, filepath: str):
        """Export to TSV format."""
        if not self.entries:
            return
        
        # Get all unique field names
        fieldnames = set()
        for entry in self.entries:
            fieldnames.update(entry.keys())
        
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(self.entries)
    
    def to_xml(self, filepath: str):
        """Export to XML format (TEI-like)."""
        # Create root element
        root = ET.Element("lexicon")
        root.set("language", self.metadata.get('language', 'Rakhine'))
        root.set("iso_code", self.metadata.get('iso_code', 'rki'))
        
        # Add metadata
        metadata_elem = ET.SubElement(root, "metadata")
        for key, value in self.metadata.items():
            meta_elem = ET.SubElement(metadata_elem, key)
            meta_elem.text = str(value)
        
        # Add entries
        entries_elem = ET.SubElement(root, "entries")
        for entry in self.entries:
            entry_elem = ET.SubElement(entries_elem, "entry")
            
            for key, value in entry.items():
                if isinstance(value, list):
                    # Handle lists (like synonyms)
                    list_elem = ET.SubElement(entry_elem, key)
                    for item in value:
                        item_elem = ET.SubElement(list_elem, "item")
                        item_elem.text = str(item)
                elif isinstance(value, dict):
                    # Handle dictionaries (like etymology)
                    dict_elem = ET.SubElement(entry_elem, key)
                    for k, v in value.items():
                        sub_elem = ET.SubElement(dict_elem, k)
                        sub_elem.text = str(v)
                else:
                    elem = ET.SubElement(entry_elem, key)
                    elem.text = str(value)
        
        # Write to file with pretty printing
        xml_str = ET.tostring(root, encoding='utf-8')
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def to_sql(self, filepath: str):
        """Export to SQL format."""
        if not self.entries:
            return
        
        sql_statements = []
        
        # Create table
        sql_statements.append("""
CREATE TABLE IF NOT EXISTS lexicon (
    id TEXT PRIMARY KEY,
    rakhine TEXT NOT NULL,
    romanization TEXT,
    ipa TEXT,
    pos TEXT,
    gloss_en TEXT,
    gloss_my TEXT,
    definition_en TEXT,
    definition_my TEXT,
    example TEXT,
    example_translation TEXT,
    dialect TEXT,
    notes TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
        
        # Insert data
        for entry in self.entries:
            # Escape single quotes
            def escape(text):
                return str(text).replace("'", "''") if text else ""
            
            columns = []
            values = []
            
            for key, value in entry.items():
                if value is not None:
                    columns.append(key)
                    if isinstance(value, (list, dict)):
                        values.append(f"'{json.dumps(value)}'")
                    else:
                        values.append(f"'{escape(value)}'")
            
            if columns:
                columns_str = ", ".join(columns)
                values_str = ", ".join(values)
                sql_statements.append(f"INSERT INTO lexicon ({columns_str}) VALUES ({values_str});")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(sql_statements))
    
    def to_markdown(self, filepath: str, limit: int = None):
        """Export to Markdown format for documentation."""
        entries = self.entries[:limit] if limit else self.entries
        
        md_lines = [
            "# Rakhine Lexicon",
            f"\n**Total entries:** {len(self.entries)}",
            f"**Language:** {self.metadata.get('language', 'Rakhine')} ({self.metadata.get('iso_code', 'rki')})",
            f"**Version:** {self.metadata.get('version', '1.0.0')}",
            f"**Last updated:** {self.metadata.get('last_updated', 'N/A')}",
            "\n---\n"
        ]
        
        for entry in entries:
            md_lines.append(f"\n## {entry.get('id', 'N/A')}")
            md_lines.append(f"\n**Rakhine:** {entry.get('rakhine', 'N/A')}")
            md_lines.append(f"**Romanization:** {entry.get('romanization', 'N/A')}")
            
            if entry.get('ipa'):
                md_lines.append(f"**IPA:** {entry.get('ipa')}")
            
            md_lines.append(f"**Part of speech:** {entry.get('pos', 'N/A')}")
            md_lines.append(f"**English gloss:** {entry.get('gloss_en', 'N/A')}")
            
            if entry.get('gloss_my'):
                md_lines.append(f"**Burmese gloss:** {entry.get('gloss_my')}")
            
            if entry.get('definition_en'):
                md_lines.append(f"\n**Definition:** {entry.get('definition_en')}")
            
            if entry.get('example'):
                md_lines.append(f"\n**Example:** {entry.get('example')}")
                if entry.get('example_translation'):
                    md_lines.append(f"*Translation:* {entry.get('example_translation')}")
            
            if entry.get('notes'):
                md_lines.append(f"\n**Notes:** {entry.get('notes')}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
    
    def to_excel(self, filepath: str):
        """Export to Excel format."""
        if not self.entries:
            return
        
        df = pd.DataFrame(self.entries)
        
        # Reorder columns for better readability
        preferred_order = ['id', 'rakhine', 'romanization', 'ipa', 'pos', 
                          'gloss_en', 'gloss_my', 'definition_en', 'definition_my',
                          'example', 'example_translation', 'dialect', 'notes', 'source']
        
        # Only include columns that exist
        columns = [col for col in preferred_order if col in df.columns]
        columns += [col for col in df.columns if col not in preferred_order]
        
        df = df[columns]
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Lexicon', index=False)
            
            # Add metadata sheet
            metadata_df = pd.DataFrame([self.metadata])
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Lexicon']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

def main():
    """Export lexicon to all formats."""
    # Load lexicon
    with open("data/lexicon.json", 'r', encoding='utf-8') as f:
        lexicon_data = json.load(f)
    
    exporter = LexiconExporter(lexicon_data)
    
    # Export to various formats
    print("Exporting lexicon to various formats...")
    
    exporter.to_json("data/exports/lexicon.json")
    print("  ✓ JSON export complete")
    
    exporter.to_tsv("data/exports/lexicon.tsv")
    print("  ✓ TSV export complete")
    
    exporter.to_xml("data/exports/lexicon.xml")
    print("  ✓ XML export complete")
    
    exporter.to_sql("data/exports/lexicon.sql")
    print("  ✓ SQL export complete")
    
    exporter.to_markdown("data/exports/lexicon.md", limit=50)
    print("  ✓ Markdown export complete (first 50 entries)")
    
    exporter.to_excel("data/exports/lexicon.xlsx")
    print("  ✓ Excel export complete")
    
    print("\nAll exports saved to data/exports/")

if __name__ == "__main__":
    main()
