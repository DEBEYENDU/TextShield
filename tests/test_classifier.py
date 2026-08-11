"""Tests for the ML classifier wrapper (uses the trained model)."""
from __future__ import annotations

import pytest

from app.ml.classifier import HAM, SPAM, SpamClassifier

SPAM_MESSAGES = [
    "Congratulations! You have won a cash prize. Click now.",
    "Your bank account will be blocked. Verify immediately using this link.",
    "Earn Rs.50,000 per month from home. Pay Rs.999 registration fee.",
    "Your parcel is stuck. Pay Rs.35 to reschedule delivery now.",
    "You have been selected for a free iPhone. Claim within 1 hour.",
]

HAM_MESSAGES = [
    "Hey, are we meeting at 5 PM today?",
    "Please find attached the assignment, submit it by Monday.",
    "Your order from Amazon has been delivered. Thank you.",
    "The class is postponed to 3 PM tomorrow.",
    "Your recharge of Rs.299 was successful.",
]


@pytest.fixture(scope="module")
def clf() -> SpamClassifier:
    model = SpamClassifier()
    assert model.load(), "Trained model files are required - run scripts/train_model.py"
    return model


@pytest.mark.parametrize("message", SPAM_MESSAGES)
def test_spam_messages_are_spam(clf, message):
    prediction = clf.predict(message)
    assert prediction.label == SPAM
    assert prediction.probability >= 0.5


@pytest.mark.parametrize("message", HAM_MESSAGES)
def test_ham_messages_are_ham(clf, message):
    prediction = clf.predict(message)
    assert prediction.label == HAM
    assert prediction.probability >= 0.5


def test_probability_bounds(clf):
    for message in SPAM_MESSAGES + HAM_MESSAGES:
        prediction = clf.predict(message)
        assert 0.0 <= prediction.probability <= 1.0


def test_empty_text_does_not_crash(clf):
    prediction = clf.predict("")
    assert prediction.label in {SPAM, HAM}


def test_is_spam_property(clf):
    assert clf.predict(SPAM_MESSAGES[0]).is_spam
    assert not clf.predict(HAM_MESSAGES[0]).is_spam