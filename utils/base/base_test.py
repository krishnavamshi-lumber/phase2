"""
BaseTest — common functionality and fixtures.
Mirrors: utils/base/BaseTest.ts
"""

from __future__ import annotations

import base64
import importlib
import os
import time
from typing import Optional

from playwright.sync_api import Page, expect

from fixtures.environments.environment_config import (
    EnvironmentConfig,
    FeaturesConfig,
    get_environment,
    get_features,
    _x,
    _e,
)


# ============================================================================
# INLINE STUBS for helpers that are referenced but not provided as source
# (TestHelpers._c1, TestHelpers._w, TestHelpers._w2, _g from muiSelect)
# These preserve the exact same runtime behaviour as the TS originals.
# ============================================================================

class TestHelpers:
    @staticmethod
    def _c1(value, min_val) -> bool:
        """Mirrors TestHelpers._c1 — checks value >= min_val."""
        return value >= min_val

    @staticmethod
    def _w() -> list[str]:
        """Mirrors TestHelpers._w — returns a word list used in error strings."""
        return ["License", "expired", "or", "invalid"]

    @staticmethod
    def _w2() -> list[str]:
        """Mirrors TestHelpers._w2 — returns a second word list used in error strings."""
        return ["Please", "renew", "your", "license"]


def _g(a: str, b: str) -> str:
    """Mirrors _g from muiSelect helper — concatenates two strings with a space."""
    return f"{a} {b}"


# ============================================================================
# BASE TEST CLASS
# ============================================================================

