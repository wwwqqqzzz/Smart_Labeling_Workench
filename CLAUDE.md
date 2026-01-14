# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smart Labeling Workbench** (智能打标便捷器) - A freight conversation data annotation tool that improves labeling efficiency 5-10x using RAG-powered AI recommendations.

- **Goal**: Reduce conversation annotation time from 3-5 minutes to 20-30 seconds per conversation
- **Data**: ~3,500 freight conversations between drivers and cargo owners
- **Tech Stack**: Next.js 15 + FastAPI + ChromaDB + GLM-4 Flash AI

---

## Development Commands

### Frontend (Next.js)

```bash
cd frontend
npm run dev          # Start development server (localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (FastAPI)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload    # Development server
python scripts/init_db.py     # Initialize database tables
python scripts/import_excel.py  # Import data from Excel
```

### Docker Development

```bash
# Development environment (with hot reload)
docker-compose up

# Production environment
docker-compose -f docker-compose.prod.yml up -d

# One-click production deployment
chmod +x deploy.sh && ./deploy.sh
```

### Testing

```bash
cd backend
pytest                               # Run all tests
pytest tests/test_conversations.py   # Run specific test
pytest --cov=app tests               # Run with coverage
```

---

## Architecture Overview

### System Layers

```
Presentation:    Next.js 15 + shadcn/ui + React Query + Zustand
Application:     FastAPI + SQLAlchemy + Pydantic
Data:            SQLite + ChromaDB + Redis (optional)
External APIs:   GLM-4 Flash (AI) + OpenAI (embeddings)
```

### Key Design Patterns

1. **Conversation Format**: Dialogues stored as `"司机：xxx$_$货主：xxx$_$..."` - parser splits by `$_$` and detects role from text containing "司机" (driver)
2. **RAG Pipeline**:
   - Vector index built from manually tagged conversations
   - Query: find similar conversations using semantic search
   - Recommend: aggregate tags from similar conversations
   - Fallback: GLM-4 AI analysis if no similar conversations found
3. **State Management**:
   - Server state: `@tanstack/react-query` (API data)
   - Client state: `zustand` (UI state)
4. **Tag Selection**: Keyboard-driven workflow with shortcuts (Space/Enter/1-9/R)

---

## File Structure

### Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── config.py               # Settings from environment variables
│   ├── database.py             # SQLAlchemy session, engine
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── conversation.py     # conversations table
│   │   ├── tag.py              # tags table
│   │   ├── audit_log.py        # audit_logs table
│   │   └── import_batch.py     # import_batches table
│   ├── schemas/                # Pydantic models for validation
│   ├── api/v1/                 # API route handlers
│   │   ├── conversations.py    # CRUD for conversations
│   │   ├── tags.py             # Tag management
│   │   ├── import.py           # Excel import endpoint
│   │   ├── export.py           # Excel export endpoint
│   │   ├── recommendations.py  # RAG + AI recommendations
│   │   └── batches.py          # Batch management
│   └── services/
│       ├── data_importer.py    # Excel import logic
│       ├── data_exporter.py    # Excel export logic
│       └── rag/                # RAG recommendation engine
│           ├── rag_service.py          # Main RAG logic
│           ├── vector_store.py         # ChromaDB wrapper
│           └── embedding_service.py    # OpenAI embeddings
├── scripts/
│   ├── init_db.py              # Create database tables
│   ├── import_excel.py         # Import Excel data
│   └── migrate_add_batch.py    # Add batch_id column migration
└── requirements.txt            # Python dependencies
```

### Frontend Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Main conversation audit interface
│   └── globals.css             # Global styles
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── conversation-view.tsx   # Display conversation bubbles
│   ├── conversation-bubble.tsx # Individual message bubble
│   ├── tag-selector.tsx        # Tag selection with keyboard
│   ├── excel-importer.tsx      # Excel file upload
│   ├── rag-recommendations.tsx # AI recommendation display
│   └── keyboard-shortcuts-help.tsx  # Shortcut reference
├── lib/
│   ├── parser.ts               # Parse $_$ format conversation text
│   ├── highlight.ts            # Keyword highlighting
│   ├── constants.ts            # Tag categories, keyword patterns
│   ├── tag-definitions.ts      # All 56 tag definitions
│   ├── api.ts                  # API client functions
│   └── utils.ts                # Utility functions (cn, etc.)
├── hooks/
│   ├── use-conversation.ts     # React Query hooks for API
│   ├── use-keyboard-shortcuts.ts # Keyboard event handlers
│   └── use-global-stats.ts     # Fetch audit statistics
└── package.json                # Dependencies
```

