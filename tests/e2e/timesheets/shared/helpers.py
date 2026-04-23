"""
Shared UI/navigation helpers.
Used by both Phase 1 and Phase 2.
"""

from __future__ import annotations

import re
from datetime import datetime, date
from typing import Optional

from playwright.sync_api import Page, expect


# ── Payroll type used for pay-period dropdown matching ────────────────────────
PAYROLL_TYPE = "Regular"  # change to "Off Cycle" if needed


# ============================================================================
# DATE HELPERS
# ============================================================================

MONTHS: dict[str, str] = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def _normalize_date(d: date) -> date:
    return date(d.year, d.month, d.day)


def ui_text_to_date_str(month_str: str, day_str: str, year_str: str) -> Optional[str]:
    month = MONTHS.get(month_str)
    if not month:
        return None
    return f"{year_str}-{month}-{day_str.zfill(2)}"


def _fmt_for_pay_period(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.day:02d} {dt.strftime('%b')} {dt.year}"


# ============================================================================
# TIMESHEET WEEK NAVIGATION
# ============================================================================

def get_current_displayed_week_start_str(page: Page) -> Optional[str]:
    try:
        range_display = page.get_by_test_id("timesheet-date-range-display")
        texts = range_display.locator("p").all_text_contents()
        print(f"   [DEBUG] Raw UI date texts: {texts}")

        year = re.sub(r"\D", "", (texts[2] or "").strip())
        start_match = re.match(r"^([A-Za-z]+)\s+(\d+)", (texts[0] or "").strip())

        if not start_match or not year:
            return None

        return ui_text_to_date_str(start_match.group(1), start_match.group(2), year)
    except Exception:
        return None


def is_target_date_in_displayed_week(page: Page, target_date_str: str) -> bool:
    try:
        range_display = page.get_by_test_id("timesheet-date-range-display")
        texts = range_display.locator("p").all_text_contents()

        year = re.sub(r"\D", "", (texts[2] or "").strip())
        start_match = re.match(r"^([A-Za-z]+)\s+(\d+)", (texts[0] or "").strip())
        end_match   = re.match(r"^([A-Za-z]+)\s+(\d+)", (texts[1] or "").strip())

        if not start_match or not end_match or not year:
            return False

        week_start = ui_text_to_date_str(start_match.group(1), start_match.group(2), year)
        week_end   = ui_text_to_date_str(end_match.group(1),   end_match.group(2),   year)

        if not week_start or not week_end:
            return False

        print(f"   [DEBUG] Displayed week: {week_start} to {week_end} | target: {target_date_str}")
        return week_start <= target_date_str <= week_end
    except Exception:
        return False


def navigate_to_week(page: Page, target_date_str: str) -> None:
    print(f"   [INFO] Navigating to week containing: {target_date_str}")

    for _ in range(52):
        if is_target_date_in_displayed_week(page, target_date_str):
            print("   [INFO] Correct week is already displayed")
            return

        current_week_start_str = get_current_displayed_week_start_str(page)
        if not current_week_start_str:
            print("   [WARN] Could not parse displayed week — skipping navigation")
            return

        if target_date_str > current_week_start_str:
            page.get_by_test_id("timesheet-date-next-button").click()
            print(f"   [INFO] Clicked Next (current: {current_week_start_str})")
        else:
            page.get_by_test_id("timesheet-date-prev-button").click()
            print(f"   [INFO] Clicked Prev (current: {current_week_start_str})")

        page.wait_for_timeout(800)

    print("   [WARN] Max navigation iterations reached — proceeding anyway")


# ============================================================================
# PAYROLL OVERVIEW — PAY PERIOD SELECTION
# ============================================================================

def select_pay_period_in_overview(
    page: Page,
    start_date_str: str,
    end_date_str: str,
    pay_type: str = PAYROLL_TYPE,
) -> Optional[tuple[str, str]]:
    """
    Select the pay period on the Payroll Overview page.
    Returns (period_start, period_end) as YYYY-MM-DD strings, or None.
    """
    target_date = _normalize_date(datetime.strptime(start_date_str, "%Y-%m-%d").date())
    suffix = f"({pay_type})"
    print(f"   [INFO] Looking for {pay_type} period containing: {target_date}")

    dropdown_btn = page.locator('button[data-testid="payroll-detail-pay-period-dropdown"]')
    expect(dropdown_btn).to_be_visible(timeout=30_000)

    # Check if the currently shown period already matches
    current_text = dropdown_btn.inner_text()
    if suffix in current_text:
        match = re.search(r"(\d{1,2} \w{3} \d{4}) - (\d{1,2} \w{3} \d{4})", current_text)
        if match:
            try:
                s = _normalize_date(datetime.strptime(match.group(1), "%d %b %Y").date())
                e = _normalize_date(datetime.strptime(match.group(2), "%d %b %Y").date())
                if s <= target_date <= e:
                    print(f"   [INFO] Pay period already selected: {current_text.strip()}")
                    return (s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"))
            except ValueError:
                pass

    dropdown_btn.click()
    print("   [INFO] Opened pay period dropdown")
    page.wait_for_timeout(1000)

    menu_items = page.get_by_role("menuitem")
    view_more  = page.get_by_role("menuitem", name="View More")

    for attempt in range(20):
        count = menu_items.count()
        print(f"   [INFO] Scanning {count} menu item(s) (attempt {attempt + 1})")

        for i in range(count):
            item = menu_items.nth(i)
            text = item.text_content() or ""

            if suffix not in text:
                continue

            print(f"   [DEBUG] Checking: {text.strip()}")
            match = re.search(r"(\d{1,2} \w{3} \d{4}) - (\d{1,2} \w{3} \d{4})", text)
            if not match:
                continue

            try:
                s = _normalize_date(datetime.strptime(match.group(1), "%d %b %Y").date())
                e = _normalize_date(datetime.strptime(match.group(2), "%d %b %Y").date())
            except ValueError:
                continue

            if s <= target_date <= e:
                item.click()
                print(f"   [INFO] Selected pay period: {text.strip()}")
                return (s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"))

        view_more_count = view_more.count()
        if view_more_count > 0 and view_more.first.is_visible():
            count_before = count
            view_more.first.click()
            print("   [INFO] Clicked View More")

            wait_attempts = 0
            while menu_items.count() <= count_before and wait_attempts < 20:
                page.wait_for_timeout(500)
                wait_attempts += 1

            print(f"   [INFO] Items: {count_before} to {menu_items.count()}")
            continue

        break

    raise RuntimeError(
        f"No {pay_type} period found in dropdown containing date: {target_date}"
    )
