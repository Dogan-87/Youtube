# Image Scraper

A Python web scraper that downloads images from a website and automatically navigates through pages using Selenium.

## Features
- Automatically downloads all images from each page
- Navigates through pages using the "next" button
- Creates a dedicated folder for downloaded images
- Handles both relative and absolute image URLs
- Supports JPG and PNG image formats

## Setup
1. Install Python 3.7 or higher
2. Install Chrome browser
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage
1. Open `image_scraper.py`
2. Replace `YOUR_URL_HERE` with the target website URL
3. Run the script:
```bash
python image_scraper.py
```

The images will be downloaded to a `downloaded_images` folder in the same directory.

## Notes
- The script looks for elements with a class containing "next" for pagination. You might need to adjust the CSS selector based on the target website.
- Images are saved with incremental numbers (image_0.jpg, image_1.jpg, etc.)
- The script runs in headless mode by default (no visible browser). Remove the `--headless` option in the code to see the browser in action.
