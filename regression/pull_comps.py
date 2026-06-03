import argparse
import logging
import os
import re
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/sale/snapshot"
DEFAULT_OUTPUT_DIR = "comps_output"
DEFAULT_START_DATE = "2023-06-01"
DEFAULT_END_DATE = "2026-05-31"
DEFAULT_PAGE_SIZE = 100
MAX_RECORDS_PER_FIPS = 1000
REQUEST_DELAY_SECONDS = 0.5
MAX_504_RETRIES = 3
RETRY_DELAY_SECONDS = 2
DEFAULT_AREA_DEFINITIONS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1oX4dQc-WzzP7KoegnXTpaaVwHBuapa9MklQDQPPd3yQ/edit?usp=sharing"
)
GOOGLE_SHEETS_ID_PATTERN = re.compile(
    r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)"
)

# MVP launch market only. Restore ALL_TARGET_METROS when ready for full multi-market pull.
ALL_TARGET_METROS = [
    "Greenville, SC",
    "Washington, DC",
    "Atlanta, GA",
    "Dallas, TX",
    "Houston, TX",
    "Phoenix, AZ",
    "Charlotte, NC",
    "Tampa, FL",
    "Denver, CO",
    "Nashville, TN",
    "Raleigh, NC",
    "Austin, TX",
]

TARGET_METROS = [
    "Greenville, SC",
]

VALIDATION_SAMPLE_SIZE = 10
VALIDATION_OUTPUT = "validation_sample.csv"

METRO_TITLE_MAP = {
    "Phoenix": "Phoenix-Mesa-Chandler, AZ",
    "Raleigh": "Raleigh-Cary, NC",
    "Greenville, SC": "Greenville-Anderson-Greer, SC",
    "Washington, DC": "Washington-Arlington-Alexandria, DC-VA-MD-WV",
    "Atlanta, GA": "Atlanta-Sandy Springs-Roswell, GA",
    "Dallas, TX": "Dallas-Fort Worth-Arlington, TX",
    "Houston, TX": "Houston-Pasadena-The Woodlands, TX",
    "Phoenix, AZ": "Phoenix-Mesa-Chandler, AZ",
    "Charlotte, NC": "Charlotte-Concord-Gastonia, NC-SC",
    "Tampa, FL": "Tampa-St. Petersburg-Clearwater, FL",
    "Denver, CO": "Denver-Aurora-Centennial, CO",
    "Nashville, TN": "Nashville-Davidson--Murfreesboro--Franklin, TN",
    "Raleigh, NC": "Raleigh-Cary, NC",
    "Austin, TX": "Austin-Round Rock-San Marcos, TX",
}


def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "pull_comps.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def get_api_key() -> str:
    api_key = os.getenv("ATTOM_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ATTOM_API_KEY is not set. Add it to your environment or a .env file."
        )
    return api_key


def sanitize_filename(value: str, max_length: int = 80) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*,]', "", value)
    cleaned = cleaned.replace(" ", "_").strip("_")
    return cleaned[:max_length] or "metro"


def metro_output_path(output_dir: Path, bls_area_title: str) -> Path:
    return output_dir / f"{sanitize_filename(bls_area_title)}.csv"


def fetch_page_with_retries(
    fips: str,
    page: int,
    start_date: str,
    end_date: str,
    api_key: str,
    page_size: int,
) -> tuple[requests.Response | None, str | None]:
    for attempt in range(1, MAX_504_RETRIES + 1):
        try:
            response = requests.get(
                API_URL,
                headers={"apikey": api_key, "accept": "application/json"},
                params={
                    "fips": fips,
                    "startsalesearchdate": start_date,
                    "endsalesearchdate": end_date,
                    "pagesize": page_size,
                    "page": page,
                },
                timeout=60,
            )
            if response.status_code == 504:
                if attempt < MAX_504_RETRIES:
                    logging.warning(
                        "FIPS %s page %s returned 504, retry %s/%s",
                        fips,
                        page,
                        attempt,
                        MAX_504_RETRIES,
                    )
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue
                return response, f"HTTP 504 after {MAX_504_RETRIES} retries"

            return response, None
        except requests.RequestException as exc:
            if attempt < MAX_504_RETRIES:
                logging.warning(
                    "FIPS %s page %s request failed (%s), retry %s/%s",
                    fips,
                    page,
                    exc,
                    attempt,
                    MAX_504_RETRIES,
                )
                time.sleep(RETRY_DELAY_SECONDS * attempt)
                continue
            return None, str(exc)

    return None, f"HTTP 504 after {MAX_504_RETRIES} retries"


