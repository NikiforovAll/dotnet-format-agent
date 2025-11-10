#!/usr/bin/env python3
"""Bump version across workspace pyproject.toml files."""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string into tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(version: str, bump_type: Literal["major", "minor", "patch"]) -> str:
    """Bump semantic version by type."""
    major, minor, patch = parse_version(version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_version_in_file(file_path: Path, new_version: str) -> bool:
    """Update version in a pyproject.toml file."""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")

    # Match version = "x.y.z" pattern
    pattern = r'(version\s*=\s*")[^"]+(")'
    updated_content = re.sub(pattern, rf'\g<1>{new_version}\g<2>', content)

    if content != updated_content:
        file_path.write_text(updated_content, encoding="utf-8")
        return True
    return False


def update_changelog(changelog_path: Path, new_version: str) -> bool:
    """Update CHANGELOG.md with new version section."""
    if not changelog_path.exists():
        return False

    content = changelog_path.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the [Unreleased] section
    unreleased_pattern = r"## \[Unreleased\]"

    if not re.search(unreleased_pattern, content):
        print("  Warning: [Unreleased] section not found in CHANGELOG.md")
        return False

    # Replace [Unreleased] with new version and add new [Unreleased] section
    new_content = re.sub(
        unreleased_pattern,
        f"## [Unreleased]\n\n## [{new_version}] - {today}",
        content,
        count=1
    )

    if content != new_content:
        changelog_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <major|minor|patch>")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ["major", "minor", "patch"]:
        print(f"Error: Invalid bump type '{bump_type}'. Use: major, minor, or patch")
        sys.exit(1)

    # Find workspace root (has workspace member definitions)
    workspace_root = Path.cwd()
    root_pyproject = workspace_root / "pyproject.toml"

    if not root_pyproject.exists():
        print("Error: pyproject.toml not found in current directory")
        sys.exit(1)

    # Read current version from root
    content = root_pyproject.read_text(encoding="utf-8")
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)

    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    current_version = version_match.group(1)
    new_version = bump_version(current_version, bump_type)

    print(f"Bumping version: {current_version} -> {new_version}")

    # Update all pyproject.toml files
    files_to_update = [
        root_pyproject,
        workspace_root / "src" / "tde" / "pyproject.toml",
        workspace_root / "src" / "tda" / "pyproject.toml",
    ]

    updated_files = []
    for file_path in files_to_update:
        if update_version_in_file(file_path, new_version):
            updated_files.append(str(file_path.relative_to(workspace_root)))
            print(f"  Updated: {file_path.relative_to(workspace_root)}")

    # Update CHANGELOG.md
    changelog_path = workspace_root / "CHANGELOG.md"
    if update_changelog(changelog_path, new_version):
        updated_files.append("CHANGELOG.md")
        print(f"  Updated: CHANGELOG.md")

    if updated_files:
        print(f"\nSuccessfully updated {len(updated_files)} files")
    else:
        print("\nNo files were updated")


if __name__ == "__main__":
    main()
