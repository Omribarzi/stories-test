# Stories Pipeline - Python Service

End-to-end automated pipeline for generating personalized children's books with Hebrew text, nikud, and AI-generated illustrations.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and GOOGLE_APPLICATION_CREDENTIALS

# 4. Generate a book
python3 run_full_book_10pages.py "child_name" 6 "story_topic"
```

## For detailed documentation, see:
- [Main README](../../docs/README.md) - Complete overview
- [Pipeline Status](../../docs/STATUS.md) - Current state and known issues
