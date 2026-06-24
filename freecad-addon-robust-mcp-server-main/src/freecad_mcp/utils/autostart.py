"""Auto-starter utility for FreeCAD headless mode.

This module provides cross-platform functionality to automatically
locate and start FreeCAD with the MCP Bridge if it is not already running.
"""

import contextlib
import logging
import os
import platform
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoStarter:
    """Manages auto-starting FreeCAD if it's not currently running."""

    def __init__(self, host: str, xmlrpc_port: int, socket_port: int) -> None:
        self.host = host
        self.xmlrpc_port = xmlrpc_port
        self.socket_port = socket_port
        self._process: subprocess.Popen | None = None
        self._temp_script_path: str | None = None

    def _find_windows(self) -> list[str]:
        """Find FreeCAD on Windows."""
        paths = []
        base_paths = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for base in base_paths:
            if not base:
                continue
            for d in sorted(Path(base).glob("FreeCAD*"), reverse=True):
                cmd_path = d / "bin" / "FreeCADCmd.exe"
                gui_path = d / "bin" / "FreeCAD.exe"
                if cmd_path.exists():
                    paths.append(str(cmd_path))
                elif gui_path.exists():
                    paths.append(str(gui_path))
        return paths

    def _find_mac(self) -> list[str]:
        """Find FreeCAD on macOS."""
        return [
            "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd",
            str(Path("~/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd").expanduser()),
        ]

    def _find_linux(self) -> list[str]:
        """Find FreeCAD on Linux."""
        import shutil
        paths = []
        for cmd in ["freecadcmd", "FreeCADCmd"]:
            p = shutil.which(cmd)
            if p:
                paths.append(p)
        paths.extend([
            "/usr/bin/freecadcmd",
            "/usr/local/bin/freecadcmd",
            "/opt/freecad/bin/FreeCADCmd",
        ])
        return paths

    def _find_freecad(self) -> str | None:
        """Attempt to find the FreeCAD executable across different platforms."""
        if "FREECAD_CMD" in os.environ:
            return os.environ["FREECAD_CMD"]

        system = platform.system()
        if system == "Windows":
            paths = self._find_windows()
        elif system == "Darwin":
            paths = self._find_mac()
        else:
            paths = self._find_linux()

        for path in paths:
            if Path(path).exists() and os.access(path, os.X_OK):
                return path
        return None

    def _generate_bootstrap_script(self) -> str:
        """Generate the Python script that FreeCAD will run."""
        return f"""
import sys
import os
import time

try:
    import FreeCAD
except ImportError:
    print("ERROR: Must be run inside FreeCAD")
    sys.exit(1)

def start_mcp():
    print("Auto-starting Robust MCP Bridge...")
    mod_paths = [
        os.path.join(FreeCAD.getUserAppDataDir(), "Mod"),
        os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod"),
        os.path.join(FreeCAD.ConfigGet("AppHomePath"), "Mod"),
    ]
    local_source_mod = r"{Path(__file__).resolve().parent.parent.parent.parent / 'freecad'}"
    if os.path.exists(local_source_mod):
        mod_paths.append(local_source_mod)

    bridge_path = None
    for mod_path in mod_paths:
        p1 = os.path.join(mod_path, "RobustMCPBridge")
        p2 = os.path.join(mod_path, "freecad", "RobustMCPBridge")
        if os.path.exists(os.path.join(p1, "freecad_mcp_bridge", "server.py")):
            bridge_path = p1
            break
        elif os.path.exists(os.path.join(p2, "freecad_mcp_bridge", "server.py")):
            bridge_path = p2
            break

    if not bridge_path:
        print("ERROR: RobustMCPBridge workbench not found in FreeCAD Mod paths.")
        print("Paths checked:", mod_paths)
        sys.exit(1)

    print(f"Found bridge at: {{bridge_path}}")
    sys.path.insert(0, bridge_path)

    try:
        from freecad_mcp_bridge.server import FreecadMCPPlugin
        plugin = FreecadMCPPlugin(
            host="{self.host}",
            port={self.socket_port},
            xmlrpc_port={self.xmlrpc_port},
            enable_xmlrpc=True
        )
        plugin.start()
        print("MCP Bridge Auto-Started Successfully on ports {self.socket_port} (JSON-RPC) and {self.xmlrpc_port} (XML-RPC)")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"ERROR: Failed to start MCP Bridge: {{e}}")
        sys.exit(1)

start_mcp()
"""

    def start(self) -> bool:
        """Start FreeCAD in the background if not running."""
        exe = self._find_freecad()
        if not exe:
            logger.error("Could not locate FreeCAD executable for auto-start.")
            return False

        logger.info("Auto-starting FreeCAD using: %s", exe)
        script = self._generate_bootstrap_script()

        fd, self._temp_script_path = tempfile.mkstemp(suffix=".py", prefix="freecad_mcp_bootstrap_")
        with os.fdopen(fd, "w") as f:
            f.write(script)

        try:
            self._process = subprocess.Popen(  # noqa: S603
                [exe, self._temp_script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            logger.error("Failed to spawn FreeCAD process: %s", e)
            if self._temp_script_path and Path(self._temp_script_path).exists():
                with contextlib.suppress(OSError):
                    Path(self._temp_script_path).unlink()
                self._temp_script_path = None
            return False

    def stop(self) -> None:
        """Stop the spawned FreeCAD process if we started one."""
        if self._process:
            logger.info("Stopping auto-started FreeCAD process...")
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                logger.error("Error terminating FreeCAD process: %s", e)
            self._process = None

        if self._temp_script_path and Path(self._temp_script_path).exists():
            try:
                Path(self._temp_script_path).unlink()
            except OSError:
                logger.warning("Could not remove temporary bootstrap script: %s", self._temp_script_path)
            self._temp_script_path = None

