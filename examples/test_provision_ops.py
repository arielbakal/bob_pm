"""
Example usage of the provision_ops node with Linear GraphQL.
Demonstrates how to create cycles and issues from an approved roadmap.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import create_initial_state, update_state
from src.nodes.provision_ops import provision_ops, validate_provisioning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample roadmap for testing (using current dates)
from datetime import datetime, timedelta

# Calculate next week's dates
today = datetime.now()
next_monday = today + timedelta(days=(7 - today.weekday()))
next_sunday = next_monday + timedelta(days=6)

SAMPLE_ROADMAP = f"""# Sprint {next_monday.strftime('%Y-W%U')} ({next_monday.strftime('%b %d')}-{next_sunday.strftime('%d')})

## Goals
- Implement authentication system with OAuth2
- Refactor database layer for better performance
- Add comprehensive test coverage

## Issues

### [HIGH] Implement OAuth2 authentication
**Priority:** High

Integrate Google OAuth2 for user authentication with token refresh mechanism.

**Acceptance Criteria:**
- [ ] Google OAuth integration working
- [ ] Token refresh mechanism implemented
- [ ] Session management with Redis
- [ ] Login/logout flows tested

### [HIGH] Add JWT token validation
**Priority:** High

Implement JWT token validation middleware for API endpoints.

**Acceptance Criteria:**
- [ ] JWT validation middleware created
- [ ] Token expiration handling
- [ ] Refresh token rotation
- [ ] Unit tests for validation logic

### [MEDIUM] Refactor database query builder
**Priority:** Medium

Extract database query logic into reusable query builder pattern.

**Acceptance Criteria:**
- [ ] Query builder class implemented
- [ ] Support for complex joins
- [ ] Connection pooling configured
- [ ] Migration from raw SQL complete

### [MEDIUM] Add database connection pooling
**Priority:** Medium

Configure connection pooling for better database performance.

**Acceptance Criteria:**
- [ ] Pool configuration optimized
- [ ] Connection lifecycle management
- [ ] Performance benchmarks run
- [ ] Documentation updated

### [LOW] Update API documentation
**Priority:** Low

Update OpenAPI/Swagger documentation for new auth endpoints.

**Acceptance Criteria:**
- [ ] Auth endpoints documented
- [ ] Example requests added
- [ ] Error responses documented
- [ ] Postman collection updated
"""


def main():
    """
    Test the provision_ops node with a sample roadmap.
    
    Prerequisites:
    1. Set LINEAR_API_KEY environment variable
    2. Set LINEAR_WORKSPACE_ID environment variable (optional)
    3. Have an approved roadmap in state
    """
    
    # Check for required environment variables
    if not os.getenv("LINEAR_API_KEY"):
        logger.error("LINEAR_API_KEY not set")
        logger.info("Please set it to your Linear API key:")
        logger.info("export LINEAR_API_KEY=lin_api_xxxxx")
        logger.info("\nGet your API key from: https://linear.app/settings/api")
        
        # Show demo mode
        logger.info("\n" + "="*60)
        logger.info("DEMO MODE - No actual Linear provisioning")
        logger.info("="*60 + "\n")
        
        logger.info("Sample Roadmap:")
        logger.info("-" * 60)
        print(SAMPLE_ROADMAP)
        logger.info("-" * 60)
        
        logger.info("\nThis roadmap would create:")
        logger.info("  - 1 Sprint Cycle: Sprint 2024-W03")
        logger.info("  - 5 Issues:")
        logger.info("    * [HIGH] Implement OAuth2 authentication")
        logger.info("    * [HIGH] Add JWT token validation")
        logger.info("    * [MEDIUM] Refactor database query builder")
        logger.info("    * [MEDIUM] Add database connection pooling")
        logger.info("    * [LOW] Update API documentation")
        
        logger.info("\nTo test with real Linear:")
        logger.info("1. Get API key from https://linear.app/settings/api")
        logger.info("2. Set LINEAR_API_KEY environment variable")
        logger.info("3. Run this script again")
        
        return
    
    # Create initial state with approved roadmap
    workflow_id = f"test-provision-{datetime.utcnow().isoformat()}"
    logger.info(f"Creating workflow: {workflow_id}")
    
    initial_state = create_initial_state(workflow_id=workflow_id)
    
    # Simulate approved roadmap
    state_with_roadmap = update_state(
        initial_state,
        roadmap=SAMPLE_ROADMAP,
        roadmap_version=1,
        approval_status="approved",
        approval_token="test-approval-token"
    )
    
    logger.info("State prepared with approved roadmap")
    logger.info(f"Roadmap length: {len(SAMPLE_ROADMAP)} characters")
    
    try:
        logger.info("\n" + "="*60)
        logger.info("STARTING LINEAR PROVISIONING")
        logger.info("="*60 + "\n")
        
        # Execute provision_ops node
        logger.info("This may take 30-60 seconds to create cycle and issues...")
        updated_state = provision_ops(state_with_roadmap)
        
        logger.info("\n" + "="*60)
        logger.info("PROVISIONING COMPLETE")
        logger.info("="*60 + "\n")
        
        # Display results
        cycle_id = updated_state.get("linear_cycle_id")
        issue_ids = updated_state.get("linear_issue_ids", [])
        
        logger.info("Provisioning Results:")
        logger.info(f"  Cycle ID: {cycle_id}")
        logger.info(f"  Issues Created: {len(issue_ids)}")
        logger.info(f"  Provisioning Status: {updated_state.get('provisioning_status')}")
        
        if issue_ids:
            logger.info("\n  Issue IDs:")
            for i, issue_id in enumerate(issue_ids, 1):
                logger.info(f"    {i}. {issue_id}")
        
        # Validate provisioning
        validation = validate_provisioning(updated_state)
        logger.info("\nValidation Results:")
        logger.info(f"  Valid: {validation['valid']}")
        logger.info(f"  Cycle Created: {validation['cycle_created']}")
        logger.info(f"  Issues Created: {validation['issues_created']}")
        
        if validation['warnings']:
            logger.warning(f"  Warnings: {validation['warnings']}")
        
        # Show state updates
        logger.info("\nState Updates:")
        logger.info(f"  Last Updated: {updated_state['last_updated']}")
        logger.info(f"  Workflow ID: {updated_state['workflow_id']}")
        
        logger.info("\n" + "="*60)
        logger.info("SUCCESS - Check Linear workspace for created items")
        logger.info("="*60)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
        
    except Exception as e:
        logger.error(f"Provisioning failed: {e}")
        raise


if __name__ == "__main__":
    main()

# Made with Bob
