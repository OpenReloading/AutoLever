FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm@sha256:68aef3859e340a2b0cc63260978c5d40e82f48e30fb00503c59cea9104ff8a6b

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Node 24 for the Playwright MCP server; each Playwright build installs its own Chromium.
RUN curl -fsSLo /tmp/node.tar.xz https://nodejs.org/dist/v24.21.0/node-v24.21.0-linux-x64.tar.xz \
 && echo 'fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6  /tmp/node.tar.xz' | sha256sum -c - \
 && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --exclude='*.md' --exclude=LICENSE \
 && rm /tmp/node.tar.xz \
 && npm install -g @playwright/mcp@0.0.83 \
 && node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" install --with-deps chromium \
 && python -m venv /tmp/pw \
 && /tmp/pw/bin/pip install --no-cache-dir playwright==1.64.0 \
 && /tmp/pw/bin/playwright install --with-deps chromium \
 && rm -rf /tmp/pw /root/.npm /var/lib/apt/lists/* \
 && chmod -R a+rX /ms-playwright

# OpenSCAD for the render checks of cad/ (tests/test_cad.py)
RUN apt-get update && apt-get install -y --no-install-recommends openscad \
 && rm -rf /var/lib/apt/lists/*

USER vscode
