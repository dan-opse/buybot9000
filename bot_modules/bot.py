import time
import logging
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import undetected_chromedriver as uc
import json
import os
from helpers import human_like_delay, human_like_typing, randomize_page_load, save_cookies, load_cookies, simulate_mouse_movement, random_movement, perform_random_interactions
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pokemon_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PokemonTCGBot:
    def __init__(self):
        """Initializes the bot. No webpage interaction."""
        self.base_url = "https://www.pokemoncenter.com/en-ca/"
        self.check_interval = 30
        self.target_keywords = []
        self.payment_info = {
            "card_number": os.getenv("CARD_NUMBER"),
            "expiry_month": os.getenv("CARD_EXPIRY_MONTH"),
            "expiry_year": os.getenv("CARD_EXPIRY_YEAR"),
            "cvv": os.getenv("CARD_CVV", ""),  # CVV is optional
            "paypal_email": os.getenv("PAYPAL_EMAIL"),
            "paypal_password": os.getenv("PAYPAL_PASSWORD")
        }
        self.cookies_file = "pokemon_cookies.json"
        self.load_config()
        self.setup_browser()

    def load_config(self):
        """Loads configuration from config.json. No webpage interaction."""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.target_keywords = config.get('target_keywords', [])
                self.check_interval = config.get('check_interval', 30)
                self.exact_product_url = config.get('exact_product_url', "")
                self.category_url = config.get('category_url', f"{self.base_url}/category/tcg-cards")
                self.random_delay_min = config.get('random_delay_min', 2)
                self.random_delay_max = config.get('random_delay_max', 6)
                self.quantity = config.get('quantity', 1)
                self.retry_limit = config.get('retry_limit', 3)
                self.headless_mode = config.get('headless_mode', False)
                self.proxies = config.get('proxies', [])  # Load proxies from config

            # Enhanced proxy loading
                self.proxies = config.get('proxies', [])
                self.proxy_rotation_frequency = config.get('proxy_rotation_frequency', 5)  # How often to rotate
                self.current_proxy_index = 0
            
                if self.proxies:
                    logger.info(f"Loaded {len(self.proxies)} proxies for rotation")
                else:
                    logger.warning("No proxies configured - bot may be detected more easily")

        except FileNotFoundError:
            logger.error("Config file not found. Creating default config.")
            self.create_default_config()

    def rotate_proxy(self):
        """Rotate to the next proxy in the list"""
        if not self.proxies or len(self.proxies) <= 1:
            return
            
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        new_proxy = self.proxies[self.current_proxy_index]
        logger.info(f"Rotating to proxy: {new_proxy}")
        
        # Reset the browser with new proxy
        self.driver.quit()
        self.setup_browser()

    def create_default_config(self):
        """Creates a default config file if it doesn't exist. No webpage interaction."""
        default_config = {
            "target_keywords": ["Scarlet & Violet", "Destined Rivals"],
            "check_interval": 30,
            "exact_product_url": "",
            "category_url": f"{self.base_url}/category/tcg-cards",
            "max_price": 199.99,
            "random_delay_min": 2,
            "random_delay_max": 6,
            "quantity": 4,  # Default quantity
            "retry_limit": 3,  # Default retry limit
            "headless_mode": False  # Default headless mode
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        self.target_keywords = default_config["target_keywords"]
        self.exact_product_url = default_config["exact_product_url"]
        self.category_url = default_config["category_url"]
        self.random_delay_min = default_config["random_delay_min"]
        self.random_delay_max = default_config["random_delay_max"]
        self.quantity = default_config["quantity"]
        self.retry_limit = default_config["retry_limit"]
        self.headless_mode = default_config["headless_mode"]

    def setup_browser(self):
        """Initialize the browser with enhanced anti-detection measures."""
        try:
            # Randomize browser window size (within reasonable bounds)
            window_width = random.randint(1280, 1920)
            window_height = random.randint(800, 1080)
            
            # Randomize user agent from a pool of recent, common browsers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            ]
            user_agent = random.choice(user_agents)
            
            options = uc.ChromeOptions()
            options.add_argument(f"--window-size={window_width},{window_height}")
            options.add_argument(f"user-agent={user_agent}")
            
            # Add all your existing arguments
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--enable-javascript")  # Ensure JavaScript is enabled
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-browser-side-navigation")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-breakpad")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-component-update")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-domain-reliability")
            options.add_argument("--disable-features=AudioServiceOutOfProcess")
            options.add_argument("--disable-hang-monitor")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--force-color-profile=srgb")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--no-first-run")
            options.add_argument("--safebrowsing-disable-auto-update")
            options.add_argument("--password-store=basic")
            options.add_argument("--use-mock-keychain")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")

            # Add randomized timezone and locale
            timezones = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Toronto", "America/Vancouver"]
            options.add_argument(f"--timezone={random.choice(timezones)}")

            # Randomize hardware acceleration features
            if random.choice([True, False]):
                options.add_argument("--disable-gpu")

            # Randomize browser window size slightly
            width = random.randint(1280, 1920)
            height = random.randint(800, 1080)
            options.add_argument(f"--window-size={width},{height}")

            # Add proxy if available with proper authentication
            if self.proxies:
                proxy = random.choice(self.proxies)
                if '@' in proxy:  # Proxy with authentication
                    proxy_parts = proxy.split('@')
                    auth = proxy_parts[0]
                    address = proxy_parts[1]
                    
                    auth_plugin_path = self.create_proxy_auth_extension(auth)
                    options.add_extension(auth_plugin_path)
                    options.add_argument(f"--proxy-server={address}")
                else:
                    options.add_argument(f"--proxy-server={proxy}")
                logger.info(f"Using proxy: {proxy.split('@')[-1] if '@' in proxy else proxy}")


            if self.headless_mode:
                options.add_argument("--headless")  # Run in headless mode

            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, random.randint(10, 15))


            if hasattr(self, 'driver') and self.driver:
                # Remove webdriver specific properties
                self.driver.execute_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Remove automation-related properties
                    if (window.navigator.plugins) {
                        // Add a fake plugin to make it look more realistic
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                                { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
                                { name: 'Native Client', filename: 'internal-nacl-plugin' }
                            ]
                        });
                    }
                    
                    // Remove common automation fingerprints
                    const originalFunction = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' || 
                        parameters.name === 'geolocation' || 
                        parameters.name === 'persistent-storage' || 
                        parameters.name === 'camera' ? 
                            Promise.resolve({state: 'prompt'}) : 
                            originalFunction(parameters)
                    );
                """)

            # Execute additional JavaScript to modify navigator properties
            self.driver.execute_script("""
                // Override navigator properties to make detection harder
                const originalNavigator = window.navigator;
                delete window.navigator;
                window.navigator = {
                    __proto__: originalNavigator,
                    // Randomize hardwareConcurrency
                    hardwareConcurrency: Math.floor(Math.random() * 8) + 4,
                    // Override deviceMemory if supported
                    deviceMemory: Math.floor(Math.random() * 8) + 4,
                    // Other properties remain unchanged
                    get userAgent() { return originalNavigator.userAgent; },
                    get appVersion() { return originalNavigator.appVersion; },
                    get language() { return originalNavigator.language; },
                    get languages() { return originalNavigator.languages; },
                    get cookieEnabled() { return originalNavigator.cookieEnabled; },
                    get doNotTrack() { return originalNavigator.doNotTrack; },
                };
            """)

            # Enhanced stealth settings with more realistic values
            stealth(
                self.driver,
                languages=["en-US", "en-CA", "en"],
                vendor="Google Inc.",
                platform="Win32" if random.random() < 0.7 else "MacIntel",
                webgl_vendor="Intel Inc." if random.random() < 0.5 else "NVIDIA Corporation",
                renderer=random.choice([
                    "Intel Iris OpenGL Engine", 
                    "NVIDIA GeForce GTX", 
                    "AMD Radeon Pro"
                ]),
                fix_hairline=True,
            )

            # Navigate to a common site first, then the target
            common_sites = ["https://www.google.com", "https://www.youtube.com", "https://www.reddit.com"]
            self.driver.get(random.choice(common_sites))
            human_like_delay(1, 3)
            
            load_cookies()
            logger.info("Browser initialized with enhanced anti-detection measures")
        except Exception as e:
            logger.error(f"Browser setup failed: {str(e)}")
            self.setup_fallback_browser()

    def setup_fallback_browser(self):
        """Initializes a fallback browser with proxy support."""
        options = Options()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Add proxy if available
        if self.proxies:
            proxy = random.choice(self.proxies)  # Randomly select a proxy
            options.add_argument(f"--proxy-server={proxy}")
            logger.info(f"Using proxy: {proxy}")

        if self.headless_mode:
            options.add_argument("--headless")  # Run in headless mode

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, random.randint(10, 15))
        load_cookies(self.driver, self.cookies_file)  # Load cookies from file
        logger.info("Fallback browser initialized with proxy")

    def set_random_headers(self):
        """Set random HTTP headers to appear more human-like"""
        try:
            # Define a list of common headers and values
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63"
            ]
            
            accept_languages = [
                "en-US,en;q=0.9",
                "en-CA,en;q=0.9",
                "en-GB,en;q=0.9"
            ]
            
            # Randomly select values
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept-Language": random.choice(accept_languages),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": random.choice(["none", "same-origin"]),
                "Sec-Fetch-User": "?1"
            }
            
            # Apply to WebDriver (using CDP in Chrome)
            if hasattr(self.driver, "execute_cdp_cmd"):
                self.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
                logger.info("Applied random HTTP headers")
        except Exception as e:
            logger.warning(f"Failed to set random headers: {str(e)}")


    def click_element_with_retry(self, selector=None, by=By.CSS_SELECTOR, retries=None, element=None):
        """Clicks an element with retry logic."""
        if retries is None:
            retries = self.retry_limit
        for attempt in range(retries):
            try:
                if element is None:
                    element = self.wait.until(EC.element_to_be_clickable((by, selector)))

                # Call simulate_mouse_movement with the element
                simulate_mouse_movement(self.driver, element)
                
                # Small pause before clicking
                time.sleep(random.uniform(0.2, 0.5))
                
                element.click()
                return True
            except (ElementNotInteractableException, StaleElementReferenceException) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(1)  # Wait before retrying
                if element is None:
                    element = self.wait.until(EC.element_to_be_clickable((by, selector)))
        logger.error(f"Failed to click element after {retries} attempts.")
        return False

    def check_for_product(self):
        """Checks if the target product is in stock with more human-like browsing."""
        try:
            # Randomly decide whether to navigate to home page first (20% chance)
            if random.random() < 0.2:
                self.driver.get(self.base_url)
                human_like_delay(2, 4)
                # Simulate browsing behavior
                self.browse_random_category()
                human_like_delay(1, 3)
            
            # Navigate to target page
            if self.exact_product_url:
                self.driver.get(self.exact_product_url)
            else:
                self.driver.get(self.category_url)
            
            human_like_delay(self.random_delay_min, self.random_delay_max)
            simulate_mouse_movement(self.driver)
            
            # Scroll down slowly to look at products
            for _ in range(random.randint(3, 7)):
                self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
                human_like_delay(0.5, 1.5)
            
            # Find all product titles on the page
            product_titles = self.driver.find_elements(By.CSS_SELECTOR, "h1.product-title--lz7HX")
            
            # Randomly hover over a few products before finding target
            if len(product_titles) > 3:
                sample_size = min(len(product_titles), random.randint(1, 3))
                for title in random.sample(product_titles, sample_size):
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", title)
                    human_like_delay(0.5, 2)
            
            # Now look for the target product
            for title in product_titles:
                product_name = title.text
                if any(keyword.lower() in product_name.lower() for keyword in self.target_keywords):
                    logger.info(f"Found target product: {product_name}")
                    
                    # Scroll to product
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", title)
                    human_like_delay(1, 2)
                    
                    # Hover over product before clicking
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var mouseoverEvent = new MouseEvent('mouseover', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        element.dispatchEvent(mouseoverEvent);
                    """, title)
                    human_like_delay(0.5, 1.5)
                    
                    try:
                        product_link = title.find_element(By.XPATH, "./ancestor::a")
                        if self.click_element_with_retry(element=product_link):
                            return True
                        else:
                            logger.error("Failed to click the product link.")
                            return False
                    except NoSuchElementException:
                        logger.error("Product link not found.")
                        return False
            
            logger.info("Target product not found on the category page.")
            return False
        except Exception as e:
            logger.error(f"Failed to check for product: {str(e)}")
            return False

    def browse_random_category(self):
        """Simulates browsing behavior by clicking on a random category"""
        try:
            # Find menu items or category links
            category_links = self.driver.find_elements(By.CSS_SELECTOR, ".mega-menu-item, .category-link")
            
            if category_links:
                # Select a random category
                random_category = random.choice(category_links)
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", random_category)
                human_like_delay(0.5, 1.5)
                
                # Hover before clicking
                self.driver.execute_script("""
                    var element = arguments[0];
                    var mouseoverEvent = new MouseEvent('mouseover', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(mouseoverEvent);
                """, random_category)
                human_like_delay(0.5, 1.5)
                
                # Click the category
                random_category.click()
                human_like_delay(2, 4)
                
                # Scroll down to look at products
                scroll_amount = random.randint(2, 5)
                for _ in range(scroll_amount):
                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
                    human_like_delay(0.5, 1.5)
                    
                # Go back to previous page
                self.driver.back()
                human_like_delay(1, 2)
                
        except Exception as e:
            logger.warning(f"Random browsing failed: {str(e)}")

    def add_to_cart(self):
        """Adds the product to the cart. Webpage: Product page."""
        try:
            # Random interactions to look human
            self.perform_random_interactions()
            
            # Check for out-of-stock indicators
            try:
                out_of_stock = self.driver.find_element(By.CSS_SELECTOR, ".out-of-stock-message")
                if out_of_stock:
                    logger.info("Product is out of stock.")
                    return False
            except NoSuchElementException:
                pass  # No out-of-stock message found

            # Locate the quantity input field
            try:
                qty_field = self.driver.find_element(By.ID, "productQuantity")
                
                # Simulate mouse movement to the quantity field
                simulate_mouse_movement(self.driver, qty_field)
                
                qty_field.clear()  # Clear the default value (usually 1)
                human_like_typing(qty_field, str(self.quantity))
            except NoSuchElementException:
                logger.warning("Quantity field not found. Proceeding with default quantity (1).")

            # Scroll to the "Add to Cart" button with smoother behavior
            try:
                add_to_cart_btn = self.driver.find_element(By.CSS_SELECTOR, "button.add-to-cart-button--PZmQF")
                
                # Use smoother scrolling
                self.driver.execute_script(
                    """
                    function smoothScroll(element, duration) {
                        var start = window.pageYOffset || document.documentElement.scrollTop;
                        var elementPos = element.getBoundingClientRect().top;
                        var startTime = null;
                    
                        function animation(currentTime) {
                            if (startTime === null) startTime = currentTime;
                            var timeElapsed = currentTime - startTime;
                            var ease = function (t) { return t<0.5 ? 2*t*t : -1+(4-2*t)*t; };
                            var run = ease(Math.min(timeElapsed / duration, 1)) * elementPos;
                            window.scrollTo(0, start + run);
                            if (timeElapsed < duration) requestAnimationFrame(animation);
                        }
                        
                        requestAnimationFrame(animation);
                    }
                    
                    smoothScroll(arguments[0], 1000);
                    """, add_to_cart_btn
                )
                
                human_like_delay(self.random_delay_min, self.random_delay_max)
                
                # Move mouse to button
                simulate_mouse_movement(self.driver, add_to_cart_btn)
                
                # Click the "Add to Cart" button
                if not self.click_element_with_retry("button.add-to-cart-button--PZmQF"):
                    return False
                
                # Wait for confirmation
                self.wait.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".snackbar-message--nyi2n")))

                # Add some delay before saving cookies
                human_like_delay(self.random_delay_min, self.random_delay_max)
                
                # Save cookies after adding to cart
                save_cookies(self.driver, self.cookies_file)

                logger.info(f"Added {self.quantity} item(s) to cart!")
                return True
            except Exception as e:
                logger.error(f"Failed to add product to cart: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Failed to add product to cart: {str(e)}")
            return False
    
    def validate_cart(self):
        """Validates the cart contents. Webpage: Cart page."""
        try:
            self.driver.get(f"{self.base_url}/cart")  # Navigate to the cart page
            # Check if the cart is empty
            try:
                empty_cart_message = self.driver.find_element(By.CSS_SELECTOR, ".empty-cart-message")
                if empty_cart_message:
                    logger.error("Cart is empty.")
                    return False
            except NoSuchElementException:
                pass  # Cart is not empty

            product_name = self.driver.find_element(By.CSS_SELECTOR, ".product-name").text
            product_quantity = self.driver.find_element(By.CSS_SELECTOR, ".product-quantity input").get_attribute("value")
            
            if self.target_keywords[0] in product_name and int(product_quantity) == self.quantity:
                logger.info("Cart validation successful.")
                return True
            else:
                logger.error("Cart validation failed.")
                return False
        except Exception as e:
            logger.error(f"Failed to validate cart: {str(e)}")
            return False

    def checkout(self):
        """Initiates the checkout process. Webpage: Cart page."""
        try:
            # Step 1: Access the cart
            if not self.click_element_with_retry("a.header-cart--_2R2kd"):
                logger.error("Failed to access the cart.")
                return False
            
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
            simulate_mouse_movement(self.driver)

            # Step 2: Use preferred payment method
            if self.config.get("payment_method") == "paypal":
                return self.use_paypal()
            else:
                return self.use_card()
        except Exception as e:
            logger.error(f"Checkout failed: {str(e)}")
            return False

    def use_paypal(self):
        """Completes checkout using PayPal. Webpage: PayPal payment page."""
        try:
            # Click the PayPal button
            if not self.click_element_with_retry("div.paypal-button[data-funding-source='paypal']"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            # Click the "Continue to Review Order" button
            if not self.click_element_with_retry("button#payment-submit-btn"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            logger.info("PayPal payment completed successfully!")
            return True
        except Exception as e:
            logger.error(f"PayPal payment failed: {str(e)}")
            return False

    def use_card(self):
        """Completes checkout using card payment. Webpage: Checkout payment page."""
        try:
            # Click the checkout button
            if not self.click_element_with_retry("button.btn--ICBoB.btn-secondary--mtUol.btn-lg--uGcjb[data-ge-checkout-button='true']"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            # Select payment method (Credit/Debit Card)
            if not self.click_element_with_retry("#billing-selector"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
            if not self.click_element_with_retry("option[value='credit-card']"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            # Enter card information
            try:
                # Card number (iframe)
                card_number_iframe = self.driver.find_element(By.CSS_SELECTOR, "#card-number-container iframe")
                self.driver.switch_to.frame(card_number_iframe)
                card_number_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                human_like_typing(card_number_field, self.payment_info["card_number"])  # Use helper function
                self.driver.switch_to.default_content()
                human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

                # Expiry month
                if not self.click_element_with_retry("#expiryMonth"):
                    return False
                human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
                if not self.click_element_with_retry(f"option[value='{self.payment_info['expiry_month']}']"):
                    return False
                human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

                # Expiry year
                if not self.click_element_with_retry("#expiryYear"):
                    return False
                human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
                if not self.click_element_with_retry(f"option[value='{self.payment_info['expiry_year']}']"):
                    return False
                human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

                # CVV (iframe, optional)
                try:
                    cvv_iframe = self.driver.find_element(By.CSS_SELECTOR, "#security-code-container iframe")
                    self.driver.switch_to.frame(cvv_iframe)
                    cvv_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                    human_like_typing(cvv_field, self.payment_info["cvv"])  # Use helper function
                    self.driver.switch_to.default_content()
                    human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
                except NoSuchElementException:
                    logger.warning("CVV field not found. Skipping...")
            except Exception as e:
                logger.error(f"Failed to enter card information: {str(e)}")
                return False

            # Agree to terms and conditions
            if not self.click_element_with_retry("#privacy-agreement-checkbox"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            # Click the "Place Order" button
            if not self.click_element_with_retry("button[value='PLACE ORDER']"):
                return False
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function

            # Wait for order confirmation
            self.wait.until(EC.url_contains("success"))
            logger.info("Card payment completed successfully!")
            return True
        except Exception as e:
            logger.error(f"Card payment failed: {str(e)}")
            return False

    def run(self):
        """Main bot loop with improved randomization and human-like behavior"""
        logger.info("Starting Pokemon TCG buying bot")
        try:
            success = False
            check_count = 0
            
            while not success:
                check_count += 1
                
                # Randomize check interval to avoid detection
                actual_interval = self.check_interval * random.uniform(0.8, 1.2)
                
                # Vary logging format slightly (bots tend to be too consistent)
                current_time = datetime.now()
                if random.random() > 0.5:
                    log_msg = f"Check #{check_count} at {current_time.strftime('%H:%M:%S')}"
                else:
                    log_msg = f"Attempt {check_count} ({current_time.strftime('%Y-%m-%d %H:%M')})"
                
                logger.info(log_msg)
                
                # Rotate proxy occasionally
                if hasattr(self, 'proxies') and self.proxies and check_count % getattr(self, 'proxy_rotation_frequency', 5) == 0:
                    if hasattr(self, 'rotate_proxy'):
                        self.rotate_proxy()
                
                # Randomize initial waiting period
                initial_wait = random.uniform(5, 15)  
                logger.info(f"Initial wait: {initial_wait:.2f} seconds...")
                time.sleep(initial_wait)

                # Proceed with the bot's logic
                if self.check_for_product():
                    # Do some random interactions between steps
                    human_like_delay(self.random_delay_min * 2, self.random_delay_max * 2)
                    self.perform_random_interactions()
                    
                    if self.add_to_cart(): 
                        # More random interactions
                        human_like_delay(self.random_delay_min, self.random_delay_max)
                        self.perform_random_interactions()
                        
                        if self.validate_cart():
                            # More random interactions
                            human_like_delay(self.random_delay_min, self.random_delay_max)
                            self.perform_random_interactions()
                            
                            if self.checkout():
                                logger.info("Purchase completed successfully!")
                                success = True
                                break
                    else:
                        logger.error("Failed to complete purchase")
                        # Variable retry timing
                        wait_time = self.check_interval * random.uniform(1.5, 2.5)
                        logger.info(f"Waiting {wait_time:.2f} seconds before retry...")
                        time.sleep(wait_time)
                
                # More human-like random interval instead of fixed
                logger.info(f"Next check in approximately {actual_interval:.2f} seconds")
                time.sleep(actual_interval)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        finally:
            save_cookies(self.driver, self.cookies_file)
            self.driver.quit()
            logger.info("Bot shutting down")