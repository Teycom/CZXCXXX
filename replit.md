# Overview

The Google Ads Campaign Automation Bot is a desktop application that integrates with AdsPower browser profiles to automate Google Ads campaign creation. The system uses Selenium WebDriver for browser automation and provides a Tkinter-based GUI for user interaction. It manages multiple browser profiles through AdsPower's local API and automates the complete campaign creation workflow on Google Ads.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Desktop Application Architecture
The application follows a modular, component-based architecture with clear separation of concerns:

- **Main Application Controller** (`main.py`): Tkinter-based GUI that orchestrates all components
- **AdsPower Integration Layer** (`adspower_manager.py`): Handles communication with AdsPower's local API
- **Browser Automation Engine** (`google_ads_automation.py`): Selenium-based automation for Google Ads interactions
- **Configuration Management** (`config.py`): Centralized configuration using dataclasses
- **Logging System** (`logger.py`): Structured logging with file rotation

## Browser Automation Strategy
The system uses Selenium WebDriver with undetected-chromedriver and selenium-stealth to avoid detection. It maintains a selector-based approach for UI element interaction with fallback strategies for different language interfaces (English/Portuguese).

## Profile Management
AdsPower profiles are managed through their local API (default port 50325), allowing the bot to:
- Retrieve available browser profiles
- Start/stop browsers for specific profiles
- Maintain session state across multiple campaigns

## Configuration Pattern
Uses dataclass-based configuration with separate configs for:
- AdsPower API settings
- Automation behavior (timeouts, delays, screenshots)
- Google Ads specific settings
- Logging preferences

## Error Handling and Resilience
Implements retry mechanisms, timeout handling, and comprehensive logging for debugging automation issues. The system gracefully handles connection failures and API errors.

# External Dependencies

## Required Services
- **AdsPower**: Local browser profile management service (API endpoint: localhost:50325)
- **Google Ads**: Target platform for campaign automation

## Python Packages
- **selenium**: Web browser automation framework
- **undetected-chromedriver**: Anti-detection Chrome driver
- **selenium-stealth**: Additional stealth capabilities
- **requests**: HTTP client for AdsPower API communication
- **tkinter**: GUI framework (included with Python)

## Browser Requirements
- Chrome/Chromium browser managed through AdsPower profiles
- WebDriver compatibility for automation

## File System Dependencies
- Local directory structure for logs and screenshots
- Configuration file storage for campaign templates
- Session state persistence for active browsers