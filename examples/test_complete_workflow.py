"""
Complete workflow test with human-in-the-loop approval.
Tests the full LangGraph StateGraph from audio to Linear issues.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import create_initial_state
from src.graph import create_workflow, run_workflow, resume_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_complete_workflow():
    """
    Test complete workflow with interrupt and approval.
    
    Workflow:
    1. Process meeting audio
    2. Scan codebase
    3. Generate roadmap
    4. INTERRUPT for approval
    5. Resume with approval
    6. Provision Linear issues
    """
    logger.info("=" * 60)
    logger.info("COMPLETE WORKFLOW TEST")
    logger.info("=" * 60)
    
    # Create workflow
    workflow = create_workflow(checkpointer_path="test_workflow.db")
    
    # Create initial state
    workflow_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        meeting_audio_path="examples/sample_meeting.mp3"
    )
    
    logger.info(f"Workflow ID: {workflow_id}")
    
    # Phase 1: Run until interrupt
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: Running workflow until human gate")
    logger.info("=" * 60)
    
    state_at_interrupt = run_workflow(workflow, initial_state, workflow_id)
    
    # Display roadmap for approval
    logger.info("\n" + "=" * 60)
    logger.info("ROADMAP FOR APPROVAL")
    logger.info("=" * 60)
    print(state_at_interrupt.get("roadmap", "No roadmap generated"))
    
    # Simulate human approval
    logger.info("\n" + "=" * 60)
    logger.info("SIMULATING HUMAN APPROVAL")
    logger.info("=" * 60)
    
    approval_status = "approved"  # Change to "rejected" to test regeneration
    approval_feedback = None
    
    logger.info(f"Approval status: {approval_status}")
    
    # Phase 2: Resume with approval
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Resuming workflow with approval")
    logger.info("=" * 60)
    
    final_state = resume_workflow(
        workflow,
        workflow_id,
        approval_status,
        approval_feedback
    )
    
    # Display results
    logger.info("\n" + "=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 60)
    
    logger.info(f"Cycle ID: {final_state.get('linear_cycle_id')}")
    logger.info(f"Issues created: {len(final_state.get('linear_issue_ids', []))}")
    logger.info(f"Provisioning status: {final_state.get('provisioning_status')}")
    
    return final_state


def test_rejection_loop():
    """
    Test roadmap rejection and regeneration loop.
    """
    logger.info("=" * 60)
    logger.info("REJECTION LOOP TEST")
    logger.info("=" * 60)
    
    # Create workflow
    workflow = create_workflow(checkpointer_path="test_rejection.db")
    
    # Create initial state
    workflow_id = f"rejection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        meeting_audio_path="examples/sample_meeting.mp3"
    )
    
    # Run until interrupt
    logger.info("Running workflow until first interrupt...")
    state_at_interrupt = run_workflow(workflow, initial_state, workflow_id)
    
    # Reject with feedback
    logger.info("\nRejecting roadmap with feedback...")
    approval_status = "rejected"
    approval_feedback = "Please add more detail to the authentication task and break it into smaller issues."
    
    # Resume - should regenerate roadmap
    logger.info("Resuming workflow - should regenerate roadmap...")
    for event in workflow.stream(
        {"approval_status": approval_status, "approval_feedback": approval_feedback},
        {"configurable": {"thread_id": workflow_id}}
    ):
        logger.info(f"Event: {list(event.keys())}")
    
    # Get state after regeneration (should be at human_gate again)
    state_after_regen = workflow.get_state({"configurable": {"thread_id": workflow_id}})
    
    logger.info("\nRoadmap regenerated - at human gate again")
    logger.info(f"Next node: {state_after_regen.next}")
    
    # Now approve
    logger.info("\nApproving regenerated roadmap...")
    final_state = resume_workflow(workflow, workflow_id, "approved", None)
    
    logger.info("\nWorkflow complete after regeneration")
    logger.info(f"Issues created: {len(final_state.get('linear_issue_ids', []))}")
    
    return final_state


if __name__ == "__main__":
    try:
        # Test 1: Normal approval flow
        logger.info("\n\n" + "=" * 60)
        logger.info("TEST 1: NORMAL APPROVAL FLOW")
        logger.info("=" * 60)
        final_state = test_complete_workflow()
        logger.info("\n✅ Normal approval flow test PASSED")
        
        # Test 2: Rejection and regeneration
        logger.info("\n\n" + "=" * 60)
        logger.info("TEST 2: REJECTION AND REGENERATION")
        logger.info("=" * 60)
        final_state_rejection = test_rejection_loop()
        logger.info("\n✅ Rejection loop test PASSED")
        
        logger.info("\n\n" + "=" * 60)
        logger.info("ALL TESTS PASSED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {e}", exc_info=True)
        sys.exit(1)

# Made with Bob