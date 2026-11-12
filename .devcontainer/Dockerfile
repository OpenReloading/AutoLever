FROM mcr.microsoft.com/devcontainers/python:3.15-bookworm@sha256:25ac34e3c1a4c5b19a89ece73ed0278e92afc1cfd25ecb51714891e82bede421

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# The Python Playwright version below is the pin of requirements.in (build context: the repository root), which Dependabot updates.
COPY requirements.in /tmp/requirements.in

# Node 24 for the Playwright MCP server; each Playwright build installs its own Chromium.
RUN curl -fsSLo /tmp/node.tar.xz https://nodejs.org/dist/v24.21.0/node-v24.21.0-linux-x64.tar.xz \
 && echo 'fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6  /tmp/node.tar.xz' | sha256sum -c - \
 && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --exclude='*.md' --exclude=LICENSE \
 && rm /tmp/node.tar.xz \
 && npm install -g @playwright/mcp@0.0.83 \
 && node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" install --with-deps chromium \
 && python -m venv /tmp/pw \
 && pin=$(grep -x 'playwright==[0-9.]*' /tmp/requirements.in) \
 && /tmp/pw/bin/pip install --no-cache-dir "$pin" \
 && /tmp/pw/bin/playwright install --with-deps chromium \
 && rm -rf /tmp/pw /tmp/requirements.in /root/.npm /var/lib/apt/lists/* \
 && chmod -R a+rX /ms-playwright

# OpenSCAD for the render checks of cad/ (tests/test_cad.py)
RUN apt-get update && apt-get install -y --no-install-recommends openscad \
 && rm -rf /var/lib/apt/lists/*

USER vscode
