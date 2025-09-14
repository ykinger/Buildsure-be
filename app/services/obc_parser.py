"""
Ontario Building Code Parser
Parses OBC markdown content and extracts structured data.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OBCArticle:
    reference: str
    part: Optional[str]
    section: Optional[str]
    subsection: Optional[str]
    article: Optional[str]
    content: str


class OBCParser:
    """Parser for Ontario Building Code markdown content."""
    
    def __init__(self):
        # Regex patterns for different heading levels
        self.section_pattern = re.compile(r'^### (\d+\.\d+)\.\s*(.+)$', re.MULTILINE)
        self.subsection_pattern = re.compile(r'^#### (\d+\.\d+\.\d+)\.\s*(.+)$', re.MULTILINE)
        self.article_pattern = re.compile(r'^#### (\d+\.\d+\.\d+\.\d+)\.\s*(.+)$', re.MULTILINE)
    
    def parse_reference(self, reference: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
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
    
    def extract_content_between_headings(self, text: str, start_pos: int, next_pos: Optional[int]) -> str:
        """
        Extract content between two headings.
        
        Args:
            text: Full text content
            start_pos: Start position of current heading
            next_pos: Start position of next heading (None if last)
            
        Returns:
            Content between headings, cleaned up
        """
        if next_pos is None:
            content = text[start_pos:]
        else:
            content = text[start_pos:next_pos]
        
        # Remove the heading line itself
        lines = content.split('\n')
        if lines:
            lines = lines[1:]  # Remove first line (the heading)
        
        # Join back and clean up
        content = '\n'.join(lines).strip()
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    def parse_obc_content(self, content: str) -> List[OBCArticle]:
        """
        Parse OBC markdown content and extract articles.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of OBCArticle objects
        """
        articles = []
        
        # Find all article headings (4-level deep: x.x.x.x)
        article_matches = list(self.article_pattern.finditer(content))
        
        for i, match in enumerate(article_matches):
            reference = match.group(1)
            title = match.group(2)
            start_pos = match.start()
            
            # Find the next article heading to determine content boundaries
            next_pos = None
            if i + 1 < len(article_matches):
                next_pos = article_matches[i + 1].start()
            
            # Extract content for this article
            article_content = self.extract_content_between_headings(content, start_pos, next_pos)
            
            # Include the title in the content
            full_content = f"{title}\n\n{article_content}".strip()
            
            # Parse reference components
            part, section, subsection, article_num = self.parse_reference(reference)
            
            # Create article object
            article = OBCArticle(
                reference=reference,
                part=part,
                section=section,
                subsection=subsection,
                article=article_num,
                content=full_content
            )
            
            articles.append(article)
        
        return articles
    
    def parse_file(self, file_path: str) -> List[OBCArticle]:
        """
        Parse an OBC markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of OBCArticle objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_obc_content(content)
