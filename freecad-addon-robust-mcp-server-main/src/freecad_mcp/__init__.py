"""FreeCAD Robust MCP Server - AI assistant integration for FreeCAD.

SPDX-License-Identifier: MIT
Copyright (c) 2025 Sean P. Kane (GitHub: spkane)

This package provides an MCP (Model Context Protocol) server that enables
integration between AI assistants (Claude, GPT, etc.) and FreeCAD, allowing
AI-assisted development and debugging of 3D models, macros, and workbenches.

Example:
    Run the Robust MCP Server::

        $ freecad-mcp

    Or with Python::

        >>> from freecad_mcp.server import main
        >>> main()
"""

__version__ = "0.1.0"

__author__ = "Sean P. Kane"
__email__ = "spkane@gmail.com"

from freecad_mcp.server import mcp

__all__ = ["__version__", "mcp"]
