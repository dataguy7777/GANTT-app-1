import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# Set the page configuration
st.set_page_config(
    page_title="📊 Gantt Chart Generator",
    layout="wide",
)

# Title of the app
st.title("📊 Gantt Chart Generator")

# Initialize session state for data
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()

# Main area for data import
st.header("Import Gantt Data")

import_option = st.radio(
    "Choose data import method:",
    ('Upload Excel File', 'Paste CSV Data'),
    horizontal=True
)

def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

def load_csv(pasted_data):
    try:
        df = pd.read_csv(StringIO(pasted_data))
        return df
    except Exception as e:
        st.error(f"Error parsing CSV data: {e}")
        return None

if import_option == 'Upload Excel File':
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = load_excel(uploaded_file)
        if df is not None:
            st.session_state['data'] = df
            st.success("Excel file loaded successfully!")
elif import_option == 'Paste CSV Data':
    pasted_csv = st.text_area("Paste your CSV data here", height=300)
    if pasted_csv:
        df = load_csv(pasted_csv)
        if df is not None:
            st.session_state['data'] = df
            st.success("CSV data loaded successfully!")

# Display the current data
st.header("Current Data")
if not st.session_state['data'].empty:
    st.dataframe(st.session_state['data'])
else:
    st.warning("No data available. Please upload an Excel file or paste CSV data to proceed.")

# Proceed only if data is available
if not st.session_state['data'].empty:
    # Data Cleaning: Keep only Activity, Start Date, End Date
    st.subheader("Manage Columns")

    with st.expander("Remove Unwanted Columns"):
        all_columns = st.session_state['data'].columns.tolist()
        # Define the required columns
        required_columns = ['Activity', 'Start Date', 'End Date']
        # Determine which required columns are present
        existing_required = [col for col in required_columns if col in all_columns]
        # Set default to existing required columns
        default_columns = existing_required if existing_required else all_columns[:3]  # Fallback to first three columns if required not present
        columns_to_keep = st.multiselect(
            "Select columns to keep:",
            options=all_columns,
            default=default_columns
        )
        if columns_to_keep:
            st.session_state['data'] = st.session_state['data'][columns_to_keep]
            st.success("Columns updated successfully!")

    # Ensure the necessary columns are present
    missing_columns = [col for col in ['Activity', 'Start Date', 'End Date'] if col not in st.session_state['data'].columns]
    if missing_columns:
        st.warning(f"Missing required column(s): {', '.join(missing_columns)}. Please ensure your data includes 'Activity', 'Start Date', and 'End Date'.")
    else:
        # Convert date columns to datetime
        for date_col in ['Start Date', 'End Date']:
            st.session_state['data'][date_col] = pd.to_datetime(st.session_state['data'][date_col], errors='coerce')

        # Drop rows with invalid dates
        initial_row_count = st.session_state['data'].shape[0]
        st.session_state['data'] = st.session_state['data'].dropna(subset=['Start Date', 'End Date'])
        final_row_count = st.session_state['data'].shape[0]
        if final_row_count < initial_row_count:
            st.info(f"Dropped {initial_row_count - final_row_count} row(s) due to invalid dates.")

        # Add new activity
        st.subheader("Add New Activity")
        with st.form("add_activity_form"):
            new_activity = st.text_input("Activity")
            new_start = st.date_input("Start Date")
            new_end = st.date_input("End Date")
            submitted = st.form_submit_button("Add Activity")
            if submitted:
                if new_activity and new_start and new_end:
                    if new_end < new_start:
                        st.error("End Date cannot be before Start Date.")
                    else:
                        new_row = {
                            'Activity': new_activity,
                            'Start Date': pd.to_datetime(new_start),
                            'End Date': pd.to_datetime(new_end)
                        }
                        st.session_state['data'] = st.session_state['data'].append(new_row, ignore_index=True)
                        st.success("New activity added!")
                else:
                    st.error("Please fill in all fields.")

        # Remove activity
        st.subheader("Remove Activity")
        with st.form("remove_activity_form"):
            activity_to_remove = st.selectbox("Select activity to remove", st.session_state['data']['Activity'].unique())
            remove_submitted = st.form_submit_button("Remove Activity")
            if remove_submitted:
                st.session_state['data'] = st.session_state['data'][st.session_state['data']['Activity'] != activity_to_remove]
                st.success(f"Activity '{activity_to_remove}' removed!")

        # Generate Gantt Chart
        st.subheader("Gantt Chart")

        if st.session_state['data'].empty:
            st.warning("No data available to generate Gantt chart.")
        else:
            fig = px.timeline(
                st.session_state['data'],
                x_start="Start Date",
                x_end="End Date",
                y="Activity",
                title="Gantt Chart",
                labels={"Activity": "Activity", "Start Date": "Start Date", "End Date": "End Date"},
            )
            fig.update_yaxes(autorange="reversed")  # To have the first activity on top
            st.plotly_chart(fig, use_container_width=True)

        # Option to download the data
        st.subheader("Download Data")
        csv = st.session_state['data'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='gantt_data.csv',
            mime='text/csv',
        )
