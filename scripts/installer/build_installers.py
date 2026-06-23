import os
import platform
import subprocess
import sys
from pathlib import Path

def main():
    # Ensure we are in the repository root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    
    os.chdir(repo_root)
    
    installer_script = script_dir / "installer.py"
    
    if not installer_script.exists():
        print(f"Error: Could not find {installer_script}")
        sys.exit(1)
        
    print(f"Building installer for {platform.system()}...")
    
    # Run PyInstaller
    # --onefile: creates a single executable
    # --windowed: no console window (for GUI)
    # --name: the name of the output executable
    # --clean: clean PyInstaller cache
    cmd = [
        "uv", "run", "pyinstaller",
        "--onefile",
        "--windowed",
        "--clean",
        "--name", "FreeCAD-MCP-Installer",
        str(installer_script)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful!")
        dist_dir = repo_root / "dist"
        
        system = platform.system()
        if system == "Windows":
            exe_path = dist_dir / "FreeCAD-MCP-Installer.exe"
        else:
            exe_path = dist_dir / "FreeCAD-MCP-Installer"
            
        if exe_path.exists():
            print(f"Installer built at: {exe_path}")
        else:
            print("Warning: Build completed but output file not found in 'dist' directory.")
            
    except subprocess.CalledProcessError as e:
        print(f"\nError: PyInstaller failed with code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
