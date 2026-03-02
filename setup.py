"""
AlbertDesk - Remote Desktop Control Software Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="albertdesk",
    version="1.2.0",
    author="Albert",
    author_email="albert@albertdesk.dev",
    description="Professional remote desktop control software with LAN and internet support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/erickson558/albertdesk",
    project_urls={
        "Bug Tracker": "https://github.com/erickson558/albertdesk/issues",
        "Documentation": "https://github.com/erickson558/albertdesk/wiki",
        "Source Code": "https://github.com/erickson558/albertdesk",
        "Releases": "https://github.com/erickson558/albertdesk/releases",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Topic :: System :: Networking",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Communications",
        "Environment :: X11 Applications :: Qt",
    ],
    keywords="remote-desktop vnc rdp screen-sharing remote-control cloudflare-tunnel",
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "Pillow>=10.0.0",
        "mss>=9.0.0",
    ],
    extras_require={
        "dev": [
            "pyinstaller>=6.0.0",
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "albertdesk=main:main",
        ],
    },
)
