"""
Gemini API LLM initialization and configuration for Nexus-PM orchestrator.
Supports both Gemini API (with API key) and Vertex AI (with service account).
Handles multimodal content (audio, text) with 1M token context window.
"""

import os
import warnings
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Suppress Python version deprecation warnings from Google libraries
warnings.filterwarnings('ignore', category=FutureWarning)

# Load environment variables from .env file
load_dotenv()

# Try to import both Gemini API and Vertex AI
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_API_AVAILABLE = True
except ImportError:
    GEMINI_API_AVAILABLE = False

try:
    from langchain_google_vertexai import ChatVertexAI
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

from langchain_core.messages import HumanMessage, SystemMessage


class GeminiClient:
    """
    Unified client for Gemini API and Vertex AI with retry logic and multimodal support.
    
    Supports two authentication methods:
    1. Gemini API: Simple API key (GEMINI_API_KEY or GOOGLE_API_KEY)
    2. Vertex AI: Service account credentials (GOOGLE_APPLICATION_CREDENTIALS)
    
    Features:
    - 1-million-token context window for full codebase analysis
    - Native multimodal support (audio, text, images)
    - Automatic retry on API failures
    - Streaming support for long-running operations
    """
    
    def __init__(
        self,
        model_name: str = "gemini-pro",
        max_output_tokens: int = 8192,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        use_vertex_ai: bool = False,
        project_id: Optional[str] = None,
        location: str = "us-central1"
    ):
        """
        Initialize Gemini client (API or Vertex AI).
        
        Args:
            model_name: Gemini model to use (default: gemini-pro)
            max_output_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            api_key: Gemini API key (for API mode, defaults to env vars)
            use_vertex_ai: If True, use Vertex AI instead of Gemini API
            project_id: GCP project ID (for Vertex AI only)
            location: GCP region (for Vertex AI only)
        """
        self.model_name = model_name
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.use_vertex_ai = use_vertex_ai
        
        # Determine which backend to use
        if use_vertex_ai:
            self._init_vertex_ai(project_id, location)
        else:
            self._init_gemini_api(api_key)
    
    def _init_gemini_api(self, api_key: Optional[str] = None):
        """Initialize Gemini API client with API key."""
        if not GEMINI_API_AVAILABLE:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                "or pass api_key parameter. Get your key from: https://makersuite.google.com/app/apikey"
            )
        
        # Initialize LangChain ChatGoogleGenerativeAI
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            max_output_tokens=self.max_output_tokens,
            temperature=self.temperature
        )
        
        self.backend = "gemini_api"
    
    def _init_vertex_ai(self, project_id: Optional[str] = None, location: str = "us-central1"):
        """Initialize Vertex AI client with service account."""
        if not VERTEX_AI_AVAILABLE:
            raise ImportError(
                "langchain-google-vertexai not installed. "
                "Install with: pip install langchain-google-vertexai"
            )
        
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        
        # Verify credentials
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Please set it to the path of your service account key JSON file."
            )
        
        # Initialize LangChain ChatVertexAI
        self.llm = ChatVertexAI(
            model_name=self.model_name,
            max_output_tokens=self.max_output_tokens,
            temperature=self.temperature,
            project=self.project_id,
            location=self.location
        )
        
        self.backend = "vertex_ai"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        multimodal_content: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Invoke Gemini with automatic retry on failures.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system instructions
            multimodal_content: Optional list of multimodal content items
                Format: [{"type": "audio", "data": bytes}, ...]
        
        Returns:
            Generated text response
            
        Raises:
            Exception: After 3 failed retry attempts
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # Build human message with multimodal content
        if multimodal_content:
            # Multimodal format
            content_parts = [{"type": "text", "text": prompt}]
            content_parts.extend(multimodal_content)
            messages.append(HumanMessage(content=content_parts))
        else:
            messages.append(HumanMessage(content=prompt))
        
        # Invoke with retry
        response = self.llm.invoke(messages)
        return response.content
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ):
        """
        Stream response from Gemini (for long-running operations).
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system instructions
            
        Yields:
            Response chunks as they arrive
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        # Stream with retry
        for chunk in self.llm.stream(messages):
            yield chunk.content
    
    def process_audio(
        self,
        audio_path: str,
        task_prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Process audio file directly with Gemini multimodal capabilities.
        Uses native Google Genai SDK for audio support (LangChain doesn't support audio yet).
        
        Note: Audio processing requires Gemini API (not Vertex AI).
        
        Args:
            audio_path: Path to .mp3 audio file
            task_prompt: Instructions for what to extract from audio
            system_prompt: Optional system instructions
            
        Returns:
            Extracted information as text
            
        Example:
            >>> client = GeminiClient()
            >>> result = client.process_audio(
            ...     "meeting.mp3",
            ...     "Extract action items and technical decisions"
            ... )
        """
        # Audio processing requires native Genai SDK (not LangChain)
        if not GEMINI_API_AVAILABLE:
            raise Exception("Audio processing requires google-genai package")
        
        # Import native Genai SDK for audio support
        from google import genai
        from google.genai import types
        
        # Get API key
        api_key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY or GOOGLE_API_KEY required for audio processing")
        
        # Create native client
        client = genai.Client(api_key=api_key)
        
        # Read audio file
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # Build prompt with system instructions
        full_prompt = task_prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{task_prompt}"
        
        # Create multimodal content with audio
        response = client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part(text=full_prompt),
                types.Part(
                    inline_data=types.Blob(
                        data=audio_data,
                        mime_type="audio/mp3"
                    )
                )
            ]
        )
        
        return response.text
    
    def analyze_codebase(
        self,
        codebase_context: str,
        analysis_prompt: str
    ) -> str:
        """
        Analyze large codebase using 1M token context window.
        
        Args:
            codebase_context: Full codebase structure and content
            analysis_prompt: What to analyze/extract
            
        Returns:
            Analysis results
            
        Note:
            Gemini 1.5 Pro supports up to 1 million tokens, allowing
            full repository analysis in a single call.
        """
        system_prompt = """You are a senior software architect analyzing a codebase.
Provide concise, actionable insights about architecture, patterns, and technical debt."""
        
        full_prompt = f"""Codebase Context:
{codebase_context}

Analysis Task:
{analysis_prompt}"""
        
        return self.invoke(
            prompt=full_prompt,
            system_prompt=system_prompt
        )


