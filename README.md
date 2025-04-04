<div align="center">

# 🔏 Privacy-Preserving Emotion Analysis

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Unlicense-green.svg)](LICENSE)
[![Transformers](https://img.shields.io/badge/🤗_Transformers-v4.28+-blueviolet.svg)](https://huggingface.co/transformers/)
[![TenSEAL](https://img.shields.io/badge/TenSEAL-Latest-orange.svg)](https://github.com/OpenMined/TenSEAL)
[![Flask](https://img.shields.io/badge/Flask-v2.0+-lightgrey.svg)](https://flask.palletsprojects.com/)
[![spaCy](https://img.shields.io/badge/spaCy-v3.5+-9cf.svg)](https://spacy.io/)
[![Chart.js](https://img.shields.io/badge/Chart.js-v3.9+-yellow.svg)](https://www.chartjs.org/)

<!-- <p align="center">
  <img src="https://user-images.githubusercontent.com/your-username/encode-zkML-bootcamp-project/screenshots/banner.png" alt="Project Banner" width="600">
</p> -->

Analyze emotions in Bluesky posts with advanced NLP and protect privacy using Fully Homomorphic Encryption

</div>

<div align="center">

 [🔍 Overview](#-overview)
| [✨ Features](#-features)
| [🏗️ Architecture](#️-architecture)
| [🔄 How It Works](#-how-it-works)
| [🛠️ Technologies Used](#️-technologies-used)
| [🚀 Getting Started](#-getting-started)
| [📘 Usage](#-usage)
| [🖼️ Screenshots](#️-screenshots)
| [🔒 Privacy Features](#-privacy-features)
| [🤝 Contributing](#-contributing)
| [📄 License](#-license)

</div>

## 🔍 Overview

This project implements a privacy-preserving emotion analysis system for Bluesky posts using Fully Homomorphic Encryption (FHE). It allows users to analyze emotions related to specific questions or topics without revealing the actual posts or the emotion analysis model. The system detects 7 distinct emotions (joy, sadness, anger, fear, surprise, disgust, neutral) using a DistilRoBERTa model and visualizes results with interactive charts.

## ✨ Features

- **Advanced Keyword Extraction** using spaCy NLP for better post relevance
- **Nuanced Emotion Analysis** with DistilRoBERTa detecting 7 emotions
- **Privacy Protection** using TenSEAL for Fully Homomorphic Encryption
- **Interactive Visualizations** with Chart.js
- **User-Friendly Web Interface** built with Bootstrap
- **Command-Line Interface** for automated processing
- **Automatic Setup** with a single batch file

## 🏗️ Architecture

```mermaid
graph TD
    A[User] -->|Question/Topic| B[Web Interface]
    B -->|API Request| C[Flask Backend]
    C -->|Keyword Extraction| D[spaCy NLP]
    D -->|Keywords| E[Bluesky API]
    E -->|Retrieved Posts| F[Emotion Analysis]
    F -->|Uses| G[DistilRoBERTa Model]
    F -->|For Privacy| I[FHE Integration]
    I -->|Encrypt| J[Encrypted Data]
    J -->|Compute On| K[Encrypted Computation]
    K -->|Decrypt| L[Secure Results]
    F -->|Results| H[Interactive Visualization]
    H -->|Display| B
    L -->|Privacy Info| B

    subgraph Frontend
    B
    H
    end

    subgraph Backend Services
    C
    D
    E
    F
    G
    I
    J
    K
    L
    end
```

## 🔄 How It Works

```mermaid
sequenceDiagram
    participant User
    participant WebUI as Web Interface
    participant API as Flask API
    participant NLP as Keyword Extractor
    participant BSky as Bluesky API
    participant FHE as FHE Integrator
    participant Model as Emotion Model

    User->>WebUI: Submit question & credentials
    WebUI->>API: POST /analyze
    API->>NLP: Extract keywords from question
    NLP-->>API: Return relevant keywords
    API->>BSky: Search posts with keywords
    BSky-->>API: Return matching posts
    API->>FHE: Generate embeddings
    FHE->>FHE: Encrypt embeddings
    FHE->>FHE: Perform computation on encrypted data
    FHE->>FHE: Decrypt results
    FHE-->>API: Return secure results
    API->>Model: Additional analysis for visualization
    Model-->>API: Return visualization data
    API->>WebUI: Send analysis results & FHE details
    WebUI->>User: Display results with privacy information
```

## 🛠️ Technologies Used

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Chart.js
- **Backend**: Python 3.8+, Flask
- **Machine Learning**:
  - Transformers (DistilRoBERTa)
  - spaCy (NLP)
  - ONNX (Model export)
- **Privacy**: TenSEAL for Fully Homomorphic Encryption
- **API Integration**: Bluesky atproto
- **Visualization**: Matplotlib, Chart.js

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Bluesky account (for authenticated API access)
- Windows (for .bat script) or compatible environment

### Installation

1. **Clone this repository**:
   ```bash
   git clone <repo-url>
   cd encode-zkML-bootcamp-project
   ```

2. **Quick Setup (Windows)**:
   ```bash
   setup_and_run.bat
   ```
   This script will create a virtual environment, install dependencies, export the model, and start the web server.

3. **Manual Setup**:
   ```bash
   # Create and activate virtual environment (optional)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

4. **Export the emotion analysis model**:
   ```bash
   python src/main.py --export-model
   ```

5. **Prepare the FHE environment**:
   ```bash
   python src/main.py --prepare-fhe
   ```

## 📘 Usage

### Web Interface

1. **Start the web application**:
   ```bash
   python run_web_app.py
   ```
   Then open your browser and navigate to `http://localhost:5000`

2. **Analyze emotions with FHE**:
   - Enter your question or topic
   - Optionally provide Bluesky credentials for authenticated access
   - Click "Analyze Emotions"
   - The system automatically performs analysis using Fully Homomorphic Encryption
   - Results are displayed with privacy information

### Command-Line Interface

1. **Analyze emotions for a question (CLI mode)**:
   ```bash
   python src/main.py --question "What do people think about AI?" --username your_bluesky_username --password your_bluesky_password --visualize
   ```

<!-- ## 🖼️ Screenshots

![Web Interface](screenshots/web_interface.png)
![Emotion Results](screenshots/sentiment_results.png) -->

## 🔒 Privacy Features

- **Input Privacy**: The Bluesky posts are encrypted before analysis, ensuring privacy.
- **Model Privacy**: The emotion analysis model weights remain confidential.
- **Computation on Encrypted Data**: Fully Homomorphic Encryption allows computations to be performed directly on encrypted data without decryption.
- **Seamless Integration**: FHE is integrated directly into the analysis workflow, providing privacy by default.
- **End-to-End Encryption**: Data remains encrypted throughout the entire computation process, with only the final results being decrypted.

## 🔐 FHE Implementation Details

This project uses a hybrid approach to Fully Homomorphic Encryption:

1. **Feature Extraction**: The DistilRoBERTa model is used to generate embeddings from the input text.

2. **Encryption**: The embeddings are encrypted using TenSEAL's CKKS scheme, which supports operations on encrypted floating-point numbers.

3. **Encrypted Computation**: The classification is performed on the encrypted embeddings using the weights extracted from the original model. This involves:
   - Matrix multiplication on encrypted data
   - Addition of bias terms
   - Classification of emotions based on the encrypted scores

4. **Decryption**: Only the final results are decrypted, ensuring that the raw data and intermediate computations remain private.

This approach provides a good balance between privacy and performance, using FHE for the most sensitive parts of the computation while maintaining reasonable efficiency.

## 🤝 Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

## 📄 License

This project is licensed under the Unlicense. See the [LICENSE](LICENSE) file for more details.
