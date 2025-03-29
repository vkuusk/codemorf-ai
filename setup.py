from setuptools import setup, find_packages

setup(
    name="codemorf",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "langgraph>=0.0.10",
        "openai>=1.3.0",
        "ollama>=0.1.0",
        "anthropic>=0.18.0",
        "setuptools",
    ],
    entry_points={
        "console_scripts": [
            "codemorf=cli.codemorf:main",
        ],
    },
    python_requires=">=3.8",
    description="A tool that uses LLMs to refactor code",
    author="Vlad Kuusk",
    author_email="vkuusk@cembryonix.com",
    url="https://github.com/vkuusk/codemorf-ai",
)
