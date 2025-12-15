#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music Analysis Report Script (Using utils.py)
==============================================

This script analyzes music data from multiple artists, calculates popularity scores,
and generates a detailed analysis report.

Usage:
    python music_report.py <target_directory> [--output filename]

Example:
    python music_report.py /path/to/directory --output music_analysis_report.txt
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple, Dict

from utils import FileSystemTools


class MusicAnalyzer:
    """Analyzer that generates music popularity reports"""
    
    def __init__(self, target_dir: str, output_filename: str = "music_analysis_report.txt"):
        """
        Initialize the music analyzer
        
        Args:
            target_dir: Target directory containing music data
            output_filename: Name of the output report file (default: music_analysis_report.txt)
        """
        self.target_dir = target_dir
        self.output_filename = output_filename
        self.songs = []
    
    async def generate_report(self):
        """Main workflow to generate music analysis report"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Find music directory
            print("Step 1: Locating music directory...")
            music_dir = os.path.join(self.target_dir, "music")
            
            # Step 2: Read song data from artists
            print("Step 2: Reading song data...")
            await self._read_artist_data(fs, music_dir)
            print(f"  Found {len(self.songs)} songs\n")
            
            # Step 3: Calculate popularity scores
            print("Step 3: Calculating popularity scores...")
            self._calculate_popularity_scores()
            
            # Step 4: Sort by popularity
            print("Step 4: Sorting songs by popularity...")
            self.songs.sort(key=lambda x: x['popularity_score'], reverse=True)
            
            # Step 5: Generate report
            print("Step 5: Generating report...")
            report = self._generate_report_content()
            
            # Step 6: Write report
            print("Step 6: Writing report...")
            output_path = os.path.join(music_dir, self.output_filename)
            success = await fs.write_file(output_path, report)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Analysis report saved to 'music/{self.output_filename}'")
    
    async def _read_artist_data(self, fs: FileSystemTools, music_dir: str):
        """
        Read song data from all artist directories
        
        Args:
            fs: FileSystemTools instance
            music_dir: Path to music directory
        """
        files, dirs = await fs.list_directory(music_dir)
        
        for artist_dir in dirs:
            artist_path = os.path.join(music_dir, artist_dir)
            artist_files, _ = await fs.list_directory(artist_path)
            
            for filename in artist_files:
                if filename.endswith('.csv') or filename.endswith('.txt'):
                    file_path = os.path.join(artist_path, filename)
                    content = await fs.read_text_file(file_path)
                    
                    if content:
                        print(f"  Reading: {artist_dir}/{filename}")
                        self._parse_song_data(content, filename)
    
    def _parse_song_data(self, content: str, filename: str):
        """
        Parse song data from file content
        
        Args:
            content: File content
            filename: Name of the file
        """
        lines = content.strip().split('\n')
        
        # Determine file format
        if filename.endswith('.csv'):
            # CSV format: skip header, parse data
            for line in lines[1:]:  # Skip header
                if line.strip():
                    self._parse_csv_line(line)
        else:
            # TXT format: parse each line
            for line in lines:
                if line.strip():
                    self._parse_txt_line(line)
    
    def _parse_csv_line(self, line: str):
        """Parse a CSV line"""
        parts = line.split(',')
        if len(parts) >= 4:
            song_name = parts[0].strip()
            try:
                rating = float(parts[1].strip())
                play_count = int(parts[2].strip())
                release_year = int(parts[3].strip())
                
                self.songs.append({
                    'name': song_name,
                    'rating': rating,
                    'play_count': play_count,
                    'release_year': release_year
                })
            except ValueError:
                pass
    
    def _parse_txt_line(self, line: str):
        """Parse a TXT line"""
        # Format: Song Name - Rating: X, Plays: Y, Year: Z
        match = re.match(r'(.+?)\s*-\s*Rating:\s*([\d.]+),\s*Plays:\s*(\d+),\s*Year:\s*(\d+)', line)
        if match:
            song_name = match.group(1).strip()
            rating = float(match.group(2))
            play_count = int(match.group(3))
            release_year = int(match.group(4))
            
            self.songs.append({
                'name': song_name,
                'rating': rating,
                'play_count': play_count,
                'release_year': release_year
            })
    
    def _calculate_popularity_scores(self):
        """Calculate popularity scores for all songs"""
        for song in self.songs:
            rating = song['rating']
            play_count = song['play_count']
            release_year = song['release_year']
            
            # Normalize play count (0-1 scale)
            play_count_normalized = play_count / 250.0
            
            # Calculate year factor (recency bonus)
            year_factor = (2025 - release_year) / 25.0
            
            # Calculate popularity score
            popularity_score = (rating * 0.4) + (play_count_normalized * 0.4) + (year_factor * 0.2)
            
            # Round to 3 decimal places
            song['popularity_score'] = round(popularity_score, 3)
    
    def _generate_report_content(self) -> str:
        """Generate the report content"""
        lines = []
        
        # Lines 1-20: All songs with scores
        for song in self.songs[:20]:
            lines.append(f"{song['name']}:{song['popularity_score']:.3f}")
        
        # Lines 21-25: Top 5 song names only
        for song in self.songs[:5]:
            lines.append(song['name'])
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate music analysis report with popularity scores',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate music analysis report (default output: music_analysis_report.txt)
  python music_report.py /path/to/directory
  
  # Use a custom output filename
  python music_report.py /path/to/directory --output my_report.txt
  
  # The script will:
  # 1. Read song data from music/jay_chou/ and music/jj_lin/
  # 2. Calculate popularity scores using the formula:
  #    popularity_score = (rating × 0.4) + (play_count_normalized × 0.4) + (year_factor × 0.2)
  # 3. Sort songs by popularity score (descending)
  # 4. Generate a 25-line report:
  #    - Lines 1-20: songname:score
  #    - Lines 21-25: Top 5 song names only
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing music data'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='music_analysis_report.txt',
        help='Name of the output report file (default: music_analysis_report.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create analyzer and run
    analyzer = MusicAnalyzer(
        target_dir=args.target_directory,
        output_filename=args.output
    )
    
    try:
        await analyzer.generate_report()
    except Exception as e:
        print(f"\nError during music analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