def pull_comps_by_fips(
    fips: str,
    start_date: str,
    end_date: str,
    api_key: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_records: int = MAX_RECORDS_PER_FIPS,
) -> tuple[list[dict], str | None]:
    all_results: list[dict] = []
    page = 1
    error: str | None = None

    while True:
        response, request_error = fetch_page_with_retries(
            fips,
            page,
            start_date,
            end_date,
            api_key,
            page_size,
        )
        if request_error:
            error = request_error
            logging.error("FIPS %s page %s failed: %s", fips, page, error)
            break

        if response is None:
            error = "No response received"
            logging.error("FIPS %s page %s failed: %s", fips, page, error)
            break

        try:
            data = response.json()
        except ValueError:
            error = f"HTTP {response.status_code}: invalid JSON response"
            logging.error("FIPS %s page %s failed: %s", fips, page, error)
            break

        status = data.get("status", {})
        msg = status.get("msg", "")

        if response.status_code != 200:
            error = f"HTTP {response.status_code}: {msg}"
            logging.error("FIPS %s page %s failed: %s", fips, page, error)
            break

        properties = data.get("property", [])
        if not properties:
            break

        remaining = max_records - len(all_results)
        all_results.extend(properties[:remaining])
        total = status.get("total", 0)
        target = min(total, max_records)
        logging.info(
            "FIPS %s: page %s, pulled %s/%s",
            fips,
            page,
            len(all_results),
            target,
        )

        if len(all_results) >= max_records:
            break

        if len(all_results) >= total:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_results, error


def first_present(*values):
    for value in values:
        if value is not None and value != "":
            return value
    return None


def flatten_property(property_record: dict) -> dict:
    sale = property_record.get("sale", {}) or {}
    amount = sale.get("amount", {}) or {}

    return {
        "attom_id": property_record.get("identifier", {}).get("attomId"),
        "fips": property_record.get("identifier", {}).get("fips"),
        "apn": property_record.get("identifier", {}).get("apn"),
        "address": property_record.get("address", {}).get("oneLine"),
        "postal1": property_record.get("address", {}).get("postal1"),
        "state": property_record.get("address", {}).get("countrySubd"),
        "latitude": property_record.get("location", {}).get("latitude"),
        "longitude": property_record.get("location", {}).get("longitude"),
        "property_type": property_record.get("summary", {}).get("proptype"),
        "year_built": property_record.get("summary", {}).get("yearbuilt"),
        "beds": property_record.get("building", {}).get("rooms", {}).get("beds"),
        "baths": property_record.get("building", {}).get("rooms", {}).get("bathstotal"),
        "sqft": property_record.get("building", {}).get("size", {}).get("universalsize"),
        "lot_size": property_record.get("lot", {}).get("lotSize1"),
        "sale_amount": amount.get("saleamt"),
        "sale_date": first_present(
            sale.get("saleTransDate"),
            sale.get("salesearchdate"),
            amount.get("salerecdate"),
        ),
        "sale_type": amount.get("saletranstype"),
        "price_per_sqft": sale.get("calculation", {}).get("pricepersizeunit"),
    }


def build_county_fips(state_fips: str | int, county_code: str | int) -> str:
    return f"{str(state_fips).zfill(2)}{str(county_code).zfill(3)}"


def is_google_sheets_source(source: str) -> bool:
    return bool(GOOGLE_SHEETS_ID_PATTERN.search(source))


def google_sheets_csv_url(source: str) -> str:
    match = GOOGLE_SHEETS_ID_PATTERN.search(source)
    if not match:
        raise ValueError(f"Could not parse Google Sheets URL: {source}")

    sheet_id = match.group(1)
    query = parse_qs(urlparse(source).query)
    gid = query.get("gid", [None])[0]
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    )
    if gid:
        url += f"&gid={gid}"
    return url


def load_area_definitions(source: str) -> pd.DataFrame:
    if is_google_sheets_source(source):
        csv_url = google_sheets_csv_url(source)
        logging.info("Fetching area definitions from Google Sheets")
        response = requests.get(csv_url, timeout=60)
        response.raise_for_status()
        areas = pd.read_csv(StringIO(response.text), dtype=str)
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Area definitions file not found: {path}")

        if path.suffix.lower() in {".xlsx", ".xls"}:
            areas = pd.read_excel(path, dtype=str)
        else:
            areas = pd.read_csv(path, dtype=str)

    areas.columns = areas.columns.str.strip()
    return areas


