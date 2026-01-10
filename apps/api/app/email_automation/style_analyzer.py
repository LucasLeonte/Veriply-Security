"""Style analysis engine for detecting writing patterns and tone."""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)


class ToneCategory(str, Enum):
    """Writing tone categories."""
    FORMAL = "formal"
    SEMI_FORMAL = "semi_formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"


# Default professional style profile
DEFAULT_STYLE_PROFILE = {
    "tone": ToneCategory.SEMI_FORMAL.value,
    "tone_score": 0,
    "formality_score": 65,
    "greeting_pattern": "Hi [Name],",
    "closing_pattern": "Best regards,",
    "avg_email_length": 150,
    "avg_sentence_length": 12.0,
    "uses_emojis": False,
    "sample_count": 0,
}


class StyleAnalyzer:
    """Analyzes writing style from email text."""
    
    # Formal indicators
    FORMAL_MARKERS = [
        r"\bdear\s+(?:sir|madam|mr\.?|ms\.?|dr\.?)",
        r"\bregards\b",
        r"\byours\s+(?:sincerely|truly|faithfully)",
        r"\brespectfully",
        r"\bthereafter\b",
        r"\bhereinafter\b",
        r"\backnowledge\b",
        r"\bfacilitate\b",
        r"\bproceed\b",
        r"\benclosed\s+(?:please|herewith)",
    ]
    
    # Casual indicators
    CASUAL_MARKERS = [
        r"\bhi\b",
        r"\bhey\b",
        r"\bthanks\b",
        r"\bcheers\b",
        r"\btalk\s+soon\b",
        r"\blet's\b",
        r"\bwanna\b",
        r"\bgotta\b",
        r"\b(?:cool|awesome|great|nice)\b",
    ]
    
    # Friendly indicators
    FRIENDLY_MARKERS = [
        r"\bhope\s+(?:you're?|this)",
        r"\bhope\s+all\s+is\s+(?:well|good)",
        r"\blooking\s+forward",
        r"\bappreciate\b",
        r"\bthank\s+you",
        r"\bhappy\s+to\b",
        r"\bwould\s+love\b",
        r"\bwould\s+be\s+(?:great|wonderful)",
    ]
    
    # Greeting patterns
    GREETING_PATTERNS = [
        r"^(?:hi|hello|hey|dear|mr\.?|ms\.?|dr\.?|greetings)",
        r"^(?:to\s+)?(?:all|team|everyone|folks|dear\s+all)",
    ]
    
    # Closing patterns
    CLOSING_PATTERNS = [
        r"(?:regards|best|thanks|cheers|sincerely|respectfully|best\s+regards)",
        r"(?:talk\s+soon|looking\s+forward|till\s+(?:then|next\s+time))",
        r"(?:appreciate|thank\s+you|thanks\s+for)",
    ]
    
    def __init__(self):
        """Initialize the style analyzer."""
        self.formal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.FORMAL_MARKERS]
        self.casual_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.CASUAL_MARKERS]
        self.friendly_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.FRIENDLY_MARKERS]
        self.greeting_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.GREETING_PATTERNS]
        self.closing_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.CLOSING_PATTERNS]
    
    def analyze_emails(self, emails: List[str]) -> Dict[str, Any]:
        """Analyze a collection of emails to extract style profile.
        
        Args:
            emails: List of email bodies
        
        Returns:
            Dict with style analysis results
        """
        if not emails:
            return self._get_default_style()
        
        # Analyze each email
        tone_scores = []
        greeting_patterns = []
        closing_patterns = []
        email_lengths = []
        sentence_lengths = []
        emoji_count = 0
        total_punctuation = {"!": 0, "?": 0, ".": 0, ",": 0}
        
        for email in emails:
            if not email or not isinstance(email, str):
                continue
            
            # Tone detection
            tone_score = self._detect_tone(email)
            tone_scores.append(tone_score)
            
            # Extract greeting
            greeting = self._extract_greeting(email)
            if greeting:
                greeting_patterns.append(greeting)
            
            # Extract closing
            closing = self._extract_closing(email)
            if closing:
                closing_patterns.append(closing)
            
            # Email length
            words = email.split()
            email_lengths.append(len(words))
            
            # Sentence length
            sentences = re.split(r'[.!?]+', email)
            for sentence in sentences:
                words_in_sent = sentence.split()
                if words_in_sent:
                    sentence_lengths.append(len(words_in_sent))
            
            # Punctuation
            emoji_count += len(re.findall(r'[😀-🙏🌀-🗿]|[🚀-🛿]', email))
            for char in email:
                if char in total_punctuation:
                    total_punctuation[char] += 1
        
        # Calculate averages and aggregates
        avg_tone_score = sum(tone_scores) / len(tone_scores) if tone_scores else 0
        tone_category = self._categorize_tone(avg_tone_score)
        
        avg_email_length = sum(email_lengths) / len(email_lengths) if email_lengths else 150
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 10
        
        # Most common greeting/closing
        common_greeting = self._get_most_common(greeting_patterns) if greeting_patterns else "Hi [Name],"
        common_closing = self._get_most_common(closing_patterns) if closing_patterns else "Best regards,"
        
        # Formality score (0-100)
        formality_score = self._calculate_formality_score(
            avg_tone_score,
            emoji_count,
            total_punctuation.get("!", 0),
            len(emails)
        )
        
        # Uses emojis
        uses_emojis = emoji_count > (len(emails) * 0.5)  # More than 0.5 emojis per email on average
        
        return {
            "tone": tone_category,
            "tone_score": avg_tone_score,
            "formality_score": int(formality_score),
            "greeting_pattern": common_greeting,
            "closing_pattern": common_closing,
            "avg_email_length": int(avg_email_length),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "uses_emojis": uses_emojis,
            "sample_count": len(emails),
        }
    
    def _detect_tone(self, text: str) -> float:
        """Detect tone of a single email.
        
        Returns:
            Float score from -2 (very formal) to 2 (very casual)
        """
        score = 0
        
        # Check formal markers
        formal_matches = sum(1 for regex in self.formal_regex if regex.search(text))
        score -= formal_matches * 0.5
        
        # Check casual markers
        casual_matches = sum(1 for regex in self.casual_regex if regex.search(text))
        score += casual_matches * 0.4
        
        # Check friendly markers
        friendly_matches = sum(1 for regex in self.friendly_regex if regex.search(text))
        score += friendly_matches * 0.3
        
        # Normalize
        return max(-2, min(2, score))
    
    def _categorize_tone(self, tone_score: float) -> str:
        """Categorize tone score into category."""
        if tone_score <= -0.5:
            return ToneCategory.FORMAL.value
        elif tone_score <= 0.3:
            return ToneCategory.SEMI_FORMAL.value
        elif tone_score <= 1.0:
            return ToneCategory.CASUAL.value
        else:
            return ToneCategory.FRIENDLY.value
    
    def _extract_greeting(self, text: str) -> Optional[str]:
        """Extract greeting from email."""
        # Get first line
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        first_line = lines[0].strip()
        
        # Match greeting pattern
        for regex in self.greeting_regex:
            match = regex.search(first_line)
            if match:
                # Extract up to first comma or colon
                greeting = match.group(0)
                greeting = re.sub(r'[,:].*$', '', greeting)
                return greeting + ("," if "," in first_line else ":")
        
        return None
    
    def _extract_closing(self, text: str) -> Optional[str]:
        """Extract closing from email."""
        # Get last 5 lines (to avoid signature)
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        # Check last few lines
        for line in reversed(lines[-5:]):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            for regex in self.closing_regex:
                match = regex.search(line)
                if match:
                    return match.group(0)
        
        return None
    
    def _get_most_common(self, patterns: List[str]) -> str:
        """Get most common pattern from list."""
        if not patterns:
            return "Best regards,"
        
        counter = Counter(patterns)
        return counter.most_common(1)[0][0]
    
    def _calculate_formality_score(
        self,
        tone_score: float,
        emoji_count: int,
        exclamation_count: int,
        email_count: int
    ) -> float:
        """Calculate formality score (0-100)."""
        # Base on tone score
        base_score = ((tone_score + 2) / 4) * 100  # Convert -2..2 to 0..100
        
        # Adjust for emojis (more emojis = less formal)
        emojis_per_email = emoji_count / email_count if email_count > 0 else 0
        emoji_adjustment = min(20, emojis_per_email * 10)
        
        # Adjust for exclamation marks (more exclamation = less formal)
        exclamations_per_email = exclamation_count / email_count if email_count > 0 else 0
        exclamation_adjustment = min(15, exclamations_per_email * 5)
        
        final_score = base_score - emoji_adjustment - exclamation_adjustment
        return max(0, min(100, final_score))
    
    def _get_default_style(self) -> Dict[str, Any]:
        """Return default professional style profile."""
        return DEFAULT_STYLE_PROFILE.copy()


