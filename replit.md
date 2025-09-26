# Overview

The Google Ads Campaign Automation Bot is an advanced desktop application that integrates with AdsPower browser profiles to automate Google Ads search campaign creation. The system features a modern Tkinter-based GUI with checkbox-based profile selection supporting 2000+ profiles, multiple ad titles (up to 15), multiple target locations/countries, and **SUPER ROBUST MULTILINGUAL SUPPORT**. It uses Selenium WebDriver with intelligent language detection and automatic fallback systems for Portuguese, English, and Spanish interfaces. The bot features advanced retry mechanisms and smart popup handling for maximum success rate across different language configurations.

# User Preferences

Preferred communication style: Simple, everyday language.
Campaign focus: Google Search campaigns only (no Display, Shopping, or Video campaigns).
Campaign objectives: Only the 4 objectives that support search campaigns - Vendas (Sales), Leads, Tráfego do site (Website traffic), and Criar campanha sem orientação (Create campaign without goal guidance).
Interface preference: Modern, professional design with efficient workflow management.

# System Architecture

## Desktop Application Architecture
The application follows a modular, component-based architecture with clear separation of concerns:

- **Main Application Controller** (`main.py`): Tkinter-based GUI that orchestrates all components
- **AdsPower Integration Layer** (`adspower_manager.py`): Handles communication with AdsPower's local API
- **Browser Automation Engine** (`google_ads_automation.py`): Selenium-based automation for Google Ads interactions
- **Configuration Management** (`config.py`): Centralized configuration using dataclasses
- **Logging System** (`logger.py`): Structured logging with file rotation

## Super Robust Multilingual Automation Strategy
The system uses Selenium WebDriver with undetected-chromedriver and selenium-stealth to avoid detection. It features **SUPER ROBUST MULTILINGUAL SUPPORT** with:

### Automatic Language Detection
- **Smart Detection**: Automatically detects Portuguese, English, or Spanish interface
- **Fallback Priority**: Detected language → Portuguese → English → Spanish
- **Multiple Attempts**: Up to 3-5 retry attempts with progressive delays

### Multilingual Selector System
- **Complete Coverage**: Comprehensive selectors for PT/EN/ES interfaces
- **Multiple Fallbacks**: Each element has multiple selector variations per language
- **Smart Retry**: Progressive retry system with increasing wait times

### Robust Error Handling
- **Smart Wait and Retry**: Intelligent retry system with page load detection
- **Popup Management**: Automatic popup closing between attempts
- **Language Adaptation**: Adapts selector strategy based on detected interface language

## Profile Management
AdsPower profiles are managed through their local API (default port 50325) with advanced selection features:
- Retrieve and display 2000+ browser profiles efficiently
- Checkbox-based individual profile selection with search filtering
- Bulk selection/deselection capabilities
- Real-time selected profile counter
- Start/stop browsers for multiple selected profiles
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