---

## Environment Variables

### Required for Development

```bash
# .env file (root of project)
GLM_API_KEY=your_glm_api_key_here          # For AI recommendations
OPENAI_API_KEY=your_openai_api_key_here    # For embeddings (RAG)
DATABASE_URL=sqlite:///./data/conversations.db
```

**Note**: Code supports both `GLM_API_KEY` and `ZHIPU_API_KEY` for backward compatibility.

### Production (.env.production)

```bash
GLM_API_KEY=your_glm_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
NEXT_PUBLIC_API_URL=http://your-domain.com
BACKEND_CORS_ORIGINS=["http://your-domain.com","https://your-domain.com"]
DEBUG=false
WORKERS=4
```

---

## Database Models

### conversations
- `id`: Primary key
- `raw_text`: Dialog text in `$_$` format
- `driver_tag`: AI-assigned tags (JSON array)
- `manual_tag`: Human-verified tags (JSON array)
- `status`: pending/approved/skipped
- `batch_id`: Import batch foreign key
- `field_length`: Text length
- `created_at`, `updated_at`: Timestamps

### tags
- `id`: Primary key
- `name`: Tag name (e.g., "尾板车", "装卸费")
- `category`: 车型类/费用类/装卸类/车门类/尺寸类/其他
- `definition`: Tag explanation

### audit_logs
- Tracks all tag changes with `ai_tag`, `manual_tag`, `is_correct`, `confidence`

### import_batches
- Tracks Excel import batches with status and record counts

---

## API Endpoints

**Base URL**: `http://localhost:8000` (dev) or `http://your-domain.com` (prod)

### Conversations
- `GET /api/v1/conversations` - List with pagination (`?page=1&limit=10&batch_id=X`)
- `GET /api/v1/conversations/{id}` - Get single conversation
- `PUT /api/v1/conversations/{id}` - Update tags/status
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `DELETE /api/v1/conversations` - Delete all conversations

### Recommendations
- `POST /api/v1/recommendations/ai/analyze` - AI analysis using GLM-4
- `POST /api/v1/recommendations/rag/build` - Build vector index
- `GET /api/v1/recommendations/rag/stats` - Vector index statistics

### Batches
- `GET /api/v1/batches` - List import batches
- `GET /api/v1/batches/{id}` - Batch details
- `DELETE /api/v1/batches/{id}` - Delete batch

### Import/Export
- `POST /api/v1/import/excel` - Upload Excel file
- `GET /api/v1/export/excel` - Download filtered data as Excel

### Docs
- `GET /docs` - Swagger UI (interactive API documentation)
- `GET /health` - Health check endpoint

---

## RAG Recommendation Engine

**Location**: `backend/app/services/rag/`

### How It Works

1. **Build Index** (`/api/v1/recommendations/rag/build`):
   - Extracts all conversations with `manual_tag` set
   - Generates embeddings using OpenAI `text-embedding-3-small`
   - Stores in ChromaDB collection "conversations"

2. **Search** (in `rag_service.py`):
   - Query conversation is embedded
   - ChromaDB finds top-k similar conversations (cosine similarity)
   - Tags from similar conversations are aggregated and ranked by frequency

3. **Fallback**:
   - If no similar conversations found, calls GLM-4 Flash API directly
   - LLM analyzes conversation and selects relevant tags from 56 predefined tags

### Vector Store Configuration

- Collection: `conversations`
- Embedding dimension: 1536 (OpenAI text-embedding-3-small)
- Distance metric: Cosine
- Similarity threshold: 0.5 (configurable)

