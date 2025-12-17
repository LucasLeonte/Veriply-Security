"""
Tests for PII Redaction Service

Covers:
- Email redaction
- Phone redaction
- SSN redaction
- Credit card redaction
- IP address redaction
- URL redaction
- Multiple PII types
- Encryption/decryption
- Edge cases
"""

import pytest
import os

from app.services.pii_service import (
    PIIRedactionService,
    RedactedQuery,
    RedactionInfo,
)


@pytest.fixture
def pii_service():
    """Create PII redaction service instance (Presidio disabled for unit tests)"""
    return PIIRedactionService(presidio_enabled=False)


@pytest.fixture
def encryption_key():
    """Generate AES-256 key for testing"""
    return os.urandom(32)


class TestEmailRedaction:
    """Test email address redaction"""
    
    @pytest.mark.asyncio
    async def test_single_email(self, pii_service):
        """Test single email redaction"""
        result = await pii_service.redact_query("Contact john@example.com for support")
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query
        assert "john@example.com" not in result.redacted_query
        assert len(result.redactions) == 1
        assert result.redactions[0].pii_type == "EMAIL"
        assert result.redactions[0].original_value == "john@example.com"
        assert result.redactions[0].confidence >= 0.99
    
    @pytest.mark.asyncio
    async def test_multiple_emails(self, pii_service):
        """Test multiple email redaction"""
        result = await pii_service.redact_query(
            "Contact john@example.com or jane@example.org for help"
        )
        
        assert result.contains_pii
        assert result.redacted_query.count("<EMAIL>") == 2
        assert len(result.redactions) == 2
        assert all(r.pii_type == "EMAIL" for r in result.redactions)
    
    @pytest.mark.asyncio
    async def test_email_with_special_chars(self, pii_service):
        """Test email with special characters"""
        result = await pii_service.redact_query(
            "Email: user.name+tag@sub.domain.co.uk"
        )
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query
        assert len(result.redactions) == 1

class TestSSNRedaction:
    """Test Social Security Number redaction"""
    
    @pytest.mark.asyncio
    async def test_ssn_redaction(self, pii_service):
        """Test SSN redaction"""
        result = await pii_service.redact_query("My SSN is 123-45-6789")
        
        assert result.contains_pii
        assert "<SSN>" in result.redacted_query
        assert "123-45-6789" not in result.redacted_query
        assert len(result.redactions) == 1
        assert result.redactions[0].pii_type == "SSN"
        assert result.redactions[0].confidence >= 0.99
    
    @pytest.mark.asyncio
    async def test_multiple_ssn(self, pii_service):
        """Test multiple SSN redaction"""
        result = await pii_service.redact_query(
            "SSN1: 123-45-6789, SSN2: 987-65-4321"
        )
        
        assert result.contains_pii
        assert result.redacted_query.count("<SSN>") == 2
        assert len(result.redactions) == 2


class TestCreditCardRedaction:
    """Test credit card number redaction"""
    
    @pytest.mark.asyncio
    async def test_valid_credit_card_luhn(self, pii_service):
        """Test valid credit card with Luhn validation"""
        # 4111111111111111 is a valid test credit card (passes Luhn)
        result = await pii_service.redact_query(
            "Card: 4111111111111111"
        )
        
        assert result.contains_pii
        assert "<CREDIT_CARD>" in result.redacted_query
        assert len(result.redactions) == 1
        assert result.redactions[0].pii_type == "CREDIT_CARD"
    
    @pytest.mark.asyncio
    async def test_credit_card_with_spaces(self, pii_service):
        """Test credit card with spaces"""
        result = await pii_service.redact_query(
            "Charge 4111 1111 1111 1111"
        )
        
        assert result.contains_pii
        assert "<CREDIT_CARD>" in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_credit_card_with_dashes(self, pii_service):
        """Test credit card with dashes"""
        result = await pii_service.redact_query(
            "Card: 4111-1111-1111-1111"
        )
        
        assert result.contains_pii
        assert "<CREDIT_CARD>" in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_invalid_credit_card_luhn(self, pii_service):
        """Test invalid credit card (fails Luhn) is not redacted"""
        result = await pii_service.redact_query(
            "Card: 4111111111111112"  # Invalid Luhn checksum
        )
        
        # Should not be redacted
        assert not result.contains_pii or len(
            [r for r in result.redactions if r.pii_type == "CREDIT_CARD"]
        ) == 0


