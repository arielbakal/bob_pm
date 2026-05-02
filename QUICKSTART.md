# Quick Start Guide - Nexus-PM Agent

Get started with Nexus-PM in 5 minutes using your Gemini API key!

## 🚀 Setup (3 steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- LangGraph for workflow orchestration
- Gemini API for AI capabilities
- Linear GraphQL client
- Other utilities

### 2. Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy your API key

### 3. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your keys
nano .env  # or use any text editor
```

Add your credentials:
```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For Linear integration
LINEAR_API_KEY=lin_api_xxxxx
```

## ✅ Test It Works

### Test 1: Gemini API Connection

```bash
python -c "
from src.llm import get_gemini_client
client = get_gemini_client()
print(client.invoke('Say hello in one sentence'))
"
```

Expected output: A friendly greeting from Gemini!

### Test 2: Linear Provisioning (Demo Mode)

```bash
python examples/test_provision_ops.py
```

This shows what would be created in Linear (works without LINEAR_API_KEY).

### Test 3: Audio Processing (Demo Mode)

```bash
python examples/test_ingest_strategy.py
```

This shows what audio processing would do (works without audio file).

## 🎯 Real Usage Examples

### Example 1: Simple Text Generation

```python
from src.llm import get_gemini_client

# Initialize client (uses GEMINI_API_KEY from environment)
client = get_gemini_client()

# Generate text
response = client.invoke(
    prompt="Explain LangGraph in 2 sentences",
    system_prompt="You are a helpful AI assistant"
)

print(response)
```

### Example 2: Analyze Code

```python
from src.llm import get_gemini_client

client = get_gemini_client()

code = """
def calculate_total(items):
    return sum(item * 1.1 for item in items)
"""

analysis = client.analyze_codebase(
    codebase_context=code,
    analysis_prompt="What does this function do and what's the 1.1 multiplier for?"
)

print(analysis)
```

### Example 3: Create Linear Issues (Requires LINEAR_API_KEY)

```python
from src.state import create_initial_state, update_state
from src.nodes import provision_ops

# Sample roadmap
roadmap = """# Sprint 2024-W03 (Jan 15-22)

## Issues

### [HIGH] Implement authentication
**Acceptance Criteria:**
- [ ] OAuth integration
- [ ] Session management
"""

# Create state
state = create_initial_state(workflow_id="test-sprint")
state = update_state(
    state,
    roadmap=roadmap,
    approval_status="approved"
)

# Provision to Linear
result = provision_ops(state)

print(f"Created cycle: {result['linear_cycle_id']}")
print(f"Created issues: {result['linear_issue_ids']}")
```

## 🔧 Troubleshooting

### "GEMINI_API_KEY not found"

**Solution:** Make sure you've:
1. Created a `.env` file (copy from `.env.example`)
2. Added your API key: `GEMINI_API_KEY=your_key_here`
3. The `.env` file is in the project root directory

### "Import langchain_google_genai could not be resolved"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### "LINEAR_API_KEY not set" (when testing Linear)

**Solution:** Either:
1. Get a Linear API key from https://linear.app/settings/api
2. Add it to `.env`: `LINEAR_API_KEY=lin_api_xxxxx`
3. Or run in demo mode (it will show what would be created)

### Rate Limits

Gemini API has rate limits. If you hit them:
- Wait a few seconds between requests
- The code has automatic retry logic (3 attempts)
- Consider upgrading your API quota

## 📚 What's Implemented

✅ **Working Now:**
- Gemini API integration with retry logic
- Linear GraphQL client for issue management
- Roadmap parsing from markdown
- State management for workflows

🚧 **Coming Soon:**
- GitHub codebase analysis
- AI roadmap generation
- Human-in-the-loop approval gates
- Cyclic monitoring for blockers

## 🎓 Next Steps

1. **Read the full README:** See [`README.md`](README.md) for detailed documentation
2. **Check the implementation plan:** See [`stategraph-plan.md`](stategraph-plan.md) for architecture
3. **Explore examples:** Look in `examples/` directory for more use cases
4. **Contribute:** Help implement the remaining nodes!

## 💡 Pro Tips

**Tip 1: Use .env for credentials**
Never commit API keys to git. Always use `.env` file (it's in `.gitignore`).

**Tip 2: Test in demo mode first**
Both example scripts work without credentials - they show what would happen.

**Tip 3: Start with simple prompts**
Test your Gemini API connection with simple prompts before complex workflows.

**Tip 4: Check the logs**
Examples use logging - watch the console for detailed progress.

## 🆘 Need Help?

- Check existing issues in the repository
- Read the agent guidance in `AGENTS.md`
- Review the blueprint in `blueprint.md`
- Look at mode-specific rules in `.bob/rules-*/AGENTS.md`

## 🎉 You're Ready!

You now have:
- ✅ Gemini API working
- ✅ Linear client ready (optional)
- ✅ Example scripts to learn from
- ✅ Foundation for building workflows

Start experimenting with the examples and build your own workflows!