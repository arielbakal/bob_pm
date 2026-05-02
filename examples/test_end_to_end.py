"""
End-to-End Test: Audio → Summary → Roadmap → Linear Issues

This test demonstrates the complete workflow:
1. Process meeting audio file
2. Extract strategy summary
3. Generate structured roadmap
4. Create Linear cycle and issues

Prerequisites:
- GEMINI_API_KEY in environment
- LINEAR_API_KEY in environment (optional - runs in dry-run mode without it)
- Audio file at examples/sample_meeting.mp3
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import create_initial_state, update_state
from src.nodes import (
    ingest_strategy,
    validate_strategy_summary,
    generate_roadmap_from_summary,
    validate_roadmap_format,
    provision_ops,
    validate_provisioning
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str, char: str = "="):
    """Print a formatted section header."""
    logger.info("")
    logger.info(char * 60)
    logger.info(title)
    logger.info(char * 60)
    logger.info("")


def main():
    """
    Run end-to-end test: Audio → Summary → Roadmap → Linear Issues
    """
    
    print_section("NEXUS-PM END-TO-END TEST")
    
    # ========================================
    # Step 0: Validate Prerequisites
    # ========================================
    
    logger.info("Checking prerequisites...")
    
    # Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY not set")
        logger.info("\nTo get your API key:")
        logger.info("1. Go to: https://makersuite.google.com/app/apikey")
        logger.info("2. Click 'Create API Key'")
        logger.info("3. Add to .env file: GEMINI_API_KEY=your_key_here")
        return
    
    logger.info("✓ Gemini API key found")
    
    # Check Linear API key (optional)
    linear_key = os.getenv("LINEAR_API_KEY")
    if not linear_key:
        logger.warning("⚠ LINEAR_API_KEY not set - will run in dry-run mode")
        logger.info("To create actual Linear issues, add LINEAR_API_KEY to .env")
        dry_run = True
    else:
        logger.info("✓ Linear API key found")
        dry_run = False
    
    # Check audio file
    audio_file = "examples/sample_meeting.mp3"
    if not os.path.exists(audio_file):
        logger.error(f"❌ Audio file not found: {audio_file}")
        logger.info("\nPlease ensure sample_meeting.mp3 exists in examples/")
        return
    
    logger.info(f"✓ Audio file found: {audio_file}")
    
    # ========================================
    # Step 1: Initialize State
    # ========================================
    
    print_section("STEP 1: INITIALIZE WORKFLOW")
    
    workflow_id = f"e2e-test-{datetime.utcnow().isoformat()}"
    logger.info(f"Workflow ID: {workflow_id}")
    
    state = create_initial_state(
        workflow_id=workflow_id,
        meeting_audio_path=audio_file
    )
    
    logger.info("✓ Initial state created")
    logger.info(f"  - Workflow ID: {state['workflow_id']}")
    logger.info(f"  - Audio Path: {state['meeting_audio_path']}")
    logger.info(f"  - Approval Status: {state['approval_status']}")
    
    # ========================================
    # Step 2: Process Audio → Strategy Summary
    # ========================================
    
    print_section("STEP 2: PROCESS AUDIO FILE")
    
    logger.info("Processing meeting audio with Gemini...")
    logger.info("This may take 10-30 seconds...")
    
    try:
        state = ingest_strategy(state)
        
        logger.info("✓ Audio processing complete")
        logger.info(f"  - Summary length: {len(state['strategy_summary'])} characters")
        
        # Validate summary
        validation = validate_strategy_summary(state['strategy_summary'])
        if validation['valid']:
            logger.info("✓ Summary validation passed")
        else:
            logger.warning(f"⚠ Summary validation issues: {validation['missing_sections']}")
        
        # Show summary preview
        logger.info("\nStrategy Summary Preview:")
        logger.info("-" * 60)
        preview = state['strategy_summary'][:500]
        logger.info(preview + "..." if len(state['strategy_summary']) > 500 else preview)
        logger.info("-" * 60)
        
    except Exception as e:
        logger.error(f"❌ Audio processing failed: {e}")
        return
    
    # ========================================
    # Step 3: Generate Roadmap from Summary
    # ========================================
    
    print_section("STEP 3: GENERATE ROADMAP")
    
    logger.info("Converting summary to structured roadmap...")
    logger.info("This may take 10-20 seconds...")
    
    try:
        roadmap = generate_roadmap_from_summary(state['strategy_summary'])
        
        logger.info("✓ Roadmap generation complete")
        logger.info(f"  - Roadmap length: {len(roadmap)} characters")
        
        # Validate roadmap format
        validation = validate_roadmap_format(roadmap)
        if validation['valid']:
            logger.info("✓ Roadmap format validation passed")
        else:
            logger.warning(f"⚠ Roadmap validation issues: {validation['issues']}")
        
        if validation['warnings']:
            logger.warning(f"⚠ Warnings: {validation['warnings']}")
        
        # Update state with roadmap and approve it
        state = update_state(
            state,
            roadmap=roadmap,
            approval_status="approved"  # Auto-approve for testing
        )
        
        # Show roadmap preview
        logger.info("\nGenerated Roadmap Preview:")
        logger.info("-" * 60)
        preview = roadmap[:800]
        logger.info(preview + "..." if len(roadmap) > 800 else preview)
        logger.info("-" * 60)
        
    except Exception as e:
        logger.error(f"❌ Roadmap generation failed: {e}")
        return
    
    # ========================================
    # Step 4: Provision Linear Operations
    # ========================================
    
    print_section("STEP 4: CREATE LINEAR ISSUES")
    
    if dry_run:
        logger.info("Running in DRY-RUN mode (no Linear API key)")
        logger.info("Showing what would be created...")
        
        # Parse roadmap to show what would be created
        from src.nodes.provision_ops import parse_roadmap
        parsed = parse_roadmap(roadmap)
        
        logger.info(f"\nWould create:")
        logger.info(f"  - Cycle: {parsed['cycle_name']}")
        logger.info(f"  - Issues: {len(parsed['issues'])}")
        
        for i, issue in enumerate(parsed['issues'], 1):
            logger.info(f"\n  Issue {i}:")
            logger.info(f"    Title: {issue['title']}")
            logger.info(f"    Priority: {issue['priority']}")
            logger.info(f"    Acceptance Criteria: {len(issue['acceptance_criteria'])} items")
        
        logger.info("\n✓ Dry-run complete")
        logger.info("\nTo create actual Linear issues:")
        logger.info("1. Add LINEAR_API_KEY to your .env file")
        logger.info("2. Run this test again")
        
    else:
        logger.info("Creating Linear cycle and issues...")
        logger.info("This may take 30-60 seconds...")
        
        try:
            state = provision_ops(state)
            
            logger.info("✓ Linear provisioning complete")
            logger.info(f"  - Cycle ID: {state['linear_cycle_id']}")
            logger.info(f"  - Issues created: {len(state['linear_issue_ids'])}")
            
            # Validate provisioning
            validation = validate_provisioning(state)
            if validation['valid']:
                logger.info("✓ Provisioning validation passed")
            else:
                logger.warning(f"⚠ Provisioning validation issues: {validation['issues']}")
            
            # Show created issues
            logger.info("\nCreated Issues:")
            logger.info("-" * 60)
            for issue_id in state['linear_issue_ids']:
                logger.info(f"  - {issue_id}")
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"❌ Linear provisioning failed: {e}")
            logger.info("\nThis might be due to:")
            logger.info("- Invalid LINEAR_API_KEY")
            logger.info("- Network connectivity issues")
            logger.info("- Linear API rate limits")
            return
    
    # ========================================
    # Final Summary
    # ========================================
    
    print_section("END-TO-END TEST COMPLETE", "=")
    
    logger.info("Workflow Summary:")
    logger.info(f"  - Workflow ID: {state['workflow_id']}")
    logger.info(f"  - Audio File: {state['meeting_audio_path']}")
    logger.info(f"  - Strategy Summary: {len(state['strategy_summary'])} chars")
    logger.info(f"  - Roadmap: {len(state['roadmap'])} chars")
    logger.info(f"  - Approval Status: {state['approval_status']}")
    
    if not dry_run:
        logger.info(f"  - Linear Cycle: {state['linear_cycle_id']}")
        logger.info(f"  - Linear Issues: {len(state['linear_issue_ids'])}")
        logger.info("\n✓ Check your Linear workspace to see the created items!")
    else:
        logger.info("\n✓ Dry-run completed successfully")
    
    logger.info("\n" + "=" * 60)
    logger.info("SUCCESS - End-to-end workflow completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

# Made with Bob
