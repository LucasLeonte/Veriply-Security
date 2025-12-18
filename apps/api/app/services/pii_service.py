"""
PII Redaction Service

Two-tier PII detection and redaction:
1. Tier 1: Rule-based regex detection (emails, phones, SSN, credit cards, IPs, URLs)
2. Tier 2: ML-based NER detection (Microsoft Presidio for context-dependent PII like names)
"""

import os
import re
import uuid
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass, field
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import logging

logger = logging.getLogger(__name__)


@dataclass
class RedactionInfo:
    """Information about a single redacted entity"""
    pii_type: str
    original_value: str
    redacted_as: str
    position: Tuple[int, int]  # Start and end character offsets
    confidence: float
    detection_method: str  # "regex" or "presidio"


@dataclass
class RedactedQuery:
    """Result of PII redaction"""
    query_id: str
    original_query: str  # Unredacted (will be encrypted before storage)
    redacted_query: str
    redactions: List[RedactionInfo] = field(default_factory=list)
    contains_pii: bool = False
    original_encrypted: Optional[bytes] = None
    encryption_iv: Optional[bytes] = None


class PIIRedactionService:
    """
    Service for detecting and redacting PII from queries.
    Uses two-tier approach: fast regex patterns + ML-based NER.
    """
    
    # Tier 1: Regex patterns for high-confidence PII
    PATTERNS = {
        "EMAIL": {
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "replacement": "<EMAIL>",
            "confidence": 0.99,
        },
        "SSN": {
            "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
            "replacement": "<SSN>",
            "confidence": 0.99,
        },
        "CREDIT_CARD": {
            # Luhn validation will be applied separately
            "pattern": r"\b(?:\d[ -]*?){13,19}\b",
            "replacement": "<CREDIT_CARD>",
            "confidence": 0.85,  # Lower confidence, needs Luhn validation
        },
        "IP_ADDRESS": {
            "pattern": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "replacement": "<IP_ADDRESS>",
            "confidence": 0.98,
        },
        "URL": {
            "pattern": r"https?://[^\s]+",
            "replacement": "<URL>",
            "confidence": 0.99,
        },
    }
    
    # Minimum confidence threshold for redaction
    MIN_CONFIDENCE = 0.95
    
    def __init__(self, presidio_enabled: bool = True):
        """
        Initialize PII Redaction Service.
        
        Args:
            presidio_enabled: Whether to use Microsoft Presidio for ML-based detection
        """
        self.presidio_enabled = presidio_enabled
        self.analyzer = None
        self.anonymizer = None
        
        if presidio_enabled:
            self._init_presidio()
    
    def _init_presidio(self):
        """Initialize Microsoft Presidio for ML-based NER detection"""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Microsoft Presidio initialized successfully")
        except ImportError:
            logger.warning("Microsoft Presidio not installed. Using regex-only detection.")
            self.presidio_enabled = False
    
    async def redact_query(
        self,
        query_text: str,
        encryption_key: Optional[bytes] = None,
    ) -> RedactedQuery:
        """
        Detect and redact PII from query.
        
        Args:
            query_text: Original query text
            encryption_key: Optional AES-256 key for encrypting original query
        
        Returns:
            RedactedQuery with redacted text and redaction metadata
        """
        if not query_text or not query_text.strip():
            return RedactedQuery(
                query_id=str(uuid.uuid4()),
                original_query=query_text,
                redacted_query=query_text,
                redactions=[],
                contains_pii=False,
            )
        
        # Tier 1: Regex-based detection
        redactions = self._detect_with_regex(query_text)
        
        # Tier 2: ML-based detection (if enabled)
        if self.presidio_enabled:
            ml_redactions = self._detect_with_presidio(query_text)
            # Merge detections, resolving conflicts
            redactions = self._resolve_conflicts(redactions, ml_redactions)
        
        # Apply redactions
        redacted_query = self._apply_redactions(query_text, redactions)
        
        # Encrypt original if key provided
        encrypted_data = None
        encryption_iv = None
        if encryption_key:
            encrypted_data, encryption_iv = self._encrypt_query(
                query_text, encryption_key
            )
        
        result = RedactedQuery(
            query_id=str(uuid.uuid4()),
            original_query=query_text,
            redacted_query=redacted_query,
            redactions=redactions,
            contains_pii=len(redactions) > 0,
            original_encrypted=encrypted_data,
            encryption_iv=encryption_iv,
        )
        
        logger.info(
            f"Query redacted: {len(redactions)} PII entities found",
            extra={"redactions": len(redactions), "query_id": result.query_id}
        )
        
        return result
    
    def _detect_with_regex(self, text: str) -> List[RedactionInfo]:
        """
        Tier 1: Detect PII using regex patterns.
        
        Args:
            text: Text to scan for PII
        
        Returns:
            List of RedactionInfo objects for detected PII
        """
        redactions = []
        
        for pii_type, config in self.PATTERNS.items():
            pattern = config["pattern"]
            replacement = config["replacement"]
            confidence = config["confidence"]
            
            # Find all matches
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original_value = match.group(0)
                start, end = match.span()
                
                # Additional validation for credit cards
                if pii_type == "CREDIT_CARD":
                    if not self._is_valid_credit_card(original_value):
                        continue
                    confidence = 0.99  # Valid Luhn number
                
                # Only add if meets confidence threshold or after validation boost
                if confidence < self.MIN_CONFIDENCE and pii_type != "CREDIT_CARD":
                    continue
                
                # Skip false positives for IPs (version numbers, timestamps)
                if pii_type == "IP_ADDRESS":
                    if self._is_likely_version_number(original_value):
                        continue
                
                redaction = RedactionInfo(
                    pii_type=pii_type,
                    original_value=original_value,
                    redacted_as=replacement,
                    position=(start, end),
                    confidence=confidence,
                    detection_method="regex",
                )
                redactions.append(redaction)
        
        return redactions
    
    def _detect_with_presidio(self, text: str) -> List[RedactionInfo]:
        """
        Tier 2: Detect PII using Microsoft Presidio NER.
        
        Args:
            text: Text to scan for PII
        
        Returns:
            List of RedactionInfo objects for detected PII
        """
        if not self.analyzer:
            return []
        
        redactions = []
        
        try:
            # Analyze text for PII
            results = self.analyzer.analyze(
                text=text,
                language="en",
                entities=[
                    "PERSON",
                    "ORGANIZATION",
                    "LOCATION",
                    "DOMAIN_NAME",
                ],
                score_threshold=0.5,  # 50% confidence for consideration
            )
            
            for result in results:
                entity_type = result.entity_type
                
                # Map Presidio entity types to our redaction markers
                redaction_map = {
                    "PERSON": "<PERSON>",
                    "ORGANIZATION": "<ORGANIZATION>",
                    "LOCATION": "<LOCATION>",
                    "DOMAIN_NAME": "<DOMAIN>",
                }
                
                if entity_type not in redaction_map:
                    continue
                
                original_value = text[result.start : result.end]
                
                # Only redact high-confidence detections
                if result.score >= self.MIN_CONFIDENCE:
                    redaction = RedactionInfo(
                        pii_type=entity_type,
                        original_value=original_value,
                        redacted_as=redaction_map[entity_type],
                        position=(result.start, result.end),
                        confidence=result.score,
                        detection_method="presidio",
                    )
                    redactions.append(redaction)
        
        except Exception as e:
            logger.error(f"Presidio analysis failed: {e}")
        
        return redactions
    
    def _resolve_conflicts(
        self,
        regex_redactions: List[RedactionInfo],
        presidio_redactions: List[RedactionInfo],
    ) -> List[RedactionInfo]:
        """
        Resolve overlapping detections between regex and Presidio.
        Prefer higher confidence scores and more specific detections.
        
        Args:
            regex_redactions: Redactions from regex patterns
            presidio_redactions: Redactions from Presidio NER
        
        Returns:
            Merged list with conflicts resolved
        """
        # Combine all redactions
        all_redactions = regex_redactions + presidio_redactions
        
        if not all_redactions:
            return []
        
        # Sort by position
        all_redactions.sort(key=lambda r: r.position[0])
        
        # Remove overlapping detections (keep higher confidence)
        merged = []
        for redaction in all_redactions:
            # Check for overlaps with existing redactions
            overlaps = [
                r for r in merged
                if (r.position[0] < redaction.position[1] and
                    r.position[1] > redaction.position[0])
            ]
            
            if not overlaps:
                merged.append(redaction)
            else:
                # Keep the one with higher confidence
                for overlap in overlaps:
                    if redaction.confidence > overlap.confidence:
                        merged.remove(overlap)
                        merged.append(redaction)
        
        return merged
    
    def _apply_redactions(
        self,
        text: str,
        redactions: List[RedactionInfo],
    ) -> str:
        """
        Apply redactions to text.
        Process from end to start to preserve character positions.
        
        Args:
            text: Original text
            redactions: List of redactions to apply
        
        Returns:
            Text with PII redacted
        """
        if not redactions:
            return text
        
        # Sort by position (reverse) to apply from end to start
        sorted_redactions = sorted(
            redactions, key=lambda r: r.position[0], reverse=True
        )
        
        result = text
        for redaction in sorted_redactions:
            start, end = redaction.position
            result = result[:start] + redaction.redacted_as + result[end:]
        
        return result
    
    @staticmethod
    def _is_valid_credit_card(card_number: str) -> bool:
        """
        Validate credit card using Luhn algorithm.
        
        Args:
            card_number: Card number with potential spaces/dashes
        
        Returns:
            True if valid Luhn checksum
        """
        # Remove spaces and dashes
        digits_only = card_number.replace(" ", "").replace("-", "")
        
        # Must be 13-19 digits
        if not digits_only.isdigit() or len(digits_only) < 13 or len(digits_only) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(digits_only)):
            d = int(digit)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        
        return total % 10 == 0
    
    @staticmethod
    def _is_likely_version_number(ip_like: str) -> bool:
        """
        Check if IP-like string is actually a version number.
        
        Args:
            ip_like: String matching IP pattern
        
        Returns:
            True if likely a version number (e.g., 1.2.3.4 where values > 255)
        """
        parts = ip_like.split(".")
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                if int(part) > 255:
                    return True
        except ValueError:
            pass
        
        return False
    
    @staticmethod
    def _encrypt_query(
        query_text: str,
        key: bytes,
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt original query using AES-256-GCM.
        
        Args:
            query_text: Query to encrypt
            key: 32-byte AES-256 key
        
        Returns:
            Tuple of (ciphertext, iv)
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        
        # Generate random 96-bit IV (12 bytes) for GCM
        iv = os.urandom(12)
        
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(iv, query_text.encode(), None)
        
        return ciphertext, iv
    
    @staticmethod
    def decrypt_query(
        ciphertext: bytes,
        iv: bytes,
        key: bytes,
    ) -> str:
        """
        Decrypt original query (for support/debugging only).
        
        Args:
            ciphertext: Encrypted query
            iv: Initialization vector
            key: AES-256 key
        
        Returns:
            Decrypted query text
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(iv, ciphertext, None)
        
        return plaintext.decode()
    
    def to_dict(self, result: RedactedQuery) -> Dict[str, Any]:
        """
        Convert RedactedQuery to dictionary for JSON serialization.
        
        Args:
            result: RedactedQuery object
        
        Returns:
            Dictionary representation
        """
        return {
            "query_id": result.query_id,
            "original_query": result.original_query,
            "redacted_query": result.redacted_query,
            "contains_pii": result.contains_pii,
            "redactions": [
                {
                    "type": r.pii_type,
                    "value": r.original_value,
                    "redacted_as": r.redacted_as,
                    "position": list(r.position),
                    "confidence": r.confidence,
                    "method": r.detection_method,
                }
                for r in result.redactions
            ],
        }