# Singleton instance for reuse across nodes
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client(
    model_name: str = "gemini-2.5-flash",
    max_output_tokens: int = 8192,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    use_vertex_ai: bool = False
) -> GeminiClient:
    """
    Get or create singleton Gemini client.
    
    Automatically detects which backend to use:
    - If GEMINI_API_KEY or GOOGLE_API_KEY is set: Use Gemini API
    - If GOOGLE_APPLICATION_CREDENTIALS is set: Use Vertex AI
    - If use_vertex_ai=True: Force Vertex AI
    
    Args:
        model_name: Gemini model to use
        max_output_tokens: Maximum tokens in response
        temperature: Sampling temperature
        api_key: Optional API key (for Gemini API)
        use_vertex_ai: Force Vertex AI instead of Gemini API
        
    Returns:
        GeminiClient instance
    """
    global _gemini_client
    
    if _gemini_client is None:
        # Auto-detect backend if not specified
        if not use_vertex_ai:
            # Check if Gemini API key is available
            has_api_key = bool(
                api_key or 
                os.getenv("GEMINI_API_KEY") or 
                os.getenv("GOOGLE_API_KEY")
            )
            
            # Use Gemini API if key is available, otherwise try Vertex AI
            use_vertex_ai = not has_api_key
        
        _gemini_client = GeminiClient(
            model_name=model_name,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            api_key=api_key,
            use_vertex_ai=use_vertex_ai
        )
    
    return _gemini_client


# Backward compatibility aliases
VertexAIClient = GeminiClient
get_vertex_client = get_gemini_client

# Made with Bob
