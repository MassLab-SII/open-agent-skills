#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music Analysis Report Script (Using utils.py)
==============================================

This script analyzes music data from multiple artists, calculates popularity scores,
and generates a detailed analysis report.

Usage:
    python music_report.py <target_directory> [--output filename] [--rating-weight W1] [--play-count-weight W2] [--year-weight W3]

Example:
    python music_report.py /path/to/directory --output music_analysis_report.txt
    python music_report.py /path/to/directory --rating-weight 0.5 --play-count-weight 0.3 --year-weight 0.2
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple, Dict

from utils import FileSystemTools


class MusicAnalyzer:
    """Analyzer that generates music popularity reports"""
    
    def __init__(self, target_dir: str, output_filename: str = "music_analysis_report.txt",
                 rating_weight: float = 0.4, play_count_weight: float = 0.4, year_weight: float = 0.2):
        """
        Initialize the music analyzer
        
        Args:
            target_dir: Target directory containing music data
            output_filename: Name of the output report file (default: music_analysis_report.txt)
            rating_weight: Weight for rating in popularity score (default: 0.4)
            play_count_weight: Weight for normalized play count in popularity score (default: 0.4)
            year_weight: Weight for year factor in popularity score (default: 0.2)
        """
        self.target_dir = target_dir
        self.output_filename = output_filename
        self.rating_weight = rating_weight
        self.play_count_weight = play_count_weight
        self.year_weight = year_weight
        self.songs = []
    
    async def generate_report(self):
        """Main workflow to generate music analysis report"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Find music directory
            print("Step 1: Locating music directory...")
            if self.target_dir.rstrip('/').rstrip('\\').endswith('music'):
                music_dir = self.target_dir
            else:
                music_dir = os.path.join(self.target_dir, 'music')
            
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
            # TXT format: parse multi-line block format
            self._parse_txt_content(content)
    
    def _parse_csv_line(self, line: str):
        """Parse a CSV line"""
        # The CSV format is: song_name,album,year,rating,play_count,notes
        # Note: The 'notes' field may contain commas, so we limit the split to 5 parts
        # (song_name, album, year, rating, play_count, rest_of_line)
        parts = line.split(',', 5)
        
        if len(parts) >= 5:
            song_name = parts[0].strip()
            # parts[1] is album (unused)
            try:
                release_year = int(parts[2].strip())
                rating = float(parts[3].strip())
                play_count = int(parts[4].strip())
                
                self.songs.append({
                    'name': song_name,
                    'rating': rating,
                    'play_count': play_count,
                    'release_year': release_year
                })
            except ValueError:
                pass
    
    def _parse_txt_content(self, content: str):
        """
        Parse TXT content in multi-line block format.
        
        Expected format:
        N. song-name (Year)
           - Album: ...
           - Features: ...
           - Personal Rating: ⭐⭐⭐⭐⭐
           - Play Count: XXX+
        """
        lines = content.split('\n')
        
        current_song = None
        
        for line in lines:
            # Match song header: "N. SongName (Year)"
            header_match = re.match(r'^\d+\.\s*(.+?)\s*\((\d{4})\)', line)
            if header_match:
                # Save previous song if exists
                if current_song and self._is_complete_song(current_song):
                    self.songs.append(current_song)
                
                # Start new song
                current_song = {
                    'name': header_match.group(1).strip(),
                    'release_year': int(header_match.group(2)),
                    'rating': None,
                    'play_count': None
                }
                continue
            
            if current_song:
                # Match Personal Rating (count stars)
                if 'Personal Rating:' in line or 'Rating:' in line:
                    star_count = line.count('⭐')
                    if star_count > 0:
                        current_song['rating'] = float(star_count)
                
                # Match Play Count: XXX+ or XXX
                play_match = re.search(r'Play Count:\s*(\d+)', line)
                if play_match:
                    current_song['play_count'] = int(play_match.group(1))
        
        # Don't forget the last song
        if current_song and self._is_complete_song(current_song):
            self.songs.append(current_song)
    
    def _is_complete_song(self, song: dict) -> bool:
        """Check if a song entry has all required fields"""
        return (song.get('name') and 
                song.get('rating') is not None and 
                song.get('play_count') is not None and 
                song.get('release_year') is not None)
    
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
            
            # Calculate popularity score using configurable weights
            popularity_score = (rating * self.rating_weight) + (play_count_normalized * self.play_count_weight) + (year_factor * self.year_weight)
            
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
  #    popularity_score = (rating × W1) + (play_count_normalized × W2) + (year_factor × W3)
  #    where W1, W2, W3 are configurable weights (default: 0.4, 0.4, 0.2)
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
    parser.add_argument(
        '--rating-weight',
        type=float,
        default=0.4,
        help='Weight for rating in popularity score (default: 0.4)'
    )
    parser.add_argument(
        '--play-count-weight',
        type=float,
        default=0.4,
        help='Weight for normalized play count in popularity score (default: 0.4)'
    )
    parser.add_argument(
        '--year-weight',
        type=float,
        default=0.2,
        help='Weight for year factor in popularity score (default: 0.2)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    target_dir = os.path.abspath(args.target_directory)
    
    # Validate directory exists
    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist")
        return
    
    # Create analyzer and run
    analyzer = MusicAnalyzer(
        target_dir=target_dir,
        output_filename=args.output,
        rating_weight=args.rating_weight,
        play_count_weight=args.play_count_weight,
        year_weight=args.year_weight
    )
    
    try:
        await analyzer.generate_report()
    except Exception as e:
        print(f"\nError during music analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

