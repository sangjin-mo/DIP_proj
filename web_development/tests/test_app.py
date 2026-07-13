import tempfile
import unittest
from pathlib import Path

from app import create_app


class ThermoGuardTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "DATABASE": str(Path(self.temp_dir.name) / "test.db"),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def login(self, username="admin", password="admin1234"):
        self.client.get("/login")
        with self.client.session_transaction() as session:
            token = session["csrf_token"]
        return self.client.post(
            "/login",
            data={"username": username, "password": password, "csrf_token": token},
            follow_redirects=True,
        )

    def test_admin_can_open_dashboard_and_snapshot(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("실시간 통합 모니터링".encode(), response.data)
        snapshot = self.client.get("/api/snapshot")
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual(len(snapshot.get_json()["cameras"]), 1)
        self.assertEqual(len(snapshot.get_json()["cameras"][0]["hotspots"]), 3)

    def test_member_cannot_open_admin_settings(self):
        self.login("member", "member1234")
        response = self.client.get("/settings")
        self.assertEqual(response.status_code, 403)

    def test_invalid_login_is_rejected(self):
        response = self.login("admin", "wrong-password")
        self.assertIn("아이디 또는 비밀번호".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
