import json
import os
import platform
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path


def get_config_paths():
    system = platform.system()
    paths = {}

    if system == "Windows":
        appdata = os.getenv("APPDATA", "")
        home = os.path.expanduser("~")
        paths["Claude Desktop"] = Path(appdata) / "Claude" / "claude_desktop_config.json"
        paths["Cline"] = Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        paths["Antigravity"] = Path(home) / ".gemini" / "config" / "mcp_config.json"
    elif system == "Darwin":
        home = os.path.expanduser("~")
        paths["Claude Desktop"] = Path(home) / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        paths["Cline"] = Path(home) / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        paths["Antigravity"] = Path(home) / ".gemini" / "config" / "mcp_config.json"
    else:  # Linux
        home = os.path.expanduser("~")
        paths["Claude Desktop"] = Path(home) / ".config" / "Claude" / "claude_desktop_config.json"
        paths["Cline"] = Path(home) / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        paths["Antigravity"] = Path(home) / ".gemini" / "config" / "mcp_config.json"
    
    return paths


def update_config(file_path, command, args):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    if "mcpServers" not in data:
        data["mcpServers"] = {}
        
    data["mcpServers"]["freecad"] = {
        "command": command,
        "args": args
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def uninstall_config(file_path):
    if not file_path.exists():
        return
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return
        
    if "mcpServers" in data and "freecad" in data["mcpServers"]:
        del data["mcpServers"]["freecad"]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreeCAD MCP Server Installer")
        self.minsize(550, 450)
        self.resizable(False, False)
        
        self.paths = get_config_paths()
        self.selections = {}
        
        self._build_ui()

    def _build_ui(self):
        # Header
        header_frame = ttk.Frame(self, padding="20")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="FreeCAD Robust MCP Server", font=("Helvetica", 16, "bold")).pack()
        ttk.Label(header_frame, text="Select the AI assistants you want to configure:").pack(pady=(5, 0))

        # Checkboxes frame
        self.clients_frame = ttk.LabelFrame(self, text="AI Assistants", padding="15")
        self.clients_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for name, path in self.paths.items():
            var = tk.BooleanVar(value=True)
            self.selections[name] = var
            cb = ttk.Checkbutton(self.clients_frame, text=f"{name}", variable=var)
            cb.pack(anchor=tk.W, pady=2)
            
            status_text = "Found" if path.exists() else "Will be created"
            status_color = "green" if path.exists() else "gray"
            ttk.Label(self.clients_frame, text=f"  Config: {path}\n  Status: {status_text}", foreground=status_color, font=("Helvetica", 8)).pack(anchor=tk.W, pady=(0, 10))



        # Buttons
        btn_frame = ttk.Frame(self, padding="20")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Install", command=self.install).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Uninstall", command=self.uninstall).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def install(self):
        selected_clients = [name for name, var in self.selections.items() if var.get()]
        if not selected_clients:
            messagebox.showwarning("Warning", "Please select at least one AI assistant to configure.")
            return

        if getattr(sys, 'frozen', False):
            repo_path = Path(sys.executable).parent
        else:
            repo_path = Path(__file__).resolve().parent.parent.parent
            
        command = "uv"
        args = ["run", "--link-mode=copy", "--directory", str(repo_path), "freecad-mcp"]

        success_count = 0
        for name in selected_clients:
            try:
                update_config(self.paths[name], command, args)
                success_count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure {name}:\n{e}")

        if success_count > 0:
            messagebox.showinfo("Success", f"Successfully configured {success_count} AI assistant(s)!")
            self.destroy()

    def uninstall(self):
        selected_clients = [name for name, var in self.selections.items() if var.get()]
        if not selected_clients:
            messagebox.showwarning("Warning", "Please select at least one AI assistant to configure.")
            return
            
        success_count = 0
        for name in selected_clients:
            try:
                uninstall_config(self.paths[name])
                success_count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to uninstall from {name}:\n{e}")

        if success_count > 0:
            messagebox.showinfo("Success", f"Successfully removed configuration from {success_count} AI assistant(s)!")
            self.destroy()

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
