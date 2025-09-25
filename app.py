import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from io import StringIO
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Custom CSS for gradient theme
def apply_gradient_theme():
    st.markdown("""
    <style>
    /* Main gradient background */
    .main .block-container {
        border-radius: 15px;
        margin: 1rem;
    }
    
    /* Gradient header styling */
    .gradient-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .gradient-header h1 {
        color: white;
        text-align: left;
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Gradient cards */
    .gradient-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Gradient buttons */
    .stButton > button {
        background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Gradient text areas */
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 10px;
        color: white;
        backdrop-filter: blur(5px);
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(255,255,255,0.7);
    }
    
    /* Gradient file uploader */
    .stFileUploader > div {
        background: rgba(255,255,255,0.1);
        border: 2px dashed rgba(255,255,255,0.3);
        border-radius: 15px;
        padding: 2rem;
        backdrop-filter: blur(5px);
    }
    
    /* Gradient expander */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(79,172,254,0.3) 0%, rgba(0,242,254,0.2) 100%);
        border-radius: 10px;
        color: white;
    }
    
    /* Gradient success/error messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(76,175,80,0.2) 0%, rgba(76,175,80,0.1) 100%);
        border: 1px solid rgba(76,175,80,0.3);
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(244,67,54,0.2) 0%, rgba(244,67,54,0.1) 100%);
        border: 1px solid rgba(244,67,54,0.3);
        border-radius: 10px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255,152,0,0.2) 0%, rgba(255,152,0,0.1) 100%);
        border: 1px solid rgba(255,152,0,0.3);
        border-radius: 10px;
    }
    
    /* Gradient download button */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Custom text styling */
    .gradient-text {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }
    
    /* Sidebar gradient */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f4c75 0%, #3282b8 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Configure page
st.set_page_config(
    page_title="Retina",
    page_icon="⚡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Gemini API
def initialize_gemini():
    """Initialize Gemini API with API key from environment variable"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        st.error("Please set the GEMINI_API_KEY environment variable")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def parse_file_to_text(file_content, file_type):
    """Parse CSV/XLSX content and convert to readable text format"""
    try:
        if file_type == 'csv':
            # Try to read CSV with different separators
            df = pd.read_csv(StringIO(file_content))
        elif file_type == 'xlsx':
            # Read XLSX file
            df = pd.read_excel(file_content)
        
        # Filter out rows containing "HeartBeat" in any column
        heartbeat_mask = df.astype(str).apply(lambda x: x.str.contains('HeartBeat', case=False, na=False)).any(axis=1)
        filtered_df = df[heartbeat_mask == False]
        
        # Convert DataFrame to text format
        text_content = "OCPP Log Data:\n\n"
        
        # Add column headers
        text_content += "Columns: " + ", ".join(filtered_df.columns.tolist()) + "\n\n"
        
        # Add data rows (excluding HeartBeat rows)
        row_counter = 1
        for index, row in filtered_df.iterrows():
            text_content += f"Row {row_counter}:\n"
            for col in filtered_df.columns:
                text_content += f"  {col}: {row[col]}\n"
            text_content += "\n"
            row_counter += 1
        
        return text_content
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return None

def load_example_logs():
    """Load example OCPP logs from the example CSV file"""
    try:
        with open('example_OCPP_log.csv', 'r') as file:
            return file.read()
    except FileNotFoundError:
        st.error("Example log file not found. Please ensure 'example_OCPP_log.csv' exists in the current directory.")
        return None
    except Exception as e:
        st.error(f"Error loading example logs: {str(e)}")
        return None

def analyze_logs_with_gemini(log_content, model):
    """Send log content to Gemini for analysis"""
    try:
        prompt = f"""You are an expert in analyzing OCPP 1.6 logs.

Task:
Analyze the provided OCPP logs and generate a structured result in the format below.

Result format requirements:

Please provide:
1. Summary of what happened
2. Identified issues and their severity 
3. Root cause analysis
4. Recommended troubleshooting steps 
5. Prevention measures for the future

Log Content:
{log_content}

Important:
- Report only based on the log content.
- If any data is missing, mark it as "0" or "Not found".
- Use clear formatting with proper line breaks and bullet points.
- Structure your response with clear headings and sections.
"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error analyzing logs with Retina : {str(e)}")
        return None

def create_report_content(analysis_result, log_content=None, file_name=None):
    """Create a formatted report content for download"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
Retina LOG ANALYSIS REPORT
Generated on: {timestamp}
{'=' * 50}

"""
    
    if file_name:
        report += f"Source File: {file_name}\n"
    else:
        report += "Source: Text Input\n"
    
    report += f"\n{'=' * 50}\n"
    report += "ANALYSIS RESULTS\n"
    report += f"{'=' * 50}\n\n"
    report += analysis_result
    
    if log_content:
        report += f"\n\n{'=' * 50}\n"
        report += "ORIGINAL LOG CONTENT\n"
        report += f"{'=' * 50}\n\n"
        # Truncate log content if too long for report
        if len(log_content) > 2000:
            report += log_content[:2000] + "\n\n... (Content truncated for report readability)"
        else:
            report += log_content
    
    report += f"\n\n{'=' * 50}\n"
    report += f"Report generated by Retina\n"
    report += f"Timestamp: {timestamp}\n"
    report += f"{'=' * 50}"
    
    return report

def main():
    # Apply gradient theme
    apply_gradient_theme()
    
    # Gradient header
    st.markdown("""
    <div class="gradient-header">
        <h1>Retina ⚡️</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Main description with gradient card
    st.markdown("""
    <div class="gradient-card">
        <p style="color: white; font-size: 1.2rem; text-align: center; margin: 0;">
            Upload CSV files or paste OCPP 1.6 logs to analyze issues and get troubleshooting recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Gemini
    model = initialize_gemini()
    
    # Create two columns for input methods
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="gradient-card">
            <h2 style="color: white; margin-top: 0;">📝 Paste Logs</h2>
        </div>
        """, unsafe_allow_html=True)
        log_text = st.text_area(
            "Paste your OCPP 1.6 logs here:",
            height=300,
            placeholder="Paste your OCPP logs here..."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            analyze_text_btn = st.button("Analyze Pasted Logs", type="primary")
        with col_btn2:
            load_example_btn = st.button("Load Example Logs", type="secondary")
    
    with col2:
        st.markdown("""
        <div class="gradient-card">
            <h2 style="color: white; margin-top: 0;">📁 Upload File</h2>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choose a CSV or XLSX file",
            type=['csv', 'xlsx'],
            help="Upload a CSV or XLSX file containing OCPP log data"
        )
        
        analyze_file_btn = st.button("Analyze File", type="primary")
    
    # Handle example logs loading
    if load_example_btn:
        example_content = load_example_logs()
        if example_content:
            st.session_state.example_logs_loaded = True
            st.session_state.example_logs_content = example_content
            st.success("Example logs loaded successfully!")
    
    # Process text input
    if analyze_text_btn and log_text.strip():
        with st.spinner("Analyzing logs with Gemini..."):
            analysis_result = analyze_logs_with_gemini(log_text, model)
            
            if analysis_result:
                st.markdown("""
                <div class="gradient-card">
                    <h2 style="color: white; margin-top: 0;">📊 Analysis Results</h2>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="gradient-card">
                    <div style="color: white; line-height: 1.6; white-space: pre-wrap;">
                        {analysis_result}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add download button for text analysis
                report_content = create_report_content(analysis_result, log_content=log_text)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"retina_analysis_report_{timestamp}.txt"
                
                st.download_button(
                    label="📥 Download Report",
                    data=report_content,
                    file_name=filename,
                    mime="text/plain",
                    type="primary"
                )
            else:
                st.error("Failed to analyze the logs. Please check your API key and try again.")
    
    # Process file upload
    if analyze_file_btn and uploaded_file is not None:
        try:
            # Determine file type
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'csv':
                # Read CSV content
                file_content = uploaded_file.read().decode('utf-8')
            elif file_type == 'xlsx':
                # For XLSX, we need to pass the file object directly
                file_content = uploaded_file
            
            # Parse file to text
            with st.spinner("Parsing file..."):
                parsed_text = parse_file_to_text(file_content, file_type)
            
            if parsed_text:
                st.success("File parsed successfully!")
                
                # Show preview of parsed content
                with st.expander("Preview Parsed Content"):
                    st.text(parsed_text[:1000] + "..." if len(parsed_text) > 1000 else parsed_text)
                
                # Analyze with Gemini
                with st.spinner("Analyzing logs with Gemini..."):
                    analysis_result = analyze_logs_with_gemini(parsed_text, model)
                
                if analysis_result:
                    st.markdown("""
                    <div class="gradient-card">
                        <h2 style="color: white; margin-top: 0;">📊 Analysis Results</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="gradient-card">
                        <div style="color: white; line-height: 1.6; white-space: pre-wrap;">
                            {analysis_result}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add download button for file analysis
                    report_content = create_report_content(analysis_result, log_content=parsed_text, file_name=uploaded_file.name)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"retina_analysis_report_{timestamp}.txt"
                    
                    st.download_button(
                        label="📥 Download Report",
                        data=report_content,
                        file_name=filename,
                        mime="text/plain",
                        type="primary"
                    )
                else:
                    st.error("Failed to analyze the logs. Please check your API key and try again.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    # Show error messages for empty inputs
    if analyze_text_btn and not log_text.strip():
        st.warning("Please paste some logs before analyzing.")
    
    if analyze_file_btn and uploaded_file is None:
        st.warning("Please upload a file before analyzing.")
    
    # Display example logs if loaded
    if st.session_state.get('example_logs_loaded', False):
        st.markdown("---")
        st.markdown("""
        <div class="gradient-card">
            <h2 style="color: white; margin-top: 0;">📋 Example OCPP Logs</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Show the example logs content
        with st.expander("View Example Logs Content"):
            st.text(st.session_state.example_logs_content)
        
        # Parse and analyze example logs
        col_parse, col_analyze = st.columns(2)
        
        with col_parse:
            if st.button("Parse Example Logs", type="secondary"):
                with st.spinner("Parsing example logs..."):
                    parsed_example = parse_file_to_text(st.session_state.example_logs_content, 'csv')
                    if parsed_example:
                        st.session_state.parsed_example_logs = parsed_example
                        st.success("Example logs parsed successfully!")
        
        with col_analyze:
            if st.button("Analyze Example Logs", type="primary"):
                if st.session_state.get('parsed_example_logs'):
                    with st.spinner("Analyzing example logs with Gemini..."):
                        analysis_result = analyze_logs_with_gemini(st.session_state.parsed_example_logs, model)
                        
                        if analysis_result:
                            st.markdown("""
                            <div class="gradient-card">
                                <h2 style="color: white; margin-top: 0;">📊 Example Logs Analysis Results</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="gradient-card">
                                <div style="color: white; line-height: 1.6; white-space: pre-wrap;">
                                    {analysis_result}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add download button for example logs analysis
                            report_content = create_report_content(analysis_result, log_content=st.session_state.parsed_example_logs, file_name="example_OCPP_log.csv")
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"retina_example_analysis_report_{timestamp}.txt"
                            
                            st.download_button(
                                label="📥 Download Example Report",
                                data=report_content,
                                file_name=filename,
                                mime="text/plain",
                                type="primary"
                            )
                        else:
                            st.error("Failed to analyze the example logs. Please check your API key and try again.")
                else:
                    st.warning("Please parse the example logs first.")
    
    # Add footer with instructions
    st.markdown("---")
    st.markdown("""
    <div class="gradient-card">
        <h3 style="color: white; margin-top: 0;">💡 Instructions</h3>
        <div style="color: white; line-height: 1.8;">
            <ol style="margin: 0; padding-left: 1.5rem;">
                <li><strong>For text logs</strong>: Paste your OCPP 1.6 logs directly into the text area</li>
                <li><strong>For files</strong>: Upload a CSV or XLSX file containing log data</li>
                <li><strong>Example logs</strong>: Click "Load Example Logs" to try the app with sample data</li>
                <li><strong>Analysis</strong>: Click the analyze button to get detailed insights and troubleshooting steps</li>
                <li><strong>Download Report</strong>: After analysis, click "📥 Download Report" to save the results as a text file</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
