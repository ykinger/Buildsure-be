"""
Guideline Processor Service
Handles parsing and chunking of Ontario Building Code markdown files.
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GuidelineChunk:
    """Data class for storing parsed guideline chunks."""
    
    def __init__(self, section_reference: str, section_title: str, 
                 section_level: int, chunk_text: str):
        self.section_reference = section_reference
        self.section_title = section_title
        self.section_level = section_level
        self.chunk_text = chunk_text


class GuidelineProcessor:
    """Processes Ontario Building Code markdown files into structured chunks."""
    
    def __init__(self):
        # Regex patterns for different section levels in markdown
        self.patterns = {
            'division': re.compile(r'^## (Division [A-Z]) - (.+)$', re.MULTILINE),
            'part': re.compile(r'^### (Part \d+) - (.+)$', re.MULTILINE),
            'section': re.compile(r'^#### (\d+\.\d+) (.+)$', re.MULTILINE),
            'subsection': re.compile(r'^##### (\d+\.\d+\.\d+) (.+)$', re.MULTILINE),
            'sub_subsection': re.compile(r'^###### (\d+\.\d+\.\d+\.\d+) (.+)$', re.MULTILINE),
        }
    
    def load_markdown_file(self, file_path: str) -> str:
        """Load markdown content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"Successfully loaded markdown file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error loading markdown file {file_path}: {str(e)}")
            raise
    
    def extract_sections(self, content: str) -> List[Dict]:
        """Extract all sections with their positions and metadata."""
        sections = []
        
        # Find all section types and their positions
        for section_type, pattern in self.patterns.items():
            for match in pattern.finditer(content):
                section_ref = match.group(1)
                section_title = match.group(2).strip()
                start_pos = match.start()
                
                # Determine section level based on section type and reference pattern
                if section_type == 'division':
                    level = 1
                elif section_type == 'part':
                    level = 2
                elif section_type == 'section':
                    level = len(section_ref.split('.'))
                elif section_type == 'subsection':
                    level = len(section_ref.split('.'))
                elif section_type == 'sub_subsection':
                    level = len(section_ref.split('.'))
                else:
                    level = len(section_ref.split('.'))
                
                sections.append({
                    'type': section_type,
                    'reference': section_ref,
                    'title': section_title,
                    'level': level,
                    'start_pos': start_pos,
                    'match': match
                })
        
        # Sort by position in document
        sections.sort(key=lambda x: x['start_pos'])
        logger.info(f"Found {len(sections)} sections")
        
        return sections
    
    def extract_section_content(self, content: str, current_section: Dict, 
                              next_section: Optional[Dict]) -> str:
        """Extract content for a specific section."""
        start_pos = current_section['start_pos']
        
        if next_section:
            end_pos = next_section['start_pos']
            section_content = content[start_pos:end_pos].strip()
        else:
            section_content = content[start_pos:].strip()
        
        return section_content
    
    def clean_content(self, content: str) -> str:
        """Clean and format section content."""
        # Remove excessive whitespace while preserving structure
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Keep the line structure but clean up spacing
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Join lines and remove excessive blank lines
        cleaned_content = '\n'.join(cleaned_lines)
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip()
    
    def process_markdown_file(self, file_path: str) -> List[GuidelineChunk]:
        """Process a markdown file and return structured chunks."""
        logger.info(f"Starting to process markdown file: {file_path}")
        
        # Load the markdown content
        content = self.load_markdown_file(file_path)
        
        # Extract all sections
        sections = self.extract_sections(content)
        
        if not sections:
            logger.warning("No sections found in the markdown file")
            return []
        
        chunks = []
        
        # Process each section
        for i, section in enumerate(sections):
            try:
                # Get the next section for content boundary
                next_section = sections[i + 1] if i + 1 < len(sections) else None
                
                # Extract content for this section
                section_content = self.extract_section_content(content, section, next_section)
                
                # Clean the content
                cleaned_content = self.clean_content(section_content)
                
                # Create chunk
                chunk = GuidelineChunk(
                    section_reference=section['reference'],
                    section_title=section['title'],
                    section_level=section['level'],
                    chunk_text=cleaned_content
                )
                
                chunks.append(chunk)
                
                logger.debug(f"Processed section {section['reference']}: {section['title']}")
                
            except Exception as e:
                logger.error(f"Error processing section {section['reference']}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(chunks)} chunks from {file_path}")
        return chunks
    
    def get_processing_stats(self, chunks: List[GuidelineChunk]) -> Dict:
        """Get statistics about the processed chunks."""
        if not chunks:
            return {"total_chunks": 0}
        
        stats = {
            "total_chunks": len(chunks),
            "sections_by_level": {},
            "average_content_length": 0,
            "total_content_length": 0
        }
        
        total_length = 0
        for chunk in chunks:
            level = chunk.section_level
            stats["sections_by_level"][level] = stats["sections_by_level"].get(level, 0) + 1
            total_length += len(chunk.chunk_text)
        
        stats["total_content_length"] = total_length
        stats["average_content_length"] = total_length // len(chunks) if chunks else 0
        
        return stats