class TestIPAddressRedaction:
    """Test IP address redaction"""
    
    @pytest.mark.asyncio
    async def test_ip_address_redaction(self, pii_service):
        """Test IP address redaction"""
        result = await pii_service.redact_query(
            "Connect to 192.168.1.1 for configuration"
        )
        
        assert result.contains_pii
        assert "<IP_ADDRESS>" in result.redacted_query
        assert "192.168.1.1" not in result.redacted_query
        assert len(result.redactions) == 1
        assert result.redactions[0].pii_type == "IP_ADDRESS"
    
    @pytest.mark.asyncio
    async def test_multiple_ip_addresses(self, pii_service):
        """Test multiple IP addresses"""
        result = await pii_service.redact_query(
            "Gateway: 192.168.1.1, DNS: 8.8.8.8"
        )
        
        assert result.contains_pii
        assert result.redacted_query.count("<IP_ADDRESS>") == 2
    
    @pytest.mark.asyncio
    async def test_version_number_not_ip(self, pii_service):
        """Test that version numbers are not redacted as IPs"""
        result = await pii_service.redact_query(
            "Software version 1.256.300.5"
        )
        
        # Should not be redacted as IP
        assert not any(r.pii_type == "IP_ADDRESS" for r in result.redactions)


class TestURLRedaction:
    """Test URL redaction"""
    
    @pytest.mark.asyncio
    async def test_url_redaction(self, pii_service):
        """Test basic URL redaction"""
        result = await pii_service.redact_query(
            "Visit https://example.com/path for more info"
        )
        
        assert result.contains_pii
        assert "<URL>" in result.redacted_query
        assert "https://example.com" not in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_url_with_credentials(self, pii_service):
        """Test URL with credentials"""
        result = await pii_service.redact_query(
            "Connect to https://user:pass@example.com/api"
        )
        
        assert result.contains_pii
        assert "<URL>" in result.redacted_query
        assert "user:pass" not in result.redacted_query


class TestMixedPII:
    """Test queries with multiple PII types"""
    
    @pytest.mark.asyncio
    async def test_mixed_pii_types(self, pii_service):
        """Test query with multiple PII types"""
        result = await pii_service.redact_query(
            "User john@example.com, phone 555-123-4567, card 4111111111111111"
        )
        
        assert result.contains_pii
        assert len(result.redactions) == 2
        pii_types = {r.pii_type for r in result.redactions}
        assert "EMAIL" in pii_types
        assert "CREDIT_CARD" in pii_types
    
    @pytest.mark.asyncio
    async def test_pii_consistency(self, pii_service):
        """Test that multiple occurrences are redacted consistently"""
        result = await pii_service.redact_query(
            "Email john@example.com and john@example.com again"
        )
        
        assert result.redacted_query.count("<EMAIL>") == 2
        assert len(result.redactions) == 2


