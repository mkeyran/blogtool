"""
Setup script for creating macOS app bundle with py2app.
"""
from setuptools import setup

APP = ['blogtool/cli.py']
DATA_FILES = [
    ('', ['resources/icon.icns']),
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'resources/icon.icns',
    'plist': {
        'CFBundleName': 'BlogTool',
        'CFBundleDisplayName': 'BlogTool',
        'CFBundleIdentifier': 'com.keyran.blogtool',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'BTOL',
        'CFBundleExecutable': 'BlogTool',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15',
        'NSHumanReadableCopyright': 'Copyright © 2024 keyran',
        'CFBundleDocumentTypes': [],
        'NSAppleScriptEnabled': False,
        'NSPrincipalClass': 'NSApplication',
    },
    'packages': [
        'blogtool',
        'blogtool.core',
        'blogtool.ui',
        'blogtool.utils',
    ],
    'includes': [
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'click',
        'requests',
    ],
    'excludes': [
        'tkinter',
        'test',
        'tests',
        'pytest',
        'setuptools',
        'pip',
        'distutils',
    ],
    'resources': [
        'resources/icon.icns',
    ],
    'optimize': 2,
    'compressed': True,
    'strip': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='BlogTool',
    version='0.1.0',
    description='Qt-based Hugo blog management console',
    author='keyran',
    author_email='keyran@example.com',
)