import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from io import StringIO, BytesIO
import csv
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

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

# Function to load Excel files
def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

# Function to load CSV data
def load_csv(pasted_data, sep):
    try:
        df = pd.read_csv(StringIO(pasted_data), sep=sep)
        return df
    except Exception as e:
        st.error(f"Error parsing data with separator '{sep}': {e}")
        return None

# Header for data import
st.header("1. Import Gantt Data")

# Radio button for selecting import method
import_option = st.radio(
    "Choose data import method:",
    ('Upload Excel File', 'Paste Data'),
    horizontal=True
)

# Data import logic
if import_option == 'Upload Excel File':
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = load_excel(uploaded_file)
        if df is not None:
            st.session_state['data'] = df
            st.success("Excel file loaded successfully!")
elif import_option == 'Paste Data':
    # Radio buttons for separator selection
    separator_option = st.radio(
        "Select data separator:",
        ('Auto-detect', 'Comma (,)', 'Tab (\\t)', 'Semicolon (;)'),
        horizontal=True
    )
    
    # Container for paste area
    paste_container = st.empty()
    
    if separator_option == 'Auto-detect':
        # Text area for sample data
        sample = paste_container.text_area("Paste a sample of your data here for separator detection:", height=150)
        if sample:
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=[',', '\t', ';'])
                sep = dialect.delimiter
                st.write(f"**Detected Separator:** '{sep}'")
                
                # Text area for full data
                full_data = paste_container.text_area("Paste your full data here:", height=300)
                if full_data:
                    df = load_csv(full_data, sep)
                    if df is not None:
                        st.session_state['data'] = df
                        st.success("Data loaded successfully!")
            except csv.Error:
                st.warning("Could not automatically detect the separator. Please select it manually below.")
    else:
        # Mapping separators
        sep_map = {
            'Comma (,)': ',',
            'Tab (\\t)': '\t',
            'Semicolon (;)': ';'
        }
        sep = sep_map.get(separator_option, ',')  # Default to comma
        # Text area for full data
        pasted_data = paste_container.text_area("Paste your data here:", height=300)
        if pasted_data:
            df = load_csv(pasted_data, sep)
            if df is not None:
                st.session_state['data'] = df
                st.success("Data loaded successfully!")

# Header for current data
st.header("2. Current Data")
if not st.session_state['data'].empty:
    # Allow users to edit the DataFrame
    edited_df = st.data_editor(st.session_state['data'], num_rows="dynamic")
    if edited_df is not None:
        st.session_state['data'] = edited_df
        st.success("Data updated successfully!")
else:
    st.warning("No data available. Please upload an Excel file or paste data to proceed.")

