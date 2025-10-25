# Otium - AI-Powered System Administration

Full-stack application for AI-powered Linux system administration with SSH support.

## 🏗️ Project Structure

This is a monorepo containing both frontend and backend:

```
CALHACKS-OTIUM/
├── backend/          # Python FastAPI backend
│   └── llm-os-agent/ # Main application code
└── frontend/         # Next.js frontend
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd llm-os-agent
uvicorn api_server:app --reload
```

Backend runs on: `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:3000`

## 🔑 Environment Variables

### Backend
- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: Server port (default: 8000)

### Frontend
Configure in `frontend/.env.local` (if needed)

## 📚 Tech Stack

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PostgreSQL** - Database
- **SSH** - Remote system administration

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Radix UI** - Component library

## 🎯 Features

- AI-powered command generation
- SSH-based system administration
- Secure user authentication
- Real-time command execution
- State-aware execution monitoring

## 📝 License

MIT
