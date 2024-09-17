# Streamlit Demos

- [Geo IP / FQDN Lookup](./iplookup)
  - This is a simple example to lookup geo-coordinates to overlay on a map.
- [Bicycle Gearing / Speed Calculator](./cycling-gearing-calculator)
  - I am cyclist...what did you expect?
- [Tesseract + Bedrock (AI)](./tesseract)
  - Using Tesseract and Amazon Bedrock to help in OCR, classification, and summarization of text from images.

## Getting Started

Most demo projects are Python-based and are provided alongside a _requirements.txt_ manifest.

```bash
# Drop into the demo folder
cd ./iplookup

# Initialize a Python virtual environment
python -m venv .env

# Activate the virtual environment
source .env/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the project
streamlit run main.py
```