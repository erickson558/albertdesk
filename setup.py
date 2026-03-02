"""
AlbertDesk - Remote Desktop Control Software Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="albertdesk",
    version="1.0.0",
    author="Albert",
    description="Professional remote desktop control software with LAN and internet support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/albertdesk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Networking",
        "Topic :: Multimedia :: Graphics :: Viewers",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "Pillow>=10.0.0",
        "mss>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "albertdesk=albertdesk.main:main",
        ],
    },
)
