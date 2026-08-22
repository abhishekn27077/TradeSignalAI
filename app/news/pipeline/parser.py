import html
import re


class NewsParser:
    """
    Cleans and normalizes raw text from HTML, Markdown, or raw string data.
    """
    @staticmethod
    def clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        
        # 1. Decode HTML entities (&amp; -> &)
        text = html.unescape(raw_text)
        
        # 2. Strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 3. Strip URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # 4. Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

news_parser = NewsParser()
