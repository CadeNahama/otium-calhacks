# Migration from OpenAI to Anthropic Claude

## Summary
Successfully migrated the AI command generation system from OpenAI to Anthropic Claude.

## Changes Made

### 1. Dependencies (requirements.txt)
- **Removed**: `openai>=1.3.0`
- **Added**: `anthropic>=0.18.0`

### 2. Command Generator (backend/llm-os-agent/command_generator.py)
- Updated imports from `openai` to `anthropic`
- Changed model from `gpt-3.5-turbo` to `claude-3-5-sonnet-20241022`
- Renamed constants:
  - `DEFAULT_OPENAI_MODEL` → `DEFAULT_CLAUDE_MODEL`
  - `DEFAULT_OPENAI_MAX_TOKENS` → `DEFAULT_CLAUDE_MAX_TOKENS`
  - `DEFAULT_OPENAI_TEMPERATURE` → `DEFAULT_CLAUDE_TEMPERATURE`
- Updated client initialization:
  - `self.openai_client = OpenAI(api_key=api_key)` → `self.anthropic_client = Anthropic(api_key=api_key)`
- Refactored API call method:
  - `_call_openai()` → `_call_claude()`
  - Updated to use Anthropic's Messages API format
  - System prompt now passed as separate parameter
  - Response accessed via `response.content[0].text` instead of `response.choices[0].message.content`

### 3. Configuration (backend/llm-os-agent/config.py)
- Updated AI provider from `"openai"` to `"anthropic"`
- Renamed configuration section from `"openai"` to `"anthropic"`
- Updated default model to `claude-3-5-sonnet-20241022`

### 4. Agent (backend/llm-os-agent/agent.py)
- Updated error messages to reference "Anthropic API key"
- Changed environment variable from `OPENAI_API_KEY` to `ANTHROPIC_API_KEY`

### 5. API Servers
Updated all three API server files to use `ANTHROPIC_API_KEY`:

#### api_server.py
- Changed constant `ENV_OPENAI_API_KEY` to `ENV_ANTHROPIC_API_KEY`
- Updated `get_environment_info()` function to check for Anthropic key
- Modified agent initialization to use `ANTHROPIC_API_KEY`

#### api_server_enhanced.py
- Updated agent initialization to use `ANTHROPIC_API_KEY`

#### api_server_memory.py
- Updated API key checks and error messages
- Changed environment variable reference to `ANTHROPIC_API_KEY`

### 6. Environment Configuration
#### env.example
- Changed from `OPENAI_API_KEY` to `ANTHROPIC_API_KEY`
- Updated comments to reference Anthropic Claude

#### setup_local.sh
- Updated .env file generation to use `ANTHROPIC_API_KEY`
- Modified setup instructions to reference Anthropic

### 7. Documentation
#### README.md
- Updated Railway deployment instructions
- Changed environment variable documentation from OpenAI to Anthropic

#### PROJECT_STRUCTURE.md
- Updated environment variables section to show `ANTHROPIC_API_KEY`

## API Differences

### OpenAI API Format (Old)
```python
response = self.openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.1,
    max_tokens=1000
)
return response.choices[0].message.content
```

### Anthropic Claude API Format (New)
```python
response = self.anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    temperature=0.1,
    system=system_prompt,
    messages=[
        {"role": "user", "content": user_prompt}
    ]
)
return response.content[0].text
```

## Key Benefits of Claude

1. **Better instruction following**: Claude is known for following complex instructions more accurately
2. **Longer context**: Claude 3.5 Sonnet supports up to 200K tokens
3. **More recent training data**: Claude has more up-to-date knowledge
4. **Better at technical tasks**: Claude excels at code generation and system administration tasks

## Migration Checklist

- [x] Update requirements.txt
- [x] Update command_generator.py
- [x] Update config.py
- [x] Update agent.py
- [x] Update api_server.py
- [x] Update api_server_enhanced.py
- [x] Update api_server_memory.py
- [x] Update env.example
- [x] Update setup_local.sh
- [x] Update README.md
- [x] Update PROJECT_STRUCTURE.md
- [x] Test for linter errors

## Next Steps

1. **Install dependencies**:
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Update .env file**:
   ```bash
   # Replace your existing OPENAI_API_KEY with ANTHROPIC_API_KEY
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. **Get Anthropic API Key**:
   - Visit https://console.anthropic.com/
   - Create an account or sign in
   - Generate an API key from the dashboard
   - Add it to your .env file

4. **Test the system**:
   ```bash
   cd backend/llm-os-agent
   uvicorn api_server_enhanced:app --reload
   ```

## Model Comparison

| Feature | OpenAI GPT-3.5 Turbo | Claude 3.5 Sonnet |
|---------|---------------------|-------------------|
| Context Window | 16K tokens | 200K tokens |
| Training Cutoff | Sep 2021 | Apr 2024 |
| Pricing (per 1M tokens) | $0.50/$1.50 | $3.00/$15.00 |
| Instruction Following | Good | Excellent |
| Code Generation | Good | Excellent |
| Technical Tasks | Good | Excellent |

## Notes

- The migration maintains backward compatibility with all existing features
- All system prompts and logic remain the same
- Only the AI provider API calls have been updated
- Performance may vary; recommend testing with your specific use cases

