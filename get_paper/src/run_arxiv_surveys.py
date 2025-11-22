from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from agents_papers.sources.arxiv_surveys import fetch_arxiv_surveys_for_year, write_year_file


def configure_logging() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)s %(name)s - %(message)s",
	)


def _current_year() -> int:
	return datetime.now(tz=timezone.utc).year


def main() -> None:
	parser = argparse.ArgumentParser(description="Fetch arXiv survey papers by year (2020+)")
	parser.add_argument("--start-year", type=int, default=2020, help="Start year (inclusive), default 2020")
	parser.add_argument("--end-year", type=int, default=None, help="End year (inclusive), default current year")
	# 统一到 get_paper/data/raw/arxiv_surveys
	default_base = str(Path(__file__).resolve().parents[1] / "data" / "raw" / "arxiv_surveys")
	parser.add_argument("--output-base", type=str, default=default_base, help="Base output dir")
	args = parser.parse_args()

	start_year = max(2020, int(args.start_year))
	end_year = int(args.end_year) if args.end_year else _current_year()
	if end_year < start_year:
		raise ValueError("end-year must be >= start-year")

	configure_logging()
	logger = logging.getLogger("run_arxiv_surveys")
	output_base = Path(args.output_base)

	for year in range(start_year, end_year + 1):
		logger.info("Fetching surveys for year=%s", year)
		items = fetch_arxiv_surveys_for_year(year=year)
		logger.info("Fetched items: %d for year=%s", len(items), year)
		path = write_year_file(output_base, year, items)
		logger.info("Wrote %s", str(path))


if __name__ == "__main__":
	main()


