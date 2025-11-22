# PPT Chart Generator

A Python tool that generates PowerPoint presentations with charts from natural language descriptions using LLMs.

## Prerequisites

- Python 3.11+
- OpenAI API Key (or compatible, e.g., DeepSeek)

## Installation

```bash
cd PPT
# Install dependencies (using uv or pip)
pip install -r requirements.txt
```

## Usage

Set your API Key in a `.env` file:
```ini
LLM_API_KEY=your-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

Run the generator:
```bash
# Default Style (Tech/Dark)
python -m src.main "Sales for Q1 100, Q2 150. Show me a bar chart."

# Light Style
python -m src.main "Sales for Q1 100, Q2 150" --style light

# Retro Style
python -m src.main "Sales for Q1 100, Q2 150" --style retro
```

## Styles
- **tech** (Default): Dark mode, neon colors, cyberpunk aesthetic.
- **light**: Clean, minimal, corporate white theme.
- **retro**: Solarized color palette, typewriter fonts.

## Features

- **Natural Language Parsing**: Uses LLM to understand data.
- **Auto-Chart Selection**: Automatically picks Bar, Line, Pie, or Scatter charts.
- **Multi-Style Support**: Choose from Tech, Light, or Retro themes.
- **Native PPTX**: Generates editable PowerPoint files.