# Proceed only if data is available
if not st.session_state['data'].empty:
    # Header for column remapping
    st.header("3. Column Remapping")
    st.markdown("Map your dataset's columns to the required fields for the Gantt chart.")
    
    all_columns = st.session_state['data'].columns.tolist()
    
    # Columns for dropdowns
    col1, col2, col3 = st.columns(3)
    with col1:
        activity_col = st.selectbox("Select Activity Column:", options=all_columns, key='activity_col')
    with col2:
        start_date_col = st.selectbox("Select Start Date Column:", options=all_columns, key='start_date_col')
    with col3:
        end_date_col = st.selectbox("Select End Date Column:", options=all_columns, key='end_date_col')
    
    # Button to apply column mapping
    if st.button("Apply Column Mapping"):
        if activity_col and start_date_col and end_date_col:
            try:
                # Rename columns to standard names
                mapped_data = st.session_state['data'].rename(columns={
                    activity_col: 'Activity',
                    start_date_col: 'Start Date',
                    end_date_col: 'End Date'
                })
                
                # Select only the mapped columns
                st.session_state['data'] = mapped_data[['Activity', 'Start Date', 'End Date']]
                
                st.success("Columns mapped successfully!")
            except Exception as e:
                st.error(f"Error in mapping columns: {e}")
        else:
            st.error("Please select all three columns.")
    
    # Display the mapped data
    st.subheader("Mapped Data")
    if not st.session_state['data'].empty and set(['Activity', 'Start Date', 'End Date']).issubset(st.session_state['data'].columns):
        st.dataframe(st.session_state['data'])
    else:
        st.warning("Please map the columns to proceed.")
    
    # Continue only if required columns are present
    if set(['Activity', 'Start Date', 'End Date']).issubset(st.session_state['data'].columns):
        # Data Cleaning: Convert date columns to datetime
        for date_col in ['Start Date', 'End Date']:
            # Attempt to parse dates with dayfirst=True
            st.session_state['data'][date_col] = pd.to_datetime(
                st.session_state['data'][date_col],
                dayfirst=True,
                errors='coerce'
            )
        
        # Drop rows with invalid dates
        initial_row_count = st.session_state['data'].shape[0]
        st.session_state['data'] = st.session_state['data'].dropna(subset=['Start Date', 'End Date'])
        final_row_count = st.session_state['data'].shape[0]
        if final_row_count < initial_row_count:
            st.info(f"Dropped {initial_row_count - final_row_count} row(s) due to invalid dates.")
        
        # Shorten Activity names to 50 characters
        st.session_state['data']['Activity'] = st.session_state['data']['Activity'].astype(str).str.slice(0, 50)
        
        # Editable DataFrame after cleaning
        st.header("4. Edit Data")
        edited_df = st.data_editor(st.session_state['data'], num_rows="dynamic")
        if edited_df is not None:
            st.session_state['data'] = edited_df
            st.success("Data updated successfully!")
        
        # Add new activity
        st.header("5. Add New Activity")
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
                        # Shorten Activity name to 50 characters
                        new_activity = new_activity[:50]
                        new_row = {
                            'Activity': new_activity,
                            'Start Date': pd.to_datetime(new_start),
                            'End Date': pd.to_datetime(new_end)
                        }
                        st.session_state['data'] = st.session_state['data'].append(new_row, ignore_index=True)
                        st.success("New activity added!")
                else:
                    st.error("Please fill in all fields!")
        
        # Remove activity
        st.header("6. Remove Activity")
        with st.form("remove_activity_form"):
            if not st.session_state['data']['Activity'].empty:
                activity_to_remove = st.selectbox("Select activity to remove", st.session_state['data']['Activity'].unique())
                remove_submitted = st.form_submit_button("Remove Activity")
                if remove_submitted:
                    st.session_state['data'] = st.session_state['data'][st.session_state['data']['Activity'] != activity_to_remove]
                    st.success(f"Activity '{activity_to_remove}' removed!")
            else:
                st.warning("No activities available to remove.")
        
        # Generate Gantt Charts
        st.header("7. Gantt Charts")
        
        if st.session_state['data'].empty:
            st.warning("No data available to generate Gantt charts.")
        else:
            # Plotly Gantt Chart
            st.subheader("a. Plotly Gantt Chart")
            try:
                fig_plotly = px.timeline(
                    st.session_state['data'],
                    x_start="Start Date",
                    x_end="End Date",
                    y="Activity",
                    title="Plotly Gantt Chart",
                    labels={"Activity": "Activity", "Start Date": "Start Date", "End Date": "End Date"},
                    hover_data=["Activity", "Start Date", "End Date"]
                )
                fig_plotly.update_yaxes(autorange="reversed")  # To have the first activity on top

                # Enhance the layout with month and week separators
                fig_plotly.update_layout(
                    xaxis=dict(
                        tickformat="%b %d",  # e.g., Jan 01
                        dtick="M1",  # Tick every month
                        ticklabelmode="period",
                        title="Timeline",
                    ),
                    yaxis_title="Activity",
                    template="plotly_white",
                    title_x=0.5,
                    margin=dict(l=100, r=40, t=80, b=40)
                )

                # Customize x-axis to show months and weeks
                fig_plotly.update_xaxes(
                    rangeslider_visible=True,
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=3, label="3m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(step="all")
                        ])
                    )
                )

                # Add current date marker
                current_date = pd.Timestamp.today()
                fig_plotly.add_vline(x=current_date, line_dash="dash", line_color="red")
                fig_plotly.add_annotation(
                    x=current_date,
                    y=0.95,
                    xref="x",
                    yref="paper",
                    text="Today",
                    showarrow=True,
                    arrowhead=1,
                    ax=40,
                    ay=-40,
                    font=dict(color="red", size=12, family="Arial")
                )

                # Improve overall aesthetics
                fig_plotly.update_traces(marker=dict(line=dict(width=0)))

                st.plotly_chart(fig_plotly, use_container_width=True)

                # Option to download the Plotly Gantt chart as an image
                st.subheader("Export Plotly Gantt Chart as Image")
                try:
                    img_bytes_plotly = fig_plotly.to_image(format="png", scale=2)
                    st.download_button(
                        label="Download Plotly Gantt Chart as PNG",
                        data=img_bytes_plotly,
                        file_name="gantt_chart_plotly.png",
                        mime="image/png",
                    )
                except Exception as e:
                    st.error(f"Error exporting Plotly chart as image: {e}")
            except Exception as e:
                st.error(f"Error generating Plotly Gantt chart: {e}")
            
            st.markdown("---")
            
            # Matplotlib Gantt Chart
            st.subheader("b. Matplotlib Gantt Chart")
            try:
                # Prepare data for Matplotlib
                df_mat = st.session_state['data'].copy()
                df_mat['Start Date'] = pd.to_datetime(df_mat['Start Date'])
                df_mat['End Date'] = pd.to_datetime(df_mat['End Date'])
                df_mat['Duration'] = (df_mat['End Date'] - df_mat['Start Date']).dt.days

                # Assign unique colors to activities using a professional palette
                unique_activities = df_mat['Activity'].unique()
                # Use a colormap with sufficient distinct colors
                cmap = plt.cm.get_cmap('tab20', len(unique_activities))
                color_map = {activity: cmap(i) for i, activity in enumerate(unique_activities)}
                df_mat['Color'] = df_mat['Activity'].map(color_map)

                # Create a figure and axis
                fig_mat, ax_mat = plt.subplots(figsize=(18, max(6, len(df_mat)*0.6)))

                # Plot bars
                for idx, row in df_mat.iterrows():
                    ax_mat.barh(row['Activity'], row['Duration'], left=row['Start Date'], color=row['Color'], edgecolor='black', height=0.6)
                    
                    # Add completion text if 'Completion' column exists
                    if 'Completion' in df_mat.columns:
                        completion = row['Completion']
                        ax_mat.text(row['End Date'] + pd.Timedelta(days=1), idx, f"{int(completion*100)}%", va='center', fontsize=9, color='black')

                # Set labels and title
                ax_mat.set_xlabel('Date', fontsize=12, fontweight='bold')
                ax_mat.set_ylabel('Activity', fontsize=12, fontweight='bold')
                ax_mat.set_title('Matplotlib Gantt Chart', fontsize=16, fontweight='bold', pad=20)

                # Improve date formatting
                ax_mat.xaxis_date()
                ax_mat.xaxis.set_major_locator(mdates.MonthLocator())
                ax_mat.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
                ax_mat.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
                ax_mat.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
                ax_mat.grid(which='major', axis='x', linestyle='--', alpha=0.7)
                ax_mat.grid(which='minor', axis='x', linestyle=':', alpha=0.5)

                # Rotate date labels for better readability
                plt.setp(ax_mat.get_xticklabels(), rotation=45, ha='right', fontsize=10)

                # Add legends if 'Category' exists
                if 'Category' in df_mat.columns:
                    categories = df_mat['Category'].unique()
                    legend_elements = [Patch(facecolor=color_map[activity], label=activity) for activity in unique_activities]
                    ax_mat.legend(handles=legend_elements, title='Activity', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
                
                # Marking the current date on the chart
                current_date = pd.Timestamp.today()
                ax_mat.axvline(x=current_date, color='red', linestyle='--', linewidth=1.5, label='Today')
                ax_mat.text(current_date + pd.Timedelta(days=1), len(df_mat)-1, current_date.strftime('%d/%m'), color='red', fontsize=10, va='center')

                # Adjust layout for better spacing
                plt.tight_layout()

                # Display the Matplotlib Gantt chart
                st.pyplot(fig_mat)

                # Export Matplotlib chart as image
                buf = BytesIO()
                fig_mat.savefig(buf, format='png', bbox_inches='tight', dpi=300)
                buf.seek(0)
                st.download_button(
                    label="Download Matplotlib Gantt Chart as PNG",
                    data=buf,
                    file_name="gantt_chart_matplotlib.png",
                    mime="image/png",
                )
            except Exception as e:
                st.error(f"Error generating Matplotlib Gantt chart: {e}")

    # Option to download the data
    st.header("8. Download Data")
    csv = st.session_state['data'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='gantt_data.csv',
        mime='text/csv',
    )
