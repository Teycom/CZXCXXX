#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config - Configurações do Bot
Centralizador de configurações e constantes do projeto
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AdsPowerConfig:
    """Configurações do AdsPower"""
    api_url: str = "http://localhost:50325"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    
    # Configurações avançadas de retry
    advanced_retry_enabled: bool = True
    max_retry_attempts: int = 10
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_exponential_base: float = 2.0
    retry_jitter: bool = True
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: int = 30
    
    # Health Check
    health_check_enabled: bool = True
    health_check_interval: int = 10
    health_check_timeout: int = 5
    
    # Monitoramento
    enable_detailed_logging: bool = True
    log_retry_attempts: bool = True
    log_performance_metrics: bool = True

@dataclass
class AutomationConfig:
    """Configurações de automação"""
    default_delay: float = 3.0
    page_timeout: int = 30
    element_timeout: int = 10
    headless: bool = False
    take_screenshots: bool = True
    screenshot_dir: str = "screenshots"
    max_retry_attempts: int = 3

@dataclass
class GoogleAdsConfig:
    """Configurações específicas do Google Ads"""
    base_url: str = "https://ads.google.com"
    login_timeout: int = 60
    campaign_creation_timeout: int = 120
    default_currency: str = "BRL"
    default_language: str = "pt-BR"

@dataclass
class LoggingConfig:
    """Configurações de logging"""
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_to_console: bool = True
    log_to_file: bool = True

