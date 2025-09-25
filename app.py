import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


from src.config import config
from src.models import LogFile, AnalysisResult
from src.services import FileProcessor, RateLimiter
from src.services.model_provider import ModelProviderFactory, ModelProviderType
from src.utils import (
    setup_logging,
    get_logger,
    ConfigurationError,
    APIError,
    RateLimitError,
    FileProcessingError,
    SecurityError,
    AnalysisError
)

# Setup logging
setup_logging(
    level=config.log_level,
    log_file=config.log_file
)
logger = get_logger(__name__)


class IrisAgentApp:
    """Main application class for Iris.agent."""
    
    def __init__(self):
        """Initialize the application."""
        self.file_processor = FileProcessor(
            max_file_size_mb=config.max_file_size_mb,
            max_dataframe_rows=config.max_dataframe_rows
        )
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=config.max_requests_per_minute
        )
        self.model_provider = None
        self._initialize_model_provider()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available without initializing the service."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_available_ollama_models(self) -> list:
        """Get list of available Ollama models."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception:
            return []
    
    def _initialize_model_provider(self) -> None:
        """Initialize model provider based on configuration."""
        try:
            logger.info(f"Initializing model provider: {config.model_provider}")
            
            if config.model_provider.lower() == "gemini":
                if not config.gemini_api_key:
                    raise ConfigurationError("GEMINI_API_KEY not found in environment variables")
                
                self.model_provider = ModelProviderFactory.create_provider(
                    ModelProviderType.GEMINI,
                    api_key=config.gemini_api_key,
                    max_requests_per_minute=config.max_requests_per_minute
                )
                logger.info("Gemini service initialized successfully")
                
            elif config.model_provider.lower() == "ollama":
                # Check if we're in a cloud environment
                is_cloud_env = (
                    os.getenv('STREAMLIT_CLOUD') or 
                    os.getenv('STREAMLIT_SHARING_MODE') or
                    os.getenv('STREAMLIT_SERVER_PORT') == '8501' or  # Default Streamlit Cloud port
                    'streamlit' in os.getenv('PATH', '').lower() or  # Streamlit in PATH
                    os.path.exists('/app')  # Streamlit Cloud app directory
                )
                if is_cloud_env:
                    logger.warning("Ollama not available in cloud environment, falling back to Gemini")
                    if not config.gemini_api_key:
                        raise ConfigurationError("GEMINI_API_KEY not found in environment variables for cloud deployment")
                    
                    self.model_provider = ModelProviderFactory.create_provider(
                        ModelProviderType.GEMINI,
                        api_key=config.gemini_api_key,
                        max_requests_per_minute=config.max_requests_per_minute
                    )
                    logger.info("Gemini service initialized successfully (fallback from Ollama)")
                else:
                    self.model_provider = ModelProviderFactory.create_provider(
                        ModelProviderType.OLLAMA,
                        base_url=config.ollama_base_url,
                        model_name=config.ollama_model_name,
                        max_requests_per_minute=config.max_requests_per_minute
                    )
                    logger.info("Ollama service initialized successfully")
                
            else:
                raise ConfigurationError(f"Unsupported model provider: {config.model_provider}")
            
        except Exception as e:
            logger.error(f"Failed to initialize model provider: {str(e)}")
            # Don't stop the app, just show error and continue
            st.error("⚠️ Service temporarily unavailable. Please try again later.")
            # Set a fallback provider
            self.model_provider = None
    
    def run(self) -> None:
        """Run the main application."""
        # Configure page
        st.set_page_config(
            page_title=config.app_title,
            page_icon=config.app_icon,
            # layout=config.page_layout,
            layout="wide",
            initial_sidebar_state=config.sidebar_state
        )
        
        # Apply theme
        self._apply_gradient_theme()
        
        # Health check
        if st.query_params.get("health") == "check":
            st.json({"status": "healthy", "timestamp": datetime.now().isoformat()})
            return
        
        # Main UI
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
    
    def _apply_gradient_theme(self) -> None:
        """Apply gradient theme styling."""
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
            box-shadow: 0 4px 15px;
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
        
        /* Secondary button styling */
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
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: visible !important;}
        
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
        
        /* Increase sidebar width */
        .stSidebar {
            width: 450px !important;
        }
        
        /* Adjust main content area to accommodate wider sidebar */
        .main .block-container {
            margin-left: 420px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_header(self) -> None:
        """Render the application header."""
        # Logo display
        col1, col2 = st.columns([1, 4])
        with col1:
            try:
                # Check if logo file exists
                if os.path.exists(config.app_icon):
                    st.image(config.app_icon, width=120)
                else:
                    # Fallback to text logo if image not found
                    st.markdown("""
                    <h1 style="color: white; margin: 0; font-size: 2rem;">Iris ⚡️</h1>
                    """, unsafe_allow_html=True)
            except Exception as e:
                logger.warning(f"Could not load logo image: {str(e)}")
                # Fallback to text logo
                st.markdown("""
                <h1 style="color: white; margin: 0; font-size: 2rem;">Iris ⚡️</h1>
                """, unsafe_allow_html=True)
        
        # Main content area
        st.markdown("""
        <div class="gradient-card">
            <h2 style="color: #ffffff; text-align: center; margin: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
                Welcome to Iris.agent ⚡️
            </h2>
            <p style="color: #ffffff; font-size: 1.2rem; text-align: center; margin: 1rem 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
                OCPP Log Analysis & Troubleshooting Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Info message
        st.info("💡 **For optimal analysis results, upload focused data such as a single charging session, specific transaction logs, or one day's worth of charger data rather than large multi-day files**")
    
    def _render_sidebar(self) -> None:
        """Render the sidebar."""
        with st.sidebar:
            st.markdown("### 🤖 Model Provider")
            
            # Initialize model provider selection
            if 'selected_model_provider' not in st.session_state:
                st.session_state.selected_model_provider = config.model_provider
            
            # Model provider selection
            # Check if we're in cloud environment
            is_cloud_env = (
                os.getenv('STREAMLIT_CLOUD') or 
                os.getenv('STREAMLIT_SHARING_MODE') or
                os.getenv('STREAMLIT_SERVER_PORT') == '8501' or  # Default Streamlit Cloud port
                'streamlit' in os.getenv('PATH', '').lower() or  # Streamlit in PATH
                os.path.exists('/app')  # Streamlit Cloud app directory
            )
            
            if is_cloud_env:
                # In cloud environment, show both options but indicate cloud limitation
                st.info("🌐 **Cloud Environment**: Both options available, but local models will fallback to Gemini")
                model_provider = st.radio(
                    "Choose AI Model Provider:", ["🤖 Third-party LLM", "🚀 Iris.ai (Local)"],
                    index= 0 if config.model_provider.lower() == "gemini" else 1,
                    key="model_provider_radio",
                    help="Select between cloud-based LLM or local Iris.ai models (local will fallback to Gemini in cloud)"
                )
            else:
                # In local environment, always show both options
                ollama_available = self._check_ollama_availability()
                
                if ollama_available:
                    # Show both options normally
                    model_provider = st.radio(
                        "Choose AI Model Provider:", ["🤖 Third-party LLM", "🚀 Iris.ai (Local)"],
                        index= 0 if config.model_provider.lower() == "gemini" else 1,
                        key="model_provider_radio",
                        help="Select between cloud-based LLM or local Iris.ai models"
                    )
                else:
                    # Show both options but with warning about local availability
                    st.warning("⚠️ Local Models are not available right now. You can still select them, but they will fallback to Cloud LLM.")
                    model_provider = st.radio(
                        "Choose AI Model Provider:", ["🤖 Third-party LLM", "🚀 Iris.ai (Local)"],
                        index= 0 if config.model_provider.lower() == "gemini" else 1,
                        key="model_provider_radio",
                        help="Select between cloud-based LLM or local Iris.ai models (local will fallback to Gemini if unavailable)"
                    )
            
            # Update session state and config
            selected_provider = "gemini" if model_provider == "🤖 Third-party LLM" else "ollama"
            if selected_provider != st.session_state.get('selected_model_provider'):
                st.session_state.selected_model_provider = selected_provider
                config.model_provider = selected_provider
                # Reinitialize model provider with error handling
                try:
                    self._initialize_model_provider()
                    if self.model_provider:  # Only rerun if initialization was successful
                        st.rerun()
                    else:
                        st.error("⚠️ Model provider initialization failed. Please try again.")
                except Exception as e:
                    logger.error(f"Failed to switch to {selected_provider}: {str(e)}")
                    if selected_provider == "ollama":
                        if is_cloud_env:
                            st.info("ℹ️ Ollama selected but not available in cloud environment. Using Gemini instead.")
                        else:
                            st.warning("⚠️ Ollama is not available locally. Using Gemini instead.")
                        # Keep the selection but use gemini
                        config.model_provider = "gemini"
                        st.session_state.selected_model_provider = "gemini"
                        try:
                            self._initialize_model_provider()
                            if self.model_provider:
                                st.rerun()
                            else:
                                st.error("⚠️ Service temporarily unavailable. Please try again later.")
                        except Exception as gemini_error:
                            logger.error(f"Failed to initialize Gemini fallback: {str(gemini_error)}")
                            st.error("⚠️ Service temporarily unavailable. Please try again later.")
                    elif selected_provider == "gemini":
                        # Gemini initialization failed
                        st.error("⚠️ Failed to initialize Gemini. Please check your API key and try again.")
                        # Revert to previous provider
                        previous_provider = "ollama" if st.session_state.get('selected_model_provider') == "gemini" else "gemini"
                        config.model_provider = previous_provider
                        st.session_state.selected_model_provider = previous_provider
                        st.rerun()
                    else:
                        st.error(f"⚠️ Failed to initialize {selected_provider}. Please try again.")
            
            # Show current provider info
            if self.model_provider:
                provider_name = self.model_provider.get_provider_name()
                
                # Check if there's a mismatch between selection and actual provider
                selected_provider = "gemini" if model_provider == "🤖 Third-party LLM" else "ollama"
                actual_provider = "gemini" if "Gemini" in provider_name else "ollama"
                
                if selected_provider == "ollama" and actual_provider == "gemini":
                    # User selected Ollama but we're using Gemini (fallback)
                    if is_cloud_env:
                        st.info(f"✅ Using: {provider_name} (Ollama selected but not available in cloud)")
                    else:
                        st.warning(f"⚠️ Using: {provider_name} (Ollama selected but not available locally)")
                else:
                    # Normal case - using what was selected
                    st.info(f"✅ Using: {provider_name}")
                
                # Show available models if using Ollama
                if "Ollama" in provider_name and not is_cloud_env:
                    available_models = self._get_available_ollama_models()
                    if available_models:
                        with st.expander("📋 Available Ollama Models"):
                            for model in available_models:
                                st.text(f"• {model}")
                            st.caption("💡 To use a different model, update the OLLAMA_MODEL_NAME environment variable")
            else:
                # No model provider available - show retry option
                st.error("⚠️ No model provider available")
                if st.button("🔄 Retry Model Initialization", type="secondary"):
                    try:
                        self._initialize_model_provider()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Retry failed: {str(e)}")
            
            st.markdown("---")
            st.markdown("### 📝 Choose Input Method")
            
            # Initialize session state
            if 'selected_input_method' not in st.session_state:
                st.session_state.selected_input_method = 'paste'
            
            # Input method selection
            input_method = st.radio(
                "Select how you want to provide your OCPP logs:",
                ["📝 Paste Logs", "📁 Upload File", "📋 Example Logs"],
                key="input_method_radio"
            )
            
            # Update session state
            if input_method != st.session_state.get('selected_input_method'):
                st.session_state.selected_input_method = input_method
                st.rerun()
            
            # Log filtering options
            st.markdown("---")
            st.markdown("### 🔧 Log Filtering Options")
            
            # Initialize filtering preference
            if 'use_iris_cms_filtering' not in st.session_state:
                st.session_state.use_iris_cms_filtering = False
            
            # Checkbox for Iris CMS logs filtering
            use_iris_cms_filtering = st.checkbox(
                "**Use `Iris CMS` Log Filtering**",
                value=st.session_state.use_iris_cms_filtering,
                help="Enable this option if you are using Iris CMS logs for better results",
                key="iris_cms_filtering_checkbox"
            )
            
            # Update session state
            st.session_state.use_iris_cms_filtering = use_iris_cms_filtering
    
    def _render_main_content(self) -> None:
        """Render the main content area."""
        input_method = st.session_state.get('selected_input_method', 'paste')
        
        if input_method == "📝 Paste Logs":
            self._render_text_input()
        elif input_method == "📁 Upload File":
            self._render_file_upload()
        elif input_method == "📋 Example Logs":
            self._render_example_logs()
    
    def _render_text_input(self) -> None:
        """Render text input interface."""
        st.markdown("### 📝 Paste Your OCPP Logs")
        log_text = st.text_area(
            "Paste your OCPP 1.6 logs here",
            height=300,
            key="log_text_area",
            help="Paste your OCPP 1.6 logs directly into this text area"
        )
        
        if st.button("Analyze Pasted Logs", type="primary"):
            if log_text.strip():
                self._analyze_text(log_text)
            else:
                st.warning("Please paste some logs before analyzing.")
    
    def _render_file_upload(self) -> None:
        """Render file upload interface."""
        st.markdown("### 📁 Upload File")
        uploaded_file = st.file_uploader(
            "Choose a CSV or XLSX file",
            type=['csv', 'xlsx'],
            help="Upload a CSV or XLSX file containing OCPP log data"
        )
        
        if st.button("Analyze File", type="primary"):
            if uploaded_file is not None:
                self._analyze_file(uploaded_file)
            else:
                st.warning("Please upload a file before analyzing.")
    
    def _render_example_logs(self) -> None:
        """Render example logs interface."""
        st.markdown("### 📋 Example Logs")
        st.markdown("Try the app with sample OCPP log data")
        
        col_load, col_parse, col_analyze = st.columns(3)
        
        with col_load:
            if st.button("Load Example Logs", type="secondary"):
                self._load_example_logs()
        
        with col_parse:
            if st.button("Parse Example Logs", type="secondary"):
                self._parse_example_logs()
        
        with col_analyze:
            if st.button("Analyze Example Logs", type="primary"):
                self._analyze_example_logs()
        
        # Display example logs content if loaded
        if st.session_state.get('example_logs_loaded', False):
            st.markdown("---")
            st.markdown("""
            <div class="gradient-card">
                <h2 style="color: #ffffff; margin-top: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">📋 Example OCPP Logs Content</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Example Logs Content"):
                st.text(st.session_state.example_logs_content)
    
    def _analyze_text(self, log_text: str) -> None:
        """Analyze text input."""
        if not self.model_provider:
            st.error("⚠️ Model provider is not available. Please try switching models or refresh the page.")
            return
            
        try:
            with st.spinner("Analyzing logs..."):
                # Check rate limit
                self.rate_limiter.check_rate_limit()
                
                # Analyze with selected model provider
                analysis_result = self.model_provider.analyze_logs(
                    log_text, 
                    max_content_size_kb=config.max_log_content_size_kb
                )
                
                self._display_analysis_result(analysis_result, log_text)
                
        except RateLimitError as e:
            st.error(f"⚠️ {str(e)}")
        except (APIError, AnalysisError) as e:
            logger.error(f"Analysis error (hidden from user): {str(e)}")
            st.error("⚠️ Analysis service is temporarily unavailable. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error in text analysis: {str(e)}")
            st.error("⚠️ An unexpected error occurred. Please try again.")
    
    def _analyze_file(self, uploaded_file) -> None:
        """Analyze uploaded file."""
        if not self.model_provider:
            st.error("⚠️ Model provider is not available. Please try switching models or refresh the page.")
            return
            
        try:
            # Determine file type
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            # Create log file object
            if file_type == 'csv':
                file_content = uploaded_file.read().decode('utf-8')
            elif file_type == 'xlsx':
                file_content = uploaded_file
            else:
                st.error("Unsupported file type. Please upload CSV or XLSX files.")
                return
            
            log_file = LogFile(
                filename=uploaded_file.name,
                content=file_content,
                file_type=file_type,
                size_bytes=len(file_content) if isinstance(file_content, str) else len(file_content.read())
            )
            
            # Parse file
            with st.spinner("Parsing file..."):
                parsed_text = self.file_processor.parse_file_to_text(
                    log_file, 
                    use_iris_cms_filtering=st.session_state.get('use_iris_cms_filtering', False)
                )
            
            if parsed_text:
                st.success("File parsed successfully!")
                
                # Show preview
                with st.expander("Preview Parsed Content"):
                    st.markdown("""
                    <div style="max-height: 400px; overflow-y: auto; background-color: black; padding: 10px; border-radius: 5px; border: 1px solid #ccc;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0; font-family: monospace; font-size: 12px;">{}</pre>
                    </div>
                    """.format(parsed_text), unsafe_allow_html=True)
                
                # Analyze
                with st.spinner("Analyzing logs..."):
                    # Check rate limit
                    self.rate_limiter.check_rate_limit()
                    
                    analysis_result = self.model_provider.analyze_logs(
                        parsed_text,
                        max_content_size_kb=config.max_log_content_size_kb
                    )
                    
                    self._display_analysis_result(analysis_result, parsed_text, uploaded_file.name)
            
        except (FileProcessingError, SecurityError) as e:
            st.error(f"⚠️ {str(e)}")
        except RateLimitError as e:
            st.error(f"⚠️ {str(e)}")
        except (APIError, AnalysisError) as e:
            logger.error(f"Analysis error (hidden from user): {str(e)}")
            st.error("⚠️ Analysis service is temporarily unavailable. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error in file analysis: {str(e)}")
            st.error("⚠️ An unexpected error occurred. Please try again.")
    
    def _load_example_logs(self) -> None:
        """Load example logs from file."""
        try:
            with open('example_OCPP_log.csv', 'r') as file:
                content = file.read()
                st.session_state.example_logs_loaded = True
                st.session_state.example_logs_content = content
                st.success("Example logs loaded successfully!")
                st.rerun()
        except FileNotFoundError:
            st.error("Example log file not found. Please ensure 'example_OCPP_log.csv' exists in the current directory.")
        except Exception as e:
            st.error(f"Error loading example logs: {str(e)}")
    
    def _parse_example_logs(self) -> None:
        """Parse example logs."""
        if st.session_state.get('example_logs_content'):
            try:
                with st.spinner("Parsing example logs..."):
                    log_file = LogFile(
                        filename="example_OCPP_log.csv",
                        content=st.session_state.example_logs_content,
                        file_type="csv",
                        size_bytes=len(st.session_state.example_logs_content)
                    )
                    
                    parsed_example = self.file_processor.parse_file_to_text(
                        log_file,
                        use_iris_cms_filtering=st.session_state.get('use_iris_cms_filtering', False)
                    )
                    if parsed_example:
                        st.session_state.parsed_example_logs = parsed_example
                        st.success("Example logs parsed successfully!")
            except Exception as e:
                st.error(f"Error parsing example logs: {str(e)}")
        else:
            st.warning("Please load example logs first.")
    
    def _analyze_example_logs(self) -> None:
        """Analyze example logs."""
        if not self.model_provider:
            st.error("⚠️ Model provider is not available. Please try switching models or refresh the page.")
            return
            
        if st.session_state.get('parsed_example_logs'):
            try:
                with st.spinner("Analyzing example logs..."):
                    # Check rate limit
                    self.rate_limiter.check_rate_limit()
                    
                    analysis_result = self.model_provider.analyze_logs(
                        st.session_state.parsed_example_logs,
                        max_content_size_kb=config.max_log_content_size_kb
                    )
                    
                    self._display_analysis_result(
                        analysis_result, 
                        st.session_state.parsed_example_logs, 
                        "example_OCPP_log.csv"
                    )
            except RateLimitError as e:
                st.error(f"⚠️ {str(e)}")
            except (APIError, AnalysisError) as e:
                logger.error(f"Analysis error (hidden from user): {str(e)}")
                st.error("⚠️ Analysis service is temporarily unavailable. Please try again later.")
            except Exception as e:
                logger.error(f"Unexpected error in example analysis: {str(e)}")
                st.error("⚠️ An unexpected error occurred. Please try again.")
        else:
            st.warning("Please parse the example logs first.")
    
    def _display_analysis_result(self, analysis_result: AnalysisResult, log_content: str, file_name: str = None) -> None:
        """Display analysis results."""
        # Display summary table
        if analysis_result.summary:
            st.markdown("### 📈 Session Summary")
            df_summary = pd.DataFrame(
                list(analysis_result.summary.to_dict().items()), 
                columns=['Metric', 'Value']
            )
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        # Display detailed analysis
        st.markdown("### 📊 Detailed Analysis")
        st.markdown(analysis_result.detailed_analysis)
        
        # Add download button
        pdf_content = self._create_pdf_report(analysis_result, log_content, file_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iris_agent_analysis_report_{timestamp}.pdf"
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_content,
            file_name=filename,
            mime="application/pdf",
            type="primary"
        )
    
    def _create_pdf_report(self, analysis_result: AnalysisResult, log_content: str, file_name: str = None) -> bytes:
        """Create PDF report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
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
        
        # Build content
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
        
        # Parse analysis result
        analysis_lines = analysis_result.detailed_analysis.split('\n')
        for line in analysis_lines:
            if line.strip():
                if line.startswith('**') and line.endswith('**'):
                    text = line[2:-2]
                    story.append(Paragraph(f"<b>{text}</b>", normal_style))
                elif line.startswith('|') and '|' in line[1:]:
                    continue  # Skip table rows for now
                else:
                    story.append(Paragraph(line, normal_style))
            else:
                story.append(Spacer(1, 6))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Report generated by Iris.agent", normal_style))
        story.append(Paragraph(f"Timestamp: {timestamp}", normal_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content


def main():
    """Main entry point."""
    try:
        app = IrisAgentApp()
        app.run()
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        st.error("⚠️ Application startup failed. Please check the configuration and try again.")


if __name__ == "__main__":
    main()
