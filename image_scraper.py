from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
from urllib.parse import urljoin
import base64
import random
from datetime import datetime

class ImageScraper:
    def __init__(self, url, download_folder='downloaded_images'):
        self.url = url
        self.download_folder = download_folder
        self.driver = None
        self.download_count = 0
        self.last_download_time = None
        
        # Create download folder if it doesn't exist
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        # Get the last image number
        self.last_image_number = self.get_last_image_number()
        print(f"Continuing from image number: {self.last_image_number + 1}")
    
    def get_last_image_number(self):
        try:
            # List all files in the download folder
            files = os.listdir(self.download_folder)
            
            # Filter only jpg and png files and extract their numbers
            image_numbers = []
            for file in files:
                if file.startswith('image_') and any(file.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    try:
                        # Extract number from filename (image_X.ext)
                        number = int(file.split('_')[1].split('.')[0])
                        image_numbers.append(number)
                    except (IndexError, ValueError):
                        continue
            
            # Return the highest number found, or -1 if no images exist
            return max(image_numbers) if image_numbers else -1
            
        except Exception as e:
            print(f"Error checking existing images: {str(e)}")
            return -1
    
    def setup_driver(self):
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')  # Run in headless mode (optional)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Add random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0'
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        self.driver = webdriver.Chrome(options=options)
        
    def add_random_delay(self):
        """Add a random delay between actions to simulate human behavior"""
        # Calculate delay based on download count
        base_delay = min(2 + (self.download_count // 5), 8)  # Increase delay as we download more
        random_delay = random.uniform(base_delay, base_delay + 3)
        
        # Add longer delay every few downloads
        if self.download_count > 0 and self.download_count % 5 == 0:
            random_delay += random.uniform(3, 6)
            print(f"Taking a longer break after {self.download_count} downloads...")
        
        print(f"Waiting for {random_delay:.2f} seconds...")
        time.sleep(random_delay)
    
    def simulate_human_scroll(self):
        """Simulate human-like scrolling behavior and ensure we reach all page-break elements"""
        try:
            # First, find all page-break elements
            page_breaks = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.page-break.no-gaps"))
            )
            
            if not page_breaks:
                print("No page-break elements found, using default scroll")
                # Default scroll to bottom if no page-breaks found
                total_height = self.driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
            else:
                # Get the position of the last page-break
                last_page_break = page_breaks[-1]
                total_height = self.driver.execute_script("return arguments[0].offsetTop + arguments[0].offsetHeight;", last_page_break)
                print(f"Found {len(page_breaks)} page-breaks, scrolling to last one")
            
            current_position = 0
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            while current_position < total_height:
                # Random scroll amount between 100 and 300 pixels
                scroll_amount = random.randint(300, 700)
                current_position = min(current_position + scroll_amount, total_height)
                
                # Scroll with smooth behavior
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: {current_position},
                        behavior: 'smooth'
                    }});
                """)
                
                # Random pause between scrolls
                time.sleep(random.uniform(0.2, 0.5))
                
                # Occasionally pause longer to simulate reading
                if random.random() < 0.2:  # 20% chance
                    time.sleep(random.uniform(0.5, 1.0))
                
                # Verify we haven't hit any dynamic height changes
                new_height = self.driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
                if new_height > total_height:
                    print("Page height increased, adjusting scroll target")
                    total_height = new_height
            
            # Final scroll to ensure we reach the bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 2.0))
            
            print("Completed scrolling to the bottom of the page")
            
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
            # Fallback to simple scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
    
    def find_images(self):
        """Find all image elements with retry on stale elements"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Wait for images to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                
                # Get fresh references to images
                images = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "img"))
                )
                
                return images
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1}: Failed to find images, retrying...")
                    time.sleep(2)
                    # Refresh the page if we had a stale element
                    self.driver.refresh()
                    self.simulate_human_scroll()
                else:
                    print(f"Failed to find images after {max_attempts} attempts: {str(e)}")
                    return []
        return []

    def download_image(self, img_url, index):
        try:
            print(f"\nAttempting to download: {img_url}")
            
            # Skip if not an image URL
            if not img_url or not any(img_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                print("Skipping: Not a supported image format (must be JPG, PNG, or WebP)")
                return False
                
            # Get the file extension from the URL
            file_extension = os.path.splitext(img_url)[1].lower()
            if not file_extension:
                file_extension = '.jpg'  # Default to jpg if no extension found
            
            # Create filename with the next available number
            filename = f"image_{self.last_image_number + index + 1}{file_extension}"
            filepath = os.path.join(self.download_folder, filename)
            
            # Download the image using Selenium's get method
            try:
                # Open a new tab
                self.driver.execute_script("window.open('');")
                # Switch to the new tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                # Navigate to image URL
                self.driver.get(img_url)
                
                # Get the image data
                img_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                
                # Get the base64 data of the image
                img_base64 = self.driver.execute_script("""
                    var canvas = document.createElement('canvas');
                    var context = canvas.getContext('2d');
                    var img = document.querySelector('img');
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    context.drawImage(img, 0, 0);
                    return canvas.toDataURL('image/{{ ... }}');
                """)
                
                # Convert base64 to image and save
                if img_base64:
                    # Remove the data URL prefix
                    img_data = img_base64.split(',')[1]
                    # Decode and save the image
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(img_data))
                    print(f"Successfully downloaded: {filename}")
                    
                # Close the tab and switch back
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return True
                
            except Exception as e:
                print(f"Error downloading image: {str(e)}")
                # Make sure to close the tab and switch back in case of error
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                return False
                
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return False
    
    def check_for_captcha(self):
        try:
            # More specific CAPTCHA detection for manhuaus.com
            captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "#challenge-running, #challenge-form, .cf-challenge-running")
            
            if captcha_elements and any(elem.is_displayed() for elem in captcha_elements):
                print("\n*** CAPTCHA detected! ***")
                print("Please solve the CAPTCHA in the browser window.")
                print("Waiting for CAPTCHA to be solved...")
                
                # Wait for the CAPTCHA element to disappear
                while True:
                    try:
                        visible_captcha = False
                        elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            "#challenge-running, #challenge-form, .cf-challenge-running")
                        for elem in elements:
                            if elem.is_displayed():
                                visible_captcha = True
                                break
                        
                        if not visible_captcha:
                            break
                            
                        time.sleep(2)
                    except NoSuchElementException:
                        break
                
                print("CAPTCHA check completed. Continuing...")
                time.sleep(3)  # Wait a bit after CAPTCHA check
                return True
            
            return False
        except Exception as e:
            print(f"Error checking for CAPTCHA: {str(e)}")
            return False

    def scrape_images(self):
        try:
            self.setup_driver()
            self.driver.get(self.url)
            image_count = 0
            
            while True:
                # Simulate human scrolling
                self.simulate_human_scroll()
                
                # Check for CAPTCHA before proceeding
                self.check_for_captcha()
                
                # Add random delay before processing images
                self.add_random_delay()
                
                # Find all images with retry logic
                images = self.find_images()
                if not images:
                    print("No images found on page, trying next chapter...")
                else:
                    # Download each image
                    for img in images:
                        try:
                            # Get fresh reference to image URL
                            img_url = WebDriverWait(self.driver, 3).until(
                                lambda d: img.get_attribute('src')
                            )
                            if img_url:
                                print(f'Found image URL: {img_url}')
                                if self.download_image(img_url, image_count):
                                    image_count += 1
                                    self.download_count += 1
                                    
                                    # Add random delay between downloads
                                    self.add_random_delay()
                        except Exception as e:
                            print(f"Error processing image: {str(e)}, continuing with next image...")
                            continue
                
                try:
                    print("Looking for next chapter link...")
                    # Use the exact site structure to find the next button
                    next_selector = "//div[contains(@class, 'nav-next')]//a[contains(@class, 'next_page')]"
                    
                    # Add longer delay before looking for next chapter
                    time.sleep(random.uniform(4, 7))
                    
                    try:
                        print(f"Looking for next button with selector: {next_selector}")
                        next_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, next_selector))
                        )
                        
                        if next_button:
                            print("Found next button!")
                            # Get fresh reference to href attribute
                            next_url = WebDriverWait(self.driver, 3).until(
                                lambda d: next_button.get_attribute('href')
                            )
                            
                            if next_url:
                                # Add longer delay before navigation
                                time.sleep(random.uniform(3, 5))
                                
                                # Navigate to the next chapter
                                self.driver.get(next_url)
                                print("Navigating to next chapter...")
                                
                                # Random delay after navigation
                                time.sleep(random.uniform(4, 6))
                                
                                # Check for CAPTCHA after navigation
                                self.check_for_captcha()
                            else:
                                print("No valid URL found in next button")
                                break
                        else:
                            print("Next button not found")
                            break
                    except Exception as e:
                        print(f"Could not find next button: {str(e)}")
                        break
                
                except Exception as e:
                    print(f"Error navigating to next chapter: {str(e)}")
                    break
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
            print(f"Scraping completed. Downloaded {self.download_count} images.")

if __name__ == "__main__":
    # Replace with your target URL
    target_url = "https://manhuaus.com/manga/becoming-the-swordmaster-rank-young-lord-of-the-sichuan-tang-family/chapter-1/"
    scraper = ImageScraper(target_url)
    scraper.scrape_images()