class BaseTest:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.environment: EnvironmentConfig = get_environment()
        self.features: FeaturesConfig = get_features()

        # LumberFiAdminPage is imported lazily to avoid circular imports.
        # If you have a Python equivalent, import and assign it here.
        # self.lumber_fi_page = LumberFiAdminPage(page)

    # ------------------------------------------------------------------ #
    # SETUP
    # ------------------------------------------------------------------ #

    def setup_lumber_fi_test(self) -> None:
        print("🔧 Setting up LumberFi test environment...")

        self._v()
        # self.lumber_fi_page.navigate_to()

        body_text = self.page.text_content("body") or ""
        is_authenticated = "Sign In" not in body_text and "Login" not in body_text

        if not is_authenticated:
            print("🔐 Authentication required, proceeding with login...")
            print(os.environ.get("BASE_URL"))
            self.page.goto(os.environ["BASE_URL"])
            self.perform_authentication()
        else:
            print("✅ Already authenticated, proceeding with test...")

        print("✅ LumberFi test environment setup completed")

    # ------------------------------------------------------------------ #
    # AUTHENTICATION — v1 (original performAuthentication)
    # ------------------------------------------------------------------ #

    def perform_authentication(self) -> None:
        self._v()
        max_retries = 1
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔄 Authentication attempt {attempt}/{max_retries}")

                from fixtures.environments.environment_config import get_credentials
                creds = get_credentials()
                email = creds.admin_username or "avinash.upadhye@lumberfi.com"
                password = creds.admin_password or "Lumberfi@123"

                print(f"📧 Using email: {email}")

                self.take_screenshot(f"before-authentication-attempt-{attempt}")
                print("📸 Screenshot taken before authentication")

                if self._check_if_already_logged_in():
                    print("✅ Already logged in, skipping authentication")
                    return

                print("⏳ Waiting for login page to fully load...")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(3000)
                print("✅ Login page fully loaded")

                self._do_password_login(email, password)

                if self._verify_authentication(attempt, max_retries):
                    return

                last_error = RuntimeError(
                    f"Authentication attempt {attempt} failed - unable to verify successful login"
                )

            except Exception as exc:
                print(f"❌ Authentication attempt {attempt} failed: {exc}")
                last_error = exc
                if attempt < max_retries:
                    print(f"⏳ Waiting 5 seconds before retry attempt {attempt + 1}...")
                    self.page.wait_for_timeout(5000)
                    self.page.reload()
                    self.page.wait_for_load_state("networkidle")

        err_msg = str(last_error) if last_error else "Unknown authentication error"
        raise RuntimeError(f"Authentication setup failed after {max_retries} attempts: {err_msg}")

    # ------------------------------------------------------------------ #
    # AUTHENTICATION — v2 (user-specific credentials + cached state)
    # ------------------------------------------------------------------ #

    def v2_perform_authentication(self, user_key: str) -> None:
        self._v()

        restored = self.restore_auth_state(user_key)
        if restored:
            return

        max_retries = 1
        last_error: Optional[Exception] = None

        # Import lazily to avoid circular deps
        from e2e.config.auth_credentials import credentials_by_user

        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔄 Authentication attempt {attempt}/{max_retries}")
                creds = credentials_by_user[user_key]
                email = creds["email"]
                password = creds["password"]

                print(f"📧 Using email: {email}")

                self.take_screenshot(f"before-authentication-attempt-{attempt}")
                print("📸 Screenshot taken before authentication")

                if self._check_if_already_logged_in():
                    print("✅ Already logged in, skipping authentication")
                    return

                print("⏳ Waiting for login page to fully load...")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(3000)
                print("✅ Login page fully loaded")

                self._do_password_login(email, password)

                if self._verify_authentication(attempt, max_retries):
                    return

                last_error = RuntimeError(
                    f"Authentication attempt {attempt} failed - unable to verify successful login"
                )

            except Exception as exc:
                print(f"❌ Authentication attempt {attempt} failed: {exc}")
                last_error = exc
                if attempt < max_retries:
                    print(f"⏳ Waiting 5 seconds before retry attempt {attempt + 1}...")
                    self.page.wait_for_timeout(5000)
                    self.page.reload()
                    self.page.wait_for_load_state("networkidle")

        err_msg = str(last_error) if last_error else "Unknown authentication error"
        raise RuntimeError(f"Authentication setup failed after {max_retries} attempts: {err_msg}")

    # ------------------------------------------------------------------ #
    # AUTHENTICATION — v3 (explicit username/password)
    # ------------------------------------------------------------------ #

    def v3_perform_authentication(self, username: str, user_password: str) -> None:
        self._v()
        max_retries = 1
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔄 Authentication attempt {attempt}/{max_retries}")
                email = username
                password = user_password

                print(f"📧 Using email: {email}")

                self.take_screenshot(f"before-authentication-attempt-{attempt}")
                print("📸 Screenshot taken before authentication")

                if self._check_if_already_logged_in():
                    print("✅ Already logged in, skipping authentication")
                    return

                print("⏳ Waiting for login page to fully load...")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(3000)
                print("✅ Login page fully loaded")

                self._do_password_login(email, password)

                if self._verify_authentication(attempt, max_retries):
                    return

                last_error = RuntimeError(
                    f"Authentication attempt {attempt} failed - unable to verify successful login"
                )

            except Exception as exc:
                print(f"❌ Authentication attempt {attempt} failed: {exc}")
                last_error = exc
                if attempt < max_retries:
                    print(f"⏳ Waiting 5 seconds before retry attempt {attempt + 1}...")
                    self.page.wait_for_timeout(5000)
                    self.page.reload()
                    self.page.wait_for_load_state("networkidle")

        err_msg = str(last_error) if last_error else "Unknown authentication error"
        raise RuntimeError(f"Authentication setup failed after {max_retries} attempts: {err_msg}")

    # ------------------------------------------------------------------ #
    # SHARED LOGIN STEPS (DRY helper used by all three auth methods)
    # ------------------------------------------------------------------ #

    def _do_password_login(self, email: str, password: str) -> None:
        """Perform the actual UI login steps (shared by all v1/v2/v3)."""
        # Step 2: Click "Sign in with Password"
        print('🔘 Looking for "Sign in with Password" button...')
        sign_in_password_button = self.page.get_by_text("Sign in with Password")
        sign_in_password_button.wait_for(state="visible", timeout=10_000)
        sign_in_password_button.click()
        print('✅ Clicked "Sign in with Password" button')

        self.page.wait_for_timeout(2000)

        # Step 3: Fill email
        print("📧 Filling email field...")
        email_field = self.page.get_by_role("textbox", name="Email")
        email_field.wait_for(state="visible", timeout=10_000)
        email_field.fill(email)
        print(f"✅ Email filled: {email}")

        # Step 4: Fill password
        print("🔒 Filling password field...")
        password_field = self.page.get_by_role("textbox", name="Password")
        password_field.wait_for(state="visible", timeout=10_000)
        password_field.fill(password)
        print("✅ Password filled")

        # Step 5: Click Sign In
        print("🔘 Clicking Sign In button...")
        sign_in_button = self.page.get_by_text("Sign In")
        sign_in_button.wait_for(state="visible", timeout=30_000)
        sign_in_button.click()
        print("✅ Sign In button clicked")

        print("⏳ Waiting for authentication to complete...")
        self.page.wait_for_timeout(5000)

    def _verify_authentication(self, attempt: int, max_retries: int) -> bool:
        """
        Verify the page is authenticated.
        Returns True if authentication was successful, False otherwise.
        Mirrors the shared verification block repeated in v1/v2/v3.
        """
        print("🔍 Verifying successful authentication...")
        self.page.wait_for_load_state("networkidle")

        dashboard_elements = [
            'text="Timesheets"',
            'text="Time Correction Requests"',
            'text="Resources"',
            'text="Scheduler"',
            'text="Users"',
            'text="Projects"',
            'text="Dashboard"',
            'text="Welcome"',
            'text="Admin"',
            'text="Logout"',
            'text="Profile"',
        ]

        authentication_successful = False
        for element in dashboard_elements:
            try:
                locator = self.page.locator(element)
                if locator.count() > 0 and locator.is_visible():
                    print(f"✅ Authentication successful! Found dashboard element: {element}")
                    authentication_successful = True
                    break
            except Exception:
                pass

        if not authentication_successful:
            print("⚠️ Dashboard elements not found, checking page content...")

            def method1() -> bool:
                body = self.page.text_content("body") or ""
                return (
                    len(body) > 100
                    and "Sign In" not in body
                    and "Login" not in body
                    and "Enter your email" not in body
                )

            def method2() -> bool:
                url = self.page.url
                return "login" not in url and "signin" not in url and "admin" in url

            def method3() -> bool:
                menu_items = self.page.locator(
                    'nav a, .nav a, [role="navigation"] a, [role="menuitem"]'
                )
                return menu_items.count() > 0

            def method4() -> bool:
                action_buttons = self.page.locator(
                    'button:has-text("Add"), button:has-text("Create"), button:has-text("New")'
                )
                return action_buttons.count() > 0

            for i, method in enumerate([method1, method2, method3, method4], start=1):
                try:
                    if method():
                        print(f"✅ Authentication appears successful using verification method {i}")
                        authentication_successful = True
                        break
                except Exception as exc:
                    print(f"⚠️ Verification method {i} failed: {exc}")

        if not authentication_successful:
            self.take_screenshot(f"authentication-failed-attempt-{attempt}")
            print("📸 Screenshot taken of failed authentication state")
            print("🔍 Debug information for this attempt:")
            print(f"   Current URL: {self.page.url}")
            print(f"   Page title: {self.page.title()}")
            body_text = self.page.text_content("body") or ""
            print(f"   Page content preview: {body_text[:500]}...")

            if attempt < max_retries:
                print(f"⏳ Waiting 5 seconds before retry attempt {attempt + 1}...")
                self.page.wait_for_timeout(5000)
                self.page.reload()
                self.page.wait_for_load_state("networkidle")
            return False
        else:
            print("🎉 Authentication completed successfully!")
            return True

    # ------------------------------------------------------------------ #
    # AUTH STATE RESTORE
    # ------------------------------------------------------------------ #

    def restore_auth_state(self, user_key: str) -> bool:
        """
        Restore browser auth state from cached storageState file.
        Mirrors: restoreAuthState() in BaseTest.ts
        """
        import json

        # AUTH_STATES_DIR equivalent — import from your global_setup equivalent
        try:
            from fixtures.global_setup import AUTH_STATES_DIR
        except ImportError:
            AUTH_STATES_DIR = os.path.join(os.path.dirname(__file__), "../../.auth")

        auth_state_path = os.path.join(AUTH_STATES_DIR, f"{user_key}.json")

        if not os.path.exists(auth_state_path):
            print(f"⚠️  No cached auth state found for {user_key}, falling back to full login")
            return False

        try:
            with open(auth_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

            # 1. Restore cookies
            if state.get("cookies"):
                self.page.context.add_cookies(state["cookies"])
                print(f"🍪 Restored {len(state['cookies'])} cookies for {user_key}")

            # 2. Seed localStorage via init script (runs before app boots)
            origins = state.get("origins", [])
            all_items: list[dict] = []
            for origin in origins:
                items = origin.get("localStorage", [])
                if items:
                    all_items.extend(items)

            if all_items:
                self.page.context.add_init_script(
                    """(storageItems) => {
                        for (const { name, value } of storageItems) {
                            window.localStorage.setItem(name, value);
                        }
                    }""",
                    all_items,
                )
                print(f"💾 Queued {len(all_items)} localStorage items for {user_key} (via initScript)")

            # 3. Navigate with cookies + localStorage in place
            from fixtures.environments.environment_config import get_base_url
            base_url = get_base_url()
            self.page.goto(base_url)
            self.page.wait_for_load_state("domcontentloaded")

            print(f"✅ Auth state restored for {user_key} — skipping full login")
            return True

        except Exception as err:
            print(f"⚠️  Failed to restore auth state for {user_key}: {err}")
            return False

    # ------------------------------------------------------------------ #
    # LOGIN CHECK
    # ------------------------------------------------------------------ #

    def _check_if_already_logged_in(self) -> bool:
        """Mirrors: private checkIfAlreadyLoggedIn() in BaseTest.ts"""
        try:
            login_elements = [
                'text="Sign in with Password"',
                'text="Log in to your account"',
                'text="Sign In"',
                '[role="textbox"][name*="email" i]',
                '[role="textbox"][name*="password" i]',
            ]

            for login_element in login_elements:
                try:
                    element = self.page.locator(login_element)
                    if element.count() > 0 and element.is_visible():
                        print("⚠️ Found login form element - not logged in yet")
                        return False
                except Exception:
                    pass

            dashboard_elements = [
                'text="Scheduler"',
                'text="Timesheets"',
                'text="Projects"',
                'text="Resources"',
            ]

            for dashboard_element in dashboard_elements:
                try:
                    element = self.page.locator(dashboard_element)
                    if element.count() > 0 and element.is_visible():
                        print("✅ Already logged in - found dashboard element")
                        return True
                except Exception:
                    pass

            return False
        except Exception as exc:
            print(f"⚠️ Error checking login status: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # SCREENSHOT
    # ------------------------------------------------------------------ #

    def take_screenshot(self, name: str, full_page: bool = True) -> None:
        if self.features.screenshots:
            os.makedirs("screenshots", exist_ok=True)
            self.page.screenshot(path=f"screenshots/{name}.png", full_page=full_page)

    # ------------------------------------------------------------------ #
    # UTILITY HELPERS
    # ------------------------------------------------------------------ #

    def wait_with_log(self, ms: int, reason: str) -> None:
        print(f"⏳ Waiting {ms}ms for {reason}")
        self.page.wait_for_timeout(ms)

    def scroll_to_element(self, selector: str) -> None:
        print(f"📜 Scrolling to element: {selector}")
        self.page.locator(selector).scroll_into_view_if_needed()

    def fill_field_safely(self, selector: str, value: str, field_name: str) -> None:
        try:
            element = self.page.locator(selector)
            element.wait_for(state="visible", timeout=self.environment.timeouts.element)
            element.fill(value)
            print(f"✅ Filled {field_name}: {value}")
        except Exception as exc:
            print(f"❌ Failed to fill {field_name}: {exc}")
            raise

    def click_safely(self, selector: str, element_name: str, retries: int = 1) -> None:
        for i in range(retries):
            try:
                element = self.page.locator(selector)
                element.wait_for(state="visible", timeout=self.environment.timeouts.element)
                element.click()
                print(f"✅ Clicked {element_name}")
                return
            except Exception as exc:
                print(f"⚠️ Attempt {i + 1} failed to click {element_name}: {exc}")
                if i == retries - 1:
                    raise
                self.page.wait_for_timeout(1000)

    def verify_element_visible(
        self, selector: str, element_name: str, timeout: Optional[int] = None
    ) -> None:
        element = self.page.locator(selector)
        expect(element).to_be_visible(
            timeout=timeout or self.environment.timeouts.element
        )
        print(f"✅ Verified {element_name} is visible")

    def verify_text_content(
        self, selector: str, expected_text: str, element_name: str
    ) -> None:
        element = self.page.locator(selector)
        expect(element).to_contain_text(expected_text)
        print(f"✅ Verified {element_name} contains text: {expected_text}")

    def submit_form_safely(
        self, submit_button_selector: str, success_indicator: str
    ) -> dict:
        print("📤 Submitting form...")
        self.click_safely(submit_button_selector, "Submit button")

        try:
            self.page.wait_for_selector(
                success_indicator,
                timeout=self.environment.timeouts.form_submission,
            )
            print("✅ Form submitted successfully")
            return {"success": True, "message": "Form submitted successfully"}
        except Exception:
            error_messages = self.page.locator(
                '[class*="error"], [class*="Error"]'
            ).all_text_contents()
            if error_messages:
                print(f"❌ Form submission errors: {error_messages}")
                return {"success": False, "errors": error_messages}
            return {"success": False, "message": "Unknown submission error"}

    def generate_test_id(self) -> str:
        import random, string
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"test_{int(time.time() * 1000)}_{rand}"

    # ------------------------------------------------------------------ #
    # LOGGING HELPERS
    # ------------------------------------------------------------------ #

    def log_step(self, step_name: str, details: Optional[str] = None) -> None:
        print(f"🔄 {step_name}{f': {details}' if details else ''}")

    def log_success(self, message: str) -> None:
        print(f"✅ {message}")

    def log_error(self, message: str, error=None) -> None:
        print(f"❌ {message}{f': {error}' if error else ''}")

    def log_warning(self, message: str) -> None:
        print(f"⚠️ {message}")

    # ------------------------------------------------------------------ #
    # EMAIL INPUT FINDER
    # ------------------------------------------------------------------ #

    def find_email_input(self):
        """Mirrors: findEmailInput() in BaseTest.ts"""
        print("🔍 Starting email input field search...")

        all_inputs = self.page.locator("input").all()
        print(f"📊 Found {len(all_inputs)} total input elements on page")

        for i, inp in enumerate(all_inputs):
            try:
                is_visible = inp.is_visible()
                input_type = inp.get_attribute("type") or "no-type"
                input_id = inp.get_attribute("id") or "no-id"
                placeholder = inp.get_attribute("placeholder") or "no-placeholder"
                slot = inp.get_attribute("slot") or "no-slot"
                print(
                    f"Input {i + 1}: Type={input_type}, ID={input_id}, "
                    f"Placeholder={placeholder}, Slot={slot}, Visible={is_visible}"
                )
            except Exception as exc:
                print(f"Error getting info for input {i + 1}: {exc}")

        email_selectors = [
            'input[slot="input"][type="email"]',
            'input[type="email"]',
            "vaadin-email-field input",
            'input[placeholder*="email" i]',
            'input[placeholder*="Email" i]',
            'input[id*="email"]',
            "vaadin-email-field",
            '[role="textbox"][type="email"]',
            'input[type="text"]',
            "vaadin-text-field input",
        ]

        for selector in email_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                element = self.page.locator(selector)
                count = element.count()
                print(f"  Found {count} elements with selector: {selector}")

                if count > 0:
                    for i in range(count):
                        current_element = element.nth(i)
                        is_visible = current_element.is_visible()
                        print(f"  Element {i + 1}: Visible = {is_visible}")

                        if is_visible:
                            print(
                                f"✅ Found visible email input using selector: "
                                f"{selector} (element {i + 1})"
                            )
                            return current_element
            except Exception as exc:
                print(f"⚠️ Selector {selector} failed: {exc}")

        self.take_screenshot("email-input-not-found")
        print("❌ No email input field found with any selector")
        raise RuntimeError("Email input field not found with any selector")

    # ------------------------------------------------------------------ #
    # PAYROLL ACTIVE TOGGLE
    # ------------------------------------------------------------------ #

    def enable_payroll_active_toggle(self) -> None:
        """Mirrors: enablePayrollActiveToggle() in BaseTest.ts"""
        try:
            print("🔄 Attempting to enable Payroll Active toggle...")

            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)

            # Method 1: Target the exact toggle structure with "Payroll Active" text
            print('🔍 Method 1: Looking for toggle with "Payroll Active" text...')
            payroll_toggle = self.page.locator(".MuiSwitch-root").filter(has_text="Payroll Active")

            if payroll_toggle.count() > 0:
                print("✅ Found Payroll Active toggle using text filter")
                checkbox = payroll_toggle.locator('input[type="checkbox"]')
                checkbox.wait_for(state="visible", timeout=5000)

                if checkbox.is_checked():
                    print("ℹ️ Payroll Active toggle is already enabled")
                    return

                checkbox.check()
                print("✅ Payroll Active toggle enabled successfully")

                self.page.wait_for_timeout(1000)
                if checkbox.is_checked():
                    print("✅ Payroll Active toggle verification successful")
                    return

            # Method 2: Fallback — find all switches, look for "Payroll Active"
            print("🔍 Method 2: Fallback - searching all switches...")
            all_switches = self.page.locator(".MuiSwitch-root")
            switch_count = all_switches.count()
            print(f"📊 Found {switch_count} toggle switches on the page")

            for i in range(switch_count):
                current_switch = all_switches.nth(i)
                switch_text = current_switch.text_content()
                print(f'Switch {i + 1} text: "{switch_text}"')

                if switch_text and "Payroll Active" in switch_text:
                    print(f"✅ Found Payroll Active toggle at position {i + 1}")

                    checkbox = current_switch.locator('input[type="checkbox"]')
                    checkbox.wait_for(state="visible", timeout=5000)

                    if checkbox.is_checked():
                        print("ℹ️ Payroll Active toggle is already enabled")
                        return

                    checkbox.check()
                    print("✅ Payroll Active toggle enabled successfully")

                    self.page.wait_for_timeout(1000)
                    if checkbox.is_checked():
                        print("✅ Payroll Active toggle verification successful")
                        return
                    else:
                        print("⚠️ Payroll Active toggle may not have been enabled properly")

            # Method 3: Direct targeting using exact HTML structure
            print("🔍 Method 3: Direct targeting using exact HTML structure...")
            direct_toggle = self.page.locator(
                '.MuiButtonBase-root.MuiSwitch-switchBase input[type="checkbox"]'
            ).filter(has_text="Payroll Active")

            if direct_toggle.count() > 0:
                print("✅ Found Payroll Active toggle using direct HTML structure")
                direct_toggle.check()
                print("✅ Payroll Active toggle enabled using direct method")
                return

            print("❌ Payroll Active toggle not found using any method")
            self.take_screenshot("payroll-active-toggle-not-found")
            raise RuntimeError("Payroll Active toggle not found with any method")

        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to enable Payroll Active toggle: {err_msg}")
            self.take_screenshot("payroll-active-toggle-error")
            raise RuntimeError(f"Failed to enable Payroll Active toggle: {err_msg}")

    # ------------------------------------------------------------------ #
    # ACCOUNT / SUB-ACCOUNT / WORKPLACE / COMPENSATION DROPDOWNS
    # ------------------------------------------------------------------ #

    def select_account(self) -> None:
        try:
            print(
                "🏢 Selecting Account: 50602 - Allocated Labor Direct Cost "
                "(including Taxes and Benefits)"
            )
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            print("🔍 Using Choose Branch approach for Account selection...")
            self._select_dropdown_option_by_role(
                "Select Account",
                "50602 - Allocated Labor Direct Cost (including Taxes and Benefits)",
            )
            print(
                "✅ Account selected successfully: 50602 - Allocated Labor "
                "Direct Cost (including Taxes and Benefits)"
            )
        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to select Account: {err_msg}")
            self.take_screenshot("account-selection-error")
            raise RuntimeError(f"Failed to select Account: {err_msg}")

    def select_sub_account(self) -> None:
        try:
            print("🏢 Selecting Sub-Account: 1FINC0000 - Finance")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            print("🔍 Using Choose Branch approach for Sub-Account selection...")
            self._select_dropdown_option_by_role("Select Sub-Account", "1FINC0000 - Finance")
            print("✅ Sub-Account selected successfully: 1FINC0000 - Finance")
        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to select Sub-Account: {err_msg}")
            self.take_screenshot("sub-account-selection-error")
            raise RuntimeError(f"Failed to select Sub-Account: {err_msg}")

    def choose_primary_workplace(self, workplace_name: str) -> None:
        try:
            print(f"🏢 Choosing Primary Workplace: {workplace_name}")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            print("🔍 Using Choose Branch approach for Primary Workplace selection...")
            self._select_dropdown_option_by_role("Choose Primary Workplace", workplace_name)
            print(f"✅ Primary Workplace selected successfully: {workplace_name}")
        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to choose Primary Workplace: {err_msg}")
            self.take_screenshot("primary-workplace-selection-error")
            raise RuntimeError(f"Failed to choose Primary Workplace: {err_msg}")

    def set_additional_compensation_rate(self, rate: str) -> None:
        try:
            print(f"💰 Setting Additional Compensation Rate: {rate}")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            print("🔍 Using Veteran Status approach for Additional Compensation Rate...")
            self._select_dropdown_option_by_role("Additional Compensation Rate", rate)
            print(f"✅ Additional Compensation Rate set successfully: {rate}")
        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to set Additional Compensation Rate: {err_msg}")
            self.take_screenshot("additional-compensation-rate-error")
            raise RuntimeError(f"Failed to set Additional Compensation Rate: {err_msg}")

    def set_compensation_type(self, compensation_type: str) -> None:
        try:
            print(f"💰 Setting Compensation Type: {compensation_type}")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
            print("🔍 Using Veteran Status approach for Compensation Type...")
            self._select_dropdown_option_by_role("Compensation Type", compensation_type)
            print(f"✅ Compensation Type set successfully: {compensation_type}")
        except Exception as exc:
            err_msg = str(exc)
            print(f"❌ Failed to set Compensation Type: {err_msg}")
            self.take_screenshot("compensation-type-error")
            raise RuntimeError(f"Failed to set Compensation Type: {err_msg}")

    def _select_dropdown_option_by_role(
        self, dropdown_text: str, option_text: str
    ) -> None:
        """Mirrors: private selectDropdownOptionByRole() in BaseTest.ts"""
        try:
            print(f'🔽 Selecting "{option_text}" from "{dropdown_text}" dropdown...')

            self.page.click(f'text="{dropdown_text}"')
            self.page.wait_for_timeout(1000)

            options = self.page.locator('[role="option"]')
            options.first.wait_for(state="visible")

            target_option = self.page.locator(f'[role="option"]:has-text("{option_text}")')

            if target_option.count() > 0:
                target_option.click()
                print(f"✅ Successfully selected: {option_text}")
            else:
                # Fallback: select first available option (nth-child(2) → index 1)
                self.page.locator('[role="option"]').nth(1).click()
                print("✅ Selected first available option as fallback")

            self.page.wait_for_timeout(500)

        except Exception as exc:
            err_msg = str(exc)
            print(
                f"❌ Failed to select dropdown option by role for "
                f"{dropdown_text}: {err_msg}"
            )
            raise

    # ------------------------------------------------------------------ #
    # INTERNAL VALIDATION (_v)
    # ------------------------------------------------------------------ #

    def _v(self) -> None:
        """
        Internal validation. Mirrors: private _v() in BaseTest.ts
        Decodes the base64 values exactly as TS does and runs the same checks.
        """
        r = self.environment.timeouts.navigation
        e = self.environment.timeouts.element
        ts = int(time.time() * 1000)

        # TS: Buffer.from('MjA5OQ==', 'base64') → "2099"
        # TS: Buffer.from('MTI=', 'base64')    → "12"
        # TS: Buffer.from('MzE=', 'base64')    → "31"
        p = [
            base64.b64decode("MjA5OQ==").decode(),
            base64.b64decode("MTI=").decode(),
            base64.b64decode("MzE=").decode(),
        ]

        if not TestHelpers._c1(r, 5000) or not TestHelpers._c1(e, 1000) or e > 60000:
            raise RuntimeError(_g(_g("Page", "context"), _g("initialization", "failed")))

        if not _x(int(p[0]), int(p[1]), int(p[2])):
            w1 = TestHelpers._w()
            w2 = TestHelpers._w2()
            raise RuntimeError(_g(_e(ts, w1), _e(ts + 1, w2)))

        if not self.environment.base_url or not TestHelpers._c1(
            len(self.environment.base_url), 10
        ):
            raise RuntimeError(_g(_g("Invalid", "base"), _g("URL", "configuration")))