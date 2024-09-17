# TESSERACT OCR

Simple demo that processes images, extracts text via Tesseract OCR, and then invokes Amazon Bedrock to gate, classify, and summarize the content.

## Getting Started

If you've ditched Docker in favor of Podman, the included Makefile will _make_ your life easy. The following make directive will build, publish and run the project in a container locally.

```bash
make pub
```

The container will expose the Streamlit app on port 8501. The Makefile publishes it to your localmachine on 8502:

http://localhost:8502

If you want to do this the hard way:

Make sure you have Tesseract's packages installed and available on your SYSTEM path.

Then...

```bash
# Initialize a Python virtual environment
python -m venv .env

# Activate the virtual environment
source .env/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the project
streamlit run main.py
```
