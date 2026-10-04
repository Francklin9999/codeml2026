import copy
import unittest

from nova.events import EventError, apply_event, build_baseline, replay_events


FACTS = [
    {
        "id": "F-DATE",
        "subject": "go-live",
        "type": "decision",
        "statement": "22 octobre 2026, sous conditions",
        "status": "current",
        "lifecycle_status": "APPROVED_CONDITIONAL",
        "date": "2026-09-10",
        "info_as_of": "2026-09-10",
        "authority": "committee_decision",
        "authority_rank": 9,
        "source_file": "meeting.txt",
        "locator": "M04@15:22",
    },
    {
        "id": "F-PROP",
        "subject": "go-live",
        "type": "proposal",
        "statement": "22 octobre 2026 proposé",
        "status": "proposal-only",
        "date": "2026-09-08",
        "authority": "vendor_statement",
        "source_file": "email.eml",
        "locator": "E05#body",
    },
    {
        "id": "F-SEC",
        "subject": "SEC-210",
        "type": "delivery",
        "statement": "Correctif livré, validation en attente",
        "status": "current",
        "lifecycle_status": "DELIVERED",
        "date": "2026-09-19",
        "authority": "vendor_statement",
        "authority_rank": 4,
        "source_file": "SEC-210.txt",
        "locator": "SEC-210#2026-09-19T10:22",
    },
]


def event(**updates):
    value = {
        "event_id": "LIVE-001",
        "record_time": "2026-10-04T10:00:00-04:00",
        "valid_time": "2026-10-04T09:30:00-04:00",
        "subject": "SEC-210",
        "kind": "validation",
        "statement": "Le re-test est accepté.",
        "actor": "Sophie Lambert",
        "authority": "accountable_owner_validation",
        "source": "Événement live",
        "new_status": "VALIDATED",
        "affects_answers": ["Q01", "Q08", "Q10"],
    }
    value.update(updates)
    return value


class EventTests(unittest.TestCase):
    def setUp(self):
        self.baseline = build_baseline(FACTS)

    def test_validation_updates_only_subject_and_keeps_baseline(self):
        original = copy.deepcopy(self.baseline)
        state, diff = apply_event(self.baseline, event())
        self.assertEqual("VALIDATED", state["current"]["SEC-210"]["status"])
        self.assertEqual(original, self.baseline)
        self.assertIn("go-live", diff["unchanged_subjects"])

    def test_vendor_cannot_validate(self):
        with self.assertRaisesRegex(EventError, "livraison fournisseur"):
            apply_event(
                self.baseline,
                event(actor="Julien Moreau", authority="vendor_statement"),
            )

    def test_proposal_does_not_replace_decision(self):
        state, diff = apply_event(
            self.baseline,
            event(
                subject="go-live",
                kind="proposal",
                statement="Déplacer au 29 octobre",
                authority="vendor_statement",
                actor="Julien Moreau",
            ),
        )
        self.assertEqual(
            self.baseline["current"]["go-live"], state["current"]["go-live"]
        )
        self.assertFalse(diff["changed"])

    def test_cross_subject_mutation_is_rejected(self):
        with self.assertRaisesRegex(EventError, "autre sujet"):
            apply_event(self.baseline, event(affects_subjects=["ACC-303"]))

    def test_replay_is_deterministic(self):
        second = event(
            event_id="LIVE-002",
            record_time="2026-10-04T11:00:00-04:00",
            valid_time="2026-10-04T10:30:00-04:00",
            subject="go-live",
            kind="proposal",
            authority="vendor_statement",
            actor="Julien Moreau",
            statement="Reporter au 29 octobre",
        )
        first = event()
        state_a, diffs_a = replay_events(self.baseline, [second, first])
        state_b, diffs_b = replay_events(self.baseline, [first, second])
        self.assertEqual(state_a, state_b)
        self.assertEqual(diffs_a, diffs_b)


if __name__ == "__main__":
    unittest.main()
