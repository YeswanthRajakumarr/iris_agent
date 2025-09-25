import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import logging
import time
from io import StringIO, BytesIO
import json
from datetime import datetime
from dotenv import load_dotenv
import hashlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retina.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 10
REQUEST_TIMEOUT = 60

# Custom CSS for gradient theme
def apply_gradient_theme():
    st.markdown("""
    <style>
    /* Main gradient background */
    .main .block-container {
        border-radius: 7px;
        margin: 1rem;
    }
    
    /* App background */
    .stApp {
        background: black;
        min-height: 100vh;
    }
    
    /* Gradient header styling */
    .gradient-header {
        background: linear-gradient(90deg, #4007CF 0%, #8C1AE7 100%);
        padding: 1rem 2rem;
        border-radius: 7px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px ;
    }
    
    .gradient-header h1 {
        color: white;
        text-align: left;
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    /* Gradient cards */
    .gradient-card {
        background: linear-gradient(135deg, rgba(64,7,207,0.4) 0%, rgba(140,26,231,0.3) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(64,7,207,0.5);
        border-radius: 7px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Gradient buttons */
    .stButton > button {
        background: linear-gradient(45deg, #4007CF 0%, #8C1AE7 100%);
        color: white;
        border: none;
        border-radius: 7px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Secondary button styling (grey) */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(45deg, #808080 0%, #696969 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        background: linear-gradient(45deg, #696969 0%, #555555 100%) !important;
    }
    
    /* Gradient text areas */
    .stTextArea > div > div > textarea {
        background: #ffffff;
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 7px;
        color: black;
        backdrop-filter: blur(5px);
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(0,0,0,0.5);
    }
    
    /* Gradient file uploader */
    .stFileUploader > div {
        background: rgba(255,255,255,0.1);
        border: 2px dashed rgba(255,255,255,0.3);
        border-radius: 7px;
        padding: 2rem;
        backdrop-filter: blur(5px);
    }
    
    /* Gradient expander */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(64,7,207,0.3) 0%, rgba(140,26,231,0.2) 100%);
        border-radius: 7px;
        color: white;
    }
    
    /* Gradient success/error messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(76,175,80,0.2) 0%, rgba(76,175,80,0.1) 100%);
        border: 1px solid rgba(76,175,80,0.3);
        border-radius: 7px;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(244,67,54,0.2) 0%, rgba(244,67,54,0.1) 100%);
        border: 1px solid rgba(244,67,54,0.3);
        border-radius: 7px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255,152,0,0.2) 0%, rgba(255,152,0,0.1) 100%);
        border: 1px solid rgba(255,152,0,0.3);
        border-radius: 7px;
    }
    
    /* Gradient download button */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #8C1AE7 0%, #4007CF 100%);
        color: white;
        border: none;
        border-radius: 7px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Custom text styling */
    .gradient-text {
        background: linear-gradient(45deg, #4007CF, #8C1AE7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }
    
    /* Sidebar gradient */
    .css-1d391kg {
        background: linear-gradient(180deg, #4007CF 0%, #8C1AE7 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Show Streamlit header */
    header {visibility: visible !important;}
    
    /* Ensure labels are visible */
    .stTextArea label,
    .stFileUploader label {
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* Make text in gradient cards more visible */
    .gradient-card h2,
    .gradient-card h3,
    .gradient-card p {
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important;
    }
    
    /* Make main description visible */
    .main .block-container {
        background: transparent;
    }
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
def check_rate_limit():
    """Check if user has exceeded rate limit"""
    if 'request_count' not in st.session_state:
        st.session_state.request_count = 0
        st.session_state.last_reset = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_reset > 60:  # Reset every minute
        st.session_state.request_count = 0
        st.session_state.last_reset = current_time
    
    if st.session_state.request_count >= MAX_REQUESTS_PER_MINUTE:
        st.error("⚠️ Rate limit exceeded. Please wait a moment before trying again.")
        logger.warning(f"Rate limit exceeded for session")
        return False
    
    st.session_state.request_count += 1
    return True

def initialize_gemini():
    """Initialize Gemini API with API key from environment variable"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        st.error("⚠️ Service temporarily unavailable. Please try again later.")
        st.stop()
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API initialized successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
        st.error("⚠️ Service temporarily unavailable. Please try again later.")
        st.stop()

def validate_file_size(file_content):
    """Validate file size for security"""
    max_size = 10 * 1024 * 1024  # 10MB limit
    if len(file_content) > max_size:
        logger.warning(f"File size exceeded limit: {len(file_content)} bytes")
        return False
    return True

def sanitize_input(text):
    """Sanitize input to prevent injection attacks"""
    # Only check for actual script tags, not common OCPP terms
    dangerous_patterns = ['<script>', 'javascript:', 'vbscript:']
    for pattern in dangerous_patterns:
        if pattern.lower() in text.lower():
            logger.warning(f"Potentially dangerous content detected: {pattern}")
            return False
    return True

def parse_file_to_text(file_content, file_type):
    """Parse CSV/XLSX content and convert to readable text format"""
    try:
        # Validate file size
        if not validate_file_size(file_content):
            st.error("⚠️ File too large. Please upload a file smaller than 10MB.")
            return None
        
        logger.info(f"Processing {file_type} file of size: {len(file_content)} bytes")
        
        if file_type == 'csv':
            # Try to read CSV with different separators
            df = pd.read_csv(StringIO(file_content))
        elif file_type == 'xlsx':
            # Read XLSX file
            df = pd.read_excel(file_content)
        
        # Limit number of rows for performance
        if len(df) > 10000:
            df = df.head(10000)
            logger.info("DataFrame truncated to 10,000 rows for performance")
        
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
        
        logger.info(f"Successfully parsed file with {len(filtered_df)} rows")
        return text_content
    except Exception as e:
        logger.error(f"Error parsing file: {str(e)}")
        st.error("⚠️ Error processing file. Please check the file format and try again.")
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

def highlight_key_elements(text):
    """Highlight Transaction IDs, timestamps, and errors in the analysis text"""
    import re
    
    # Highlight Transaction IDs (various formats) - using Streamlit markdown syntax
    text = re.sub(r'\b(transactionId|TransactionId|transaction_id|Transaction ID)\s*:?\s*(\d+)\b', 
                  r'**`\1: \2`**', 
                  text, flags=re.IGNORECASE)
    
    # Highlight timestamps (various formats)
    text = re.sub(r'\b(\d{1,2}:\d{2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*(?:IST|UTC|GMT)?)\b', 
                  r'**`\1`**', 
                  text)
    
    # Highlight dates
    text = re.sub(r'\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b', 
                  r'**`\1`**', 
                  text)
    
    # Highlight errors (various error patterns) - using red highlighting
    error_patterns = [
        r'\b(ERROR|Error|error|FAILED|Failed|failed|REJECTED|Rejected|rejected|TIMEOUT|Timeout|timeout)\b',
        r'\b(NotImplemented|NOT_IMPLEMENTED|not_implemented)\b',
        r'\b(AuthorizationFailed|AUTHORIZATION_FAILED|authorization_failed)\b',
        r'\b(ConnectorUnavailable|CONNECTOR_UNAVAILABLE|connector_unavailable)\b',
        r'\b(InternalError|INTERNAL_ERROR|internal_error)\b'
    ]
    
    for pattern in error_patterns:
        text = re.sub(pattern, 
                      r'**`\1`**', 
                      text)
    
    return text

def analyze_logs_with_gemini(log_content, model):
    """Send log content to Gemini for analysis"""
    try:
        # Check rate limit
        if not check_rate_limit():
            return None
        
        # Sanitize input (with debug info) - TEMPORARILY DISABLED FOR DEBUGGING
        # if not sanitize_input(log_content):
        #     logger.warning(f"Input sanitization failed for content: {log_content[:100]}...")
        #     st.error("⚠️ Invalid content detected. Please check your input.")
        #     return None
        
        # Limit log content size for production
        if len(log_content) > 50000:  # 50KB limit
            log_content = log_content[:50000] + "\n\n... (Content truncated for processing)"
            logger.info("Log content truncated to 50KB")
        
        logger.info(f"Starting analysis for content of size: {len(log_content)} characters")
        
        prompt = f"""You are an expert in analyzing OCPP 1.6 logs.

Task:
Analyze the provided OCPP logs and generate both a structured summary table and detailed analysis.

REQUIRED OUTPUT FORMAT:

**PART 1: SUMMARY TABLE**
Provide the following metrics in this exact format:

| Metric | Value |
|--------|-------|
| Total Sessions | [number] |
| Successful Sessions | [number] |
| Failed Sessions | [number] |
| Total Energy Delivered (kWh) | [number] |
| Pre-charging Failures | [number] |

**PART 2: DETAILED ANALYSIS**
Then provide:
1. Summary of what happened
2. Identified issues and their severity 
3. Root cause analysis
4. Recommended troubleshooting steps 
5. Prevention measures for the future

DEFINITIONS:
- Successful Sessions: Sessions that ended normally (including user-requested stop)
- Failed Sessions: Sessions that ended due to error, abnormal stop, or EV disconnection
- Total Energy Delivered: Sum of energy reported across all successful sessions
- Pre-charging Failures: Sessions that failed before energy delivery started (authorization failed, connector not available, EV disconnected before charging)

Log Content:
{log_content}

Important:
- Report only based on the log content.
- Focus more on charging sessions, Don't leave any Data
- If any data is missing, mark it as "0" or "Not found".
- Use clear formatting with proper line breaks and bullet points.
- Structure your response with clear headings and sections.
- When mentioning Transaction IDs, timestamps, or errors, be specific and clear.
"""
        
        # Add timeout for production
        start_time = time.time()
        response = model.generate_content(prompt)
        end_time = time.time()
        
        logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
        
        # Apply highlighting to the response
        highlighted_text = highlight_key_elements(response.text)
        return highlighted_text
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        st.error("⚠️ Analysis service temporarily unavailable. Please try again later.")
        return None

def extract_summary_table(analysis_result):
    """Extract summary table from analysis result"""
    try:
        lines = analysis_result.split('\n')
        table_data = {}
        
        for line in lines:
            if '|' in line and 'Total Sessions' in line:
                # Found the table, extract values
                for i, table_line in enumerate(lines):
                    if '|' in table_line and 'Total Sessions' in table_line:
                        # Extract Total Sessions
                        parts = table_line.split('|')
                        if len(parts) >= 3:
                            table_data['Total Sessions'] = parts[2].strip()
                    elif '|' in table_line and 'Successful Sessions' in table_line:
                        parts = table_line.split('|')
                        if len(parts) >= 3:
                            table_data['Successful Sessions'] = parts[2].strip()
                    elif '|' in table_line and 'Failed Sessions' in table_line:
                        parts = table_line.split('|')
                        if len(parts) >= 3:
                            table_data['Failed Sessions'] = parts[2].strip()
                    elif '|' in table_line and 'Total Energy Delivered' in table_line:
                        parts = table_line.split('|')
                        if len(parts) >= 3:
                            table_data['Total Energy Delivered (kWh)'] = parts[2].strip()
                    elif '|' in table_line and 'Pre-charging Failures' in table_line:
                        parts = table_line.split('|')
                        if len(parts) >= 3:
                            table_data['Pre-charging Failures'] = parts[2].strip()
        
        return table_data
    except Exception as e:
        logger.error(f"Error extracting summary table: {str(e)}")
        return {}

def create_pdf_report(analysis_result, log_content=None, file_name=None):
    """Create a PDF report for download"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a BytesIO buffer to hold the PDF
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#4007CF')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#8C1AE7')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Build the content
    story = []
    
    # Title
    story.append(Paragraph("Iris.agent LOG ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 12))
    
    # Report info
    story.append(Paragraph(f"Generated on: {timestamp}", normal_style))
    story.append(Spacer(1, 12))
    
    if file_name:
        story.append(Paragraph(f"Source File: {file_name}", normal_style))
    else:
        story.append(Paragraph("Source: Text Input", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Analysis Results
    story.append(Paragraph("ANALYSIS RESULTS", heading_style))
    story.append(Spacer(1, 12))
    
    # Parse analysis result and add as paragraphs
    analysis_lines = analysis_result.split('\n')
    for line in analysis_lines:
        if line.strip():
            # Handle markdown formatting
            if line.startswith('**') and line.endswith('**'):
                # Bold text
                text = line[2:-2]
                story.append(Paragraph(f"<b>{text}</b>", normal_style))
            elif line.startswith('|') and '|' in line[1:]:
                # Table row - skip for now, could be enhanced later
                continue
            else:
                story.append(Paragraph(line, normal_style))
        else:
            story.append(Spacer(1, 6))
    
    # Add original log content if provided
    if log_content:
        story.append(Spacer(1, 20))
        story.append(Paragraph("ORIGINAL LOG CONTENT", heading_style))
        story.append(Spacer(1, 12))
        
        # Truncate log content if too long
        if len(log_content) > 2000:
            log_preview = log_content[:2000] + "\n\n... (Content truncated for report readability)"
        else:
            log_preview = log_content
        
        # Split into paragraphs for better formatting
        log_lines = log_preview.split('\n')
        for line in log_lines[:50]:  # Limit to first 50 lines
            if line.strip():
                story.append(Paragraph(line, normal_style))
            else:
                story.append(Spacer(1, 3))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Report generated by Iris.agent", normal_style))
    story.append(Paragraph(f"Timestamp: {timestamp}", normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get the PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def create_report_content(analysis_result, log_content=None, file_name=None):
    """Create a formatted report content for download (legacy text format)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
Iris.agent LOG ANALYSIS REPORT
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
    report += f"Report generated by Iris.agent\n"
    report += f"Timestamp: {timestamp}\n"
    report += f"{'=' * 50}"
    
    return report

def main():
    # Apply gradient theme
    apply_gradient_theme()
    
    # Add health check
    if st.query_params.get("health") == "check":
        st.json({"status": "healthy", "timestamp": datetime.now().isoformat()})
        return
    
    # Logo display in top-left corner
    col1, col2 = st.columns([1, 4])
    with col1:
        # Try to display logo
        try:
            st.image("Iris_agent_logo.png", width=120)
        except:
            st.markdown("""
            <h1 style="color: white; margin: 0; font-size: 2rem;">Retina ⚡️</h1>
            """, unsafe_allow_html=True)
    
    # Main content area - focused on results
    st.markdown("""
    <div class="gradient-card">
        <h2 style="color: #ffffff; text-align: center; margin: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
            Welcome to Iris.agent ⚡️
        </h2>
        <p style="color: #ffffff; font-size: 1.2rem; text-align: center; margin: 1rem 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
            OCPP Log Analysis & Troubleshooting Platform
        </p>
        <p style="color: #ffffff; text-align: center; margin: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
            Use the sidebar to input your logs and get detailed analysis results here.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Gemini
    model = initialize_gemini()
    
    # Initialize button variables
    analyze_text_btn = False
    analyze_file_btn = False
    analyze_example_btn = False
    load_example_btn = False
    parse_example_btn = False
    
    # Sidebar for choosing input method
    with st.sidebar:
        st.markdown("### 📝 Choose Input Method")
        
        # Initialize session state for selected method
        if 'selected_input_method' not in st.session_state:
            st.session_state.selected_input_method = 'paste'
        
        # Input method selection
        input_method = st.radio(
            "Select how you want to provide your OCPP logs:",
            ["📝 Paste Logs", "📁 Upload File", "📋 Example Logs"],
            key="input_method_radio"
        )
        
        # Update session state immediately when selection changes
        if input_method != st.session_state.get('selected_input_method'):
            st.session_state.selected_input_method = input_method
            st.rerun()
    
    # Initialize other variables
    log_text = ""
    uploaded_file = None
    
    # Main area for input controls based on selection
    if input_method == "📝 Paste Logs":
        st.markdown("### 📝 Paste Your OCPP Logs")
        log_text = st.text_area(
            "Paste your OCPP 1.6 logs here",
            height=300,
            key="log_text_area",
            help="Paste your OCPP 1.6 logs directly into this text area"
        )
        analyze_text_btn = st.button("Analyze Pasted Logs", type="primary")
        
    elif input_method == "📁 Upload File":
        st.markdown("### 📁 Upload File")
        uploaded_file = st.file_uploader(
            "Choose a CSV or XLSX file",
            type=['csv', 'xlsx'],
            help="Upload a CSV or XLSX file containing OCPP log data"
        )
        analyze_file_btn = st.button("Analyze File", type="primary")
        
    elif input_method == "📋 Example Logs":
        st.markdown("### 📋 Example Logs")
        st.markdown("Try the app with sample OCPP log data")
        
        col_load, col_parse, col_analyze = st.columns(3)
        
        with col_load:
            load_example_btn = st.button("Load Example Logs", type="secondary")
        
        with col_parse:
            parse_example_btn = st.button("Parse Example Logs", type="secondary")
        
        with col_analyze:
            analyze_example_btn = st.button("Analyze Example Logs", type="primary")
    
    # Handle example logs loading
    if load_example_btn:
        example_content = load_example_logs()
        if example_content:
            st.session_state.example_logs_loaded = True
            st.session_state.example_logs_content = example_content
            st.success("Example logs loaded successfully!")
            st.rerun()
    
    # Handle example logs parsing
    if parse_example_btn:
        if st.session_state.get('example_logs_content'):
            with st.spinner("Parsing example logs..."):
                parsed_example = parse_file_to_text(st.session_state.example_logs_content, 'csv')
                if parsed_example:
                    st.session_state.parsed_example_logs = parsed_example
                    st.success("Example logs parsed successfully!")
        else:
            st.warning("Please load example logs first.")
    
    # Handle example logs analysis
    if analyze_example_btn:
        if st.session_state.get('parsed_example_logs'):
            with st.spinner("Analyzing example logs..."):
                analysis_result = analyze_logs_with_gemini(st.session_state.parsed_example_logs, model)
                
                if analysis_result:
                    # Extract and display summary table
                    summary_data = extract_summary_table(analysis_result)
                    if summary_data:
                        st.markdown("### 📈 Session Summary")
                        df_summary = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
                        st.dataframe(df_summary, use_container_width=True, hide_index=True)
                    
                    st.markdown("### 📊 Detailed Analysis")
                    st.markdown(analysis_result)
                    
                    # Add download button for example logs analysis
                    pdf_content = create_pdf_report(analysis_result, log_content=st.session_state.parsed_example_logs, file_name="example_OCPP_log.csv")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"iris_agent_example_analysis_report_{timestamp}.pdf"
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Failed to analyze the example logs. Please check your API key and try again.")
        else:
            st.warning("Please parse the example logs first.")
    
    # Process text input
    if analyze_text_btn and log_text.strip():
        with st.spinner("Analyzing logs..."):
            analysis_result = analyze_logs_with_gemini(log_text, model)
            
            if analysis_result:
                # Extract and display summary table
                summary_data = extract_summary_table(analysis_result)
                if summary_data:
                    st.markdown("### 📈 Session Summary")
                    df_summary = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
                    st.dataframe(df_summary, use_container_width=True, hide_index=True)
                
                st.markdown("### 📊 Detailed Analysis")
                st.markdown(analysis_result)
                
                # Add download button for text analysis
                pdf_content = create_pdf_report(analysis_result, log_content=log_text)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"iris_agent_analysis_report_{timestamp}.pdf"
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_content,
                    file_name=filename,
                    mime="application/pdf",
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
                with st.spinner("Analyzing logs..."):
                    analysis_result = analyze_logs_with_gemini(parsed_text, model)
                
                if analysis_result:
                    # Extract and display summary table
                    summary_data = extract_summary_table(analysis_result)
                    if summary_data:
                        st.markdown("### 📈 Session Summary")
                        df_summary = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
                        st.dataframe(df_summary, use_container_width=True, hide_index=True)
                    
                    st.markdown("### 📊 Detailed Analysis")
                    st.markdown(analysis_result)
                    
                    # Add download button for file analysis
                    pdf_content = create_pdf_report(analysis_result, log_content=parsed_text, file_name=uploaded_file.name)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"iris_agent_analysis_report_{timestamp}.pdf"
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf",
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
    
    # Display example logs content if loaded
    if st.session_state.get('example_logs_loaded', False):
        st.markdown("---")
        st.markdown("""
        <div class="gradient-card">
            <h2 style="color: #ffffff; margin-top: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">📋 Example OCPP Logs Content</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Show the example logs content
        with st.expander("View Example Logs Content"):
            st.text(st.session_state.example_logs_content)
    

if __name__ == "__main__":
    main()
