"""
NavigationHelper — page-navigation utilities.
Mirrors: utils/helpers/Navigation.helper.ts
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


class NavigationHelper:
    def __init__(self, page: Page) -> None:
        self._page = page

    # ------------------------------------------------------------------ #
    # REPORTS
    # ------------------------------------------------------------------ #

    def open_reports_menu(self) -> None:
        reports_menu = self._page.get_by_test_id("nav-reports-menu")

        if not reports_menu.count():
            reports_menu = self._page.get_by_test_id("nav-reports/timesheet-menu")

        if not reports_menu.is_visible():
            raise RuntimeError("❌ Reports menu option is not found")

        reports_menu.click()
        print("✔ Reports menu opened")

    def go_to_payroll_reports(self) -> None:
        print("Navigating → Reports → Payroll Reports")
        self.open_reports_menu()
        payroll_reports = self._page.get_by_test_id("nav-reports-payroll")
        if not payroll_reports.is_visible():
            raise RuntimeError("❌ Payroll Reports menu option is not available for this user")
        payroll_reports.click()
        self._wait_for_page("Payroll Reports")

    def go_to_reports(self) -> None:
        print("Navigating → Reports")
        self.open_reports_menu()
        self._wait_for_page("Reports")

    def go_to_timesheet_reports(self) -> None:
        print("Navigating → Reports → Timesheet Reports")
        self.open_reports_menu()
        payroll_reports = self._page.get_by_test_id("nav-reports-timesheet")
        if not payroll_reports.is_visible():
            raise RuntimeError("❌ Timesheet Reports menu option is not available for this user")
        payroll_reports.click()
        self._wait_for_page("Reports")

    # ------------------------------------------------------------------ #
    # TIMESHEET
    # ------------------------------------------------------------------ #

    def open_holiday_menu(self) -> None:
        time_menu = self._page.get_by_test_id("nav-timesheet-menu")

        if time_menu.is_visible():
            time_menu.click()
            print("✔ Time menu opened")

            holiday_menu = self._page.get_by_test_id("nav-timesheet-holiday")
            if not holiday_menu.is_visible():
                raise RuntimeError("❌ Holiday menu option is not found")
            holiday_menu.click()
            print("✔ Holiday option clicked")
        else:
            raise RuntimeError("❌ Time menu option is not found")

    def open_timesheets_page(self) -> None:
        time_menu = self._page.get_by_test_id("nav-timesheet-menu")

        if time_menu.is_visible():
            time_menu.click()
            print("✔ Time menu opened")

            timesheet_menu = self._page.get_by_test_id("nav-timesheet-weekly")
            if not timesheet_menu.is_visible():
                raise RuntimeError("❌ Timesheet menu option is not found")
            timesheet_menu.click()
            print("✔ Timesheet option clicked")
        else:
            raise RuntimeError("❌ Time menu option is not found")

    def go_to_holiday_config(self) -> None:
        print("Navigating → Time → Holiday Config")
        self.open_holiday_menu()
        self._wait_for_page("Holiday Configuration")

    def go_to_timesheet_page(self) -> None:
        print("Navigating → Time → Timesheets")
        self.open_timesheets_page()
        self._wait_for_page("Timesheets")

    def open_timesheet_overview_page(self) -> None:
        time_menu = self._page.get_by_test_id("nav-timesheet-menu")

        if time_menu.is_visible():
            time_menu.click()
            print("✔ Time menu opened")

            timesheet_overview_menu = self._page.get_by_test_id("nav-timesheet-overview")
            if not timesheet_overview_menu.is_visible():
                raise RuntimeError("❌ Timesheet Overview menu option is not found")
            timesheet_overview_menu.click()
            print("✔ Timesheet Overview option clicked")
        else:
            raise RuntimeError("❌ Time menu option is not found")

    def go_to_timesheet_overview_page(self) -> None:
        print("Navigating → Time → Timesheet Overview")
        self.open_timesheet_overview_page()
        self._wait_for_page("Timesheet Overview")

    # ------------------------------------------------------------------ #
    # SETTINGS ICON
    # ------------------------------------------------------------------ #

    def open_settings_menu(self) -> None:
        self._page.get_by_test_id("settings-button").click()
        print("✔ Settings menu opened")

    def go_to_company_settings(self) -> None:
        print("Navigating → Settings → Company Settings")
        self.open_settings_menu()
        self._page.get_by_test_id("company-settings-menu-item").click()
        self._wait_for_page("Settings")

    # ------------------------------------------------------------------ #
    # RESOURCES
    # ------------------------------------------------------------------ #

    def open_resource_menu(self) -> None:
        self._page.get_by_test_id("nav-resources-menu").click()
        print("✔ Resources menu opened")

    def go_to_resources(self) -> None:
        print("Navigating → Resources → Users")
        self.open_resource_menu()
        self._page.get_by_test_id("nav-resources-users").click()
        self._wait_for_page("Users")

    # ------------------------------------------------------------------ #
    # PROJECT / SCHEDULER
    # ------------------------------------------------------------------ #

    def open_scheduler_menu(self) -> None:
        expect(self._page.get_by_test_id("nav-scheduler-menu")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("nav-scheduler-menu").click()
        print("✔ Scheduler menu opened")

    def go_to_projects_session(self) -> None:
        print("Navigating → Scheduler → Project")
        self.open_scheduler_menu()
        expect(self._page.get_by_test_id("nav-scheduler-projects")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("nav-scheduler-projects").click()
        print('✔ Clicked on "Projects" option')

        expect(self._page.get_by_test_id("page_header_title")).to_be_visible(timeout=15_000)
        print('✔ "Projects" header visible')

    # ------------------------------------------------------------------ #
    # PAYROLL / GENERAL
    # ------------------------------------------------------------------ #

    def open_payroll_menu(self) -> None:
        expect(self._page.get_by_test_id("payroll-sidebar-button")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("payroll-sidebar-button").click()
        print("✔ Payroll menu opened")

    def go_to_general_settings(self) -> None:
        print("Navigating → Settings → Company Settings → Payroll → General")
        self.open_payroll_menu()
        expect(self._page.get_by_test_id("sidebar-general-nav")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("sidebar-general-nav").click()
        print("✔ Clicked on general option")

    # ------------------------------------------------------------------ #
    # PAYROLL / UNIONS
    # ------------------------------------------------------------------ #

    def go_to_unions_settings(self) -> None:
        print("Navigating → Settings → Company Settings → Payroll → Unions")
        expect(self._page.get_by_test_id("sidebar-unions-nav")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("sidebar-unions-nav").click()
        print("✔ Clicked on unions option")

    # ------------------------------------------------------------------ #
    # PAYROLL / PREVAILING WAGES
    # ------------------------------------------------------------------ #

    def go_to_pw_settings(self) -> None:
        print("Navigating → Settings → Company Settings → Payroll → Prevailing Wages")
        self.open_payroll_menu()
        expect(self._page.get_by_test_id("sidebar-prevailing-wages-nav")).to_be_visible(timeout=10_000)
        self._page.get_by_test_id("sidebar-prevailing-wages-nav").click()
        print("✔ Clicked on Prevailing Wages")

    # ------------------------------------------------------------------ #
    # COMMON
    # ------------------------------------------------------------------ #

    def _wait_for_page(self, heading_name: str) -> None:
        # 1️⃣ Try test id first
        header_by_test_id = (
            self._page.get_by_test_id("page_header_title")
            .filter(has_text=heading_name)
        )

        if header_by_test_id.count() > 0:
            expect(header_by_test_id).to_be_visible()
        else:
            # 2️⃣ Fallback to text-based header
            header_by_text = self._page.get_by_text(heading_name, exact=True)
            expect(header_by_text).to_be_visible()

        print(f'✔ "{heading_name}" header visible')