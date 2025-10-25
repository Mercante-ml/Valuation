#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Check the value of the 'SERVICE_TYPE' environment variable
# Render doesn't set this automatically, so we'll rely on the command override.
# We will define the default CMD in Dockerfile to run gunicorn,
# and Render's worker service will implicitly override this CMD when it starts.

# Default command (will be run by the web service)
echo "Starting Gunicorn..."
exec gunicorn valuation.wsgi:application --bind 0.0.0.0:${PORT:-8000}

# Note: For the worker, Render will likely execute the container without
# overriding the command specified in the Dockerfile's CMD if we don't
# explicitly define one in render.yaml. Since we removed startCommand,
# we need a way to differentiate. A simpler approach might be needed.

# Let's simplify: We'll have ONE Dockerfile, but rely on Render implicitly
# running the default CMD for web, and maybe needing a different start command
# for worker IF the default CMD isn't suitable.
# Re-evaluating: The Render errors suggest NO startCommand at all.
# This means the Dockerfile's CMD MUST be the single command to run.
# This won't work easily for two different services (web and worker) from one Dockerfile.

# --- ALTERNATIVE APPROACH: Separate Dockerfiles or Entrypoint logic ---

# Let's stick to ONE Dockerfile and assume Render handles the command difference.
# The default CMD will be for Gunicorn. Render's worker service type MIGHT
# automatically run 'celery' if specified somewhere else, but since we removed
# startCommand, this is unlikely.

# --- REVISED SAFER APPROACH: Use Dockerfile CMD ---
# The Dockerfile will define the Gunicorn command.
# The worker service in render.yaml *might* need a command override if Render allows it
# for workers *despite* the error message (sometimes error messages are too generic).
# OR, we use separate Dockerfiles.

# Let's assume the error means NO startCommand in render.yaml AT ALL.
# We will set the Dockerfile CMD for gunicorn.
# We will try deploying. If the Celery worker fails to start correctly (because
# it tries to run gunicorn), we'll need to adjust.