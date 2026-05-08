"""Symlink custom_components into HA config for devcontainer development."""

import os
from pathlib import Path


def setup_symlink():
    """Create symlink from config/custom_components to workspace custom_components."""
    workspace = Path(__file__).parent.parent
    config_cc = workspace / "config" / "custom_components"
    source = workspace / "custom_components"

    if config_cc.is_symlink():
        config_cc.unlink()

    if not config_cc.exists():
        os.symlink(source, config_cc)
        print(f"Symlinked {config_cc} -> {source}")


if __name__ == "__main__":
    setup_symlink()
