# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the wheel file
COPY codemorf-*.whl .

# Install the package and its dependencies
RUN pip install --no-cache-dir codemorf-*.whl

# Create a directory for user data
RUN mkdir -p /data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the entrypoint to the codemorf command
ENTRYPOINT ["codemorf"]

# Default command (can be overridden)
CMD ["--help"]
