"""Tests for data import/export utilities."""

import json

from src.core.otp import OTPAccount, OTPType, Algorithm
from src.utils.export_import import (
    export_uri_list,
    import_uri_list,
    export_json,
    import_json,
    import_aegis_backup,
)


def _sample_accounts() -> list[OTPAccount]:
    return [
        OTPAccount(
            id="id-1",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
            is_github=True,
        ),
        OTPAccount(
            id="id-2",
            issuer="AWS",
            name="root",
            secret="GEZDGNBVGY3TQOJQ",
            otp_type=OTPType.HOTP,
            algorithm=Algorithm.SHA256,
            digits=8,
            counter=3,
            group="Work",
            notes="primary account",
        ),
    ]


class TestUriList:
    def test_export_then_import_roundtrip(self):
        accounts = _sample_accounts()
        text = export_uri_list(accounts)

        # One otpauth URI per account.
        lines = text.strip().splitlines()
        assert len(lines) == 2
        assert all(line.startswith("otpauth://") for line in lines)

        imported = import_uri_list(text)
        assert [a.secret for a in imported] == [a.secret for a in accounts]
        assert imported[0].issuer == "GitHub"
        assert imported[1].otp_type == OTPType.HOTP

    def test_import_skips_malformed_lines(self):
        text = (
            "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub\n"
            "not-a-uri\n"
            "\n"
            "otpauth://invalid-without-secret\n"
        )
        accounts = import_uri_list(text)
        assert len(accounts) == 1
        assert accounts[0].secret == "JBSWY3DPEHPK3PXP"

    def test_import_empty_returns_empty(self):
        assert import_uri_list("   \n  \n") == []


class TestJson:
    def test_export_produces_valid_json(self):
        text = export_json(_sample_accounts())
        data = json.loads(text)
        assert len(data) == 2
        assert data[0]["issuer"] == "GitHub"
        assert data[1]["otp_type"] == "hotp"
        assert data[1]["digits"] == 8
        # Secrets are included in JSON export (full backup).
        assert data[0]["secret"] == "JBSWY3DPEHPK3PXP"

    def test_export_then_import_roundtrip(self):
        accounts = _sample_accounts()
        imported = import_json(export_json(accounts))

        assert len(imported) == 2
        first = imported[0]
        assert first.issuer == "GitHub"
        assert first.secret == "JBSWY3DPEHPK3PXP"
        assert first.is_github is True

        second = imported[1]
        assert second.otp_type == OTPType.HOTP
        assert second.algorithm == Algorithm.SHA256
        assert second.digits == 8
        assert second.counter == 3
        assert second.group == "Work"
        assert second.notes == "primary account"

    def test_import_assigns_fresh_unique_ids(self):
        imported = import_json(export_json(_sample_accounts()))
        ids = {a.id for a in imported}
        assert len(ids) == 2
        # IDs are regenerated, not carried over from the original objects.
        assert "id-1" not in ids

    def test_import_applies_defaults_for_missing_fields(self):
        text = json.dumps([{"secret": "JBSWY3DPEHPK3PXP"}])
        accounts = import_json(text)
        assert len(accounts) == 1
        acc = accounts[0]
        assert acc.issuer == ""
        assert acc.name == ""
        assert acc.otp_type == OTPType.TOTP
        assert acc.algorithm == Algorithm.SHA1
        assert acc.digits == 6
        assert acc.period == 30
        assert acc.group == "Default"


class TestAegisImport:
    def _backup(self, entries):
        return {"db": {"entries": entries}}

    def test_import_basic_totp_entry(self):
        backup = self._backup(
            [
                {
                    "type": "totp",
                    "issuer": "GitHub",
                    "name": "octocat",
                    "info": {
                        "secret": "JBSWY3DPEHPK3PXP",
                        "algo": 1,
                        "digits": 6,
                        "period": 30,
                    },
                }
            ]
        )
        accounts = import_aegis_backup(backup)
        assert len(accounts) == 1
        acc = accounts[0]
        assert acc.issuer == "GitHub"
        assert acc.name == "octocat"
        assert acc.secret == "JBSWY3DPEHPK3PXP"
        assert acc.otp_type == OTPType.TOTP
        # algo == 1 maps to SHA256 per the importer's mapping.
        assert acc.algorithm == Algorithm.SHA256
        assert acc.is_github is True

    def test_import_hotp_and_algo_mapping(self):
        backup = self._backup(
            [
                {
                    "type": "hotp",
                    "issuer": "Service",
                    "name": "user",
                    "info": {"secret": "ABC", "algo": 0, "counter": 7},
                },
                {
                    "type": "totp",
                    "issuer": "Other",
                    "name": "user2",
                    "info": {"secret": "DEF", "algo": 2},
                },
            ]
        )
        accounts = import_aegis_backup(backup)
        assert accounts[0].otp_type == OTPType.HOTP
        assert accounts[0].algorithm == Algorithm.SHA1
        assert accounts[0].counter == 7
        assert accounts[0].is_github is False
        assert accounts[1].algorithm == Algorithm.SHA512

    def test_import_empty_backup(self):
        assert import_aegis_backup({}) == []
        assert import_aegis_backup(self._backup([])) == []
