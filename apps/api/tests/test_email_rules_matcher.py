import pytest
from app.email_automation.matcher import EmailSample, match_email_to_rules


def test_match_by_keyword_and_folder():
    email = EmailSample(subject="Pricing request", body="Can you send a quote?", folder="INBOX")
    rules = [
        {
            "id": "r1",
            "folder_labels": ["inbox"],
            "include_keywords": ["quote", "pricing"],
            "exclude_keywords": [],
            "priority": 10,
            "is_active": True,
        }
    ]
    matched = match_email_to_rules(email, rules)
    assert matched is not None
    assert matched["id"] == "r1"


def test_exclude_keyword_blocks_match():
    email = EmailSample(subject="Newsletter", body="unsubscribe from list", folder="INBOX")
    rules = [
        {
            "id": "r1",
            "folder_labels": ["inbox"],
            "include_keywords": [],
            "exclude_keywords": ["unsubscribe"],
            "priority": 1,
            "is_active": True,
        }
    ]
    matched = match_email_to_rules(email, rules)
    assert matched is None


def test_priority_order():
    email = EmailSample(subject="Support ticket", body="urgent help needed", folder="Support")
    rules = [
        {"id": "low", "folder_labels": ["support"], "include_keywords": [], "exclude_keywords": [], "priority": 100, "is_active": True},
        {"id": "high", "folder_labels": ["support"], "include_keywords": ["urgent"], "exclude_keywords": [], "priority": 1, "is_active": True},
    ]
    matched = match_email_to_rules(email, rules)
    assert matched is not None
    assert matched["id"] == "high"
