"""
Example usage of the ingest_strategy node with Vertex AI.
Demonstrates how to process meeting audio and extract strategic insights.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import create_initial_state
from src.nodes import ingest_strategy, validate_strategy_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Test the ingest_strategy node with a sample meeting audio file.
    
    Prerequisites:
    1. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable
    2. Place a meeting audio file (.mp3) in the examples/ directory
    
    Get your API key from: https://makersuite.google.com/app/apikey
    """
    
    # Check for required environment variables
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not gemini_key:
        logger.error("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        logger.info("\nTo get your API key:")
        logger.info("1. Go to: https://makersuite.google.com/app/apikey")
        logger.info("2. Click 'Create API Key'")
        logger.info("3. Copy the key and set it:")
        logger.info("   export GEMINI_API_KEY=your_api_key_here")
        logger.info("\nOr add it to your .env file:")
        logger.info("   GEMINI_API_KEY=your_api_key_here")
        return
    
    # Example audio file path (replace with your actual file)
    audio_file = "examples/sample_meeting.mp3"
    
    if not os.path.exists(audio_file):
        logger.warning(f"Audio file not found: {audio_file}")
        logger.info("Creating a placeholder for demonstration...")
        logger.info("In production, replace this with an actual meeting recording")
        
        # For demo purposes, we'll show what the state would look like
        logger.info("\n" + "="*60)
        logger.info("DEMO MODE - No actual audio processing")
        logger.info("="*60 + "\n")
        
        # Create initial state
        workflow_id = f"demo-{datetime.utcnow().isoformat()}"
        state = create_initial_state(
            workflow_id=workflow_id,
            meeting_audio_path=audio_file
        )
        
        logger.info("Initial State:")
        logger.info(f"  Workflow ID: {state['workflow_id']}")
        logger.info(f"  Audio Path: {state['meeting_audio_path']}")
        logger.info(f"  Started At: {state['started_at']}")
        logger.info(f"  Approval Status: {state['approval_status']}")
        
        logger.info("\nTo test with real audio:")
        logger.info("1. Place a .mp3 meeting recording in examples/")
        logger.info("2. Update the audio_file path above")
        logger.info("3. Run this script again")
        
        return
    
    # Create initial state with audio path
    workflow_id = f"test-{datetime.utcnow().isoformat()}"
    logger.info(f"Creating workflow: {workflow_id}")
    
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        meeting_audio_path=audio_file
    )
    
    logger.info(f"Processing audio file: {audio_file}")
    logger.info("This may take 30-60 seconds for Vertex AI processing...")
    
    try:
        # Execute ingest_strategy node
        updated_state = ingest_strategy(initial_state)
        
        logger.info("\n" + "="*60)
        logger.info("STRATEGY EXTRACTION COMPLETE")
        logger.info("="*60 + "\n")
        
        # Display extracted strategy
        strategy = updated_state.get("strategy_summary")
        if strategy:
            logger.info("Extracted Strategy Summary:")
            logger.info("-" * 60)
            print(strategy)
            logger.info("-" * 60)
            
            # Validate the summary
            validation = validate_strategy_summary(strategy)
            logger.info("\nValidation Results:")
            logger.info(f"  Valid: {validation['valid']}")
            
            if validation['missing_sections']:
                logger.warning(f"  Missing Sections: {validation['missing_sections']}")
            
            if validation['warnings']:
                logger.warning(f"  Warnings: {validation['warnings']}")
            
            # Show state updates
            logger.info("\nState Updates:")
            logger.info(f"  Last Updated: {updated_state['last_updated']}")
            logger.info(f"  Strategy Summary Length: {len(strategy)} chars")
        else:
            logger.error("No strategy summary extracted!")
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise


if __name__ == "__main__":
    main()

# Made with Bob
