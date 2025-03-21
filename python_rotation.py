#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Rotation Module for Website Visitor Bot
---------------------------------------------
Handles proxy rotation, validation, and management with advanced features.

Author: Premium Developer (10+ years experience)
Version: 3.5.0 (Premium Edition)
"""

import os
import re
import time
import random
import logging
import requests
import ipaddress
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logger = logging.getLogger("ProxyRotator")

class ProxyType(Enum):
    """Enum representing different proxy types"""
    HTTP = auto()
    SOCKS4 = auto()
    SOCKS5 = auto()
    TOR = auto()
    RESIDENTIAL = auto()

@dataclass
class Proxy:
    """Represents a proxy configuration with validation"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: ProxyType = ProxyType.HTTP
    country: Optional[str] = None
    last_used: float = 0
    response_time: Optional[float] = None
    success_rate: float = 0.0
    failed_attempts: int = 0
    
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
    
    def get_requests_format(self) -> Dict[str, str]:
        """Returns the proxy in requests library format"""
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        proxy_str = f"{auth}{self.host}:{self.port}"
        
        if self.proxy_type in (ProxyType.HTTP, ProxyType.RESIDENTIAL):
            return {
                "http": f"http://{proxy_str}",
                "https": f"http://{proxy_str}"
            }
        elif self.proxy_type == ProxyType.SOCKS4:
            return {
                "http": f"socks4://{proxy_str}",
                "https": f"socks4://{proxy_str}"
            }
        elif self.proxy_type == ProxyType.SOCKS5:
            return {
                "http": f"socks5://{proxy_str}",
                "https": f"socks5://{proxy_str}"
            }
        elif self.proxy_type == ProxyType.TOR:
            return {
                "http": "socks5://127.0.0.1:9050",
                "https": "socks5://127.0.0.1:9050"
            }
        
        # Default fallback
        return {
            "http": f"http://{proxy_str}",
            "https": f"http://{proxy_str}"
        }
    
    def update_stats(self, success: bool, response_time: Optional[float] = None) -> None:
        """Update proxy statistics based on usage result"""
        self.last_used = time.time()
        
        if response_time is not None:
            if self.response_time is None:
                self.response_time = response_time
            else:
                # Weighted average (70% old, 30% new)
                self.response_time = 0.7 * self.response_time + 0.3 * response_time
        
        if success:
            # Increase success rate (weighted)
            self.success_rate = 0.7 * self.success_rate + 0.3 * 1.0
            self.failed_attempts = 0
        else:
            # Decrease success rate (weighted)
            self.success_rate = 0.7 * self.success_rate + 0.3 * 0.0
            self.failed_attempts += 1
    
    def is_reliable(self) -> bool:
        """Check if the proxy is considered reliable based on stats"""
        # Consider a proxy reliable if:
        # 1. Success rate is above 70% or we have no data yet
        # 2. It hasn't failed more than 3 consecutive times
        return (self.success_rate >= 0.7 or self.success_rate == 0.0) and self.failed_attempts < 3


