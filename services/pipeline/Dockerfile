FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libraqm-dev \
    libfreetype6-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Build Pillow from source so it links against libraqm (HarfBuzz nikud support)
RUN pip install --upgrade pip \
    && pip install --no-binary Pillow Pillow

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app

CMD ["python3", "run_full_book_10pages.py", "נועה", "6", "פחד לטעות ולהפסיד"]
