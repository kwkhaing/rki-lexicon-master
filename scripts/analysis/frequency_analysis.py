#!/usr/bin/env python3
"""
Frequency analysis of Rakhine lexicon.
"""

import json
from collections import Counter, defaultdict
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class FrequencyAnalyzer:
    def __init__(self, lexicon_file: str = "data/lexicon.json"):
        """Initialize analyzer with lexicon data."""
        with open(lexicon_file, 'r', encoding='utf-8') as f:
            self.lexicon_data = json.load(f)
        
        self.entries = self.lexicon_data.get('lexicon', [])
    
    def analyze_pos_distribution(self) -> Dict[str, int]:
        """Analyze distribution of parts of speech."""
        pos_counter = Counter()
        
        for entry in self.entries:
            pos = entry.get('pos', 'unknown')
            pos_counter[pos] += 1
        
        return dict(pos_counter)
    
    def analyze_word_length(self, field: str = 'rakhine') -> Dict[str, any]:
        """Analyze word length distribution."""
        lengths = []
        
        for entry in self.entries:
            if field in entry:
                word = entry[field]
                # Count characters (excluding spaces)
                length = len(word.strip())
                lengths.append(length)
        
        if not lengths:
            return {}
        
        return {
            'mean': sum(lengths) / len(lengths),
            'median': sorted(lengths)[len(lengths) // 2],
            'min': min(lengths),
            'max': max(lengths),
            'distribution': dict(Counter(lengths))
        }
    
    def find_common_words(self, n: int = 20, field: str = 'gloss_en') -> List[Tuple[str, int]]:
        """Find most common words in a given field."""
        words = []
        
        for entry in self.entries:
            if field in entry and entry[field]:
                # Split by comma/semicolon for multiple glosses
                glosses = str(entry[field]).replace(';', ',').split(',')
                for gloss in glosses:
                    words.append(gloss.strip().lower())
        
        word_counter = Counter(words)
        return word_counter.most_common(n)
    
    def analyze_dialects(self) -> Dict[str, int]:
        """Analyze dialect distribution."""
        dialect_counter = Counter()
        
        for entry in self.entries:
            dialect = entry.get('dialect', 'unspecified')
            dialect_counter[dialect] += 1
        
        return dict(dialect_counter)
    
    def find_examples(self) -> Dict[str, int]:
        """Analyze entries with example sentences."""
        with_examples = 0
        total = len(self.entries)
        
        for entry in self.entries:
            if entry.get('example'):
                with_examples += 1
        
        return {
            'with_examples': with_examples,
            'without_examples': total - with_examples,
            'percentage': (with_examples / total * 100) if total > 0 else 0
        }
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive analysis report."""
        report = []
        
        report.append("=" * 60)
        report.append("RAKHINE LEXICON FREQUENCY ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Basic statistics
        total_entries = len(self.entries)
        report.append(f"\nTotal entries: {total_entries}")
        
        # POS distribution
        pos_dist = self.analyze_pos_distribution()
        report.append(f"\nPart of Speech Distribution:")
        for pos, count in sorted(pos_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_entries) * 100
            report.append(f"  {pos:15s}: {count:4d} ({percentage:5.1f}%)")
        
        # Word length analysis
        length_stats = self.analyze_word_length('rakhine')
        if length_stats:
            report.append(f"\nRakhine Word Length:")
            report.append(f"  Average length: {length_stats['mean']:.1f} characters")
            report.append(f"  Median length: {length_stats['median']} characters")
            report.append(f"  Range: {length_stats['min']} - {length_stats['max']} characters")
        
        # Common English glosses
        common_glosses = self.find_common_words(15, 'gloss_en')
        report.append(f"\nMost Common English Glosses (top 15):")
        for gloss, count in common_glosses:
            report.append(f"  {gloss:20s}: {count:3d}")
        
        # Dialect analysis
        dialect_dist = self.analyze_dialects()
        if len(dialect_dist) > 1:
            report.append(f"\nDialect Distribution:")
            for dialect, count in sorted(dialect_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_entries) * 100
                report.append(f"  {dialect:15s}: {count:4d} ({percentage:5.1f}%)")
        
        # Example sentences
        example_stats = self.find_examples()
        report.append(f"\nExample Sentences:")
        report.append(f"  With examples: {example_stats['with_examples']} ({example_stats['percentage']:.1f}%)")
        report.append(f"  Without examples: {example_stats['without_examples']}")
        
        # Field completeness
        report.append(f"\nField Completeness:")
        total_fields = 0
        filled_fields = 0
        
        # Define important fields
        important_fields = ['rakhine', 'romanization', 'pos', 'gloss_en', 
                           'definition_en', 'example', 'ipa']
        
        for field in important_fields:
            field_count = sum(1 for entry in self.entries if entry.get(field))
            percentage = (field_count / total_entries) * 100
            report.append(f"  {field:20s}: {field_count:4d} ({percentage:5.1f}%)")
            total_fields += total_entries
            filled_fields += field_count
        
        overall_completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        report.append(f"\nOverall completeness: {overall_completeness:.1f}%")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text
    
    def create_visualizations(self, output_dir: str = "data/analysis/plots"):
        """Create visualization plots."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        # 1. POS Distribution Plot
        pos_dist = self.analyze_pos_distribution()
        if pos_dist:
            plt.figure(figsize=(10, 6))
            pos_df = pd.DataFrame(list(pos_dist.items()), columns=['POS', 'Count'])
            pos_df = pos_df.sort_values('Count', ascending=False)
            
            bars = plt.bar(pos_df['POS'], pos_df['Count'])
            plt.xlabel('Part of Speech')
            plt.ylabel('Frequency')
            plt.title('Distribution of Parts of Speech')
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(f"{output_dir}/pos_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Word Length Distribution Plot
        length_stats = self.analyze_word_length('rakhine')
        if length_stats and 'distribution' in length_stats:
            plt.figure(figsize=(10, 6))
            length_dist = length_stats['distribution']
            
            lengths = list(length_dist.keys())
            frequencies = list(length_dist.values())
            
            plt.bar(lengths, frequencies)
            plt.xlabel('Word Length (characters)')
            plt.ylabel('Frequency')
            plt.title('Distribution of Rakhine Word Lengths')
            plt.axvline(x=length_stats['mean'], color='r', linestyle='--', 
                       label=f"Mean: {length_stats['mean']:.1f}")
            plt.axvline(x=length_stats['median'], color='g', linestyle=':', 
                       label=f"Median: {length_stats['median']}")
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"{output_dir}/word_length_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Dialect Distribution Pie Chart (if data exists)
        dialect_dist = self.analyze_dialects()
        if len(dialect_dist) > 1:
            plt.figure(figsize=(8, 8))
            
            # Filter out 'unspecified' if it's too large
            filtered_dialects = {k: v for k, v in dialect_dist.items() 
                                if k != 'unspecified' or v < sum(dialect_dist.values()) / 2}
            
            labels = list(filtered_dialects.keys())
            sizes = list(filtered_dialects.values())
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('Dialect Distribution in Lexicon')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/dialect_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"Visualizations saved to {output_dir}/")

def main():
    """Run frequency analysis and generate reports."""
    analyzer = FrequencyAnalyzer()
    
    # Generate text report
    report = analyzer.generate_report("data/analysis/frequency_report.txt")
    print(report)
    
    # Create visualizations
    analyzer.create_visualizations()
    
    # Save data for further analysis
    pos_dist = analyzer.analyze_pos_distribution()
    with open("data/analysis/pos_distribution.json", 'w', encoding='utf-8') as f:
        json.dump(pos_dist, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
