import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# Set the page configuration
st.set_page_config(
    page_title="Gantt Chart Generator",
    layout="wide",
)

# Title of the app
st.title("📊 Gantt Chart Generator")

# Initialize session state for data
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame(columns=['Activity', 'Start Date', 'End Date'])

# Sidebar for data import options
st.sidebar.header("Import Data")

import_option = st.sidebar.radio(
    "Choose data import method:",
    ('Upload Excel File', 'Paste CSV Data')
)

def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.sidebar.error(f"Error reading Excel file: {e}")
        return None

def load_csv(pasted_data):
    try:
        df = pd.read_csv(StringIO(pasted_data))
        return df
    except Exception as e:
        st.sidebar.error(f"Error parsing CSV data: {e}")
        return None

if import_option == 'Upload Excel File':
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = load_excel(uploaded_file)
        if df is not None:
            st.session_state['data'] = df
            st.sidebar.success("Excel file loaded successfully!")
elif import_option == 'Paste CSV Data':
    pasted_csv = st.sidebar.text_area("Paste your CSV data here")
    if pasted_csv:
        df = load_csv(pasted_csv)
        if df is not None:
            st.session_state['data'] = df
            st.sidebar.success("CSV data loaded successfully!")

# Display the current data
st.subheader("Current Data")
st.dataframe(st.session_state['data'])

# Data Cleaning: Keep only Activity, Start Date, End Date
st.subheader("Manage Columns")

with st.expander("Remove Unwanted Columns"):
    all_columns = st.session_state['data'].columns.tolist()
    columns_to_keep = st.multiselect(
        "Select columns to keep:",
        options=all_columns,
        default=['Activity', 'Start Date', 'End Date']
    )
    if columns_to_keep:
        st.session_state['data'] = st.session_state['data'][columns_to_keep]
        st.success("Columns updated successfully!")

# Ensure the necessary columns are present
required_columns = ['Activity', 'Start Date', 'End Date']
for col in required_columns:
    if col not in st.session_state['data'].columns:
        st.warning(f"Missing required column: {col}")

# Convert date columns to datetime
for date_col in ['Start Date', 'End Date']:
    if date_col in st.session_state['data'].columns:
        st.session_state['data'][date_col] = pd.to_datetime(st.session_state['data'][date_col], errors='coerce')

# Drop rows with invalid dates
st.session_state['data'] = st.session_state['data'].dropna(subset=['Start Date', 'End Date'])

# Add new activity
st.subheader("Add New Activity")
with st.form("add_activity_form"):
    new_activity = st.text_input("Activity")
    new_start = st.date_input("Start Date")
    new_end = st.date_input("End Date")
    submitted = st.form_submit_button("Add Activity")
    if submitted:
        if new_activity and new_start and new_end:
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

