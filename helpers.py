import time
import random
import json
import os
import logging

logger = logging.getLogger(__name__)

def human_like_delay(delay_min=1, delay_max=4):
    """Add a random human-like delay"""
    time.sleep(random.uniform(delay_min, delay_max))

def human_like_typing(element, text):
    """Type text in a human-like manner"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))
        if random.random() < 0.1:
            time.sleep(random.uniform(0.2, 0.5))

def save_cookies(driver, cookies_file):
    """Save cookies to a file"""
    try:
        cookies = driver.get_cookies()
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f)
        logger.info("Cookies saved")
    except Exception as e:
        logger.error(f"Failed to save cookies: {str(e)}")

def load_cookies(driver, cookies_file):
    """Load cookies from a file"""
    try:
        if os.path.exists(cookies_file):
            driver.get("https://www.pokemoncenter.com/en-ca")
            human_like_delay()
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Couldn't load cookie: {str(e)}")
            driver.refresh()
            human_like_delay()
            logger.info("Cookies loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load cookies: {str(e)}")