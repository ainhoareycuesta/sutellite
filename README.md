# Sutellite

2026 NASA Space Apps Challenge: Harmonization of MODIS and VIIRS Hot Spots.

## Project Overview

Sutellite aims to investigate and harmonize active fire detections from NASA's MODIS and VIIRS satellite instruments.

The project focuses on understanding differences in spatial resolution, detection characteristics, and temporal coverage to support more consistent fire analysis.

## Project Structure

```text
sutellite/
|-- config/              # Shared project configuration
|-- src/                 # Source code
|-- data/                # Generated data (not raw downloads)
|-- .env.example         # Environment variable template
|-- .gitignore
|-- requirements.txt     # Python dependencies
|-- README.md
```

## Setup

### Requirements

- Python 3.12
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ainhoareycuesta/sutellite.git
   cd sutellite
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment.

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

6. Open `.env` and configure your local NASA FIRMS data directory:

   ```env
   SUTELLITE_DATA_DIR=your/local/path/to/datos_modis_viirs
   ```

Each developer must have access to the original NASA FIRMS datasets separately.

## Data

Original NASA FIRMS CSV files are stored outside the repository.

Each developer must configure their own local data directory in a `.env` file. See `.env.example` for the required variable.

Raw data should not be committed to Git.