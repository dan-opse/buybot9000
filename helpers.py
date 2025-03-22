import time
import random
import json
import os
import logging
import pyautogui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


logger = logging.getLogger(__name__)

def human_like_delay(delay_min=1, delay_max=4):
    """Add a random human-like delay with natural distribution"""
    # Use a more natural distribution (weighted towards the shorter end)
    delay = random.betavariate(2, 5) * (delay_max - delay_min) + delay_min
    time.sleep(delay)

def human_like_typing(element, text):
    """Type text in a more realistic human-like manner"""
    # Average typing speed is ~200ms per character, but varies
    # Fast typists: 80-120ms, slow: 250-350ms
    base_delay = random.uniform(0.08, 0.25)  # Base typing speed
    
    # Simulate "thinking" before typing (for longer inputs)
    if len(text) > 10:
        time.sleep(random.uniform(0.5, 1.5))
    
    for i, char in enumerate(text):
        element.send_keys(char)
        
        # Basic typing delay
        char_delay = base_delay
        
        # Slow down for special characters (simulate key switching)
        if not char.isalnum():
            char_delay *= random.uniform(1.5, 2.0)
        
        # Occasional longer pauses (thinking, distraction)
        if random.random() < 0.03:  # 3% chance of longer pause
            char_delay += random.uniform(0.7, 1.5)
        
        # Occasional typo and correction (4% chance)
        if random.random() < 0.04 and i < len(text) - 1:
            # Type a wrong character
            wrong_char = chr(ord(char) + random.randint(1, 5))
            element.send_keys(wrong_char)
            time.sleep(random.uniform(0.1, 0.3))
            # Delete it
            element.send_keys("\b")
            time.sleep(random.uniform(0.1, 0.3))
            # Type correct character again
            element.send_keys(char)
            
        time.sleep(char_delay)
        
    # Pause after completing input
    time.sleep(random.uniform(0.2, 0.5))


def perform_random_interactions(self):
    """Performs random human-like interactions with the page"""
    try:
        # Get page dimensions
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        page_width = self.driver.execute_script("return document.body.scrollWidth")
        
        # Random scroll
        if random.random() < 0.7:  # 70% chance
            # Scroll down gradually with variable speed
            target_scroll = random.randint(100, min(1000, page_height))
            current_scroll = 0
            
            while current_scroll < target_scroll:
                scroll_step = random.randint(50, 200)
                current_scroll += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.1, 0.5))
                
            # Occasionally scroll back up
            if random.random() < 0.3:
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(0, current_scroll)});")
        
        # Random mouse movements
        simulate_mouse_movement(self.driver)
        
        # Sometimes resize window slightly
        if random.random() < 0.1:  # 10% chance
            width = random.randint(1280, 1920)
            height = random.randint(800, 1080)
            self.driver.set_window_size(width, height)
        
        # Occasionally hover over random elements
        if random.random() < 0.4:  # 40% chance
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, img")
                if elements:
                    random_element = random.choice(elements)
                    hover = ActionChains(self.driver).move_to_element(random_element)
                    hover.perform()
                    time.sleep(random.uniform(0.5, 2.0))
            except:
                pass
    
    except Exception as e:
        logger.warning(f"Random interaction failed: {str(e)}")

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
    """Load cookies from a file."""
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

def simulate_mouse_movement(driver=None):
    """Simulate realistic mouse movements to evade bot detection"""
    try:
        if driver:
            # Get browser window dimensions
            window_size = driver.get_window_size()
            width, height = window_size['width'], window_size['height']
            
            # Current mouse position (estimated)
            current_x, current_y = random.randint(0, width), random.randint(0, height)
            
            # Generate 3-10 random waypoints for mouse movement
            num_waypoints = random.randint(3, 10)
            for _ in range(num_waypoints):
                # Generate random destination coordinates
                dest_x = random.randint(0, width)
                dest_y = random.randint(0, height)
                
                # Calculate distance and number of steps (more distance = more steps)
                distance = ((dest_x - current_x)**2 + (dest_y - current_y)**2)**0.5
                num_steps = max(int(distance / 10), 5)  # At least 5 steps
                
                # Easing function for natural acceleration/deceleration
                for step in range(1, num_steps + 1):
                    # Ease in-out formula
                    t = step / num_steps
                    ease = t * t * (3.0 - 2.0 * t)  # Smoothstep function
                    
                    # Calculate intermediate position
                    x = current_x + (dest_x - current_x) * ease
                    y = current_y + (dest_y - current_y) * ease
                    
                    # Move mouse (if pyautogui available)
                    try:
                        import pyautogui
                        pyautogui.moveTo(x, y, duration=0.01)
                    except ImportError:
                        if driver:
                            # If pyautogui not available, use JavaScript to simulate hover
                            hover_element = f"document.elementFromPoint({x}, {y})"
                            driver.execute_script(f"if({hover_element}) {{ const evt = new MouseEvent('mouseover', {{clientX: {x}, clientY: {y}, bubbles: true}}); {hover_element}.dispatchEvent(evt); }}")
                    
                    # Add slight pause between movements (variable timing)
                    time.sleep(random.uniform(0.001, 0.05))
                
                # Update current position
                current_x, current_y = dest_x, dest_y
                
                # Add small pause at destination
                time.sleep(random.uniform(0.05, 0.2))
                
                # 25% chance of a "hover pause" at interesting points
                if random.random() < 0.25:
                    time.sleep(random.uniform(0.2, 1.0))
    except Exception as e:
        logger.warning(f"Mouse movement simulation failed: {str(e)}")

def random_movement():
    """Perform random mouse movements"""
    import pyautogui
    
    # Current position
    current_x, current_y = pyautogui.position()
    
    # Random movement (small)
    for _ in range(random.randint(1, 3)):
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        target_x = max(0, min(current_x + offset_x, pyautogui.size()[0]))
        target_y = max(0, min(current_y + offset_y, pyautogui.size()[1]))
        
        # Generate curve points
        points = generate_curve_points(current_x, current_y, target_x, target_y, 
                                      random.randint(3, 8))
        
        # Move through points with variable speed
        for point in points:
            pyautogui.moveTo(point[0], point[1], 
                           duration=random.uniform(0.1, 0.3))
            time.sleep(random.uniform(0.02, 0.08))
        
        current_x, current_y = target_x, target_y

def randomize_page_load(driver):
    """Randomize page load behavior to appear more human"""
    try:
        # Random chance to stop loading early (like a human might)
        if random.random() < 0.1:  # 10% chance
            time.sleep(random.uniform(0.5, 2.0))
            driver.execute_script("window.stop();")
            time.sleep(random.uniform(0.5, 1.5))
            driver.refresh()  # Then refresh
        
        # Random chance to scroll slightly before page fully loads
        if random.random() < 0.3:  # 30% chance
            time.sleep(random.uniform(0.3, 1.0))
            driver.execute_script("window.scrollTo(0, %d);" % random.randint(10, 50))
    except Exception as e:
        logger.warning(f"Error during page load randomization: {str(e)}")

def generate_curve_points(start_x, start_y, end_x, end_y, num_points):
    """Generate curve points for natural mouse movement"""
    points = []
    
    # Random control point for quadratic bezier curve
    control_x = random.randint(min(start_x, end_x), max(start_x, end_x))
    control_y = random.randint(min(start_y, end_y), max(start_y, end_y))
    
    # Generate points along the curve
    for i in range(num_points + 1):
        t = i / num_points
        # Quadratic bezier formula
        x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
        y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
        points.append((x, y))
    
    return points
