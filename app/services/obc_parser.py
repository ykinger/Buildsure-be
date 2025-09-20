"""
Enhanced Ontario Building Code Parser
Parses OBC markdown content and extracts hierarchical structured data.
"""
import re
from typing import List, Dict, Optional, Tuple, Iterator
from dataclasses import dataclass


@dataclass
class OBCChunk:
    reference: str
    division: Optional[str]
    part: Optional[str]
    section: Optional[str]
    subsection: Optional[str]
    article: Optional[str]
    chunk_type: str
    title: Optional[str]
    content: str


class EnhancedOBCParser:
    """Enhanced parser for Ontario Building Code markdown content with hierarchical chunking."""
    
    def __init__(self):
        # Regex patterns for different heading levels
        self.division_pattern = re.compile(r'^# (.+)$', re.MULTILINE)
        self.part_pattern = re.compile(r'^## Part (\d+)\s*(.*)$', re.MULTILINE)
        self.section_pattern = re.compile(r'^### Section (\d+\.\d+)\.?\s*(.*)$', re.MULTILINE)
        self.subsection_pattern = re.compile(r'^#### (\d+\.\d+\.\d+)\.?\s*(.*)$', re.MULTILINE)
        self.article_pattern = re.compile(r'^##### (\d+\.\d+\.\d+\.\d+)\.?\s*(.*)$', re.MULTILINE)
        
        # Pattern for Index section
        self.index_pattern = re.compile(r'^# Index$', re.MULTILINE)
        
        # Pattern to extract clean division names
        self.clean_division_pattern = re.compile(r'^(Division [A-Z])', re.IGNORECASE)
    
    def clean_division_name(self, division_title: str) -> str:
        """
        Extract clean division name from full title.
        
        Args:
            division_title: Full division title like "Division A Compliance, Objectives and Functional Statements"
            
        Returns:
            Clean division name like "Division A"
        """
        # Handle Index specially
        if division_title.lower().startswith('index'):
            return "Index"
        
        # Extract "Division X" from the title
        match = self.clean_division_pattern.match(division_title)
        if match:
            return match.group(1)
        
        # Fallback - return original if no match
        return division_title
    
    def parse_reference_components(self, reference: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Parse a reference string into its components.
        
        Args:
            reference: Reference like "3.2.1.1"
            
        Returns:
            Tuple of (part, section, subsection, article)
        """
        parts = reference.split('.')
        
        part = parts[0] if len(parts) >= 1 else None
        section = parts[1] if len(parts) >= 2 else None
        subsection = parts[2] if len(parts) >= 3 else None
        article = parts[3] if len(parts) >= 4 else None
        
        return part, section, subsection, article
    
    def extract_content_between_positions(self, text: str, start_pos: int, end_pos: Optional[int]) -> str:
        """
        Extract content between two positions.
        
        Args:
            text: Full text content
            start_pos: Start position
            end_pos: End position (None if last)
            
        Returns:
            Content between positions, cleaned up
        """
        if end_pos is None:
            content = text[start_pos:]
        else:
            content = text[start_pos:end_pos]
        
        # Remove the heading line itself
        lines = content.split('\n')
        if lines:
            lines = lines[1:]  # Remove first line (the heading)
        
        # Join back and clean up
        content = '\n'.join(lines).strip()
        
        # Remove excessive whitespace but preserve structure
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content
    
    def find_next_heading_position(self, text: str, current_pos: int, current_level: int) -> Optional[int]:
        """
        Find the position of the next heading at the same or higher level.
        
        Args:
            text: Full text content
            current_pos: Current position
            current_level: Current heading level (1-5)
            
        Returns:
            Position of next heading or None
        """
        patterns = [
            self.division_pattern,    # Level 1
            self.part_pattern,        # Level 2
            self.section_pattern,     # Level 3
            self.subsection_pattern,  # Level 4
            self.article_pattern      # Level 5
        ]
        
        next_positions = []
        
        # Find next headings at same or higher levels
        for level in range(current_level):
            pattern = patterns[level]
            for match in pattern.finditer(text, current_pos + 1):
                next_positions.append(match.start())
        
        return min(next_positions) if next_positions else None
    
    def parse_obc_content(self, content: str) -> List[OBCChunk]:
        """
        Parse OBC markdown content and extract hierarchical chunks.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of OBCChunk objects at different hierarchy levels
        """
        chunks = []
        
        # Check if this is the Index section
        index_match = self.index_pattern.search(content)
        if index_match:
            # Handle Index section separately
            return self._parse_index_section(content)
        
        # Parse divisions
        division_matches = list(self.division_pattern.finditer(content))
        
        for div_match in division_matches:
            division_title = div_match.group(1).strip()
            clean_division = self.clean_division_name(division_title)
            division_start = div_match.start()
            division_end = self.find_next_heading_position(content, division_start, 1)
            
            if division_end is None:
                division_content = content[division_start:]
            else:
                division_content = content[division_start:division_end]
            
            # Create division chunk
            division_chunk = OBCChunk(
                reference=f"Division_{clean_division.replace(' ', '_')}",
                division=clean_division,
                part=None,
                section=None,
                subsection=None,
                article=None,
                chunk_type="division",
                title=division_title,
                content=self.extract_content_between_positions(content, division_start, division_end)
            )
            chunks.append(division_chunk)
            
            # Parse parts within this division
            chunks.extend(self._parse_parts(division_content, clean_division))
        
        return chunks
    
    def _parse_parts(self, content: str, division: str) -> List[OBCChunk]:
        """Parse parts within a division."""
        chunks = []
        part_matches = list(self.part_pattern.finditer(content))
        
        for part_match in part_matches:
            part_num = part_match.group(1)
            part_title = part_match.group(2).strip()
            part_start = part_match.start()
            part_end = self.find_next_heading_position(content, part_start, 2)
            
            if part_end is None:
                part_content = content[part_start:]
            else:
                part_content = content[part_start:part_end]
            
            # Create part chunk
            part_chunk = OBCChunk(
                reference=f"Part_{part_num}",
                division=division,
                part=part_num,
                section=None,
                subsection=None,
                article=None,
                chunk_type="part",
                title=f"Part {part_num} {part_title}".strip(),
                content=self.extract_content_between_positions(content, part_start, part_end)
            )
            chunks.append(part_chunk)
            
            # Parse sections within this part
            chunks.extend(self._parse_sections(part_content, division, part_num))
        
        return chunks
    
    def _parse_sections(self, content: str, division: str, part: str) -> List[OBCChunk]:
        """Parse sections within a part."""
        chunks = []
        section_matches = list(self.section_pattern.finditer(content))
        
        for section_match in section_matches:
            section_ref = section_match.group(1)
            section_title = section_match.group(2).strip()
            section_start = section_match.start()
            section_end = self.find_next_heading_position(content, section_start, 3)
            
            if section_end is None:
                section_content = content[section_start:]
            else:
                section_content = content[section_start:section_end]
            
            # Parse section reference
            part_num, section_num, _, _ = self.parse_reference_components(section_ref)
            
            # Create section chunk
            section_chunk = OBCChunk(
                reference=section_ref,
                division=division,
                part=part_num or part,
                section=section_num,
                subsection=None,
                article=None,
                chunk_type="section",
                title=f"Section {section_ref} {section_title}".strip(),
                content=self.extract_content_between_positions(content, section_start, section_end)
            )
            chunks.append(section_chunk)
            
            # Parse subsections within this section
            chunks.extend(self._parse_subsections(section_content, division, part_num or part, section_num))
        
        return chunks
    
    def _parse_subsections(self, content: str, division: str, part: str, section: str) -> List[OBCChunk]:
        """Parse subsections within a section."""
        chunks = []
        subsection_matches = list(self.subsection_pattern.finditer(content))
        
        for subsection_match in subsection_matches:
            subsection_ref = subsection_match.group(1)
            subsection_title = subsection_match.group(2).strip()
            subsection_start = subsection_match.start()
            subsection_end = self.find_next_heading_position(content, subsection_start, 4)
            
            if subsection_end is None:
                subsection_content = content[subsection_start:]
            else:
                subsection_content = content[subsection_start:subsection_end]
            
            # Parse subsection reference
            part_num, section_num, subsection_num, _ = self.parse_reference_components(subsection_ref)
            
            # Create subsection chunk
            subsection_chunk = OBCChunk(
                reference=subsection_ref,
                division=division,
                part=part_num or part,
                section=section_num or section,
                subsection=subsection_num,
                article=None,
                chunk_type="subsection",
                title=subsection_title,
                content=self.extract_content_between_positions(content, subsection_start, subsection_end)
            )
            chunks.append(subsection_chunk)
            
            # Parse articles within this subsection
            chunks.extend(self._parse_articles(subsection_content, division, part_num or part, section_num or section, subsection_num))
        
        return chunks
    
    def _parse_articles(self, content: str, division: str, part: str, section: str, subsection: str) -> List[OBCChunk]:
        """Parse articles within a subsection."""
        chunks = []
        article_matches = list(self.article_pattern.finditer(content))
        
        for article_match in article_matches:
            article_ref = article_match.group(1)
            article_title = article_match.group(2).strip()
            article_start = article_match.start()
            article_end = self.find_next_heading_position(content, article_start, 5)
            
            if article_end is None:
                article_content = content[article_start:]
            else:
                article_content = content[article_start:article_end]
            
            # Parse article reference
            part_num, section_num, subsection_num, article_num = self.parse_reference_components(article_ref)
            
            # Extract full article content including all sentences and clauses
            full_content = self.extract_content_between_positions(content, article_start, article_end)
            
            # Create article chunk
            article_chunk = OBCChunk(
                reference=article_ref,
                division=division,
                part=part_num or part,
                section=section_num or section,
                subsection=subsection_num or subsection,
                article=article_num,
                chunk_type="article",
                title=article_title,
                content=full_content
            )
            chunks.append(article_chunk)
        
        return chunks
    
    def _parse_index_section(self, content: str) -> List[OBCChunk]:
        """Parse the Index section separately."""
        chunks = []
        
        # Create a single chunk for the entire index
        index_chunk = OBCChunk(
            reference="Index",
            division="Index",
            part=None,
            section=None,
            subsection=None,
            article=None,
            chunk_type="index",
            title="Index",
            content=content
        )
        chunks.append(index_chunk)
        
        return chunks
    
    def parse_file(self, file_path: str) -> List[OBCChunk]:
        """
        Parse an OBC markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of OBCChunk objects
        """
        print(f"Reading file: {file_path}")
        
        # Read file in chunks to handle large files
        chunks = []
        current_content = ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read the entire file (we'll handle it efficiently)
            content = f.read()
        
        print(f"File size: {len(content)} characters")
        
        # Split content by major divisions to process separately
        division_matches = list(self.division_pattern.finditer(content))
        
        if not division_matches:
            # No divisions found, treat as single content
            return self.parse_obc_content(content)
        
        # Process each division separately
        for i, div_match in enumerate(division_matches):
            start_pos = div_match.start()
            
            # Find end position (start of next division or end of file)
            if i + 1 < len(division_matches):
                end_pos = division_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            division_content = content[start_pos:end_pos]
            division_chunks = self.parse_obc_content(division_content)
            chunks.extend(division_chunks)
            
            print(f"Processed division {i + 1}/{len(division_matches)}: {len(division_chunks)} chunks")
        
        return chunks


# Maintain backward compatibility
OBCParser = EnhancedOBCParser
OBCArticle = OBCChunk