class ProxyRotator:
    """
    Advanced proxy rotation manager with intelligent selection
    
    Features:
    - Smart proxy selection based on performance metrics
    - Automatic validation of proxies
    - Country-based filtering
    - Concurrent proxy testing
    - Support for multiple proxy types
    - Failure tracking and exponential backoff
    """
    
    def __init__(self, proxies: List[Proxy], test_url: str = "https://httpbin.org/ip", 
                 test_timeout: int = 10, min_proxies: int = 1):
        """Initialize the proxy rotator with a list of proxies"""
        self.proxies = proxies
        self.test_url = test_url
        self.test_timeout = test_timeout
        self.min_proxies = min_proxies
        self.last_used_index = -1
        self.validation_results = {}
        
        if proxies:
            self._validate_proxies()
    
    def _validate_proxies(self) -> None:
        """Validate all proxies in parallel"""
        logger.info(f"Validating {len(self.proxies)} proxies...")
        
        valid_count = 0
        with ThreadPoolExecutor(max_workers=min(10, len(self.proxies))) as executor:
            future_to_proxy = {
                executor.submit(self._test_proxy, proxy): proxy 
                for proxy in self.proxies
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result, response_time = future.result()
                    proxy.update_stats(result, response_time)
                    if result:
                        valid_count += 1
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} is valid (response time: {response_time:.2f}s)")
                    else:
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} is invalid")
                except Exception as e:
                    logger.warning(f"Error validating proxy {proxy.host}:{proxy.port}: {str(e)}")
                    proxy.update_stats(False)
        
        logger.info(f"Proxy validation completed. {valid_count}/{len(self.proxies)} proxies are valid.")
        
        if valid_count < self.min_proxies:
            logger.warning(f"Only {valid_count} valid proxies found. Minimum required: {self.min_proxies}")
    
    def _test_proxy(self, proxy: Proxy) -> Tuple[bool, Optional[float]]:
        """Test a single proxy and return (success, response_time)"""
        try:
            start_time = time.time()
            
            if proxy.proxy_type == ProxyType.TOR:
                # Special handling for Tor proxies
                # Check if Tor is running
                try:
                    response = requests.get("http://127.0.0.1:9050", timeout=2)
                    return False, None  # Direct connection to Tor proxy should fail
                except requests.exceptions.ConnectionError:
                    # Connection refused is good - Tor is running but not accepting HTTP
                    pass
                except Exception:
                    return False, None
                
                # Test with a connection through Tor
                proxies = {
                    "http": "socks5://127.0.0.1:9050",
                    "https": "socks5://127.0.0.1:9050"
                }
            else:
                proxies = proxy.get_requests_format()
            
            response = requests.get(
                self.test_url,
                proxies=proxies,
                timeout=self.test_timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Verify the response
            if response.status_code == 200:
                try:
                    # For httpbin.org/ip, verify we get an IP
                    response_json = response.json()
                    if "origin" in response_json or "ip" in response_json:
                        return True, response_time
                except Exception:
                    # If we can't parse JSON, just check status code
                    return True, response_time
            
            return False, None
            
        except requests.exceptions.Timeout:
            logger.debug(f"Proxy {proxy.host}:{proxy.port} timed out")
            return False, None
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error with proxy {proxy.host}:{proxy.port}")
            return False, None
        except Exception as e:
            logger.debug(f"Error testing proxy {proxy.host}:{proxy.port}: {str(e)}")
            return False, None
    
    def get_next_proxy(self) -> Optional[Proxy]:
        """Get the next proxy using intelligent selection"""
        if not self.proxies:
            return None
        
        # Filter to only include reliable proxies
        reliable_proxies = [p for p in self.proxies if p.is_reliable()]
        
        if not reliable_proxies:
            # If no reliable proxies, retry the least recently used proxy
            self.proxies.sort(key=lambda p: p.last_used)
            logger.warning("No reliable proxies available. Using least recently used proxy.")
            return self.proxies[0]
        
        # Use various strategies to select the best proxy
        
        # Strategy 1: Response time weighted random selection
        if all(p.response_time is not None for p in reliable_proxies):
            # Lower response time = higher weight
            # Invert and normalize response times
            max_time = max(p.response_time for p in reliable_proxies) + 0.01  # Avoid division by zero
            weights = [(max_time - p.response_time) / max_time for p in reliable_proxies]
            
            # Add small random factor to avoid getting stuck on one proxy
            weights = [w + random.uniform(0, 0.2) for w in weights]
            
            # Normalize weights
            total = sum(weights)
            weights = [w / total for w in weights]
            
            # Weighted random selection
            selected_proxy = random.choices(reliable_proxies, weights=weights, k=1)[0]
            logger.debug(f"Selected proxy {selected_proxy.host}:{selected_proxy.port} (response time: {selected_proxy.response_time:.2f}s)")
            return selected_proxy
        
        # Strategy 2: Least recently used with success rate factor
        candidates = sorted(reliable_proxies, key=lambda p: p.last_used)
        # Take top 3 candidates (or all if fewer than 3)
        candidates = candidates[:min(3, len(candidates))]
        
        # From these candidates, prefer those with higher success rates
        candidates.sort(key=lambda p: p.success_rate, reverse=True)
        
        selected_proxy = candidates[0]
        logger.debug(f"Selected proxy {selected_proxy.host}:{selected_proxy.port} (success rate: {selected_proxy.success_rate:.2f})")
        return selected_proxy
    
    def report_proxy_result(self, proxy: Proxy, success: bool, response_time: Optional[float] = None) -> None:
        """Report the result of using a proxy to update its statistics"""
        if proxy in self.proxies:
            proxy.update_stats(success, response_time)
            logger.debug(f"Updated proxy {proxy.host}:{proxy.port} stats: success={success}, response_time={response_time}")
    
    def add_proxy(self, proxy: Proxy, validate: bool = True) -> bool:
        """Add a new proxy to the rotation pool"""
        if proxy in self.proxies:
            logger.warning(f"Proxy {proxy.host}:{proxy.port} already in pool")
            return False
        
        if validate:
            result, response_time = self._test_proxy(proxy)
            proxy.update_stats(result, response_time)
            
            if not result:
                logger.warning(f"New proxy {proxy.host}:{proxy.port} failed validation")
                return False
        
        self.proxies.append(proxy)
        logger.info(f"Added new proxy {proxy.host}:{proxy.port} to pool")
        return True
    
    def remove_proxy(self, proxy: Proxy) -> bool:
        """Remove a proxy from the rotation pool"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"Removed proxy {proxy.host}:{proxy.port} from pool")
            return True
        return False
    
    def get_proxy_by_country(self, country_code: str) -> Optional[Proxy]:
        """Get a proxy from a specific country"""
        country_proxies = [p for p in self.proxies if p.country == country_code.upper() and p.is_reliable()]
        
        if not country_proxies:
            logger.warning(f"No reliable proxies found for country {country_code}")
            return None
        
        # Sort by reliability and recency
        country_proxies.sort(key=lambda p: (p.success_rate, -p.last_used), reverse=True)
        return country_proxies[0]
    
    def reset_tor_identity(self) -> bool:
        """Reset the Tor identity by sending NEWNYM signal"""
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                logger.info("Tor identity reset successfully")
                return True
        except Exception as e:
            logger.error(f"Error resetting Tor identity: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the proxy pool"""
        reliable_count = sum(1 for p in self.proxies if p.is_reliable())
        
        avg_response_time = 0
        response_times = [p.response_time for p in self.proxies if p.response_time is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "total": len(self.proxies),
            "reliable": reliable_count,
            "unreliable": len(self.proxies) - reliable_count,
            "avg_response_time": avg_response_time,
            "avg_success_rate": sum(p.success_rate for p in self.proxies) / len(self.proxies) if self.proxies else 0,
            "country_distribution": self._get_country_distribution()
        }
    
    def _get_country_distribution(self) -> Dict[str, int]:
        """Get the distribution of proxies by country"""
        countries = {}
        for proxy in self.proxies:
            if proxy.country:
                countries[proxy.country] = countries.get(proxy.country, 0) + 1
        return countries