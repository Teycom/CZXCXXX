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

# Recent Changes

## Interface & UX Improvements (September 2025)
- Fixed critical infinite recursion bug in profile selection logic that was preventing the bot from recognizing selected profiles
- Completely redesigned the user interface to be modern, beautiful, and responsive with a professional color scheme
- Implemented profile selection persistence functionality allowing users to save and load their profile selections
- Repositioned the start button to always appear on the right side as requested and improved overall layout organization
- Enhanced search functionality with placeholders and better visual feedback for profile selection status

## Core Automation Improvements (September 2025)
- **MAJOR BUG FIX**: Corrected 17+ LSP errors in google_ads_automation.py that were causing silent failures
- **SUPER DETAILED LOGGING**: Added comprehensive logging throughout the entire automation pipeline
- **Enhanced Navigation**: Improved Google Ads navigation with robust multi-language support and fallback mechanisms
- **Screenshot Debugging**: Automatic screenshots at each critical step for debugging failed automation attempts
- **Step-by-Step Validation**: Each automation step now validates success before proceeding to the next
- **Error Recovery**: Intelligent retry system with progressive delays and multiple selector attempts
- **Real-time Status Tracking**: Detailed status updates showing exactly where automation succeeds or fails

## Technical Debt Resolved
- Eliminated all LSP diagnostics errors (17 critical issues fixed)
- Replaced non-existent `self.selectors` references with working multilingual selector system
- Fixed type annotation issues and parameter handling
- Improved error handling and exception management throughout the automation pipeline
- Added proper cleanup and resource management for Selenium WebDriver instances

## Debugging & Monitoring Enhancements
- Comprehensive logging at every automation step with emoji indicators for easy identification
- Automatic screenshot capture at failure points for visual debugging
- Real-time URL tracking and page title monitoring
- Login status detection and validation
- Page source analysis for troubleshooting automation issues
- Progressive retry delays with intelligent backoff strategies