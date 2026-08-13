"""Tests for the Intent & Behavior Analysis Engine (Phase 6).

Covers sender intents, requested actions, behaviors, manipulation
techniques, urgency, trust signals, conversation style, communication
goal, confidence, determinism, config thresholds and edge cases.
The engine must never classify — it only describes behavior.
"""
from __future__ import annotations

import pytest

from app.intent.models import IntentAnalysisResult
from app.intent.pipeline import IntentPipeline
from app.intent.intent_service import INTENT_SPECS
from app.intent.action_service import ACTION_SPECS
from app.intent.behavior_service import BEHAVIOR_SPECS
from app.intent.manipulation_service import TECHNIQUE_SPECS
from app.core.settings import settings

pipeline = IntentPipeline()


def analyze(message, message_type="sms", **kw):
    return pipeline.analyze(message=message, message_type=message_type, **kw)


class TestIntents:
    def test_normal_conversation(self):
        r = analyze("Hey! How are you? Are you free this weekend? Let's meet for coffee.")
        assert "Social Conversation" in {i.name for i in r.intents}
        assert not any(i.name.startswith("Request") for i in r.intents)

    def test_promotional_message(self):
        r = analyze("Get 50% off on all shoes this weekend! Shop now at https://shoes.example.com")
        names = {i.name for i in r.intents}
        assert {"Sell", "Offer Discount"} <= names
        assert "Education" not in names

    def test_prize_announcement(self):
        r = analyze("CONGRATULATIONS! You have won a FREE iPhone 15. Claim your prize today only!")
        assert "Offer Reward" in {i.name for i in r.intents}
        assert r.urgency.level in {"medium", "high", "critical"}

    def test_bank_notification_is_not_threat(self):
        r = analyze("Dear customer, your account has been credited with Rs. 5000. Transaction ID: TXN123456.")
        names = {i.name for i in r.intents}
        assert "Notify" in names
        assert "Threaten" not in names

    def test_otp_request(self):
        r = analyze("Reply with your OTP 483920 to claim your prize today only!")
        assert "Request OTP" in {i.name for i in r.intents}

    def test_bank_otp_message_is_not_request(self):
        r = analyze("Your OTP for login is 483920. Do not share it with anyone.")
        names = {i.name for i in r.intents}
        assert "Request OTP" not in names
        assert "Notify" in names or "Warn" in names

    def test_delivery_notification(self):
        r = analyze("Your order will be delivered tomorrow between 9 AM and 12 PM. Track: https://track.example")
        assert "Notify" in {i.name for i in r.intents}
        assert "Education" not in {i.name for i in r.intents}

    def test_educational_announcement(self):
        r = analyze("Admission open for 2026 batch at City Academy. Limited seats. Call 9988776655.")
        assert "Education" in {i.name for i in r.intents}

    def test_mixed_intent_message(self):
        r = analyze("Your bank account will be blocked. Verify via https://bit.ly/x. Pay Rs.5000 now!")
        names = {i.name for i in r.intents}
        assert len(r.intents) > 1
        assert len(r.intents) <= settings.INTENT_MAX_INTENTS

    def test_ambiguous_message(self):
        r = analyze("Hello, this is a message for you. We hope everything is fine.")
        names = {i.name for i in r.intents}
        assert "Unknown" in names or "Social Conversation" in names

    def test_hindi_message_graceful(self):
        r = analyze("\u092f\u0939 \u092c\u0948\u0902\u0915 \u0905\u0915\u093e\u0909\u0902\u091f "
                    "\u0938\u0941\u0930\u0915\u094d\u0937\u093e \u092e\u0947\u0902 \u0939\u0948")
        assert isinstance(r, IntentAnalysisResult)
        assert all(0 <= i.confidence <= 1 for i in r.intents)

    def test_max_intents_respected(self):
        r = analyze(
            "URGENT! Your account will be blocked. Pay now. Call us. Reply with OTP. Visit https://x.y"
        )
        assert len(r.intents) <= settings.INTENT_MAX_INTENTS


