"""Command line interface for the blog management console."""

import sys

from .ui.app import BlogToolApp


def main() -> None:
    """Main entry point for the CLI."""
    print("Hugo Blog Management Console")
    print("Version: 0.1.0")
    print("Starting GUI application...")

    app = BlogToolApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
