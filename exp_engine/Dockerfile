FROM python:3.9-alpine

WORKDIR /exp_engine

# Install Java 11 (required by Proactive Executionware)
RUN apk --no-cache add openjdk11 --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community

# Install dependencies
COPY requirements-library.txt requirements-service.txt ./
RUN python3 -m pip install --upgrade pip setuptools wheel python-dotenv && \
    pip install --upgrade --pre proactive && \
    pip install -r requirements-library.txt && \
    pip install -r requirements-service.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

ENV PORT=5556
EXPOSE 5556

ENTRYPOINT ["python"]
CMD ["run.py"]