def default_area_definitions_source() -> str:
    return (
        os.getenv("AREA_DEFINITIONS_URL")
        or os.getenv("AREA_DEFINITIONS_PATH")
        or DEFAULT_AREA_DEFINITIONS_URL
    )


def resolve_target_metro_titles(target_metros: list[str]) -> list[str]:
    resolved: list[str] = []
    for metro in target_metros:
        if metro in METRO_TITLE_MAP:
            resolved.append(METRO_TITLE_MAP[metro])
        else:
            resolved.append(metro)
    return resolved


def filter_areas_to_target_metros(
    areas: pd.DataFrame, target_metros: list[str]
) -> pd.DataFrame:
    resolved_titles = resolve_target_metro_titles(target_metros)
    filtered = areas[areas["May 2025 Area Title"].isin(resolved_titles)].copy()

    found_titles = set(filtered["May 2025 Area Title"].unique())
    missing = [title for title in resolved_titles if title not in found_titles]
    if missing:
        raise ValueError(
            "Could not find these target metros in area definitions: "
            + ", ".join(missing)
        )

    logging.info(
        "Targeting %s metros: %s",
        len(resolved_titles),
        ", ".join(resolved_titles),
    )
    return filtered


def load_existing_log(log_path: Path) -> dict[str, dict]:
    if not log_path.exists():
        return {}

    existing = pd.read_csv(log_path)
    if "area_title" not in existing.columns:
        return {}

    return {
        str(row["area_title"]): row.to_dict()
        for _, row in existing.iterrows()
    }


def save_pull_log(log_path: Path, log_rows: list[dict], existing_log: dict[str, dict]) -> None:
    merged = existing_log.copy()
    for row in log_rows:
        merged[str(row["area_title"])] = row
    pd.DataFrame(merged.values()).to_csv(log_path, index=False)


def audit_field_coverage(df: pd.DataFrame, label: str) -> None:
    logging.info("Field coverage audit for %s (%s rows):", label, len(df))
    for column in df.columns:
        populated = df[column].notna().sum()
        if populated == 0 and (df[column].astype(str).str.strip() != "").any():
            populated = (df[column].astype(str).str.strip() != "").sum()
        pct = 100 * populated / len(df) if len(df) else 0
        logging.info("  %s: %s/%s (%.1f%%)", column, populated, len(df), pct)


