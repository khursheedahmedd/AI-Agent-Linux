from setuptools import setup, find_packages

setup(
    name="sadain-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True, # To include non-code files specified in MANIFEST.in if you add one
    install_requires=[
        "langchain",
        "langgraph",
        "langchain-groq",
        "python-dotenv",
        "typer[all]",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "sadain = sadain_cli.__main__:entry_point",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A terminal-based AI assistant.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sadain-cli", # Replace with your repo
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Choose your license
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    python_requires='>=3.9',
)