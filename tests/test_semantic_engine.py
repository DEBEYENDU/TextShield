"""Tests for the Semantic Understanding Engine (Phase 5).

Covers the pipeline, entity extraction, language detection, feature
computation, similarity service, and graceful handling of empty/malformed
inputs. The engine must never classify and must always return a valid
result object.
"""
from __future__ import annotations

import pytest

from app.semantic.semantic_models import (
    CONTEXT_DOMAINS,
    SemanticAnalysisResult,
)
from app.semantic.semantic_pipeline import SemanticPipeline
from app.semantic.semantic_service import SemanticService, SimilarityService
from app.semantic.semantic_utils import (
    detect_language,
    extract_emojis,
    parse_raw_email,
    parse_sms,
    preprocess_text,
    segment_sentences,
)

pipeline = SemanticPipeline()
service = SemanticService()
similarity = SimilarityService()


class TestUtils:
    def test_preprocess_unicode_and_whitespace(self):
        assert preprocess_text("  Hello\u2019s  world!!  \n\t More  ") == "Hello's world!! More"

    def test_preprocess_preserves_emoji(self):
        assert extract_emojis("Great news! \U0001f389\U0001f4b0 Win a prize \U0001f600") == [
            "\U0001f389",
            "\U0001f4b0",
            "\U0001f600",
        ]

    def test_segment_sentences(self):
        assert segment_sentences("Hello world! How are you? I am fine.") == [
            "Hello world!",
            "How are you?",
            "I am fine.",
        ]

    def test_segment_respects_abbreviations(self):
        assert segment_sentences("Dr. Smith said the price is Rs. 500. Next day it rose.") == [
            "Dr. Smith said the price is Rs. 500. Next day it rose."
        ]

    def test_detect_language(self):
        assert detect_language("Hello how are you today?")[0] == "en"
        assert detect_language("\u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u094b\u0938\u094d\u0924")[0] == "hi"
        assert detect_language("\u0645\u0631\u062d\u0628\u0627 \u0635\u062f\u064a\u0642\u064a")[0] == "ar"

    def test_parse_raw_email(self):
        header = (
            "From: sender@example.com\r\n"
            "Subject: Hello there\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n\r\n"
            "This is the body line one.\r\nBody line two."
        )
        parsed = parse_raw_email(header)
        assert parsed["subject"] == "Hello there"
        assert parsed["sender"] == "sender@example.com"
        assert "Body line two." in parsed["body"]

    def test_parse_sms(self):
        parsed = parse_sms("+91-98765-43210: Happy new year!")
        assert parsed["message"] == "+91-98765-43210: Happy new year!"


