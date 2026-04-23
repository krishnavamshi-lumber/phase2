"""
Phase 2 — Payroll Overview, Preview & Download.

Run 4-5 hours after Phase 1. Downloads PDFs to Google Drive at:
  Payroll_Automation/<Day>/Output/<pay_period>/

Tab 1: Select job, upload Excel (or auto-load from Drive), run Phase 2, download reports.
Tab 2: Browse previously downloaded reports.
Tab 3: View all payroll jobs.
"""

import io
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
EXCEL_PATH    = BASE_DIR / "data-driven-files" / "timesheets" / "timesheet_upload.xlsx"
DOWNLOADS_DIR = BASE_DIR / "data-driven-files" / "timesheets" / "downloads"
GDRIVE_TOKEN  = BASE_DIR / "data-driven-files" / "credentials" / "gdrive_token.json"
GDRIVE_CREDS  = BASE_DIR / "data-driven-files" / "credentials" / "gdrive_credentials.json"

_default_jobs = str(
    BASE_DIR.parent / "Report_downloads" / "data-driven-files" / "jobs" / "jobs.json"
)
JOBS_FILE = Path(os.environ.get("JOBS_FILE_PATH", _default_jobs))

# ── Company definitions (mirrored from Phase 1) ────────────────────────────────
COMPANIES = {
    "Monday":    {"email": "molly.muller@lumberfi.com",  "password": "123456"},
    "Tuesday":   {"email": "neel.madi@lumberfi.com",     "password": "123456"},
    "Wednesday": {"email": "wednesday@lumberfi.com",      "password": "123456"},
    "Thursday":  {"email": "hari.red@lumberfi.com",       "password": "123456"},
    "Friday":    {"email": "testing@gmail.com",          "password": "123456"},
}
GDRIVE_ROOT = "Payroll_Automation"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Payroll Phase 2 — Overview & Reports", page_icon="💰", layout="centered")
st.title("💰 Payroll Phase 2 — Overview & Reports")

tab_run, tab_history, tab_jobs = st.tabs(["Run Phase 2", "Past Downloads", "View Jobs"])


