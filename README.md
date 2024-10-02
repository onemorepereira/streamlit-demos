# Streamlit Demos

A colleague of mine recently introduced me to Streamlit and I honestly can't get enough. I am the kind of develoer that'll spend 2 hours modeling functional code, and then the next week working on frontend code & styling. This is a gamechanges. Here are a few of the very quick & dirty demos I've put together over the last few weeks.

If you find anything that makes you cringe, fork, fix, and open a pull request --I look at my GitHub organization at least once a week.

- [Bicycle Gearing / Speed Calculator](./cycling-gearing-calculator)
  - I am cyclist...what did you expect?
- [Geo IP / FQDN Lookup](./iplookup)
  - This is a simple example to lookup geo-coordinates to overlay on a map.
- [GPX/FIT file utilities](./activity-file-utilities)
  - Very simple UI to parse data out of GPX and FIT files from the likes of Garmin, Strava, and others.
- [Macro Tracker](./macro-tracker)
  - Simple macro nutrient and meal tracker, with fat, carb, protein, and caloric visualizations over time.
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