class TestActions:
    def test_call_and_transfer(self):
        r = analyze("Your bank account will be blocked. Pay Rs.5000 to account 123456789012. Call 9876543210 now!")
        names = {a.name for a in r.requested_actions}
        assert "Call Number" in names
        assert "Transfer Money" in names

    def test_click_link(self):
        r = analyze("Verify immediately via this link https://bit.ly/xyz")
        assert "Click Link" in {a.name for a in r.requested_actions}

    def test_reply_action(self):
        r = analyze("Reply YES to confirm your appointment.")
        assert "Reply" in {a.name for a in r.requested_actions}

    def test_purchase_action(self):
        r = analyze("Buy now and get 20% off at our store https://shop.example")
        assert "Purchase Product" in {a.name for a in r.requested_actions}

    def test_no_action_for_info(self):
        r = analyze("The office will remain closed on Monday due to a holiday.")
        assert "No Action" in {a.name for a in r.requested_actions}


class TestBehaviors:
    def test_financial_request(self):
        r = analyze("Kindly pay the due amount of Rs. 2500 to the account below.")
        assert "Financial Request" in {b.name for b in r.behaviors}

    def test_credential_request(self):
        r = analyze("Please share your OTP and password to continue.")
        assert "Credential Request" in {b.name for b in r.behaviors}

    def test_external_redirection(self):
        r = analyze("Click here https://bit.ly/xyz to update your details.")
        assert "External Redirection" in {b.name for b in r.behaviors}

    def test_marketing_behavior(self):
        r = analyze("Huge sale! 50% off on everything. Don't miss out!")
        assert "Marketing" in {b.name for b in r.behaviors}

    def test_appointment_behavior(self):
        r = analyze("Reminder: Your dentist appointment is on 25 Dec at 3 pm. Reply C to confirm.")
        assert "Appointment" in {b.name for b in r.behaviors}
        assert "Reminder" in {b.name for b in r.behaviors}

    def test_support_conversation(self):
        r = analyze("Hi, my order is not working. Can you help me with this issue?")
        assert "Support Conversation" in {b.name for b in r.behaviors}


class TestManipulation:
    def test_urgency_technique(self):
        r = analyze("Act now! This offer expires today only!")
        assert "Urgency" in {m.name for m in r.manipulation}

    def test_fear_technique(self):
        r = analyze("Your account will be blocked permanently. Legal action will be taken.")
        assert "Fear" in {m.name for m in r.manipulation}

    def test_reward_technique(self):
        r = analyze("Congratulations! You won a free gift card!")
        assert "Reward" in {m.name for m in r.manipulation}

    def test_scarcity_technique(self):
        r = analyze("Only 3 seats left for this course. Limited seats available!")
        assert "Scarcity" in {m.name for m in r.manipulation}

    def test_authority_technique(self):
        r = analyze("Official notice from the Income Tax Department regarding your filing.")
        assert "Authority" in {m.name for m in r.manipulation}

    def test_evidence_present(self):
        r = analyze("URGENT! Act immediately or your account will be blocked!")
        assert all(m.evidence for m in r.manipulation)


class TestUrgency:
    def test_none_for_friendly(self):
        r = analyze("Hey! How was your weekend? Let's catch up sometime.")
        assert r.urgency.level == "none"
        assert r.urgency.score == 0.0

    def test_critical_for_intense(self):
        r = analyze("URGENT!!! IMMEDIATE ACTION REQUIRED. YOUR ACCOUNT WILL BE SUSPENDED RIGHT NOW. ACT IMMEDIATELY.")
        assert r.urgency.level in {"high", "critical"}

    def test_urgency_evidence(self):
        r = analyze("Act immediately! Deadline is today.")
        assert r.urgency.evidence

    def test_urgency_bounds(self):
        r = analyze("Your account is being deactivated. Please act now!")
        assert 0.0 <= r.urgency.score <= 100.0
        assert 0.0 <= r.urgency.confidence <= 1.0


class TestTrustSignals:
    def test_bank_reference(self):
        r = analyze("Dear customer, your HDFC Bank account has been updated.")
        assert any(s.name == "Bank references" for s in r.trust_signals)

    def test_personal_greeting(self):
        r = analyze("Dear Mr. Sharma, we hope this message finds you well.")
        assert any(s.name == "Personal greetings" for s in r.trust_signals)

    def test_official_language(self):
        r = analyze("Kindly be informed that per regulations, your application is under review.")
        assert any(s.name == "Official language" for s in r.trust_signals)