def run_validation_pull(
    areas: pd.DataFrame,
    output_dir: Path,
    api_key: str,
    start_date: str,
    end_date: str,
    sample_size: int,
) -> Path:
    filtered = filter_areas_to_target_metros(areas, TARGET_METROS)
    county_row = (
        filtered.drop_duplicates(subset=["County Code", "FIPS Code"]).iloc[0]
    )
    county_fips = build_county_fips(
        county_row["FIPS Code"],
        county_row["County Code"],
    )
    bls_area_title = county_row["May 2025 Area Title"]
    area_code = county_row["May 2025 Area Code"]

    logging.info(
        "Validation pull: 1 county (%s), 1 page, up to %s records",
        county_fips,
        sample_size,
    )

    results, error = pull_comps_by_fips(
        county_fips,
        start_date,
        end_date,
        api_key,
        page_size=sample_size,
        max_records=sample_size,
    )
    if error:
        raise RuntimeError(f"Validation pull failed for FIPS {county_fips}: {error}")
    if not results:
        raise RuntimeError(f"Validation pull returned no records for FIPS {county_fips}")

    flat = [flatten_property(record) for record in results]
    df = pd.DataFrame(flat)
    df["area_code"] = area_code
    df["area_title"] = bls_area_title

    output_path = output_dir / VALIDATION_OUTPUT
    df.to_csv(output_path, index=False)
    logging.info("Saved validation sample to %s", output_path)
    audit_field_coverage(df, VALIDATION_OUTPUT)

    sale_dates = df["sale_date"].notna().sum()
    logging.info(
        "sale_date populated: %s/%s (%.1f%%)",
        sale_dates,
        len(df),
        100 * sale_dates / len(df) if len(df) else 0,
    )
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pull ATTOM sold comps by metro using BLS county FIPS definitions."
    )
    parser.add_argument(
        "--area-definitions",
        default=default_area_definitions_source(),
        help=(
            "Local path or Google Sheets URL for BLS area definitions. "
            "Defaults to AREA_DEFINITIONS_URL, then AREA_DEFINITIONS_PATH, "
            "then the project Google Sheet."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("COMPS_OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
        help="Directory for metro CSV files and logs.",
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument(
        "--max-records-per-county",
        type=int,
        default=MAX_RECORDS_PER_FIPS,
        help="Maximum sold comps to pull per county FIPS.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-pull metros even if a CSV already exists.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help=(
            "Pull a tiny sample (one county, one page) to verify export fields "
            "like sale_date without spending full metro quota."
        ),
    )
    parser.add_argument(
        "--validate-size",
        type=int,
        default=VALIDATION_SAMPLE_SIZE,
        help="Number of records to pull in --validate mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    setup_logging(output_dir)
    api_key = get_api_key()

    area_definitions_source = args.area_definitions
    logging.info("Loading area definitions from %s", area_definitions_source)
    areas = load_area_definitions(area_definitions_source)

    required_columns = [
        "May 2025 Area Code",
        "May 2025 Area Title",
        "State Abbreviation",
        "County Code",
        "FIPS Code",
    ]
    missing_columns = [column for column in required_columns if column not in areas.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns in area definitions: {missing_columns}")

    if args.validate:
        run_validation_pull(
            areas,
            output_dir,
            api_key,
            args.start_date,
            args.end_date,
            args.validate_size,
        )
        logging.info("Validation complete. No full metro pull was run.")
        return

    areas = filter_areas_to_target_metros(areas, TARGET_METROS)

    metros = areas.groupby(
        ["May 2025 Area Code", "May 2025 Area Title"],
        sort=False,
    )

    log_path = output_dir / "pull_log.csv"
    existing_log = load_existing_log(log_path)
    log_rows: list[dict] = []

    for (area_code, bls_area_title), group in metros:
        states = ", ".join(sorted(group["State Abbreviation"].unique()))
        output_path = metro_output_path(output_dir, bls_area_title)

        if output_path.exists() and not args.force:
            record_count = len(pd.read_csv(output_path))
            logging.info(
                "Skipping %s - already saved at %s (%s records)",
                bls_area_title,
                output_path,
                record_count,
            )
            log_rows.append(
                {
                    "area_code": area_code,
                    "area_title": bls_area_title,
                    "states": states,
                    "records": record_count,
                    "counties": len(group.drop_duplicates(subset=["County Code", "FIPS Code"])),
                    "status": "skipped",
                    "errors": "",
                    "output_file": str(output_path),
                    "pulled_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            continue

        logging.info("Processing metro: %s (%s)", bls_area_title, states)
        metro_results: list[dict] = []
        county_errors: list[str] = []

        county_rows = group.drop_duplicates(subset=["County Code", "FIPS Code"])
        for _, county_row in county_rows.iterrows():
            county_fips = build_county_fips(
                county_row["FIPS Code"],
                county_row["County Code"],
            )
            results, error = pull_comps_by_fips(
                county_fips,
                args.start_date,
                args.end_date,
                api_key,
                page_size=args.page_size,
                max_records=args.max_records_per_county,
            )
            metro_results.extend(results)
            if error:
                county_errors.append(f"{county_fips}: {error}")
            time.sleep(0.3)

        if metro_results:
            flat = [flatten_property(record) for record in metro_results]
            df = pd.DataFrame(flat)
            df = df.drop_duplicates(subset=["attom_id"], keep="first")
            df["area_code"] = area_code
            df["area_title"] = bls_area_title

            df.to_csv(output_path, index=False)

            status = "success_with_errors" if county_errors else "success"
            logging.info("Saved %s records to %s", len(df), output_path)
            if county_errors:
                logging.warning(
                    "Metro %s completed with county errors: %s",
                    bls_area_title,
                    "; ".join(county_errors),
                )

            log_rows.append(
                {
                    "area_code": area_code,
                    "area_title": bls_area_title,
                    "states": states,
                    "records": len(df),
                    "counties": len(county_rows),
                    "status": status,
                    "errors": "; ".join(county_errors),
                    "output_file": str(output_path),
                    "pulled_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
        else:
            status = "failed" if county_errors else "empty"
            logging.warning("No results for %s (%s)", bls_area_title, states)
            if county_errors:
                logging.error(
                    "Metro %s failed for all counties: %s",
                    bls_area_title,
                    "; ".join(county_errors),
                )

            log_rows.append(
                {
                    "area_code": area_code,
                    "area_title": bls_area_title,
                    "states": states,
                    "records": 0,
                    "counties": len(county_rows),
                    "status": status,
                    "errors": "; ".join(county_errors),
                    "output_file": "",
                    "pulled_at": datetime.now().isoformat(timespec="seconds"),
                }
            )

    save_pull_log(log_path, log_rows, existing_log)
    logging.info("Done. Summary log saved to %s", log_path)


if __name__ == "__main__":
    main()
