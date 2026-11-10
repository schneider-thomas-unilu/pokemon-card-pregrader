import unittest
from unittest.mock import patch

from app.backend.main.health_monitor import check_health


class HealthMonitorTests(unittest.TestCase):
    @patch("app.backend.main.health_monitor.urlopen")
    def test_accepts_healthy_response(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'{"status":"ok"}'

        check_health("http://localhost/health", 2)

        urlopen.assert_called_once_with("http://localhost/health", timeout=2)

    @patch("app.backend.main.health_monitor.urlopen")
    def test_rejects_unhealthy_response(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'{"status":"degraded"}'

        with self.assertRaisesRegex(RuntimeError, "Unexpected health response"):
            check_health("http://localhost/health", 2)


if __name__ == "__main__":
    unittest.main()
