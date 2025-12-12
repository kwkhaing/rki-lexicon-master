FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements_nlp.txt requirements_audio.txt requirements_llm.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_nlp.txt && \
    pip install --no-cache-dir -r requirements_audio.txt

COPY . .

RUN mkdir -p data corpus models

VOLUME ["/app/data", "/app/corpus", "/app/models"]

CMD ["python", "scripts/data_processing.py"]