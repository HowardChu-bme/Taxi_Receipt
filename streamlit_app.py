import datetime as dt
from io import BytesIO
import pandas as pd
import streamlit as st

# WeasyPrint for HTML -> PDF
from weasyprint import HTML

st.set_page_config(page_title="Taxi Expense Justification - Montsmed HK", page_icon="🚕", layout="centered")

# ---- Helpers ----
def init_state():
    if "records" not in st.session_state:
        st.session_state.records = []

def validate_money(amount: float) -> bool:
    return amount is not None and amount >= 0

def to_printable_html(row: dict) -> str:
    # Minimal printable summary as HTML; use this same HTML for the PDF
    styles = """
    <style>
      .print-card {font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; color: #222;}
      .print-card h2 {margin-bottom: 0.2rem;}
      .grid {display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px;}
      .section {border-top: 1px solid #ddd; margin-top: 16px; padding-top: 12px;}
      .mono {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; white-space: pre-wrap;}
      .badge {display:inline-block; padding:2px 6px; border:1px solid #999; border-radius:6px; margin:2px 6px 2px 0; font-size:12px;}
      .small {font-size: 12px; color: #555;}
    </style>
    """
    reasons_html = "".join(f'<span class="badge">{r}</span>' for r in row.get("primary_reasons", []))
    equip = (row.get("equipment") or "").strip() or "N/A"
    receipt_type = row.get("receipt_type", "N/A")
    distance = row.get("distance_km", "")
    distance_str = f"{distance} km" if distance != "" else "N/A"

    # Precompute any content that would otherwise require backslashes in f-string expressions
    desc_raw = row.get("work_description", "") or ""
    # Use pre-wrap in CSS, but also allow explicit breaks if present
    desc_html = desc_raw.replace("\n", "<br>")

    html = f"""
    {styles}
    <div class="print-card">
      <h2>Taxi Expense Justification Form</h2>
      <div class="small">Montsmed HK</div>

      <div class="section">
        <h3>Employee information</h3>
        <div class="grid">
          <div><strong>Employee Name:</strong> {row.get('employee_name','')}</div>
          <div><strong>Department:</strong> Service Engineering</div>
          <div><strong>Position:</strong> Service Engineer</div>
          <div><strong>Date of Submission:</strong> {row.get('submission_date','')}</div>
        </div>
      </div>

      <div class="section">
        <h3>Trip details</h3>
        <div class="grid">
          <div><strong>Date of Travel:</strong> {row.get('date_of_travel','')}</div>
          <div><strong>Time of Travel:</strong> {row.get('time_of_travel','')}</div>
          <div><strong>From:</strong> {row.get('from_location','')}</div>
          <div><strong>To:</strong> {row.get('to_location','')}</div>
          <div><strong>Taxi Fare Amount:</strong> HK$ {row.get('fare_amount','')}</div>
          <div><strong>Receipt Number:</strong> {row.get('receipt_number','')}</div>
        </div>
      </div>

      <div class="section">
        <h3>Justification</h3>
        <div>{reasons_html or "N/A"}</div>
        <div><strong>Other (details):</strong> {row.get('reason_other','') or 'N/A'}</div>
      </div>

      <div class="section">
        <h3>Work details</h3>
        <div class="grid">
          <div><strong>Client/Customer:</strong> {row.get('client','')}</div>
          <div><strong>Type of Service:</strong> {row.get('service_type','')}</div>
          <div><strong>Equipment (if any):</strong> {equip}</div>
        </div>
        <div style="margin-top:8px;">
          <strong>Brief Description:</strong>
          <div class="mono">{desc_html}</div>
        </div>
      </div>

      <div class="section">
        <h3>Receipt info</h3>
        <div class="grid">
          <div><strong>Receipt Attached:</strong> {receipt_type}</div>
          <div><strong>Taxi License Plate:</strong> {row.get('license_plate','')}</div>
          <div><strong>Start Time:</strong> {row.get('start_time','')}</div>
          <div><strong>End Time:</strong> {row.get('end_time','')}</div>
          <div><strong>Distance:</strong> {distance_str}</div>
        </div>
      </div>
    </div>
    """
    return html

def html_to_pdf_bytes(html: str) -> bytes:
    # Render HTML to PDF bytes in-memory using WeasyPrint
    # Using default base_url=None; for external assets, provide base_url.
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes

def record_to_csv_bytes(records: list) -> bytes:
    if not records:
        return b""
    df = pd.DataFrame(records)
    return df.to_csv(index=False).encode("utf-8")

# ---- UI ----
init_state()

st.title("TAXI EXPENSE JUSTIFICATION FORM")
st.caption("Montsmed HK")

