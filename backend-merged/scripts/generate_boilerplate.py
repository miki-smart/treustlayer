"""
Generate __init__.py files for all module directories.

This ensures Python recognizes all directories as packages.
"""
from pathlib import Path


def create_init_files():
    """Create __init__.py in all directories that don't have one."""
    
    base_dir = Path(__file__).parent.parent / "app"
    
    for directory in base_dir.rglob("*"):
        if directory.is_dir():
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""\nModule package.\n"""\n')
                print(f"Created {init_file.relative_to(base_dir.parent)}")
    
    print("\nAll __init__.py files created")


if __name__ == "__main__":
    create_init_files()
