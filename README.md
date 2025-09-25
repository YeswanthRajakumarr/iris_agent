# Retina

A Streamlit application that analyzes OCPP 1.6 logs using Google's Gemini 1.5 Flash API to identify issues and provide troubleshooting recommendations.

## Features

- 📝 **Text Log Analysis**: Paste OCPP 1.6 logs directly for analysis
- 📁 **CSV File Upload**: Upload CSV files containing log data
- 🤖 **AI-Powered Analysis**: Uses Gemini 1.5 Flash API for intelligent log analysis
- 🔍 **Comprehensive Reports**: Provides detailed analysis including:
  - Summary of what happened
  - Identified issues and their severity
  - Root cause analysis
  - Recommended troubleshooting steps
  - Prevention measures
- 📥 **Download Reports**: Save analysis results as formatted text files for documentation and sharing

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 3. Set Environment Variable

**On macOS/Linux:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**On Windows:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

### Text Log Analysis
1. Paste your OCPP 1.6 logs into the text area
2. Click "Analyze Pasted Logs"
3. Review the analysis results

### CSV File Analysis
1. Upload a CSV file containing log data
2. Click "Analyze File"
3. Review the parsed content preview
4. Check the analysis results
5. Download the report using the "📥 Download Report" button

## Supported Log Formats

The application can handle:
- Raw OCPP 1.6 log text
- CSV files with log data (automatically parsed to text format)
- Various log formats commonly used in OCPP implementations

## Example OCPP Log Format

```
[2024-01-15 10:30:15] [INFO] Charging station connected: CS001
[2024-01-15 10:30:16] [DEBUG] BootNotification request sent
[2024-01-15 10:30:16] [ERROR] BootNotification failed: InvalidCredentials
[2024-01-15 10:30:17] [WARN] Retrying BootNotification in 5 seconds
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure the `GEMINI_API_KEY` environment variable is set correctly
2. **CSV Parsing Error**: Ensure your CSV file has proper formatting and headers
3. **Analysis Timeout**: Large log files may take longer to process

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Verify your Gemini API key is valid and has sufficient quota
3. Ensure your log format is readable and contains relevant OCPP information

## Dependencies

- `streamlit`: Web application framework
- `pandas`: Data manipulation and CSV parsing
- `google-generativeai`: Google Gemini API client

## License

This project is open source and available under the MIT License.