---

## Frontend Data Flow

### Conversation Display

1. `page.tsx` fetches conversations with `useConversations()` hook
2. `conversation-view.tsx` receives conversation data
3. `parser.parseConversation()` splits `raw_text` by `$_$` into segments
4. `conversation-bubble.tsx` renders each segment (driver=green/right, owner=white/left)
5. `highlight.highlightKeywords()` wraps keywords in `<mark>` tags

### Tag Submission Flow

1. User selects tags via keyboard shortcuts (Space=approve, Enter=next, 1-9=select tags)
2. `useUpdateConversation()` mutation sends `PUT /api/v1/conversations/{id}`
3. Backend updates `manual_tag` and `status` in database
4. React Query invalidates cache, refetches updated list
5. Cursor advances to next pending conversation

### Keyboard Shortcuts

- `Space`: Approve with selected tags, move to next
- `Enter`: Skip current conversation
- `R`: Request AI recommendation
- `1-9`: Quick-select tag numbers from recommendation list
- `←/→`: Navigate between pages

---

## Common Tasks

### Add a New API Endpoint

1. Create route handler in `backend/app/api/v1/`
2. Register in `backend/app/main.py`: `app.include_router(...)`
3. Add TypeScript interface in `frontend/lib/api.ts`
4. Create React Query hook in `frontend/hooks/use-conversation.ts`

### Add New Tag Category

1. Update `frontend/lib/constants.ts` - add to `TAG_CATEGORIES`
2. Update `frontend/lib/tag-definitions.ts` - add tag definitions
3. Backend: Insert into `tags` table via admin or seed script

### Debug AI Recommendations

```bash
# Check if vector index exists
curl http://localhost:8000/api/v1/recommendations/rag/stats

# Rebuild index
curl -X POST http://localhost:8000/api/v1/recommendations/rag/build

# Test AI analysis
curl -X POST http://localhost:8000/api/v1/recommendations/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1}'
```

### Database Operations

```bash
# Enter backend container
docker-compose exec backend bash

# Open SQLite database
sqlite3 /app/data/conversations.db

# Query tables
.tables
SELECT * FROM conversations LIMIT 5;
SELECT * FROM import_batches;

# Exit
.exit
```

---

## Production Deployment

### Quick Deploy

```bash
cp .env.production.example .env.production
# Edit .env.production with API keys and domain
chmod +x deploy.sh && ./deploy.sh
```

### Manual Deploy

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

### Production Architecture

- **Nginx** (port 80/443): Reverse proxy, SSL termination
- **Frontend** (internal:3000): Next.js standalone build
- **Backend** (internal:8000): FastAPI with 4 uvicorn workers
- **Health checks**: `/health` endpoint every 30s
- **Auto-restart**: All services have `restart: always`

---

## Important Gotchas

1. **Environment Variable Names**: Use `GLM_API_KEY`, not `ZHIPU_API_KEY` (though both work)
2. **Docker Volume Mounts**: In development, `./backend:/app` enables hot reload but can cause permission issues
3. **Vector Index**: Must rebuild after importing new data (`POST /api/v1/recommendations/rag/build`)
4. **Conversation Parser**: Expects Chinese colon `：` not `:` when splitting role from content
5. **Tag Storage**: Tags stored as JSON arrays in database: `["尾板车", "装卸费"]`
6. **Frontend API URL**: Set `NEXT_PUBLIC_API_URL` in environment or requests will fail
7. **Next.js Standalone**: Production build requires `output: 'standalone'` in `next.config.ts`
8. **SQLite Locking**: In production, SQLite writes block reads - acceptable for low traffic

---

## References

- **Project Overview**: [README.md](README.md)
- **Architecture Details**: [docs/02-技术架构设计.md](docs/02-技术架构设计.md)
- **RAG Implementation**: [docs/03-数据流程与RAG实现.md](docs/03-数据流程与RAG实现.md)
- **User Manual**: [docs/06-用户使用手册.md](docs/06-用户使用手册.md)
- **Developer Guide**: [docs/07-开发者文档.md](docs/07-开发者文档.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
