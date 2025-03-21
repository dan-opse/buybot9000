import time
import logging
import random
import pyautogui
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
from helpers import human_like_delay, human_like_typing, save_cookies, load_cookies
from selenium_stealth import stealth

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
        self.shipping_info = {
            "first_name": os.getenv("SHIPPING_FIRST_NAME"),
            "last_name": os.getenv("SHIPPING_LAST_NAME"),
            "address": os.getenv("SHIPPING_ADDRESS"),
            "city": os.getenv("SHIPPING_CITY"),
            "province": os.getenv("SHIPPING_PROVINCE"),
            "zip": os.getenv("SHIPPING_ZIP"),
            "phone": os.getenv("SHIPPING_PHONE")
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
                logger.info(f"Loaded configuration: targeting {self.target_keywords}, quantity: {self.quantity}")
        except FileNotFoundError:
            logger.error("Config file not found. Creating default config.")
            self.create_default_config()

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
        """Initialize the browser with anti-detection measures and proxy support."""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
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
            options.add_argument("--disable-sync")
            options.add_argument("--force-color-profile=srgb")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--no-first-run")
            options.add_argument("--safebrowsing-disable-auto-update")
            options.add_argument("--password-store=basic")
            options.add_argument("--use-mock-keychain")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--silent")

            # Add proxy if available
            if self.proxies:
                proxy = random.choice(self.proxies)  # Randomly select a proxy
                options.add_argument(f"--proxy-server={proxy}")
                logger.info(f"Using proxy: {proxy}")

            if self.headless_mode:
                options.add_argument("--headless")  # Run in headless mode

            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, random.randint(10, 15))
            
            # Apply stealth settings
            stealth(
                self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )

            self.load_cookies()
            logger.info("Browser initialized with anti-detection measures and proxy")
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

    def click_element_with_retry(self, selector=None, by=By.CSS_SELECTOR, retries=None, element=None):
        """Clicks an element with retry logic."""
        if retries is None:
            retries = self.retry_limit
        for attempt in range(retries):
            try:
                if element is None:
                    element = self.wait.until(EC.element_to_be_clickable((by, selector)))

                simulate_mouse_movement()

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
        """Checks if the target product is in stock. Webpage: Category page."""
        try:
            if self.exact_product_url:
                self.driver.get(self.exact_product_url)  # Navigate to the product page
            else:
                self.driver.get(self.category_url)  # Navigate to the category page

            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
            simulate_mouse_movement() # Simulate mouse movements after loading the page

            # Find all product titles on the page
            product_titles = self.driver.find_elements(By.CSS_SELECTOR, "h1.product-title--lz7HX")
            for title in product_titles:
                product_name = title.text
                if any(keyword.lower() in product_name.lower() for keyword in self.target_keywords):
                    logger.info(f"Found target product: {product_name}")
                    try:
                        # Find the product link (ancestor <a> element)
                        product_link = title.find_element(By.XPATH, "./ancestor::a")
                        # Click the product link with retry logic
                        if self.click_element_with_retry(None, by=By.XPATH, selector="./ancestor::a", element=product_link):
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

    def add_to_cart(self):
        """Adds the product to the cart. Webpage: Product page."""
        try:
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
                qty_field.clear()  # Clear the default value (usually 1)
                human_like_typing(qty_field, str(self.quantity))  # Use helper function
            except NoSuchElementException:
                logger.warning("Quantity field not found. Proceeding with default quantity (1).")

            # Scroll to the "Add to Cart" button
            add_to_cart_btn = self.driver.find_element(By.CSS_SELECTOR, "button.add-to-cart-button--PZmQF")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", add_to_cart_btn)
            human_like_delay(self.random_delay_min, self.random_delay_max)  # Use helper function
            simulate_mouse_movement()

            # Click the "Add to Cart" button
            if not self.click_element_with_retry("button.add-to-cart-button--PZmQF"):
                return False

            # Wait for confirmation
            self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".snackbar-message--nyi2n")))

            # Save cookies after adding to cart
            save_cookies(self.driver, self.cookies_file)  # Use helper function

            logger.info(f"Added {self.quantity} item(s) to cart!")
            return True
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
            simulate_mouse_movement()

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
        """Main bot loop"""
        logger.info("Starting Pokemon TCG buying bot")
        try:
            success = False
            check_count = 0

            while not success:
                check_count += 1
                logger.info(f"Check #{check_count} for target product at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Sleep for 10 seconds to mimic human behavior
                logger.info("Sleeping for 10 seconds to mimic human behavior...")
                time.sleep(10)

                # Proceed with the bot's logic
                if self.check_for_product():
                    if self.add_to_cart() and self.validate_cart() and self.checkout():
                        logger.info("Purchase completed successfully!")
                        success = True
                        break
                    else:
                        logger.error("Failed to complete purchase")
                        time.sleep(self.check_interval * 2)

                logger.info(f"Waiting approximately {self.check_interval} seconds before next check")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        finally:
            save_cookies(self.driver, self.cookies_file)  # Save cookies before quitting
            self.driver.quit()
            logger.info("Bot shutting down")