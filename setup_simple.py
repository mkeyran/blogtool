"""
Simplified setup script for creating macOS app bundle with py2app.
"""
from setuptools import setup

setup(
    name="BlogTool",
    version="0.1.0",
    description="Qt-based Hugo blog management console",
    author="keyran",
    author_email="keyran@example.com",
    app=['blogtool/__main__.py'],
    data_files=[
        ('', ['resources/icon.icns']),
    ],
    options={
        'py2app': {
            'iconfile': 'resources/icon.icns',
            'argv_emulation': True,
            'site_packages': True,
            'plist': {
                'CFBundleName': 'BlogTool',
                'CFBundleDisplayName': 'BlogTool',
                'CFBundleIdentifier': 'com.keyran.blogtool',
                'CFBundleVersion': '0.1.0',
                'CFBundleShortVersionString': '0.1.0',
                'NSHighResolutionCapable': True,
                'NSRequiresAquaSystemAppearance': False,
                'LSMinimumSystemVersion': '10.15',
            },
            'packages': ['PySide6', 'shiboken6'],
            'includes': ['blogtool', 'blogtool.core', 'blogtool.ui', 'blogtool.utils'],
            'excludes': ['tkinter', 'test', 'tests'],
        }
    },
    setup_requires=['py2app'],
)