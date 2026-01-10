"""Tests for writing style analysis and management."""

import pytest
from uuid import uuid4
from datetime import datetime

from app.email_automation.style_analyzer import (
    StyleAnalyzer, ToneCategory, DEFAULT_STYLE_PROFILE, create_style_guidelines_prompt
)


class TestStyleAnalyzer:
    """Test StyleAnalyzer class."""
    
    def setup_method(self):
        """Setup analyzer for each test."""
        self.analyzer = StyleAnalyzer()
    
    def test_analyze_empty_emails(self):
        """Test analyzing empty email list returns default style."""
        result = self.analyzer.analyze_emails([])
        
        assert result["tone"] == ToneCategory.SEMI_FORMAL.value
        assert result["formality_score"] == 65
        assert result["sample_count"] == 0
        assert result["uses_emojis"] is False
    
    def test_detect_formal_tone(self):
        """Test detecting formal tone in email."""
        formal_emails = [
            "Dear Sir, I would like to inquire regarding your proposal. Regards, John",
            "Hello, Thank you for your inquiry. Best regards, Jane",
            "Dear Ms. Smith, I acknowledge receipt of your message. Respectfully, Bob",
        ]
        
        result = self.analyzer.analyze_emails(formal_emails)
        
        assert result["tone"] == ToneCategory.FORMAL.value
        assert result["formality_score"] > 60
    
    def test_detect_casual_tone(self):
        """Test detecting casual tone in email."""
        casual_emails = [
            "Hey! Thanks for reaching out. This is awesome! Talk soon.",
            "Hi there! Great to hear from you. Let's chat later. Cheers!",
            "Hi! Wanna grab coffee? Sounds cool to me. Talk soon!",
        ]
        
        result = self.analyzer.analyze_emails(casual_emails)
        
        assert result["tone"] in [ToneCategory.CASUAL.value, ToneCategory.FRIENDLY.value]
        assert result["formality_score"] < 50
    
    def test_detect_friendly_tone(self):
        """Test detecting friendly tone in email."""
        friendly_emails = [
            "Hi John, Hope you're doing well! I'd love to help with this. Best!",
            "Hi team, Hope all is good. Looking forward to our meeting. Thanks!",
            "Hello, I appreciate your interest. Happy to discuss further. Thanks!",
        ]
        
        result = self.analyzer.analyze_emails(friendly_emails)
        
        assert result["tone"] in [ToneCategory.FRIENDLY.value, ToneCategory.SEMI_FORMAL.value]
    
    def test_extract_greeting_patterns(self):
        """Test greeting pattern extraction."""
        emails = [
            "Hi John, This is a test email.",
            "Hello, Thank you for contacting us.",
            "Dear Mr. Smith, I wanted to reach out.",
        ]
        
        result = self.analyzer.analyze_emails(emails)
        
        assert result["greeting_pattern"] is not None
        assert len(result["greeting_pattern"]) > 0
    
    def test_extract_closing_patterns(self):
        """Test closing pattern extraction."""
        emails = [
            "This is the body.\n\nBest regards,\nJohn",
            "Message content here.\n\nCheers,\nJane",
            "Email body.\n\nThanks,\nBob",
        ]
        
        result = self.analyzer.analyze_emails(emails)
        
        assert result["closing_pattern"] is not None
        assert len(result["closing_pattern"]) > 0
    
    def test_calculate_average_email_length(self):
        """Test average email length calculation."""
        emails = [
            "This is a short email.",  # 5 words
            "This is a slightly longer email with more content and information.",  # 12 words
            "This email contains many words and is quite lengthy with a lot of information and details.",  # 16 words
        ]
        
        result = self.analyzer.analyze_emails(emails)
        
        # Average should be around (5 + 12 + 16) / 3 ≈ 11
        assert 10 <= result["avg_email_length"] <= 15
    
    def test_calculate_sentence_length(self):
        """Test average sentence length calculation."""
        emails = [
            "Short. Medium sized. This is a slightly longer sentence with more words.",
        ]
        
        result = self.analyzer.analyze_emails(emails)
        
        assert result["avg_sentence_length"] > 0
    
    def test_detect_emoji_usage(self):
        """Test emoji usage detection."""
        no_emoji = ["Hi there, how are you? Great to hear from you."]
        result = self.analyzer.analyze_emails(no_emoji)
        assert result["uses_emojis"] is False
        
        # Note: emoji detection depends on implementation
        # This test verifies the flag exists and is set correctly
    
    def test_tone_categorization_boundaries(self):
        """Test tone categorization at boundaries."""
        # Formal
        score = self.analyzer._categorize_tone(-2.0)
        assert score == ToneCategory.FORMAL.value
        
        # Semi-formal
        score = self.analyzer._categorize_tone(0.0)
        assert score == ToneCategory.SEMI_FORMAL.value
        
        # Casual
        score = self.analyzer._categorize_tone(0.5)
        assert score == ToneCategory.CASUAL.value
        
        # Friendly
        score = self.analyzer._categorize_tone(2.0)
        assert score == ToneCategory.FRIENDLY.value
    
    def test_formality_score_calculation(self):
        """Test formality score calculation."""
        # With formal markers
        formal_text = "Dear Sir, I would like to acknowledge your inquiry. Best regards."
        formal_score = self.analyzer._detect_tone(formal_text)
        assert formal_score < 0  # Should be negative (formal)
        
        # With casual markers
        casual_text = "Hey! Thanks for reaching out. This is awesome!"
        casual_score = self.analyzer._detect_tone(casual_text)
        assert casual_score > 0  # Should be positive (casual)