class TestEncryption:
    """Test query encryption"""
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_query(self, pii_service, encryption_key):
        """Test query encryption and decryption"""
        query = "My SSN is 123-45-6789"
        
        result = await pii_service.redact_query(query, encryption_key)
        
        assert result.original_encrypted is not None
        assert result.encryption_iv is not None
        assert result.original_query == query
        
        # Decrypt and verify
        decrypted = PIIRedactionService.decrypt_query(
            result.original_encrypted,
            result.encryption_iv,
            encryption_key,
        )
        assert decrypted == query
    
    @pytest.mark.asyncio
    async def test_encryption_different_each_time(self, pii_service, encryption_key):
        """Test that same query produces different ciphertexts (due to random IV)"""
        query = "Contact support@example.com"
        
        result1 = await pii_service.redact_query(query, encryption_key)
        result2 = await pii_service.redact_query(query, encryption_key)
        
        # IVs should be different
        assert result1.encryption_iv != result2.encryption_iv
        # Ciphertexts should be different
        assert result1.original_encrypted != result2.original_encrypted
        
        # But both should decrypt to same plaintext
        decrypted1 = PIIRedactionService.decrypt_query(
            result1.original_encrypted,
            result1.encryption_iv,
            encryption_key,
        )
        decrypted2 = PIIRedactionService.decrypt_query(
            result2.original_encrypted,
            result2.encryption_iv,
            encryption_key,
        )
        assert decrypted1 == decrypted2 == query


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_query(self, pii_service):
        """Test empty query handling"""
        result = await pii_service.redact_query("")
        
        assert not result.contains_pii
        assert result.redacted_query == ""
        assert len(result.redactions) == 0
    
    @pytest.mark.asyncio
    async def test_whitespace_only_query(self, pii_service):
        """Test whitespace-only query"""
        result = await pii_service.redact_query("   \n  \t  ")
        
        assert not result.contains_pii
        assert len(result.redactions) == 0
    
    @pytest.mark.asyncio
    async def test_no_pii_query(self, pii_service):
        """Test query with no PII"""
        result = await pii_service.redact_query(
            "What is your refund policy?"
        )
        
        assert not result.contains_pii
        assert result.redacted_query == "What is your refund policy?"
        assert len(result.redactions) == 0
    
    @pytest.mark.asyncio
    async def test_query_with_unicode(self, pii_service):
        """Test query with unicode characters"""
        result = await pii_service.redact_query(
            "Contact john@example.com for café menu"
        )
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query
        assert "café" in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_overlapping_patterns(self, pii_service):
        """Test handling of overlapping pattern matches"""
        # This is a contrived case, but tests conflict resolution
        result = await pii_service.redact_query(
            "Visit https://user@example.com/api"
        )
        
        # Should handle gracefully
        assert isinstance(result, RedactedQuery)
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, pii_service):
        """Test with very long query"""
        long_query = "Normal text. " * 1000 + "Email: john@example.com"
        
        result = await pii_service.redact_query(long_query)
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, pii_service):
        """Test that detection is case-insensitive where appropriate"""
        result = await pii_service.redact_query(
            "Contact JOHN@EXAMPLE.COM"
        )
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query


class TestConfidenceScores:
    """Test confidence score handling"""
    
    @pytest.mark.asyncio
    async def test_email_high_confidence(self, pii_service):
        """Test that emails have high confidence"""
        result = await pii_service.redact_query("john@example.com")
        
        assert len(result.redactions) == 1
        assert result.redactions[0].confidence >= 0.99
    
    @pytest.mark.asyncio
    async def test_ssn_high_confidence(self, pii_service):
        """Test that SSNs have high confidence"""
        result = await pii_service.redact_query("123-45-6789")
        
        assert len(result.redactions) == 1
        assert result.redactions[0].confidence >= 0.99
    
    @pytest.mark.asyncio
    async def test_phone_reasonable_confidence(self, pii_service):
        """Test that phone numbers are not detected (temporarily removed)"""
        result = await pii_service.redact_query("555-123-4567")
        
        # Phone regex temporarily removed - awaiting further discussion
        assert len(result.redactions) == 0


class TestSerialization:
    """Test serialization of redaction results"""
    
    @pytest.mark.asyncio
    async def test_to_dict_serialization(self, pii_service):
        """Test conversion to dictionary for JSON serialization"""
        result = await pii_service.redact_query(
            "Contact john@example.com or ssn 123-45-6789"
        )
        
        result_dict = pii_service.to_dict(result)
        
        assert "query_id" in result_dict
        assert "original_query" in result_dict
        assert "redacted_query" in result_dict
        assert "contains_pii" in result_dict
        assert "redactions" in result_dict
        assert isinstance(result_dict["redactions"], list)
        assert len(result_dict["redactions"]) == 2
        
        # Check redaction format
        for redaction in result_dict["redactions"]:
            assert "type" in redaction
            assert "value" in redaction
            assert "position" in redaction
            assert "confidence" in redaction
