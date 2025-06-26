#!/usr/bin/env python3
"""
Zillow CSV Scraper - Downloads ALL possible CSV combinations from dropdowns
Iterates through all data types and geographies for each section
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
import time
import os
import random
import argparse
import glob
from pathlib import Path
import itertools

class ZillowComprehensiveScraper:
    def __init__(self, headless=True, timeout=30):
        self.driver = None
        self.headless = headless
        self.timeout = timeout
        self.download_dir = None
        self.downloaded_files = []

    def setup_driver(self, download_dir):
        """Initialize Chrome driver with download directory"""
        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        
        options = uc.ChromeOptions()
        
        # Set download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        print("🔧 Launching Chrome...")
        self.driver = uc.Chrome(options=options)
        print(f"✅ Chrome ready, downloads: {self.download_dir}")

    def wait_for_page_load(self):
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Scroll to ensure all content loads
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            print("✅ Page loaded")
            return True
        except TimeoutException:
            print("❌ Page load timeout")
            return False

    def find_data_sections(self):
        """Find all data sections on the page"""
        section_selectors = [
            # Common patterns for data sections
            ".data-section",
            ".research-section", 
            ".download-section",
            "[data-section]",
            ".dataset",
            ".data-product",
            # Look for containers with dropdowns
            "*:has(select)",
            # Div containers that might contain dropdowns
            "div:has(select):has(button)",
            "section:has(select)",
            "article:has(select)"
        ]
        
        sections = []
        
        # Try to find parent containers that have both dropdowns and download buttons
        potential_sections = self.driver.find_elements(By.XPATH, "//div[.//select and (.//button[contains(@class, 'download')] or .//a[contains(@href, 'download')] or .//button[contains(text(), 'Download')])]")
        
        if not potential_sections:
            # Fallback: find any containers with select elements
            potential_sections = self.driver.find_elements(By.XPATH, "//div[.//select]")
        
        for i, section in enumerate(potential_sections):
            try:
                # Find dropdowns within this section
                selects = section.find_elements(By.TAG_NAME, "select")
                if selects:
                    sections.append({
                        'element': section,
                        'index': i,
                        'selects': selects
                    })
                    print(f"📊 Found section {i+1} with {len(selects)} dropdown(s)")
            except Exception as e:
                print(f"⚠️ Error processing section {i}: {e}")
        
        print(f"🎯 Found {len(sections)} data sections total")
        return sections

    def get_dropdown_options(self, select_element):
        """Get all options from a dropdown"""
        try:
            select = Select(select_element)
            options = []
            for option in select.options:
                if option.get_attribute('value') and option.get_attribute('value') != '':
                    options.append({
                        'value': option.get_attribute('value'),
                        'text': option.text.strip()
                    })
            return options
        except Exception as e:
            print(f"⚠️ Error getting dropdown options: {e}")
            return []

    def find_download_button(self, section):
        """Find download button within a section"""
        button_selectors = [
            ".//button[contains(text(), 'Download')]",
            ".//a[contains(text(), 'Download')]",
            ".//button[contains(@class, 'download')]",
            ".//a[contains(@class, 'download')]",
            ".//button[@data-download]",
            ".//a[@data-download]",
            ".//input[@type='submit']",
            ".//button[@type='submit']"
        ]
        
        for selector in button_selectors:
            try:
                buttons = section.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
            except:
                continue
        return None

    def select_dropdown_combination(self, section, combination):
        """Select a specific combination of dropdown values"""
        try:
            selects = section['selects']
            
            for i, (select_elem, option) in enumerate(zip(selects, combination)):
                # Scroll to dropdown
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_elem)
                time.sleep(0.5)
                
                select = Select(select_elem)
                select.select_by_value(option['value'])
                
                print(f"   📋 Dropdown {i+1}: {option['text']}")
                time.sleep(0.5)  # Small delay between selections
            
            return True
        except Exception as e:
            print(f"❌ Error selecting combination: {e}")
            return False

    def wait_for_download(self, timeout=15):
        """Wait for download to complete"""
        initial_files = set(glob.glob(os.path.join(self.download_dir, "*")))
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_files = set(glob.glob(os.path.join(self.download_dir, "*")))
            new_files = current_files - initial_files
            
            if new_files:
                # Check if download is complete (no temporary files)
                temp_files = [f for f in new_files if f.endswith('.crdownload') or f.endswith('.tmp')]
                if not temp_files:
                    completed_files = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
                    if completed_files:
                        print(f"✅ Downloaded: {os.path.basename(completed_files[0])}")
                        self.downloaded_files.extend(completed_files)
                        return True
            
            time.sleep(1)
        
        print("⏳ Download timeout - continuing anyway")
        return False

    def download_combination(self, section, combination, combo_num, total_combos):
        """Download a specific combination"""
        print(f"\n📥 Combination {combo_num}/{total_combos}")
        
        # Select the dropdown combination
        if not self.select_dropdown_combination(section, combination):
            return False
        
        # Find and click download button
        download_btn = self.find_download_button(section['element'])
        if not download_btn:
            print("❌ No download button found for this section")
            return False
        
        try:
            # Scroll to download button
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
            time.sleep(0.5)
            
            # Click download button
            try:
                download_btn.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", download_btn)
            
            print("🖱️ Download button clicked")
            
            # Wait for download
            self.wait_for_download()
            
            # Random delay between downloads
            delay = random.uniform(2, 4)
            time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading: {e}")
            return False

    def process_section(self, section):
        """Process all combinations for a single section"""
        print(f"\n🔄 Processing section {section['index'] + 1}")
        
        # Get all dropdown options
        all_options = []
        for i, select_elem in enumerate(section['selects']):
            options = self.get_dropdown_options(select_elem)
            all_options.append(options)
            print(f"   📋 Dropdown {i+1}: {len(options)} options")
        
        if not all_options or not all(all_options):
            print("⚠️ No valid dropdown options found")
            return 0
        
        # Generate all combinations
        combinations = list(itertools.product(*all_options))
        print(f"🔢 Total combinations for this section: {len(combinations)}")
        
        successful_downloads = 0
        
        # Download each combination
        for combo_num, combination in enumerate(combinations, 1):
            combo_description = " × ".join([opt['text'] for opt in combination])
            print(f"🎯 {combo_description}")
            
            if self.download_combination(section, combination, combo_num, len(combinations)):
                successful_downloads += 1
        
        return successful_downloads

    def run(self, url, output_dir="downloads"):
        """Main scraping process"""
        self.setup_driver(output_dir)
        
        try:
            print(f"🌐 Navigating to {url}")
            self.driver.get(url)
            
            if not self.wait_for_page_load():
                return
            
            # Find all data sections
            sections = self.find_data_sections()
            if not sections:
                print("❌ No data sections found")
                return
            
            total_downloads = 0
            
            # Process each section
            for section in sections:
                downloads = self.process_section(section)
                total_downloads += downloads
                
                # Longer delay between sections
                if section != sections[-1]:  # Not the last section
                    delay = random.uniform(5, 10)
                    print(f"⏳ Waiting {delay:.1f}s before next section...")
                    time.sleep(delay)
            
            print(f"\n🎉 Scraping complete!")
            print(f"✅ Total successful downloads: {total_downloads}")
            print(f"📁 Files saved to: {self.download_dir}")
            print(f"📊 Downloaded files: {len(self.downloaded_files)}")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔌 Browser closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zillow Comprehensive CSV Scraper - All Dropdown Combinations")
    parser.add_argument("--url", default="https://www.zillow.com/research/data/", 
                       help="Zillow Research Data URL")
    parser.add_argument("--output-dir", default="zillow_data_complete", 
                       help="Directory to save all CSV files")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browser in headless mode")
    args = parser.parse_args()

    print("🏠 Zillow Comprehensive CSV Scraper")
    print("📊 Downloads ALL possible dropdown combinations")
    print(f"🎯 Target: {args.url}")
    print(f"📁 Output: {args.output_dir}")
    print(f"👻 Headless: {args.headless}")
    print("=" * 60)

    scraper = ZillowComprehensiveScraper(headless=args.headless)
    scraper.run(args.url, args.output_dir)