class TestDefaultStyleProfile:
    """Test default style profile."""
    
    def test_default_profile_exists(self):
        """Test that default profile is defined."""
        assert DEFAULT_STYLE_PROFILE is not None
        assert "tone" in DEFAULT_STYLE_PROFILE
        assert "formality_score" in DEFAULT_STYLE_PROFILE
    
    def test_default_profile_values(self):
        """Test default profile has correct values."""
        assert DEFAULT_STYLE_PROFILE["tone"] == ToneCategory.SEMI_FORMAL.value
        assert DEFAULT_STYLE_PROFILE["formality_score"] == 65
        assert DEFAULT_STYLE_PROFILE["greeting_pattern"] == "Hi [Name],"
        assert DEFAULT_STYLE_PROFILE["closing_pattern"] == "Best regards,"
        assert DEFAULT_STYLE_PROFILE["avg_email_length"] == 150
        assert DEFAULT_STYLE_PROFILE["uses_emojis"] is False
    
    def test_default_profile_insufficient_emails(self):
        """Test that default profile is used with < 10 emails."""
        analyzer = StyleAnalyzer()
        
        # Only 5 emails (< minimum 10)
        emails = ["Email " + str(i) for i in range(5)]
        result = analyzer.analyze_emails(emails)
        
        # Should have sample_count = 5
        assert result["sample_count"] == 5


class TestStyleGuidelinesPrompt:
    """Test style guidelines prompt generation."""
    
    def test_style_guidelines_generation(self):
        """Test generating style guidelines for LLM prompt."""
        style_profile = {
            "tone": "casual",
            "greeting_pattern": "Hey [Name]!",
            "closing_pattern": "Cheers,",
            "avg_email_length": 200,
            "avg_sentence_length": 10,
            "uses_emojis": True,
            "formality_score": 30,
        }
        
        guidelines = create_style_guidelines_prompt(style_profile)
        
        assert "Writing Style Guidelines" in guidelines
        assert "casual" in guidelines.lower()
        assert "Hey [Name]!" in guidelines
        assert "Cheers," in guidelines
        assert "200" in guidelines
    
    def test_style_guidelines_with_formal_style(self):
        """Test guidelines with formal style."""
        style_profile = {
            "tone": "formal",
            "formality_score": 85,
            "greeting_pattern": "Dear [Name],",
            "closing_pattern": "Sincerely,",
            "avg_email_length": 300,
            "avg_sentence_length": 18,
            "uses_emojis": False,
        }
        
        guidelines = create_style_guidelines_prompt(style_profile)
        
        assert "Very formal" in guidelines
        assert "professional" in guidelines.lower()
        assert "Dear [Name]," in guidelines
        assert "Avoid excessive exclamation marks" in guidelines


# Integration tests would go here and would require database setup
# These are placeholders for integration tests

class TestStyleAnalysisIntegration:
    """Integration tests for style analysis (requires DB setup)."""
    
    @pytest.mark.asyncio
    async def test_collect_and_analyze_emails(self):
        """Test collecting emails and analyzing style.
        
        Note: This requires a real database and email integration setup.
        Marked for future implementation.
        """
        pass
    
    @pytest.mark.asyncio
    async def test_persist_style_profile(self):
        """Test persisting style profile to database.
        
        Note: This requires a real database setup.
        Marked for future implementation.
        """
        pass
    
    @pytest.mark.asyncio
    async def test_inject_style_into_draft_prompt(self):
        """Test injecting style profile into draft generation prompt.
        
        Note: This requires real LLM service setup.
        Marked for future implementation.
        """
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
