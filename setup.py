# setup.py
# Created for OMR Evaluation System
from setuptools import setup, find_packages

setup(
    name="omr-evaluation-system",
    version="1.0.0",
    author="Hackathon Team",
    author_email="team@hackathon.com",
    description="Automated OMR Evaluation & Scoring System using Computer Vision",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/omr-evaluation-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Image Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "opencv-python>=4.8.1",
        "numpy>=1.24.3",
        "pandas>=2.0.3",
        "Pillow>=10.0.0",
        "scikit-learn>=1.3.0",
        "scipy>=1.11.2",
        "imutils>=0.5.4",
        "matplotlib>=3.7.2",
        "seaborn>=0.12.2",
        "SQLAlchemy>=2.0.21",
        "plotly>=5.16.1",
        "streamlit-option-menu>=0.3.6",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "omr-system=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.css", "*.html", "*.jpg", "*.png"],
    },
)