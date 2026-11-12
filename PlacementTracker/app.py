from collections import Counter
from datetime import date

import pandas as pd
import streamlit as st

from database import database_connection, initialize_database

STATUS_OPTIONS = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]

st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
initialize_database()
st.title("Placement Application Tracker")

# Feature 1: Let the user enter and save a new application.
st.header("Add Application")

with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date", value=date.today())
    status = st.selectbox("Status", STATUS_OPTIONS)
    has_interview = st.checkbox("Interview scheduled")
    interview_date = (
        st.date_input("Interview Date", value=date.today())
        if has_interview
        else None
    )
    submitted = st.form_submit_button("Add Application")

if submitted:
    # Company name and job role must contain something besides whitespace.
    if not company_name.strip():
        st.error("Please enter a company name.")
    elif not job_role.strip():
        st.error("Please enter a job role.")
    else:
        with database_connection() as connection:
            connection.execute(
                """
                INSERT INTO applications
                    (company_name, job_role, application_date, status, interview_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    company_name.strip(),
                    job_role.strip(),
                    application_date.isoformat(),
                    status,
                    interview_date.isoformat() if interview_date else None,
                ),
            )
        st.success("Application added successfully.")

# Read all records once so the table and summaries use the same data.
with database_connection() as connection:
    applications = connection.execute(
        """
        SELECT
            application_id, company_name, job_role, application_date, status,
            interview_date
        FROM applications
        ORDER BY application_id DESC
        """
    ).fetchall()

columns = [
    "application_id",
    "company_name",
    "job_role",
    "application_date",
    "status",
    "interview_date",
]
applications_df = pd.DataFrame(applications, columns=columns)

st.header("View Applications")
if applications_df.empty:
    st.info("No applications are available yet. Add one using the form above.")
else:
    status_options = sorted(
        set(STATUS_OPTIONS)
        | {
            value
            for value in applications_df["status"].dropna().astype(str)
            if value
        },
        key=str.casefold,
    )
    company_search = st.text_input("Search by company name")
    selected_statuses = st.multiselect(
        "Filter by status",
        options=status_options,
        default=status_options,
    )
    filtered_df = applications_df[
        applications_df["company_name"].str.contains(
            company_search.strip(), case=False, regex=False, na=False
        )
        & applications_df["status"].isin(selected_statuses)
    ]
    st.dataframe(filtered_df, hide_index=True)
    st.download_button(
        "Export visible applications to CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="placement_applications.csv",
        mime="text/csv",
        disabled=filtered_df.empty,
    )

    st.subheader("Update application status")
    application_labels = {
        row.application_id: (
            f"{row.company_name} — {row.job_role} (ID {row.application_id})"
        )
        for row in applications_df.itertuples(index=False)
    }
    selected_id = st.selectbox(
        "Application",
        options=list(application_labels),
        format_func=application_labels.__getitem__,
    )
    selected_application = applications_df[
        applications_df["application_id"] == selected_id
    ].iloc[0]
    current_status = selected_application["status"]
    edit_status_options = (
        list(dict.fromkeys([*STATUS_OPTIONS, current_status]))
        if pd.notna(current_status)
        else STATUS_OPTIONS
    )
    new_status = st.selectbox(
        "New status",
        options=edit_status_options,
        index=edit_status_options.index(current_status)
        if current_status in edit_status_options
        else 0,
    )
    if st.button("Update Status"):
        with database_connection() as connection:
            connection.execute(
                "UPDATE applications SET status = ? WHERE application_id = ?",
                (new_status, selected_id),
            )
        st.success("Application status updated.")
        st.rerun()

    st.subheader("Delete application")
    confirm_delete = st.checkbox(
        f"Confirm deletion of {application_labels[selected_id]}"
    )
    if st.button("Delete Application", disabled=not confirm_delete):
        with database_connection() as connection:
            connection.execute(
                "DELETE FROM applications WHERE application_id = ?",
                (selected_id,),
            )
        st.success("Application deleted.")
        st.rerun()

st.header("Upcoming Interviews")
if applications_df.empty:
    st.info("No upcoming interviews are scheduled.")
else:
    interview_dates = pd.to_datetime(
        applications_df["interview_date"], errors="coerce"
    )
    upcoming_interviews = applications_df[
        interview_dates.notna()
        & (interview_dates.dt.normalize() >= pd.Timestamp(date.today()))
    ].copy()
    if upcoming_interviews.empty:
        st.info("No upcoming interviews are scheduled.")
    else:
        upcoming_interviews["interview_date"] = pd.to_datetime(
            upcoming_interviews["interview_date"]
        ).dt.strftime("%Y-%m-%d")
        upcoming_interviews = upcoming_interviews.sort_values("interview_date")
        st.dataframe(
            upcoming_interviews[
                ["company_name", "job_role", "interview_date", "status"]
            ],
            hide_index=True,
        )

# Feature 3: Display the total number of saved applications.
st.header("Total Applications")
st.metric("Applications", len(applications))

# Feature 4: Count roles and use alphabetical order to break count ties.
st.header("Most Applied Role")
role_counts = Counter(application[2] for application in applications)
if not role_counts:
    st.info("There are no applications to find a most-applied role.")
else:
    most_applied_role, role_count = sorted(
        role_counts.items(),
        key=lambda item: (-item[1], item[0].casefold(), item[0]),
    )[0]
    st.write(f"**{most_applied_role}** ({role_count} applications)")

# Feature 5: Show a count for every selectable status, including zero counts.
st.header("Status-wise Summary")
status_counts = Counter(application[4] for application in applications)
status_summary = pd.DataFrame(
    [
        {"Status": status_name, "Applications": status_counts.get(status_name, 0)}
        for status_name in STATUS_OPTIONS
    ]
)
st.table(status_summary)
st.bar_chart(status_summary.set_index("Status"))
