# Stories Platform - Monorepo

This repository contains the complete Stories Platform for generating personalized children's books with Hebrew text, nikud (vowel marks), and AI-generated illustrations.

## Repository Structure

```
stories-test/
├── apps/
│   └── web/          # Lovable UX - Web interface for story generation
├── services/
│   └── pipeline/     # Python pipeline for end-to-end book generation
└── docs/             # Documentation
```

---

## Apps

### Web Interface (`apps/web`)

A modern web application built with Vite + React + TypeScript for creating and managing personalized children's stories.

#### Quickstart - Web

```bash
cd apps/web
npm install
npm run dev
```

The web app will be available at `http://localhost:5173`

#### Build for Production

```bash
cd apps/web
npm run build
```

---

## Services

### Pipeline (`services/pipeline`)

A Python-based automated pipeline that generates complete 10-page children's books with:
- Story generation (Claude API)
- AI-generated illustrations (Imagen 3)
- Hebrew text with nikud (vowel marks)
- PDF generation with professional layout
- Quality assurance validation

#### Quickstart - Pipeline

**1. Create virtual environment:**

```bash
cd services/pipeline
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables:**

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env and add:
# - ANTHROPIC_API_KEY=your_claude_api_key
# - GOOGLE_APPLICATION_CREDENTIALS=path/to/google/credentials.json
```

**4. Run the full pipeline:**

```bash
python3 run_full_book_10pages.py <child_name> <age> <topic>
```

Example:
```bash
python3 run_full_book_10pages.py "מיכל" 6 "מיכל מגלה את הספרייה"
```

This will:
1. Generate a 10-page story (Stage 1)
2. Generate illustrations with QA validation (Stage 3)
3. Create a PDF with nikud (Stage 5)

---

## Pipeline Stages

The pipeline consists of 5 stages:

1. **Story Generation**: Claude generates a 10-page personalized story
2. ~~Visual Planning~~: (Optional - currently skipped)
3. **Image Generation**: Imagen 3 creates illustrations with QA loop:
   - Resolution check (1184x864)
   - White space percentage (<30%)
   - Border detection (no frames)
   - Text-area intrusion check (<15%)
   - Retry mechanism (max 3 attempts with delta prompts)
4. ~~Validation~~: (Integrated into Stage 3)
5. **PDF Generation**: Create final PDF with:
   - Hebrew text with nikud
   - Full-bleed images
   - Triple-constraint text layout (width + 4 words/line + 23 chars/line)
   - Professional formatting for iPad (1024x768)

---

## Outputs and Data Policy

**All generated artifacts are local and NOT committed to git:**

- `data/runs/`: Complete run outputs (stories, images, PDFs, QA reports)
- `data/.nikud_cache/`: Cached nikud dictionary
- `*.pdf`, `*.png`: Generated files
- `logs/`, `qa/`: Validation and logging data

These directories are excluded via `.gitignore` to keep the repository clean and avoid committing large binary files or sensitive data.

---

## Configuration

### Pipeline Configuration

Key parameters are defined in the code:

- **Text layout**: 30px right margin, 35% text area width
- **Word limits**: 4 words/line (font 22pt), scales with font size
- **Character limit**: 23 chars/line max (including spaces)
- **QA thresholds**:
  - White space: <30%
  - Text-area intrusion: <15%
  - Border detection: <3 uniform edges
  - Max retries: 3

### Environment Variables

Required environment variables (see `.env.example`):

- `ANTHROPIC_API_KEY`: Claude API key for story generation and nikud
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials for Imagen 3

---

## Development

### Web App Development

```bash
cd apps/web
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
npm run lint     # Run linter
```

### Pipeline Development

```bash
cd services/pipeline
source venv/bin/activate
python3 run_full_book_10pages.py --help
```

---

## Cost Estimates

Per 10-page book:
- Claude (story + nikud): ~$0.50
- Imagen 3 (10 images × 1-3 attempts): ~$1.50-$3.00
- **Total**: ~$2-3.50 per book

---

## Support & Issues

For issues or questions:
- GitHub Issues: https://github.com/Omribarzi/stories-test/issues

---

## License

Proprietary - All rights reserved