class Config:
    """Classe principal de configuração"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        
        # Configurações padrão
        self.adspower = AdsPowerConfig()
        self.automation = AutomationConfig()
        self.google_ads = GoogleAdsConfig()
        self.logging = LoggingConfig()
        
        # Configurações gerais
        self.app_name = "Google Ads Campaign Bot"
        self.app_version = "1.0.0"
        self.debug_mode = False
        
        # Carregar configurações do arquivo se existir
        self.load_config()
        
        # Criar diretórios necessários
        self._create_directories()
    
    def _create_directories(self):
        """Criar diretórios necessários"""
        directories = [
            self.logging.log_dir,
            self.automation.screenshot_dir,
            "temp",
            "exports"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Diretório criado: {directory}")
    
    def load_config(self) -> bool:
        """Carregar configurações do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Atualizar configurações do AdsPower
                if 'adspower' in data:
                    adspower_data = data['adspower']
                    self.adspower.api_url = adspower_data.get('api_url', self.adspower.api_url)
                    self.adspower.timeout = adspower_data.get('timeout', self.adspower.timeout)
                    self.adspower.retry_attempts = adspower_data.get('retry_attempts', self.adspower.retry_attempts)
                    self.adspower.retry_delay = adspower_data.get('retry_delay', self.adspower.retry_delay)
                
                # Atualizar configurações de automação
                if 'automation' in data:
                    auto_data = data['automation']
                    self.automation.default_delay = auto_data.get('default_delay', self.automation.default_delay)
                    self.automation.page_timeout = auto_data.get('page_timeout', self.automation.page_timeout)
                    self.automation.element_timeout = auto_data.get('element_timeout', self.automation.element_timeout)
                    self.automation.headless = auto_data.get('headless', self.automation.headless)
                    self.automation.take_screenshots = auto_data.get('take_screenshots', self.automation.take_screenshots)
                    self.automation.screenshot_dir = auto_data.get('screenshot_dir', self.automation.screenshot_dir)
                    self.automation.max_retry_attempts = auto_data.get('max_retry_attempts', self.automation.max_retry_attempts)
                
                # Atualizar configurações do Google Ads
                if 'google_ads' in data:
                    ads_data = data['google_ads']
                    self.google_ads.base_url = ads_data.get('base_url', self.google_ads.base_url)
                    self.google_ads.login_timeout = ads_data.get('login_timeout', self.google_ads.login_timeout)
                    self.google_ads.campaign_creation_timeout = ads_data.get('campaign_creation_timeout', self.google_ads.campaign_creation_timeout)
                    self.google_ads.default_currency = ads_data.get('default_currency', self.google_ads.default_currency)
                    self.google_ads.default_language = ads_data.get('default_language', self.google_ads.default_language)
                
                # Atualizar configurações de logging
                if 'logging' in data:
                    log_data = data['logging']
                    self.logging.level = log_data.get('level', self.logging.level)
                    self.logging.log_dir = log_data.get('log_dir', self.logging.log_dir)
                    self.logging.max_file_size = log_data.get('max_file_size', self.logging.max_file_size)
                    self.logging.backup_count = log_data.get('backup_count', self.logging.backup_count)
                    self.logging.log_to_console = log_data.get('log_to_console', self.logging.log_to_console)
                    self.logging.log_to_file = log_data.get('log_to_file', self.logging.log_to_file)
                
                # Configurações gerais
                self.debug_mode = data.get('debug_mode', self.debug_mode)
                
                print(f"Configurações carregadas de: {self.config_file}")
                return True
                
        except Exception as e:
            print(f"Erro ao carregar configurações: {str(e)}")
            print("Usando configurações padrão")
            return False
        
        return False
    
    def save_config(self) -> bool:
        """Salvar configurações no arquivo JSON"""
        try:
            config_data = {
                'app_name': self.app_name,
                'app_version': self.app_version,
                'debug_mode': self.debug_mode,
                'last_updated': datetime.now().isoformat(),
                'adspower': asdict(self.adspower),
                'automation': asdict(self.automation),
                'google_ads': asdict(self.google_ads),
                'logging': asdict(self.logging)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"Configurações salvas em: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {str(e)}")
            return False
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Obter todas as configurações como dicionário"""
        return {
            'app_name': self.app_name,
            'app_version': self.app_version,
            'debug_mode': self.debug_mode,
            'adspower': asdict(self.adspower),
            'automation': asdict(self.automation),
            'google_ads': asdict(self.google_ads),
            'logging': asdict(self.logging)
        }
    
    def update_config(self, section: str, updates: Dict[str, Any]) -> bool:
        """Atualizar seção específica da configuração"""
        try:
            if section == 'adspower':
                for key, value in updates.items():
                    if hasattr(self.adspower, key):
                        setattr(self.adspower, key, value)
            
            elif section == 'automation':
                for key, value in updates.items():
                    if hasattr(self.automation, key):
                        setattr(self.automation, key, value)
            
            elif section == 'google_ads':
                for key, value in updates.items():
                    if hasattr(self.google_ads, key):
                        setattr(self.google_ads, key, value)
            
            elif section == 'logging':
                for key, value in updates.items():
                    if hasattr(self.logging, key):
                        setattr(self.logging, key, value)
            
            elif section == 'general':
                for key, value in updates.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            
            else:
                print(f"Seção desconhecida: {section}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar configuração: {str(e)}")
            return False
    
    def reset_to_defaults(self):
        """Resetar todas as configurações para os valores padrão"""
        self.adspower = AdsPowerConfig()
        self.automation = AutomationConfig()
        self.google_ads = GoogleAdsConfig()
        self.logging = LoggingConfig()
        self.debug_mode = False
        print("Configurações resetadas para valores padrão")
    
    def validate_config(self) -> Dict[str, list]:
        """Validar configurações e retornar problemas encontrados"""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        # Validar URL do AdsPower
        if not self.adspower.api_url.startswith(('http://', 'https://')):
            issues['errors'].append("URL da API do AdsPower deve começar com http:// ou https://")
        
        # Validar timeouts
        if self.adspower.timeout <= 0:
            issues['errors'].append("Timeout do AdsPower deve ser maior que 0")
        
        if self.automation.page_timeout <= 0:
            issues['errors'].append("Timeout de página deve ser maior que 0")
        
        if self.automation.default_delay < 0:
            issues['errors'].append("Delay padrão não pode ser negativo")
        
        # Validar diretórios
        if not os.path.exists(self.logging.log_dir):
            issues['warnings'].append(f"Diretório de logs não existe: {self.logging.log_dir}")
        
        if not os.path.exists(self.automation.screenshot_dir):
            issues['warnings'].append(f"Diretório de screenshots não existe: {self.automation.screenshot_dir}")
        
        # Validar URL do Google Ads
        if not self.google_ads.base_url.startswith('https://'):
            issues['errors'].append("URL do Google Ads deve usar HTTPS")
        
        return issues
    
    def get_selenium_options(self) -> Dict[str, Any]:
        """Obter opções para configuração do Selenium"""
        return {
            'headless': self.automation.headless,
            'page_timeout': self.automation.page_timeout,
            'element_timeout': self.automation.element_timeout,
            'default_delay': self.automation.default_delay,
            'take_screenshots': self.automation.take_screenshots,
            'screenshot_dir': self.automation.screenshot_dir
        }
    
    def print_config_summary(self):
        """Imprimir resumo das configurações"""
        print("\n" + "="*50)
        print(f"{self.app_name} v{self.app_version}")
        print("="*50)
        print(f"Modo Debug: {'Ativado' if self.debug_mode else 'Desativado'}")
        print(f"AdsPower API: {self.adspower.api_url}")
        print(f"Timeout Padrão: {self.automation.page_timeout}s")
        print(f"Delay entre Ações: {self.automation.default_delay}s")
        print(f"Modo Headless: {'Ativado' if self.automation.headless else 'Desativado'}")
        print(f"Logs: {self.logging.log_dir}")
        print(f"Screenshots: {self.automation.screenshot_dir}")
        print("="*50)

# Instância global de configuração
global_config = Config()

# Funções de conveniência
def get_config() -> Config:
    """Obter instância global de configuração"""
    return global_config

def save_config() -> bool:
    """Salvar configuração global"""
    return global_config.save_config()

def load_config() -> bool:
    """Recarregar configuração global"""
    return global_config.load_config()

# Constantes do projeto
class Constants:
    """Constantes do projeto"""
    
    # Seletores CSS/XPath comuns do Google Ads
    GOOGLE_ADS_SELECTORS = {
        'login_button': "//a[contains(@href, 'accounts.google.com')]",
        'new_campaign_button': "//button[contains(text(), 'Nova campanha')] | //button[contains(text(), 'New campaign')]",
        'campaign_name_input': "input[aria-label*='nome'] | input[aria-label*='name']",
        'budget_input': "input[aria-label*='orçamento'] | input[aria-label*='budget']",
        'location_input': "input[aria-label*='localização'] | input[aria-label*='location']",
        'keyword_textarea': "textarea[aria-label*='palavra'] | textarea[aria-label*='keyword']",
        'save_continue_button': "//button[contains(text(), 'Salvar e continuar')] | //button[contains(text(), 'Save and continue')]",
        'publish_button': "//button[contains(text(), 'Publicar')] | //button[contains(text(), 'Publish')]"
    }
    
    # Tipos de campanha
    CAMPAIGN_TYPES = {
        'SEARCH': 'Pesquisa',
        'DISPLAY': 'Display',
        'SHOPPING': 'Shopping',
        'VIDEO': 'Vídeo',
        'APP': 'App'
    }
    
    # Objetivos de campanha
    CAMPAIGN_OBJECTIVES = {
        'SALES': 'Vendas',
        'LEADS': 'Leads', 
        'WEBSITE_TRAFFIC': 'Tráfego do website',
        'BRAND_AWARENESS': 'Reconhecimento da marca',
        'PRODUCT_CONSIDERATION': 'Consideração do produto'
    }
    
    # Status de campanha
    CAMPAIGN_STATUS = {
        'ENABLED': 'Ativada',
        'PAUSED': 'Pausada',
        'REMOVED': 'Removida'
    }
    
    # Códigos de resposta da API do AdsPower
    ADSPOWER_RESPONSE_CODES = {
        0: 'Sucesso',
        1: 'Erro geral',
        2: 'Parâmetros inválidos',
        3: 'Perfil não encontrado',
        4: 'Browser já ativo',
        5: 'Falha ao iniciar browser'
    }

# Instância global de constantes
constants = Constants()