def create_style_guidelines_prompt(style_profile: Dict[str, Any]) -> str:
    """Create LLM prompt guidelines from style profile.
    
    Args:
        style_profile: User's writing style profile
    
    Returns:
        Formatted prompt section with style guidelines
    """
    guidelines = f"""## Writing Style Guidelines

Based on the user's email history:

- **Tone**: {style_profile.get('tone', 'semi-formal')} (Match the sender's writing tone)
- **Greeting**: Use "{style_profile.get('greeting_pattern', 'Hi [Name],')}". Replace [Name] with the recipient's name.
- **Closing**: End with "{style_profile.get('closing_pattern', 'Best regards,')}". You can vary it slightly if appropriate.
- **Sentence Style**: Keep sentences {self._get_sentence_style(style_profile.get('avg_sentence_length', 12))}
- **Email Length**: Aim for approximately {style_profile.get('avg_email_length', 150)} words
- **Punctuation**: {"Feel free to use exclamation marks and emojis where appropriate" if style_profile.get('uses_emojis') else "Avoid excessive exclamation marks and emojis; keep punctuation professional"}
- **Formality Level**: {self._get_formality_description(style_profile.get('formality_score', 65))}

Remember: These are guidelines, not hard rules. The generated response should be appropriate for the context while matching the user's natural communication style.
"""
    return guidelines


def _get_sentence_style(avg_length: float) -> str:
    """Get sentence style description based on average length."""
    if avg_length < 8:
        return "short and concise (typically 5-8 words)"
    elif avg_length < 14:
        return "moderate length (typically 8-14 words)"
    else:
        return "longer and more complex (typically 14+ words)"


def _get_formality_description(formality_score: int) -> str:
    """Get formality description based on score."""
    if formality_score >= 80:
        return "Very formal - use professional language and formal structures"
    elif formality_score >= 60:
        return "Professional - balance between formal and conversational"
    elif formality_score >= 40:
        return "Conversational - friendly and approachable tone"
    else:
        return "Very casual - relaxed and informal language"
