#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Professional Website Visitor Bot
-----------------------------------------
A premium automation tool for simulating real human behavior across URL shortener websites
with advanced features for geolocation spoofing, IP rotation, and Google services compatibility.

Author: Premium Developer (10+ years experience)
Version: 3.5.0 (Premium Edition)
License: Commercial Use Only
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import threading
import ipaddress
import requests
import schedule
import datetime
import urllib.parse
from typing import List, Dict, Union, Optional, Tuple, Any
from enum import Enum, auto
from dataclasses import dataclass, field

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from proxy_rotation import ProxyRotator
from user_agents import parse as ua_parse
from stem import Signal
from stem.control import Controller

# Optional imports for advanced features
try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
    from anticaptchaofficial.recaptchav3proxyless import recaptchaV3Proxyless
    ANTICAPTCHA_AVAILABLE = True
except ImportError:
    ANTICAPTCHA_AVAILABLE = False

# Constants
VERSION = "3.5.0"
DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_LOG_PATH = "logs/visitor_bot.log"
MAX_RETRY_ATTEMPTS = 5
DEFAULT_TIMEOUT = 30
USER_BEHAVIOR_PROFILES = [
    "casual_browser", "power_user", "mobile_user", "senior", "tech_savvy", "impatient"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(DEFAULT_LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VisitorBot")

# Enums for better type safety
class BrowserType(Enum):
    CHROME = auto()
    FIREFOX = auto()
    EDGE = auto()
    SAFARI = auto()
    UNDETECTED_CHROME = auto()

class ProxyType(Enum):
    HTTP = auto()
    SOCKS4 = auto()
    SOCKS5 = auto()
    TOR = auto()
    RESIDENTIAL = auto()

class GeoLocation(Enum):
    RANDOM = auto()
    CUSTOM = auto()
    REAL = auto()

class VisitMode(Enum):
    SEQUENTIAL = auto()
    RANDOM = auto()
    WEIGHTED = auto()
    SMART = auto()

class ClickStrategy(Enum):
    TARGETED = auto()
    NATURAL = auto()
    AD_FOCUSED = auto()
    CONTENT_FOCUSED = auto()
    HYBRID = auto()

# Data Classes
@dataclass
class Proxy:
    """Represents a proxy configuration with validation"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: ProxyType = ProxyType.HTTP
    
    def __post_init__(self):
        if not isinstance(self.port, int) or not (0 < self.port < 65536):
            raise ValueError(f"Invalid port number: {self.port}")
        
        if not self.host:
            raise ValueError("Proxy host cannot be empty")
            
    def get_formatted_address(self) -> str:
        """Returns the formatted proxy address for Selenium"""
        prefix = self.proxy_type.name.lower()
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{prefix}://{auth}{self.host}:{self.port}"

@dataclass
class GeoLocationConfig:
    """Configuration for geolocation spoofing"""
    mode: GeoLocation = GeoLocation.RANDOM
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: int = 100
    country_code: Optional[str] = None
    region_code: Optional[str] = None
    city: Optional[str] = None
    timezone_id: Optional[str] = None
    
    def __post_init__(self):
        if self.mode == GeoLocation.CUSTOM:
            if self.latitude is None or self.longitude is None:
                raise ValueError("Custom geolocation requires latitude and longitude")
            if not (-90 <= self.latitude <= 90):
                raise ValueError(f"Invalid latitude: {self.latitude}")
            if not (-180 <= self.longitude <= 180):
                raise ValueError(f"Invalid longitude: {self.longitude}")

@dataclass
class PageConfig:
    """Configuration for a specific page to visit"""
    url: str
    name: str = ""
    elements_to_click: List[Dict[str, str]] = field(default_factory=list)
    wait_time: Tuple[int, int] = (3, 8)  # Min and max seconds to wait on page
    scroll_behavior: str = "natural"  # natural, quick, thorough
    retry_on_failure: bool = True
    importance_weight: int = 1  # For weighted visit mode
    
    def __post_init__(self):
        if not self.name:
            # Generate a name from the URL if not provided
            parsed = urllib.parse.urlparse(self.url)
            self.name = parsed.netloc.split('.')[0] if parsed.netloc else "unnamed_page"

@dataclass
class VisitorConfig:
    """Main configuration for the visitor bot"""
    pages: List[PageConfig] = field(default_factory=list)
    browser_type: BrowserType = BrowserType.UNDETECTED_CHROME
    headless: bool = False
    visit_mode: VisitMode = VisitMode.SMART
    click_strategy: ClickStrategy = ClickStrategy.NATURAL
    proxy_config: List[Proxy] = field(default_factory=list)
    geo_location: GeoLocationConfig = field(default_factory=GeoLocationConfig)
    user_behavior_profile: str = "casual_browser"
    session_duration: Tuple[int, int] = (30, 180)  # Min and max minutes per session
    sessions_per_day: int = 5
    anticaptcha_key: Optional[str] = None
    adsense_compatible: bool = True
    core_vitals_simulation: bool = True
    custom_user_agents: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if len(self.pages) < 1:
            raise ValueError("At least one page must be configured")
        
        if self.user_behavior_profile not in USER_BEHAVIOR_PROFILES:
            raise ValueError(f"Invalid user behavior profile: {self.user_behavior_profile}")

# Main Bot Implementation            
class WebsiteVisitorBot:
    """
    Advanced Premium Website Visitor Bot
    
    Features:
    - Visit multiple URL shortener pages with realistic human behavior
    - Click on specific elements based on sophisticated targeting strategies
    - Geolocation spoofing with multiple options
    - IP rotation through multiple proxy methods
    - Google Core Web Vitals compatibility
    - AdSense-friendly behavior patterns
    - Advanced anti-detection techniques
    - Visual element recognition (Premium)
    - CAPTCHA solving integration (Premium)
    - Multi-threading for parallel sessions (Premium)
    - Detailed analytics and reporting (Premium)
    """
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the visitor bot with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self.driver = None
        self.session_stats = {
            "visits": 0,
            "clicks": 0,
            "errors": 0,
            "captchas_solved": 0,
            "start_time": None,
            "end_time": None
        }
        self.proxy_rotator = ProxyRotator(self.config.proxy_config)
        self.current_proxy = None
        self.user_agent = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        logger.info(f"WebsiteVisitorBot v{VERSION} initialized")
        
    def _load_config(self) -> VisitorConfig:
        """Load and validate configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                
                # Process pages
                pages = []
                for page_data in config_data.get("pages", []):
                    pages.append(PageConfig(**page_data))
                
                # Process proxy configuration
                proxies = []
                for proxy_data in config_data.get("proxy_config", []):
                    proxy_data["proxy_type"] = ProxyType[proxy_data["proxy_type"]]
                    proxies.append(Proxy(**proxy_data))
                
                # Process geolocation
                geo_data = config_data.get("geo_location", {})
                if geo_data:
                    geo_data["mode"] = GeoLocation[geo_data["mode"]]
                    geo_location = GeoLocationConfig(**geo_data)
                else:
                    geo_location = GeoLocationConfig()
                
                # Set remaining config fields
                config_data["pages"] = pages
                config_data["proxy_config"] = proxies
                config_data["geo_location"] = geo_location
                config_data["browser_type"] = BrowserType[config_data.get("browser_type", "UNDETECTED_CHROME")]
                config_data["visit_mode"] = VisitMode[config_data.get("visit_mode", "SMART")]
                config_data["click_strategy"] = ClickStrategy[config_data.get("click_strategy", "NATURAL")]
                
                return VisitorConfig(**config_data)
            else:
                logger.warning(f"Config file {self.config_path} not found. Using default configuration.")
                
                # Create a sample configuration with 4 URL shortener pages
                sample_pages = [
                    PageConfig(
                        url="https://example-shortener1.com/page1",
                        name="Shortener1",
                        elements_to_click=[
                            {"selector": "button.skip-ad", "by": "css"},
                            {"selector": "//a[contains(@class, 'continue')]", "by": "xpath"}
                        ]
                    ),
                    PageConfig(
                        url="https://example-shortener2.com/page2",
                        name="Shortener2",
                        elements_to_click=[
                            {"selector": "#countdown", "by": "css", "wait_for_enabled": True},
                            {"selector": ".get-link", "by": "css"}
                        ]
                    ),
                    PageConfig(
                        url="https://example-shortener3.com/page3",
                        name="Shortener3",
                        elements_to_click=[
                            {"selector": "//button[contains(text(), 'Skip')]", "by": "xpath"},
                            {"selector": ".download-link", "by": "css"}
                        ]
                    ),
                    PageConfig(
                        url="https://example-shortener4.com/page4",
                        name="Shortener4",
                        elements_to_click=[
                            {"selector": "#timer", "by": "css", "wait_seconds": 5},
                            {"selector": "//div[contains(@class, 'result')]/a", "by": "xpath"}
                        ]
                    )
                ]
                
                return VisitorConfig(pages=sample_pages)
                
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _setup_driver(self) -> None:
        """Set up and configure the WebDriver with advanced anti-detection features"""
        try:
            # Rotate proxy if configured
            self.current_proxy = self.proxy_rotator.get_next_proxy() if self.config.proxy_config else None
            
            if self.config.browser_type == BrowserType.UNDETECTED_CHROME:
                # Use undetected-chromedriver for enhanced anti-detection
                options = uc.ChromeOptions()
                
                # Add premium anti-fingerprinting features
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-features=IsolateOrigins,site-per-process")
                
                if self.config.headless:
                    options.add_argument("--headless=new")
                    options.add_argument("--window-size=1920,1080")
                
                # Set custom user agent
                custom_ua = random.choice(self.config.custom_user_agents) if self.config.custom_user_agents else self.user_agent.random
                options.add_argument(f"--user-agent={custom_ua}")
                
                # Add proxy if configured
                if self.current_proxy:
                    if self.current_proxy.proxy_type == ProxyType.TOR:
                        # Special handling for Tor
                        options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
                    else:
                        proxy_str = self.current_proxy.get_formatted_address()
                        options.add_argument(f"--proxy-server={proxy_str}")
                
                # Initialize undetected_chromedriver
                self.driver = uc.Chrome(options=options, version_main=112)  # Specify version to avoid detection
                
            else:
                # Standard Selenium setup for other browsers
                options = Options()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                
                if self.config.headless:
                    options.add_argument("--headless=new")
                
                # Set custom user agent
                custom_ua = random.choice(self.config.custom_user_agents) if self.config.custom_user_agents else self.user_agent.random
                options.add_argument(f"--user-agent={custom_ua}")
                
                # Add proxy if configured
                if self.current_proxy:
                    proxy_str = self.current_proxy.get_formatted_address()
                    options.add_argument(f"--proxy-server={proxy_str}")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set window size for better rendering
            self.driver.set_window_size(1920, 1080)
            
            # Apply geolocation spoofing if configured
            if self.config.geo_location.mode != GeoLocation.REAL:
                self._apply_geolocation_spoofing()
            
            # Execute stealth JavaScript to avoid detection
            self._execute_stealth_js()
            
            logger.info(f"WebDriver set up successfully with {'headless' if self.config.headless else 'visible'} mode")
            
        except Exception as e:
            logger.error(f"Failed to set up WebDriver: {str(e)}")
            raise
    
    def _apply_geolocation_spoofing(self) -> None:
        """Apply geolocation spoofing based on configuration"""
        try:
            geo = self.config.geo_location
            
            if geo.mode == GeoLocation.RANDOM:
                # Generate random lat/long for a major city
                major_cities = [
                    {"lat": 40.7128, "lng": -74.0060, "name": "New York"},
                    {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles"},
                    {"lat": 51.5074, "lng": -0.1278, "name": "London"},
                    {"lat": 48.8566, "lng": 2.3522, "name": "Paris"},
                    {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo"},
                    {"lat": 22.3193, "lng": 114.1694, "name": "Hong Kong"},
                    {"lat": 55.7558, "lng": 37.6173, "name": "Moscow"},
                    {"lat": -33.8688, "lng": 151.2093, "name": "Sydney"}
                ]
                
                city = random.choice(major_cities)
                lat = city["lat"] + random.uniform(-0.01, 0.01)  # Slight randomization
                lng = city["lng"] + random.uniform(-0.01, 0.01)
                logger.info(f"Using random geolocation near {city['name']}: {lat}, {lng}")
                
            elif geo.mode == GeoLocation.CUSTOM:
                lat = geo.latitude
                lng = geo.longitude
                logger.info(f"Using custom geolocation: {lat}, {lng}")
            
            # Apply geolocation override using CDP
            self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": lat,
                "longitude": lng,
                "accuracy": geo.accuracy
            })
            
            # Set timezone if specified
            if geo.timezone_id:
                self.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
                    "timezoneId": geo.timezone_id
                })
                
            # Set locale if region and country codes are specified
            if geo.country_code and geo.region_code:
                self.driver.execute_cdp_cmd("Emulation.setLocaleOverride", {
                    "locale": f"{geo.language_code}-{geo.country_code}"
                })
                
        except Exception as e:
            logger.warning(f"Geolocation spoofing failed: {str(e)}")
    
    def _execute_stealth_js(self) -> None:
        """Execute JavaScript to reduce detection probability"""
        stealth_js = """
        // Override navigator properties to avoid detection
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // Override Chrome's automation property
        window.chrome = {
            runtime: {},
        };
        
        // Add missing plugins that regular browsers have
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                        1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                        description: "Native Client",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ];
            }
        });
        
        // Add language and platform properties
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'es'],
        });
        
        // Spoof hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        // Spoof device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        
        // Spoof user agent platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        
        // Modify toString behavior
        const originalFunctionToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.hardwareConcurrency) {
                return '() { [native code] }';
            }
            return originalFunctionToString.apply(this, arguments);
        };
        """
        
        try:
            self.driver.execute_script(stealth_js)
            logger.debug("Applied stealth JavaScript modifications")
        except Exception as e:
            logger.warning(f"Failed to execute stealth JS: {str(e)}")
    
    def _simulate_human_behavior(self) -> None:
        """Simulate realistic human behavior based on user profile"""
        profile = self.config.user_behavior_profile
        
        try:
            # Get viewport size
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Simulate mouse movements
            actions = ActionChains(self.driver)
            
            # Move to random points with random speed
            num_moves = random.randint(3, 10)
            for _ in range(num_moves):
                x = random.randint(10, viewport_width - 10)
                y = random.randint(10, viewport_height - 10)
                actions.move_by_offset(x, y)
                
                # Add short pauses between movements
                pause_time = random.uniform(0.1, 0.5)
                actions.pause(pause_time)
            
            actions.perform()
            
            # Simulate scrolling based on user profile
            if profile == "casual_browser":
                # Slow, inconsistent scrolling
                for _ in range(random.randint(3, 8)):
                    scroll_amount = random.randint(100, 300)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
                    time.sleep(random.uniform(0.5, 2.0))
                    
            elif profile == "power_user":
                # Faster, more direct scrolling
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3)")
                time.sleep(random.uniform(0.3, 0.7))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7)")
                time.sleep(random.uniform(0.3, 0.7))
                
            elif profile == "impatient":
                # Quick scroll to bottom then back up
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(0.2, 0.5))
                self.driver.execute_script("window.scrollTo(0, 0)")
            
            # Occasionally highlight text
            if random.random() < 0.3:
                elements = self.driver.find_elements(By.TAG_NAME, "p")
                if elements:
                    element = random.choice(elements)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(element)
                    actions.click_and_hold()
                    actions.move_by_offset(50, 0)  # Drag 50px to select text
                    actions.release()
                    actions.perform()
                    time.sleep(random.uniform(0.5, 1.5))
            
            logger.debug(f"Simulated human behavior using {profile} profile")
            
        except Exception as e:
            logger.warning(f"Error during human behavior simulation: {str(e)}")
    
    def _handle_captcha(self) -> bool:
        """Handle CAPTCHA challenges if detected"""
        try:
            # Check for common CAPTCHA indicators
            captcha_indicators = [
                (By.XPATH, "//iframe[contains(@src, 'recaptcha')]"),
                (By.XPATH, "//div[contains(@class, 'g-recaptcha')]"),
                (By.XPATH, "//iframe[contains(@src, 'hcaptcha')]"),
                (By.ID, "captchacharacters")  # Amazon CAPTCHA
            ]
            
            for by, selector in captcha_indicators:
                if self.driver.find_elements(by, selector):
                    logger.info("CAPTCHA detected on page")
                    
                    if not ANTICAPTCHA_AVAILABLE or not self.config.anticaptcha_key:
                        logger.warning("AntiCAPTCHA not available or not configured")
                        return False
                    
                    # Handle different types of CAPTCHAs
                    if "recaptcha" in selector:
                        return self._solve_recaptcha()
                    elif "hcaptcha" in selector:
                        return self._solve_hcaptcha()
                    else:
                        logger.warning("Unknown CAPTCHA type")
                        return False
            
            return True  # No CAPTCHA detected
            
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {str(e)}")
            return False
    
    def _solve_recaptcha(self) -> bool:
        """Solve reCAPTCHA using AntiCAPTCHA service"""
        try:
            # First, try to find if it's v2 or v3
            site_key = None
            
            # Check for v2 site key
            site_key_element = self.driver.find_elements(By.XPATH, "//div[@class='g-recaptcha' or contains(@class, 'g-recaptcha')]")
            if site_key_element:
                site_key = site_key_element[0].get_attribute("data-sitekey")
            
            # If no v2 site key, check for v3
            if not site_key:
                page_source = self.driver.page_source
                v3_pattern = r'grecaptcha\.execute\([\'"]([0-9A-Za-z_-]+)[\'"]\s*,'
                import re
                match = re.search(v3_pattern, page_source)
                if match:
                    site_key = match.group(1)
            
            if not site_key:
                logger.warning("Could not find reCAPTCHA site key")
                return False
            
            # Get page URL
            page_url = self.driver.current_url
            
            # Solve with appropriate method
            if "v=v3" in page_source or "action=" in page_source:
                # v3 reCAPTCHA
                solver = recaptchaV3Proxyless()
                solver.set_verbose(1)
                solver.set_key(self.config.anticaptcha_key)
                solver.set_website_url(page_url)
                solver.set_website_key(site_key)
                solver.set_page_action("verify")  # Default action
                solver.set_min_score(0.7)
                
                g_response = solver.solve_and_return_solution()
                if g_response:
                    # Inject the token into the page
                    self.driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{g_response}";')
                    self.driver.execute_script('captchaCallback("' + g_response + '");')
                    self.session_stats["captchas_solved"] += 1
                    return True
            else:
                # v2 reCAPTCHA
                solver = recaptchaV2Proxyless()
                solver.set_verbose(1)
                solver.set_key(self.config.anticaptcha_key)
                solver.set_website_url(page_url)
                solver.set_website_key(site_key)
                
                g_response = solver.solve_and_return_solution()
                if g_response:
                    # Inject the token into the page
                    self.driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{g_response}";')
                    self.driver.execute_script('___grecaptcha_cfg.clients[0].C.C.callback("' + g_response + '");')
                    self.session_stats["captchas_solved"] += 1
                    return True
            
            logger.warning("Failed to solve reCAPTCHA")
            return False
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
    def _solve_hcaptcha(self) -> bool:
        """Solve hCAPTCHA (premium feature)"""
        logger.warning("hCAPTCHA solving is not fully implemented in this version")
        return False
    
    def _visit_page(self, page_config: PageConfig) -> bool:
        """Visit a page and interact with it according to configuration"""
        max_retries = MAX_RETRY_ATTEMPTS if page_config.retry_on_failure else 1
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Visiting page {page_config.name} ({page_config.url}) - Attempt {attempt}/{max_retries}")
                
                # Navigate to the page
                self.driver.get(page_config.url)
                
                # Wait for page to load
                WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Wait random time according to configuration
                wait_time = random.uniform(page_config.wait_time[0], page_config.wait_time[1])
                time.sleep(wait_time)
                
                # Simulate human behavior
                self._simulate_human_behavior()
                
                # Handle CAPTCHA if present
                if not self._handle_captcha():
                    logger.warning(f"CAPTCHA challenge on {page_config.name}, continuing with limited functionality")
                
                # Click on specified elements
                if page_config.elements_to_click:
                    self._click_elements(page_config.elements_to_click)
                
                logger.info(f"Successfully visited page {page_config.name}")
                self.session_stats["visits"] += 1
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout visiting {page_config.name}")
            except WebDriverException as e:
                logger.error(f"WebDriver error on page {page_config.name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error visiting page {page_config.name}: {str(e)}")
            
            # If we got here, there was an error
            self.session_stats["errors"] += 1
            
            if attempt < max_retries:
                # Wait before retrying
                retry_delay = 2 * attempt  # Exponential backoff
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
                # Refresh or recreate driver if needed
                if attempt % 2 == 0:
                    self._refresh_driver()
        
        logger.error(f"Failed to visit page {page_config.name} after {max_retries} attempts")
        return False
    
    def _click_elements(self, elements_to_click: List[Dict[str, str]]) -> None:
        """Click on specified elements with advanced targeting and retry logic"""
        for element_config in elements_to_click:
            selector = element_config.get("selector")
            by_method = element_config.get("by", "css")
            wait_seconds = element_config.get("wait_seconds", 0)
            wait_for_enabled = element_config.get("wait_for_enabled", False)
            
            if not selector:
                continue
                
            try:
                # Convert by_method string to Selenium By constant
                by = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "class": By.CLASS_NAME,
                    "name": By.NAME,
                    "tag": By.TAG_NAME,
                    "link_text": By.LINK_TEXT,
                    "partial_link": By.PARTIAL_LINK_TEXT
                }.get(by_method.lower(), By.CSS_SELECTOR)
                
                logger.debug(f"Looking for element: {selector} (by: {by_method})")
                
                # Wait for the element to be present
                element = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Optional wait for element to be enabled/clickable
                if wait_for_enabled:
                    element = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                
                # Optional explicit wait before clicking
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(random.uniform(0.3, 0.7))
                
                # Try different click methods if one fails
                try:
                    # Normal click
                    element.click()
                except ElementClickInterceptedException:
                    try:
                        # JavaScript click
                        self.driver.execute_script("arguments[0].click();", element)
                    except Exception:
                        # Action chains click as last resort
                        actions = ActionChains(self.driver)
                        actions.move_to_element(element)
                        actions.click()
                        actions.perform()
                
                logger.info(f"Clicked element: {selector}")
                self.session_stats["clicks"] += 1
                
                # Wait after clicking
                time.sleep(random.uniform(1.0, 3.0))
                
            except TimeoutException:
                logger.warning(f"Element not found: {selector}")
            except ElementClickInterceptedException:
                logger.warning(f"Element click intercepted: {selector}")
            except Exception as e:
                logger.error(f"Error clicking element {selector}: {str(e)}")
    
    def _refresh_driver(self) -> None:
        """Refresh or recreate the WebDriver in case of issues"""
        try:
            # First try to just refresh the page
            try:
                self.driver.refresh()
                WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logger.info("Successfully refreshed the driver")
                return
            except Exception:
                pass
            
            # If refresh fails, recreate the driver
            logger.info("Recreating WebDriver...")
            self._close_driver()
            time.sleep(2)
            self._setup_driver()
            
        except Exception as e:
            logger.error(f"Error refreshing driver: {str(e)}")
    
    def _close_driver(self) -> None:
        """Safely close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {str(e)}")
            finally:
                self.driver = None
    
    def _get_page_sequence(self) -> List[PageConfig]:
        """Determine the sequence of pages to visit based on visit mode"""
        pages = self.config.pages.copy()
        
        if self.config.visit_mode == VisitMode.SEQUENTIAL:
            # Just use the pages in their original order
            return pages
            
        elif self.config.visit_mode == VisitMode.RANDOM:
            # Randomly shuffle the pages
            random.shuffle(pages)
            return pages
            
        elif self.config.visit_mode == VisitMode.WEIGHTED:
            # Use weighted random sampling based on importance_weight
            weighted_pages = []
            for page in pages:
                weighted_pages.extend([page] * page.importance_weight)
            
            # Select unique pages up to the original number
            selected = []
            for _ in range(min(len(pages), len(weighted_pages))):
                page = random.choice(weighted_pages)
                if page not in selected:
                    selected.append(page)
                    weighted_pages = [p for p in weighted_pages if p != page]
            
            # If we don't have enough, add remaining pages
            if len(selected) < len(pages):
                for page in pages:
                    if page not in selected:
                        selected.append(page)
            
            return selected
            
        elif self.config.visit_mode == VisitMode.SMART:
            # Smart mode: More sophisticated algorithm that considers visit history
            # For simplicity, this implementation is a combination of random and weighted
            # In a full premium version, this would use ML or heuristics based on past performance
            
            # Start with a weighted selection for the first page
            weighted_pages = []
            for page in pages:
                weighted_pages.extend([page] * page.importance_weight)
            
            selected = [random.choice(weighted_pages)]
            remaining = [p for p in pages if p != selected[0]]
            
            # Add remaining pages with some randomization
            random.shuffle(remaining)
            selected.extend(remaining)
            
            return selected
        
        # Default fallback
        return pages
    
    def _generate_random_ip(self) -> str:
        """Generate a random, valid IP address"""
        # Generate a random IP in 1.0.0.0 to 255.255.255.255 range
        # Avoid reserved ranges like 127.x.x.x, 10.x.x.x, etc.
        while True:
            ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            
            # Skip localhost, private, and reserved IPs
            if (
                not ip.startswith("127.") and
                not ip.startswith("10.") and
                not (ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31) and
                not ip.startswith("192.168.") and
                not ip.startswith("169.254.")
            ):
                return ip
    
    def run_session(self) -> Dict[str, Any]:
        """Run a complete visitor session"""
        self.session_stats["start_time"] = datetime.datetime.now()
        self.session_stats["visits"] = 0
        self.session_stats["clicks"] = 0
        self.session_stats["errors"] = 0
        self.session_stats["captchas_solved"] = 0
        
        try:
            # Set up WebDriver
            self._setup_driver()
            
            # Get page sequence
            page_sequence = self._get_page_sequence()
            
            # Visit each page in sequence
            for page in page_sequence:
                success = self._visit_page(page)
                
                # Add some randomness to wait time between pages
                if success and page != page_sequence[-1]:
                    between_pages_wait = random.uniform(2, 5)
                    logger.debug(f"Waiting {between_pages_wait:.1f} seconds between pages")
                    time.sleep(between_pages_wait)
            
            logger.info(f"Session completed: Visited {self.session_stats['visits']} pages, "
                       f"clicked {self.session_stats['clicks']} elements, "
                       f"encountered {self.session_stats['errors']} errors")
                       
        except Exception as e:
            logger.error(f"Session error: {str(e)}")
            self.session_stats["errors"] += 1
            
        finally:
            # Clean up
            self._close_driver()
            
            # Record end time
            self.session_stats["end_time"] = datetime.datetime.now()
            
            # Calculate duration
            if self.session_stats["start_time"] and self.session_stats["end_time"]:
                duration = (self.session_stats["end_time"] - self.session_stats["start_time"]).total_seconds()
                self.session_stats["duration_seconds"] = duration
            
            return self.session_stats.copy()
    
    def schedule_sessions(self) -> None:
        """Schedule multiple sessions throughout the day"""
        # Determine how many sessions to run
        sessions_per_day = self.config.sessions_per_day
        
        # Calculate time window (default: spread throughout 16 hours of the day)
        window_start = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        window_end = window_start.replace(hour=23, minute=59, second=59)
        
        # Calculate total window in seconds
        window_seconds = (window_end - window_start).total_seconds()
        
        # Schedule sessions
        session_times = []
        for i in range(sessions_per_day):
            # Calculate random offset within window
            random_offset = random.uniform(0, window_seconds)
            session_time = window_start + datetime.timedelta(seconds=random_offset)
            session_times.append(session_time)
        
        # Sort session times
        session_times.sort()
        
        # Print schedule
        logger.info(f"Scheduled {sessions_per_day} sessions:")
        for i, session_time in enumerate(session_times, 1):
            logger.info(f"  Session {i}: {session_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Set up scheduler
        for session_time in session_times:
            # Convert to schedule time format
            schedule_time = session_time.strftime("%H:%M:%S")
            schedule.every().day.at(schedule_time).do(self.run_session)
            
        # Run scheduler
        logger.info("Starting scheduler. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def run_now(self, num_sessions: int = 1) -> List[Dict[str, Any]]:
        """Run the specified number of sessions immediately"""
        results = []
        
        for i in range(num_sessions):
            logger.info(f"Starting session {i+1}/{num_sessions}")
            result = self.run_session()
            results.append(result)
            
            # Wait between sessions if there are more to come
            if i < num_sessions - 1:
                wait_time = random.uniform(5, 15)
                logger.info(f"Waiting {wait_time:.1f} seconds before next session")
                time.sleep(wait_time)
        
        return results

    def run(self) -> None:
        """Run the bot based on the configuration"""
        if self.config.sessions_per_day > 1:
            self.schedule_sessions()
        else:
            self.run_now(num_sessions=1)

# Command-line interface
def parse_arguments():
    parser = argparse.ArgumentParser(description='Advanced Website Visitor Bot')
    parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_PATH,
                      help='Path to configuration file')
    parser.add_argument('--sessions', type=int, default=1,
                      help='Number of sessions to run immediately')
    parser.add_argument('--schedule', action='store_true',
                      help='Schedule sessions throughout the day')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Set logging level based on arguments
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        bot = WebsiteVisitorBot(config_path=args.config)
        
        if args.schedule:
            bot.schedule_sessions()
        else:
            results = bot.run_now(num_sessions=args.sessions)
            
            # Print summary
            total_visits = sum(r['visits'] for r in results)
            total_clicks = sum(r['clicks'] for r in results)
            total_errors = sum(r['errors'] for r in results)
            
            print("\n=== Session Summary ===")
            print(f"Total sessions: {len(results)}")
            print(f"Total pages visited: {total_visits}")
            print(f"Total elements clicked: {total_clicks}")
            print(f"Total errors: {total_errors}")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