# ════════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def _gdrive_service():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        if not GDRIVE_CREDS.exists():
            return None, "gdrive_credentials.json not found."
        creds = None
        if GDRIVE_TOKEN.exists():
            creds = Credentials.from_authorized_user_file(str(GDRIVE_TOKEN), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            GDRIVE_TOKEN.write_text(creds.to_json())
        if not creds or not creds.valid:
            return None, "Not authenticated. Use sidebar OAuth flow."
        return build("drive", "v3", credentials=creds), None
    except Exception as e:
        return None, str(e)


def _find_folder(svc, name: str, parent: str = None) -> str | None:
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent:
        q += f" and '{parent}' in parents"
    r = svc.files().list(q=q, fields="files(id)").execute()
    f = r.get("files", [])
    return f[0]["id"] if f else None


def _create_folder(svc, name: str, parent: str = None) -> str:
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        meta["parents"] = [parent]
    return svc.files().create(body=meta, fields="id").execute()["id"]


def _get_or_create(svc, name: str, parent: str = None) -> str:
    fid = _find_folder(svc, name, parent)
    return fid if fid else _create_folder(svc, name, parent)


def _find_file(svc, name: str, parent: str) -> str | None:
    q = f"name='{name}' and '{parent}' in parents and trashed=false"
    r = svc.files().list(q=q, fields="files(id)").execute()
    f = r.get("files", [])
    return f[0]["id"] if f else None


def _download_bytes(svc, file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    buf = io.BytesIO()
    dl  = MediaIoBaseDownload(buf, svc.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


def fetch_excel_from_drive(company_day: str) -> tuple[bytes | None, str | None]:
    """Fetch <day>_input.xlsx from Drive. Returns (bytes, error)."""
    svc, err = _gdrive_service()
    if err:
        return None, err
    try:
        root = _find_folder(svc, GDRIVE_ROOT)
        if not root:
            return None, f"'{GDRIVE_ROOT}' not found in Drive."
        day_f = _find_folder(svc, company_day, root)
        if not day_f:
            return None, f"'{company_day}' folder not found."
        inp_f = _find_folder(svc, "Input", day_f)
        if not inp_f:
            return None, f"'Input' folder not found in '{company_day}'."
        fname = f"{company_day.lower()}_input.xlsx"
        fid   = _find_file(svc, fname, inp_f)
        if not fid:
            return None, f"'{fname}' not found in {company_day}/Input/."
        return _download_bytes(svc, fid), None
    except Exception as e:
        return None, f"Drive error: {e}"


def upload_pdfs_to_drive(company_day: str, period_folder: str, pdf_map: dict) -> str | None:
    """Upload files to Payroll_Automation/<Day>/Output/<period_folder>/. Returns error or None."""
    import mimetypes
    svc, err = _gdrive_service()
    if err:
        return err
    try:
        from googleapiclient.http import MediaIoBaseUpload
        root  = _get_or_create(svc, GDRIVE_ROOT)
        day_f = _get_or_create(svc, company_day, root)
        out_f = _get_or_create(svc, "Output", day_f)
        per_f = _get_or_create(svc, period_folder, out_f)
        for name, data in pdf_map.items():
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            existing = _find_file(svc, name, per_f)
            media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime)
            if existing:
                svc.files().update(fileId=existing, media_body=media).execute()
            else:
                svc.files().create(
                    body={"name": name, "parents": [per_f]},
                    media_body=media, fields="id"
                ).execute()
        return None
    except Exception as e:
        return f"Drive upload error: {e}"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("☁️ Google Drive")
    _svc, _err = _gdrive_service()
    if _svc:
        st.success("✅ Connected")
    else:
        st.warning(_err or "Not connected")
        if GDRIVE_CREDS.exists():
            if st.button("🔑 Authenticate (one-time)"):
                try:
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(GDRIVE_CREDS), ["https://www.googleapis.com/auth/drive"]
                    )
                    creds = flow.run_local_server(port=0)
                    GDRIVE_TOKEN.write_text(creds.to_json())
                    st.success("Done! Refresh the page.")
                except Exception as e:
                    st.error(str(e))
        else:
            st.caption("Place `gdrive_credentials.json` in `data-driven-files/credentials/`.")


# ── Helper ─────────────────────────────────────────────────────────────────────
def _load_jobs() -> list[dict]:
    if not JOBS_FILE.exists():
        return []
    try:
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Run Phase 2
# ══════════════════════════════════════════════════════════════════════════════
with tab_run:
    st.markdown(
        "Select a payroll job and company, upload the matching timesheet Excel "
        "(or auto-load from Google Drive), then run Phase 2. "
        "Reports will be saved to Google Drive **and** available for local download."
    )

    for _k, _v in [
        ("p2_running", False), ("p2_logs", ""), ("p2_success", None),
        ("p2_run_folder", None), ("p2_period_folder", None), ("p2_company", None),
        ("p2_gdrive_bytes", None), ("p2_gdrive_name", None), ("p2_gdrive_err", None),
        ("p2_prev_company", None),
    ]:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # ── Step 1: Select Job ─────────────────────────────────────────────────────
    st.subheader("1. Select Payroll Job")
    col_ref, _ = st.columns([1, 5])
    with col_ref:
        if st.button("Refresh Jobs"):
            st.rerun()

    jobs = _load_jobs()
    if not jobs:
        st.warning(f"No jobs found. Make sure Phase 1 has run.\n\n`{JOBS_FILE}`")
        st.stop()

    job_options: dict[str, dict] = {}
    for i, job in enumerate(jobs, 1):
        period = f"{job.get('pay_period_start','?')} to {job.get('pay_period_end','?')}"
        label  = f"#{i}  |  {job.get('username','?')}  |  {period}  |  [{job.get('status','?')}]"
        job_options[label] = job

    sel_label   = st.selectbox("Available jobs from Phase 1", list(job_options.keys()))
    sel_job     = job_options[sel_label]
    status_icon = {"WAITING": "🟡", "COMPLETE": "🟢", "FAILED": "🔴"}.get(sel_job.get("status",""), "⚪")
    st.info(
        f"{status_icon} **run_id:** `{sel_job['run_id']}`  |  "
        f"**Status:** `{sel_job.get('status','?')}`  |  "
        f"**Phase 1 completed:** `{sel_job.get('phase1_completed_at','?')}`"
    )
    if sel_job.get("status") == "COMPLETE":
        st.warning("This job is already COMPLETE. You can still re-run it.")

    # ── Step 2: Select Company ─────────────────────────────────────────────────
    st.subheader("2. Select Company")

    # Try to pre-select company based on username in job
    def _guess_company(username: str) -> str:
        for name, info in COMPANIES.items():
            if info["email"] and info["email"].lower() == username.lower():
                return name
        return list(COMPANIES.keys())[0]

    default_company = _guess_company(sel_job.get("username", ""))
    p2_company = st.selectbox(
        "Company (determines Google Drive folder for output)",
        options=list(COMPANIES.keys()),
        index=list(COMPANIES.keys()).index(default_company),
        key="p2_company_sel",
    )
    p2_info = COMPANIES[p2_company]
    st.info(
        f"👤 **{p2_company}** — `{p2_info['email'] or '(not configured)'}`  \n"
        f"📤 Reports → `{GDRIVE_ROOT}/{p2_company}/Output/<period>/`"
    )

    # Reset cached Drive excel when company changes
    if st.session_state.p2_prev_company != p2_company:
        st.session_state.p2_gdrive_bytes = None
        st.session_state.p2_gdrive_name  = None
        st.session_state.p2_gdrive_err   = None
        st.session_state.p2_prev_company = p2_company

    # ── Step 3: Excel file ─────────────────────────────────────────────────────
    st.subheader("3. Timesheet Excel")
    st.caption("Needed for employee name verification. Use the same file uploaded in Phase 1.")

    col_dl, _ = st.columns([1, 4])
    with col_dl:
        if st.button("📥 Load from Drive", key="p2_load_drive"):
            with st.spinner("Fetching from Google Drive..."):
                data, err = fetch_excel_from_drive(p2_company)
            st.session_state.p2_gdrive_bytes = data
            st.session_state.p2_gdrive_name  = f"{p2_company.lower()}_input.xlsx" if data else None
            st.session_state.p2_gdrive_err   = err

    if st.session_state.p2_gdrive_err:
        st.error(f"Drive: {st.session_state.p2_gdrive_err}")
    elif st.session_state.p2_gdrive_bytes:
        st.success(f"✅ Loaded from Drive: **{st.session_state.p2_gdrive_name}**")

    st.caption("Upload a custom file to override the Drive file:")
    uploaded_excel = st.file_uploader("Custom Excel override", type=["xlsx"], key="p2_excel")
    if uploaded_excel:
        st.success(f"Override: **{uploaded_excel.name}**")

    # Resolve active excel
    if uploaded_excel:
        p2_excel_bytes = bytes(uploaded_excel.getbuffer())
        p2_excel_name  = uploaded_excel.name
    elif st.session_state.p2_gdrive_bytes:
        p2_excel_bytes = st.session_state.p2_gdrive_bytes
        p2_excel_name  = st.session_state.p2_gdrive_name
    else:
        p2_excel_bytes = None
        p2_excel_name  = None

    if p2_excel_name:
        st.caption(f"📄 Active: **{p2_excel_name}**")
    else:
        st.caption("⚠️ No Excel loaded.")

    # ── Step 4: Environment ────────────────────────────────────────────────────
    st.subheader("4. Environment")
    env    = st.selectbox("Environment", ["staging", "production", "development"], index=0, key="p2_env")
    headed = st.checkbox("Headed mode", value=False, key="p2_headed")

    # ── Run button ─────────────────────────────────────────────────────────────
    st.divider()
    run_clicked = st.button(
        "🚀 Run Phase 2 — Payroll Overview & Download",
        disabled=st.session_state.p2_running or p2_excel_bytes is None,
        type="primary",
        use_container_width=True,
        key="p2_run",
    )
    if p2_excel_bytes is None:
        st.caption("Load or upload the timesheet Excel to enable this button.")

    # ── Execution ──────────────────────────────────────────────────────────────
    if run_clicked and p2_excel_bytes and sel_job:
        # Save Excel to expected filename
        timesheet_filename = sel_job.get("timesheet_file", p2_excel_name)
        save_path = EXCEL_PATH.parent / timesheet_filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(p2_excel_bytes)

        # Create timestamped local run folder
        run_folder = DOWNLOADS_DIR / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_folder.mkdir(parents=True, exist_ok=True)

        st.session_state.p2_running    = True
        st.session_state.p2_logs       = ""
        st.session_state.p2_success    = None
        st.session_state.p2_run_folder = str(run_folder)
        st.session_state.p2_company    = p2_company

        cmd = [sys.executable, "-m", "pytest",
               "tests/e2e/timesheets/phase2/test_payroll_overview.py",
               "-s", "--tb=short"]
        if headed:
            cmd.append("--headed")

        env_vars = os.environ.copy()
        env_vars["NODE_ENV"]             = env
        env_vars["PYTHONIOENCODING"]     = "utf-8"
        env_vars["PYTHONUTF8"]           = "1"
        env_vars["PAYROLL_RUN_ID"]       = sel_job["run_id"]
        env_vars["REPORT_DOWNLOAD_DIR"]  = str(run_folder)
        env_vars["JOBS_FILE_PATH"]       = str(JOBS_FILE)

        st.subheader("5. Live Output")
        log_box = st.empty()
        lines: list[str] = [
            f"\n{'=' * 60}",
            f"Company : {p2_company}  ({p2_info['email']})",
            f"run_id  : {sel_job['run_id']}",
            f"period  : {sel_job.get('pay_period_start')} to {sel_job.get('pay_period_end')}",
            f"{'=' * 60}",
        ]
        log_box.code("\n".join(lines[-200:]), language="text")

        try:
            proc = subprocess.Popen(
                cmd, cwd=str(BASE_DIR), env=env_vars,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            for line in proc.stdout:
                lines.append(line.rstrip())
                log_box.code("\n".join(lines[-200:]), language="text")
            proc.wait()
            success = proc.returncode == 0
        except Exception as e:
            lines.append(f"ERROR: {e}")
            success = False

        # Rename PDFs and determine period folder name
        safe_name    = p2_excel_name.replace(".xlsx", "").replace(" ", "_")
        _ps_file     = run_folder / "period_suffix.txt"
        final_folder = run_folder
        period_folder_name = None

        if _ps_file.exists():
            _raw  = _ps_file.read_text(encoding="utf-8").strip()
            _per  = _raw.lstrip("_")
            period_folder_name = _per  # e.g. "2026-04-13_to_2026-04-19"

            day_label = p2_company.lower()  # "monday", "tuesday", etc.

            _rename_map = {
                f"payroll_paycheck{_raw}.pdf": f"paycheck_{day_label}.pdf",
                f"cash_requirement{_raw}.pdf": f"cash_requirement_{day_label}.pdf",
                f"paystub{_raw}.pdf":          f"paystub_{day_label}.pdf",
            }
            for old_name, new_name in _rename_map.items():
                old_p = run_folder / old_name
                if old_p.exists():
                    old_p.rename(run_folder / new_name)

            # Rename local folder to period
            _new_folder = DOWNLOADS_DIR / _per
            if _new_folder.exists():
                _new_folder = DOWNLOADS_DIR / f"{_per}_{safe_name}"
            run_folder.rename(_new_folder)
            final_folder = _new_folder

        st.session_state.p2_logs        = "\n".join(lines)
        st.session_state.p2_success      = success
        st.session_state.p2_running      = False
        st.session_state.p2_run_folder   = str(final_folder)
        st.session_state.p2_period_folder = period_folder_name
        st.rerun()

    # ── Output ─────────────────────────────────────────────────────────────────
    if st.session_state.p2_logs and not st.session_state.p2_running:
        st.subheader("5. Output")
        with st.expander("Show full log", expanded=(st.session_state.p2_success is False)):
            st.code(st.session_state.p2_logs, language="text")

    if st.session_state.p2_success is True:
        st.success("Phase 2 completed! All reports downloaded.")
        st.subheader("6. Reports")

        rf           = Path(st.session_state.p2_run_folder)
        period_name  = st.session_state.p2_period_folder
        company_day  = st.session_state.p2_company
        found_pdfs   = sorted(rf.glob("*.pdf")) if rf.exists() else []

        # ── Upload to Google Drive ─────────────────────────────────────────────
        if found_pdfs and period_name and company_day:
            upload_map = {p.name: p.read_bytes() for p in found_pdfs}
            # Include the run log if present
            _log_file = rf / "phase2_run.log"
            if _log_file.exists():
                upload_map[_log_file.name] = _log_file.read_bytes()
            with st.spinner(f"Uploading {len(upload_map)} file(s) to Google Drive..."):
                drive_err = upload_pdfs_to_drive(company_day, period_name, upload_map)
            if drive_err:
                st.warning(f"Drive upload issue: {drive_err}")
            else:
                st.success(
                    f"✅ Uploaded to Drive: "
                    f"`{GDRIVE_ROOT}/{company_day}/Output/{period_name}/`"
                )

        # ── Local download buttons ─────────────────────────────────────────────
        if found_pdfs:
            st.caption("You can also download them locally:")
            for pdf_path in found_pdfs:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {pdf_path.name}",
                        data=f.read(),
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        key=str(pdf_path),
                        use_container_width=True,
                    )
            # Show run log if present
            _log_dl = rf / "phase2_run.log"
            if _log_dl.exists():
                with open(_log_dl, "rb") as f:
                    st.download_button(
                        label="⬇️ phase2_run.log",
                        data=f.read(),
                        file_name="phase2_run.log",
                        mime="text/plain",
                        key=str(_log_dl),
                        use_container_width=True,
                    )
                with st.expander("View run log"):
                    st.code(_log_dl.read_text(encoding="utf-8"), language="text")
        else:
            st.warning("No PDF files found in the run folder.")

    elif st.session_state.p2_success is False:
        st.error("Phase 2 failed. Check the output log above.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Past Downloads
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("Previously downloaded payroll reports from this machine.")
    past = (
        sorted([d for d in DOWNLOADS_DIR.iterdir() if d.is_dir()], reverse=True)
        if DOWNLOADS_DIR.exists() else []
    )
    if not past:
        st.caption("No past downloads. Run Phase 2 first.")
    else:
        for run_dir in past:
            pdfs = sorted(run_dir.glob("*.pdf"))
            if not pdfs:
                continue
            with st.expander(f"📁 {run_dir.name}  ({len(pdfs)} file(s))"):
                # Re-upload to Drive button
                reup_col, _ = st.columns([1, 3])
                with reup_col:
                    if st.button(f"☁️ Upload to Drive", key=f"reup_{run_dir.name}"):
                        # Infer company from folder/filename
                        day = None
                        for d in COMPANIES:
                            if d.lower() in run_dir.name.lower() or any(d.lower() in p.name for p in pdfs):
                                day = d
                                break
                        if not day:
                            day = st.selectbox(
                                "Which company?", list(COMPANIES.keys()),
                                key=f"sel_{run_dir.name}"
                            )
                        if day:
                            pm = {p.name: p.read_bytes() for p in pdfs}
                            err = upload_pdfs_to_drive(day, run_dir.name, pm)
                            if err:
                                st.error(err)
                            else:
                                st.success(f"Uploaded to Drive: {GDRIVE_ROOT}/{day}/Output/{run_dir.name}/")

                for pdf_path in pdfs:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {pdf_path.name}",
                            data=f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            key=str(pdf_path),
                            use_container_width=True,
                        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — View Jobs
# ══════════════════════════════════════════════════════════════════════════════
with tab_jobs:
    st.markdown(f"All payroll runs submitted by Phase 1.  \nReading from: `{JOBS_FILE}`")
    if st.button("Refresh", key="refresh_jobs_tab3"):
        st.rerun()

    all_jobs = _load_jobs()
    if not all_jobs:
        st.info("No jobs found. Run Phase 1 first.")
    else:
        import pandas as pd
        rows = [{
            "run_id":    j.get("run_id",""),
            "username":  j.get("username",""),
            "period":    f"{j.get('pay_period_start','?')} to {j.get('pay_period_end','?')}",
            "file":      j.get("timesheet_file",""),
            "status":    j.get("status","?"),
            "submitted": j.get("phase1_completed_at",""),
            "completed": j.get("phase2_completed_at",""),
        } for j in reversed(all_jobs)]
        df = pd.DataFrame(rows)
        def _col(v):
            if v=="COMPLETE": return "background-color:#d4edda;color:#155724"
            if v=="FAILED":   return "background-color:#f8d7da;color:#721c24"
            return "background-color:#fff3cd;color:#856404"
        st.dataframe(df.style.map(_col, subset=["status"]), use_container_width=True, hide_index=True)
        st.caption(
            f"Total: {len(all_jobs)}  |  "
            f"Waiting: {sum(1 for j in all_jobs if j.get('status')=='WAITING')}  |  "
            f"Complete: {sum(1 for j in all_jobs if j.get('status')=='COMPLETE')}  |  "
            f"Failed: {sum(1 for j in all_jobs if j.get('status')=='FAILED')}"
        )