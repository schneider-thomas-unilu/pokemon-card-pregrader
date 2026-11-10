import argparse
import json
import logging
import os
import time
from urllib.error import URLError
from urllib.request import urlopen


logger = logging.getLogger("pregrader.health_monitor")


def check_health(url: str, timeout: float) -> None:
    with urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Health endpoint returned HTTP {response.status}")
        body = json.loads(response.read())
    if not isinstance(body, dict) or body.get("status") != "ok":
        raise RuntimeError(f"Unexpected health response: {body!r}")


def monitor(url: str, interval: float, timeout: float) -> None:
    logger.info("Monitoring %s every %s seconds", url, interval)
    while True:
        try:
            check_health(url, timeout)
        except (URLError, TimeoutError, OSError, RuntimeError, json.JSONDecodeError) as error:
            logger.warning("API health check failed: %s (%s)", error, url)
        else:
            logger.info("API health check passed (%s)", url)
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll the PreGrader API health endpoint.")
    parser.add_argument(
        "--url",
        default=os.getenv("HEALTH_CHECK_URL", "http://127.0.0.1:8000/health"),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "20")),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "5")),
    )
    args = parser.parse_args()
    if args.interval <= 0 or args.timeout <= 0:
        parser.error("--interval and --timeout must be positive numbers")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        monitor(args.url, args.interval, args.timeout)
    except KeyboardInterrupt:
        logger.info("Health monitor stopped")


if __name__ == "__main__":
    main()
