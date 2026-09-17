"""Tests for observation store."""

from app.hunting.observations import ObservationStore
from app.hunting.models import Observation
from datetime import datetime


def test_observation_store():
    store = ObservationStore()
    obs = Observation(
        observation_id="o1",
        analysis_id="a1",
        message_id="m1",
        timestamp=datetime.utcnow(),
        channel="email"
    )
    store.add(obs)
    assert store.count() == 1
    retrieved = store.get("o1")
    assert retrieved is not None
    assert retrieved.message_id == "m1"


def test_list_by_analysis():
    store = ObservationStore()
    obs1 = Observation(observation_id="o1", analysis_id="a1", message_id="m1", timestamp=datetime.utcnow(), channel="email")
    obs2 = Observation(observation_id="o2", analysis_id="a1", message_id="m2", timestamp=datetime.utcnow(), channel="sms")
    store.add(obs1)
    store.add(obs2)
    results = store.list_by_analysis("a1")
    assert len(results) == 2
