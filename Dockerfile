# syntax=docker/dockerfile:1

# ============================================================
# 1. Base image nhe & bao mat (Debian Slim, khong phai full)
#    Chon python:3.11-slim thay vi alpine de tranh loi build
#    cac package khoa hoc (numpy/pandas/statsmodels can glibc).
# ============================================================
FROM python:3.11-slim

# ============================================================
# 4. Bien moi truong
# ============================================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    DATABASE_URL=sqlite:////app/data/chi-tieu.db

# ============================================================
# 3. Working directory ro rang
# ============================================================
WORKDIR ${APP_HOME}

# ============================================================
# 2. Layer caching: copy file dependency TRUOC, roi moi copy source.
#    Khi chi sua code ma khong doi requirements, Docker se reuse
#    layer pip install nay (nhanh hon rat nhieu).
# ============================================================
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy toan bo ma nguon (da loai tru venv/.db qua .dockerignore)
COPY . .

# Tao thu muc luu DB + cap quyen
RUN mkdir -p /app/data

# ============================================================
# 5. Non-root user (tang bao mat)
# ============================================================
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser ${APP_HOME}
USER appuser

# ============================================================
# Mo port
# ============================================================
EXPOSE 8000

# ============================================================
# 6. Lenh chay ung dung
# ============================================================
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
