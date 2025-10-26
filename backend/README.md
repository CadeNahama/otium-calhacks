# Ping AI Agent Backend

AI-powered Linux system administration backend with SSH support.

## Local Development

To start locally:
```bash
cd llm-os-agent
uvicorn api_server:app --reload
```

## Railway Deployment

### Prerequisites
- Railway account
- Railway CLI installed (`npm i -g @railway/cli`)

### Deployment Steps

1. **Login to Railway:**
   ```bash
   railway login
   ```

2. **Initialize Railway project:**
   ```bash
   railway init
   ```

3. **Set environment variables:**
   ```bash
   railway variables set ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

### Environment Variables Required

- `ANTHROPIC_API_KEY`: Your Anthropic Claude API key
- `PORT`: Railway will set this automatically

### Build Configuration

The project includes:
- `Procfile`: Defines how to start the application
- `railway.json`: Railway-specific configuration
- `requirements.txt`: Production dependencies only
- `.dockerignore`: Optimizes build process

### API Endpoints

Once deployed, your API will be available at:
- Health check: `GET /api/health`
- API docs: `GET /docs`
- Connect to server: `POST /api/connect`
- Submit task: `POST /api/commands`

### Monitoring

- Railway dashboard provides logs and metrics
- Health check endpoint for monitoring
- Automatic restarts on failure