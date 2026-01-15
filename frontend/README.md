# Research Radar Frontend

React-based UI for Research Radar with UMD build support.

## Setup

Install dependencies:

```bash
npm install
```

## Development

Run the development server with API proxy:

```bash
npm run dev
```

The dev server will run on `http://localhost:5173` and proxy API requests to `http://localhost:8000`.

## Build

Build the UMD bundle:

```bash
npm run build
```

This creates a UMD bundle in the `dist/` directory that can be used standalone or integrated with the FastAPI backend.

## Production

The built files in `dist/` are served by the FastAPI backend at `http://localhost:8000`.

## Architecture

- **Vite**: Build tool with React plugin
- **React 18**: UI framework
- **react-markdown**: Markdown rendering for analysis results
- **UMD Format**: Universal module definition for maximum compatibility

## API Integration

The frontend communicates with the FastAPI backend via `/api/analyze` endpoint:

```javascript
POST /api/analyze
{
  "paper_id": "2510.24081",
  "keywords": ["LLMs", "Transformers"]
}
```

Response:
```javascript
{
  "paper_id": "2510.24081",
  "summary": "...",
  "analysis": {...},
  "status": "success"
}
```
