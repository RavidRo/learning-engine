#!/usr/bin/env bash
set -euo pipefail

# Setup script for Codex cloud environments. It prepares the same tools used by
# the repository Taskfiles so agents can run backend and webapp checks without
# spending task time on one-off installation work.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_BIN="${HOME}/.local/bin"
export PATH="${LOCAL_BIN}:${HOME}/.cargo/bin:${PATH}"

PYTHON_VERSION="3.14"
PNPM_VERSION="11.1.2"
NODE_VERSION="24"
TASK_VERSION="v3.51.1"

mkdir -p "${LOCAL_BIN}"
cd "${REPO_ROOT}"

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  curl -LsSf https://astral.sh/uv/install.sh | sh
}

install_task() {
  if command -v task >/dev/null 2>&1; then
    return
  fi

  local os
  local arch
  local archive
  local temp_dir
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "${arch}" in
    x86_64 | amd64) arch="amd64" ;;
    aarch64 | arm64) arch="arm64" ;;
    *)
      echo "Unsupported architecture for Task binary install: ${arch}" >&2
      return 1
      ;;
  esac

  archive="task_${os}_${arch}.tar.gz"
  temp_dir="$(mktemp -d)"
  curl -fsSL --retry 3 --output "${temp_dir}/${archive}" \
    "https://github.com/go-task/task/releases/download/${TASK_VERSION}/${archive}"
  tar -xzf "${temp_dir}/${archive}" -C "${temp_dir}" task
  install -m 0755 "${temp_dir}/task" "${LOCAL_BIN}/task"
  rm -rf "${temp_dir}"
}

install_node_with_nvm() {
  if command -v node >/dev/null 2>&1; then
    return
  fi

  export NVM_DIR="${NVM_DIR:-${HOME}/.nvm}"
  if [ ! -s "${NVM_DIR}/nvm.sh" ]; then
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  fi

  # shellcheck source=/dev/null
  . "${NVM_DIR}/nvm.sh"
  nvm install "${NODE_VERSION}"
  nvm use "${NODE_VERSION}"
}

install_pnpm() {
  if command -v corepack >/dev/null 2>&1; then
    corepack enable
    corepack prepare "pnpm@${PNPM_VERSION}" --activate
    return
  fi

  npm install --global "pnpm@${PNPM_VERSION}"
}

install_uv
uv python install "${PYTHON_VERSION}"
install_node_with_nvm
install_task
install_pnpm

task backend:sync
pnpm --dir webapp install --frozen-lockfile

task --list
