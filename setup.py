from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="polyglot-rag-assistant",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A multilingual voice-enabled flight search assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/polyglot-rag-assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=1.0.0",
        "httpx>=0.25.2",
        "numpy>=1.24.3",
        "livekit>=0.11.1",
        "anthropic>=0.21.3",
        "openai>=1.12.0",
        "langchain>=0.1.16",
        "langgraph>=0.0.37",
        "faiss-cpu>=1.7.4",
        "gradio>=4.19.2",
    ],
    entry_points={
        "console_scripts": [
            "polyglot-rag=main:main",
            "polyglot-gradio=frontend.gradio_app:main",
            "polyglot-mcp=mcp_servers.flight_search_server:main",
        ],
    },
)