with st.form("taxi_form", clear_on_submit=False):
    st.subheader("Employee information")
    c1, c2 = st.columns(2)
    with c1:
        employee_name = st.text_input("Employee Name", placeholder="Full name", max_chars=80)
        department = st.text_input("Department", value="Service Engineering", disabled=True)
        date_submission = st.date_input("Date of Submission", value=dt.date.today(), format="YYYY-MM-DD")
    with c2:
        position = st.text_input("Position", value="Service Engineer", disabled=True)

    st.subheader("Trip details")
    c3, c4 = st.columns(2)
    with c3:
        date_of_travel = st.date_input("Date of Travel", format="YYYY-MM-DD")
        from_location = st.text_input("From (Pick-up Location)")
        fare_amount = st.number_input("Taxi Fare Amount (HK$)", min_value=0.0, step=1.0)
        receipt_number = st.text_input("Receipt Number", max_chars=50)
    with c4:
        time_of_travel = st.time_input("Time of Travel")
        to_location = st.text_input("To (Destination)")
        license_plate = st.text_input("Taxi License Plate", max_chars=20)

    st.subheader("Justification for taxi use")
    st.write("Primary Reason for Taxi (check all that apply):")
    reason_options = [
        "Equipment Transport",
        "Early Arrival Requirement",
        "Emergency Call",
        "Special Event/Meeting",
        "Time-Critical Service",
        "Weather/Safety Conditions",
        "Public Transport Unavailable",
        "Other",
    ]
    cols = st.columns(2)
    selected = []
    for i, label in enumerate(reason_options):
        with cols[i % 2]:
            val = st.checkbox(label, key=f"reason_{i}")
            if val:
                selected.append(label)
    reason_other = ""
    if "Other" in selected:
        reason_other = st.text_input("Other (describe)", max_chars=200)

    st.subheader("Work details")
    c5, c6 = st.columns(2)
    with c5:
        client = st.text_input("Client/Customer")
        equipment = st.text_area(
            "Equipment Being Transported (if applicable)",
            height=80,
            placeholder="List equipment and quantities if relevant",
        )
    with c6:
        service_type = st.selectbox(
            "Type of Service",
            ["Installation", "Maintenance", "Repair", "Follow-up", "Other"],
            index=1,
        )
        work_description = st.text_area("Brief Description of Work/Purpose", height=120)

    st.subheader("Receipt attachment")
    receipt_type = st.radio(
        "Receipt provided",
        options=[
            "Original taxi receipt attached",
            "Electronic receipt attached",
            "Hand-written receipt (if machine-printed not available)",
        ],
        index=1,
    )
    receipt_file = st.file_uploader(
        "Upload receipt (PDF/JPG/PNG, up to ~8MB recommended)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=False,
        help="Keep files small to avoid memory issues on shared hosting.",
    )

    st.subheader("Receipt info (optional)")
    c7, c8, c9 = st.columns(3)
    with c7:
        start_time = st.time_input("Start Time", value=None, step=60, key="start_time")
    with c8:
        end_time = st.time_input("End Time", value=None, step=60, key="end_time")
    with c9:
        distance_km = st.number_input("Distance (km)", min_value=0.0, step=0.1, format="%.1f")

    submitted = st.form_submit_button("Submit")

# Handle submission
if submitted:
    errors = []
    if not employee_name.strip():
        errors.append("Employee Name is required.")
    if not from_location.strip():
        errors.append("Pick-up Location is required.")
    if not to_location.strip():
        errors.append("Destination is required.")
    if not validate_money(fare_amount):
        errors.append("Fare amount must be a non-negative number.")
    if not selected:
        errors.append("Select at least one primary reason.")
    if "Other" in selected and not reason_other.strip():
        errors.append("Please describe the 'Other' reason.")
    if not work_description.strip():
        errors.append("Brief description of work/purpose is required.")
    if receipt_file and receipt_file.size > 8 * 1024 * 1024:
        errors.append("Receipt file is too large (>8MB). Please upload a smaller file.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        record = {
            "employee_name": employee_name.strip(),
            "department": "Service Engineering",
            "position": "Service Engineer",
            "submission_date": date_submission.isoformat(),
            "date_of_travel": date_of_travel.isoformat(),
            "time_of_travel": time_of_travel.strftime("%H:%M"),
            "from_location": from_location.strip(),
            "to_location": to_location.strip(),
            "fare_amount": round(float(fare_amount), 2),
            "receipt_number": receipt_number.strip(),
            "primary_reasons": selected,
            "reason_other": reason_other.strip(),
            "client": client.strip(),
            "service_type": service_type,
            "equipment": equipment.strip(),
            "work_description": work_description.strip(),
            "receipt_type": receipt_type,
            "license_plate": license_plate.strip(),
            "start_time": start_time.strftime("%H:%M") if start_time else "",
            "end_time": end_time.strftime("%H:%M") if end_time else "",
            "distance_km": float(distance_km) if distance_km else "",
            "uploaded_receipt_name": receipt_file.name if receipt_file else "",
        }
        st.session_state.records.append(record)
        st.success("Form submitted. Entry saved in session (not persisted to a database).")

        with st.expander("Preview printable summary", expanded=True):
            preview_html = to_printable_html(record)
            st.markdown(preview_html, unsafe_allow_html=True)

            # Offer download of receipt if uploaded
            if receipt_file:
                st.write("Attached receipt:")
                st.download_button(
                    "Download uploaded receipt",
                    data=receipt_file.getvalue(),
                    file_name=receipt_file.name,
                    mime=receipt_file.type or "application/octet-stream",
                )

            # Download PDF summary
            try:
                pdf_bytes = html_to_pdf_bytes(preview_html)
                st.download_button(
                    "Download PDF summary",
                    data=pdf_bytes,
                    file_name=f"taxi_expense_{record.get('submission_date','')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

# Data section
st.divider()
st.subheader("Saved entries (this session)")
if st.session_state.records:
    df = pd.DataFrame(st.session_state.records).drop(columns=["primary_reasons"], errors="ignore")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Download CSV",
        data=record_to_csv_bytes(st.session_state.records),
        file_name="taxi_expenses.csv",
        mime="text/csv",
    )
else:
    st.info("No entries yet.")

st.caption("Note: Data is stored only in the current session. For persistence, connect a database or Google Sheet.")