class TestStyleGoal:
    def test_informal_style(self):
        r = analyze("Hey! Wanna grab lunch tomorrow? Lol, it's been ages.")
        assert r.conversation_style.style == "Informal"

    def test_marketing_style(self):
        r = analyze("Big sale! Flat 50% off on all items. Shop now!")
        assert r.conversation_style.style in {"Marketing", "Promotional"}

    def test_transactional_style(self):
        r = analyze("Your payment of Rs. 5000 was successful. Transaction ID: TXN123.")
        assert r.conversation_style.style == "Transactional"

    def test_goal_obtain_credentials(self):
        r = analyze("Reply with your OTP to verify your account.")
        assert r.communication_goal.goal == "Obtain Credentials"

    def test_goal_offer_opportunity(self):
        r = analyze("You have won a free iPhone! Claim it today only!")
        assert r.communication_goal.goal == "Offer Opportunity"

    def test_goal_share_information_default(self):
        r = analyze("The office will remain closed on Monday due to a public holiday.")
        assert r.communication_goal.goal == "Share Information"

    def test_goal_continue_conversation(self):
        r = analyze("Hey! How are you? Are we meeting this weekend?")
        assert r.communication_goal.goal == "Continue Conversation"


class TestPipeline:
    def test_result_shape(self):
        r = analyze("Please share your OTP.")
        assert isinstance(r, IntentAnalysisResult)
        assert set(r.confidence) == {
            "intents", "requested_actions", "behaviors", "manipulation",
            "urgency", "trust_signals", "conversation_style", "communication_goal",
        }
        assert all(0 <= v <= 1 for v in r.confidence.values())

    def test_deterministic(self):
        msg = "Your bank account will be blocked. Pay Rs.5000 to account 123456789012 now!"
        first = analyze(msg)
        second = analyze(msg)
        assert first.model_dump() == second.model_dump()

    def test_semantic_result_reused(self):
        from app.semantic.semantic_pipeline import SemanticPipeline

        calls = {"n": 0}

        class TrackingPipeline(SemanticPipeline):
            def analyze(self, *a, **kw):
                calls["n"] += 1
                return super().analyze(*a, **kw)

        pipe = IntentPipeline(semantic_pipeline=TrackingPipeline())
        semantic = pipe.semantic_pipeline.analyze(message="Pay Rs.5000 now!", message_type="sms")
        assert calls["n"] == 1
        pipe.analyze(semantic_result=semantic)
        assert calls["n"] == 1  # semantic not re-run when supplied

    def test_threshold_config(self, monkeypatch):
        monkeypatch.setattr(settings, "INTENT_CONFIDENCE_THRESHOLD", 0.99)
        r = analyze("Please share your OTP with us.")
        assert all(i.confidence < 0.99 for i in r.intents)
        assert any(i.name == "Unknown" for i in r.intents)

    def test_max_intents_config(self, monkeypatch):
        monkeypatch.setattr(settings, "INTENT_MAX_INTENTS", 1)
        r = analyze("URGENT! Account blocked. Pay now. Call us. Visit https://x.y")
        assert len(r.intents) <= 1

    def test_empty_message(self):
        r = analyze("")
        assert r.intents[0].name == "Unknown"
        assert r.requested_actions[0].name == "No Action"
        assert r.urgency.level == "none"
        assert r.conversation_style.style == "Unknown"
        assert r.communication_goal.goal == "Share Information"

    def test_email_input(self):
        r = pipeline.analyze(
            subject="Your order is confirmed",
            sender="noreply@shop.example",
            body="Your order will be delivered by 25 Dec. Track: https://track.example",
            message_type="email",
        )
        assert "Notify" in {i.name for i in r.intents}

    def test_all_specs_have_names(self):
        assert all(s.name for s in INTENT_SPECS)
        assert all(s.name for s in ACTION_SPECS)
        assert all(s.name for s in BEHAVIOR_SPECS)
        assert all(s.name for s in TECHNIQUE_SPECS)

    def test_engine_never_classifies(self):
        r = analyze("Your account will be blocked. Pay Rs.5000 to 123456789012 now!")
        dump = r.model_dump()
        flat = str(dump).lower()
        for forbidden in ("spam", "phish", "risk_score", "malicious"):
            assert forbidden not in flat
