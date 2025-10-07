import re
from typing import List, Tuple

def sectionize_text(text: str) -> List[Tuple[str,str]]:
    """
    Very simple sectionizer: split on headings that look like '1. ', '##', or uppercase headings.
    Returns list of (section_header, section_text).
    """
    # naive splitter using blank lines and headings
    candidates = re.split(r'\n{2,}', text)
    sections = []
    for idx, c in enumerate(candidates):
        header = c.strip().split('\n',1)[0][:100]
        body = c.strip()
        sections.append((header or f"section-{idx+1}", body))
    return sections