class TestPipeline:
    def test_short_message(self):
        result = service.analyze_sms("Win a free iPhone today! Reply YES to claim now.", include_embeddings=False)
        assert isinstance(result, SemanticAnalysisResult)
        assert result.language == "en"
        assert any(t.topic == "Prize" for t in result.topics)
        assert result.embedding_provider in {"sentence_transformers", "fallback_hashing"}
        assert result.confidence.language >= 0.5

    def test_long_email(self):
        body = " ".join(
            [
                "Dear customer,",
                "Your order for the new laptop has been shipped.",
                "The tracking number is 1Z999AA10123456784.",
                "Estimated delivery is on 25 Dec 2026.",
                "Please contact support@store.example for any questions.",
                "Thank you for shopping with us at Tech Store Ltd.",
            ]
        )
        result = service.analyze_email(subject="Your order shipped", sender="noreply@techstore.example", body=body)
        types = {e.type for e in result.entities}
        assert "email" in types
        assert "tracking_number" in types
        assert "date" in types
        assert any(t.topic == "Delivery" for t in result.topics)
        assert result.embedding_dimension == 384
        assert set(result.embeddings) == {"message", "sentences", "subject", "body"}

    def test_multiple_languages(self):
        hindi = "\u092f\u0939 \u092c\u0948\u0902\u0915 \u0905\u0915\u093e\u0909\u0902\u091f \u0938\u0941\u0930\u0915\u094d\u0937\u093e \u092e\u0947\u0902 \u0939\u0948"
        result = service.analyze_sms(hindi, include_embeddings=False)
        assert result.language in {"hi", "en"}
        assert len(result.contexts) >= 1

    def test_empty_message_graceful(self):
        result = service.analyze_text("", include_embeddings=False)
        assert result.language == "unknown"
        assert result.contexts[0].domain == "unknown"
        assert result.topics == []
        assert result.entities == []

    def test_empty_email_graceful(self):
        result = service.analyze_email(subject=None, sender=None, body=None, email_raw="")
        assert isinstance(result, SemanticAnalysisResult)
        assert result.contexts[0].domain == "unknown"

    def test_malformed_email_raw_graceful(self):
        result = service.analyze_email(email_raw="\xff\xfe\x00 not a real email header")
        assert isinstance(result, SemanticAnalysisResult)

    def test_urls_phones_money(self):
        message = (
            "Call 9876543210 now or visit https://bit.ly/xyz to pay Rs.5000 "
            "before 2026-09-30."
        )
        result = service.analyze_text(message, include_embeddings=False)
        types = {e.type: e.value for e in result.entities}
        assert types.get("url") == "https://bit.ly/xyz"
        assert types.get("phone") == "9876543210"
        assert types.get("money") == "Rs.5000"
        assert types.get("date") == "2026-09-30"
        assert result.semantic_features.url_count == 1
        assert result.semantic_features.phone_count == 1
        assert result.semantic_features.money_count == 1

    def test_no_phone_inside_tracking_or_account(self):
        message = "Account 123456789012 blocked. Track 1Z999AA10123456784."
        result = service.analyze_text(message, include_embeddings=False)
        phones = [e.value for e in result.entities if e.type == "phone"]
        assert phones == []

    def test_emoji_mixed(self):
        message = "\U0001f4b0 Congratulations! You won 5000 rupees! Claim: 9876543210 \U0001f389"
        result = service.analyze_sms(message, include_embeddings=False)
        assert result.semantic_features.emoji_count >= 1
        assert any(t.topic == "Prize" for t in result.topics)

    def test_question_and_imperative_features(self):
        message = "Hi! Please verify your account now. Are you available tomorrow at 3 pm?"
        result = service.analyze_text(message, include_embeddings=False)
        assert result.semantic_features.question_count == 1
        assert result.semantic_features.imperative_count >= 1
        assert result.semantic_features.has_request is True

    def test_context_domains_are_known(self):
        result = service.analyze_text("Your bank card is ready for activation.")
        assert all(c.domain in CONTEXT_DOMAINS for c in result.contexts)
        assert result.confidence.context >= 0

    def test_embedding_cache_and_clear(self):
        service.embedding.clear_cache()
        vec_a = service.embedding.embed_one("hello world")
        vec_b = service.embedding.embed_one("hello world")
        assert vec_a == vec_b
        assert service.embedding.cache_info()["size"] == 1
        service.embedding.clear_cache()
        assert service.embedding.cache_info()["size"] == 0

    def test_batch_analyze(self):
        results = service.batch_analyze(
            [("Simple hello.", "text"), ("Your loan is approved. Call 9876543210.", "sms")]
        )
        assert len(results) == 2
        assert results[0].contexts[0].domain in CONTEXT_DOMAINS


class TestSimilarity:
    def test_cosine_identical_vectors(self):
        assert similarity.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    def test_cosine_orthogonal_vectors(self):
        assert similarity.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_cosine_mismatched_length(self):
        assert similarity.cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_embedding_distance(self):
        dist = similarity.embedding_distance([0.0, 0.0], [3.0, 4.0])
        assert dist == pytest.approx(5.0)

    def test_sentence_similarity_related(self):
        hi = similarity.sentence_similarity("I love my new phone", "This new phone is great")
        lo = similarity.sentence_similarity("I love my new phone", "The stock market fell today")
        assert hi > 0.4
        assert lo < hi

    def test_sentence_similarity_identical(self):
        assert similarity.sentence_similarity("same text", "same text") > 0.99
