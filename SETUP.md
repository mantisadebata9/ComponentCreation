# Figma-to-Jutro Agent: Setup Instructions

## Prerequisites

- Python 3.9+
- Node.js 16+ (for Jutro Storybook preview)
- Git
- Figma account with API access

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/mantisadebata9/figma-to-jutro-agent.git
cd figma-to-jutro-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create `.env` file:

```bash
FIGMA_API_KEY=your_figma_api_key
OPENAI_API_KEY=your_openai_api_key  # Optional
OUTPUT_DIR=./output
```

Get Figma API Key:
1. Go to https://www.figma.com/developers
2. Create a personal access token
3. Copy and paste into `.env`

### 5. Run Streamlit App

```bash
cd ..
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`

## Quick Start

### Method 1: From Figma URL

1. Get your Figma design URL (from share button)
2. Paste into app
3. Click "Load from Figma"
4. View preview and download code

### Method 2: From .fig File

1. Export your Figma file as .fig
2. Upload via file picker
3. Wait for processing
4. Download generated components

### Method 3: From Image

1. Take screenshot of design
2. Upload PNG/JPG
3. App will auto-detect components
4. Generate code

## Project Structure

```
figma-to-jutro-agent/
├── backend/
│   ├── agent/                 # Core agent logic
│   │   ├── figma_reader.py    # Figma integration
│   │   ├── component_detector.py
│   │   ├── jutro_mapper.py
│   │   └── code_generator.py
│   ├── services/              # Helper services
│   ├── config/                # Configuration files
│   └── requirements.txt
├── frontend/
│   ├── app.py                 # Streamlit main app
│   └── pages/
├── output/                    # Generated code
│   ├── src/pages/
│   ├── src/components/
│   └── src/layout/
├── tests/
├── examples/
└── docs/
```

## Configuration

### Custom Component Mapping

Edit `backend/config/component_mapping.json`:

```json
{
  "BUTTON": {
    "jutro_component": "Button",
    "package": "@jutro/components",
    "props": ["variant", "size", "onClick"]
  }
}
```

### Jutro Components Reference

See `backend/config/jutro_components.json` for available components.

## Testing

```bash
cd backend
pytest tests/
```

## Troubleshooting

### Issue: "Invalid Figma URL"
- Ensure URL is from share/public link
- Format: `https://www.figma.com/file/{FILE_KEY}/...`

### Issue: "API Key not found"
- Check `.env` file exists
- Verify `FIGMA_API_KEY` is set
- Restart app after changing `.env`

### Issue: No components detected
- Ensure design has named frames/components
- Check component names match patterns
- See `/examples` for sample designs

## Next Steps

1. ✅ Install and setup
2. 🎨 Upload your first design
3. 👀 Review generated components
4. 🔧 Customize component mapping
5. 📦 Integrate into your Jutro project

## Support

- Documentation: `/docs`
- Examples: `/examples`
- Issues: GitHub Issues
