#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Automation - Automação de Criação de Campanhas
Responsável pela automação do navegador para criar campanhas no Google Ads
"""

import time
import logging
import os
from typing import Dict, Optional, List
from datetime import datetime
import traceback
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
# REMOVIDO: import undetected_chromedriver as uc
# CORREÇÃO: Não usar undetected_chromedriver que ignora debuggerAddress
# CORREÇÃO CRÍTICA: Usar APENAS webdriver.Remote() - webdriver.Chrome() local PROIBIDO
from selenium_stealth import stealth
from adspower_manager import AdsPowerManager
from retry_system import (
    RetryManager, RetryConfig, create_webdriver_retry_manager,
    RetryExhaustedException, CircuitOpenException, with_retry
)

class GoogleAdsAutomation:
    """Automação para criação de campanhas no Google Ads"""
    
    def __init__(self, enable_advanced_retry: bool = True):
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        self.adspower_manager = AdsPowerManager(enable_advanced_retry=enable_advanced_retry)
        self.enable_advanced_retry = enable_advanced_retry
        
        # Sistema de retry robusto para WebDriver e navegação
        if self.enable_advanced_retry:
            self.webdriver_retry_manager = create_webdriver_retry_manager(self.logger)
            self.navigation_retry_manager = self._create_navigation_retry_manager()
            self.logger.info("🚀 Sistema de retry avançado ATIVADO para WebDriver e navegação")
        else:
            self.webdriver_retry_manager = None
            self.navigation_retry_manager = None
            self.logger.info("⚠️ Sistema de retry avançado DESATIVADO")
        
        # Configurações padrão
        self.default_timeout = 30
        self.default_delay = 3
        self.max_retries = 3
        self.retry_delay = 2
        self.current_language = 'auto'  # Detectar automaticamente
        
        # Seletores multilíngues super robustos - Português, Inglês, Espanhol
        self.multilingual_selectors = {
            'campaigns_menu': {
                'pt': ["//span[contains(text(), 'Campanhas')]", "//a[contains(text(), 'Campanhas')]", "//div[contains(@data-value, 'campaigns')]"],
                'en': ["//span[contains(text(), 'Campaigns')]", "//a[contains(text(), 'Campaigns')]", "//div[contains(@data-value, 'campaigns')]"],
                'es': ["//span[contains(text(), 'Campañas')]", "//a[contains(text(), 'Campañas')]", "//div[contains(@data-value, 'campaigns')]"]
            },
            'new_campaign_btn': {
                'pt': ["//button[contains(@aria-label, 'Nova campanha')]", "//button[contains(text(), '+')]", "//button[contains(@class, 'mdc-fab')]", "//button[contains(@class, 'create')]"],
                'en': ["//button[contains(@aria-label, 'New campaign')]", "//button[contains(text(), '+')]", "//button[contains(@class, 'mdc-fab')]", "//button[contains(@class, 'create')]"],
                'es': ["//button[contains(@aria-label, 'Nueva campaña')]", "//button[contains(text(), '+')]", "//button[contains(@class, 'mdc-fab')]", "//button[contains(@class, 'create')]"]
            },
            'objectives': {
                'sem_orientacao': {
                    'pt': ["//button[contains(text(), 'sem orientação')]", "//div[contains(text(), 'sem orientação')]", "//button[contains(text(), 'Criar campanha sem orientação')]"],
                    'en': ["//button[contains(text(), 'without goal')]", "//div[contains(text(), 'without goal')]", "//button[contains(text(), 'Create campaign without goal')]"],
                    'es': ["//button[contains(text(), 'sin orientación')]", "//div[contains(text(), 'sin orientación')]", "//button[contains(text(), 'Crear campaña sin orientación')]"]
                },
                'vendas': {
                    'pt': ["//div[contains(text(), 'Vendas')]", "//button[contains(text(), 'Vendas')]"],
                    'en': ["//div[contains(text(), 'Sales')]", "//button[contains(text(), 'Sales')]"],
                    'es': ["//div[contains(text(), 'Ventas')]", "//button[contains(text(), 'Ventas')]"]
                },
                'leads': {
                    'pt': ["//div[contains(text(), 'Leads')]", "//button[contains(text(), 'Leads')]"],
                    'en': ["//div[contains(text(), 'Leads')]", "//button[contains(text(), 'Leads')]"],
                    'es': ["//div[contains(text(), 'Clientes potenciales')]", "//button[contains(text(), 'Leads')]"]
                },
                'trafego': {
                    'pt': ["//div[contains(text(), 'Tráfego do site')]", "//div[contains(text(), 'Tráfego do website')]"],
                    'en': ["//div[contains(text(), 'Website traffic')]", "//div[contains(text(), 'Traffic')]"],
                    'es': ["//div[contains(text(), 'Tráfico del sitio web')]", "//div[contains(text(), 'Tráfico')]"]
                }
            },
            'search_network': {
                'pt': ["//div[contains(text(), 'Pesquisa')]", "//button[contains(text(), 'Pesquisa')]", "//div[contains(text(), 'Rede de Pesquisa')]"],
                'en': ["//div[contains(text(), 'Search')]", "//button[contains(text(), 'Search')]", "//div[contains(text(), 'Search Network')]"],
                'es': ["//div[contains(text(), 'Búsqueda')]", "//button[contains(text(), 'Búsqueda')]", "//div[contains(text(), 'Red de Búsqueda')]"]
            },
            'continue_btn': {
                'pt': ["//button[contains(text(), 'Continuar')]", "//button[contains(text(), 'Próximo')]", "//button[contains(@aria-label, 'Continuar')]"],
                'en': ["//button[contains(text(), 'Continue')]", "//button[contains(text(), 'Next')]", "//button[contains(@aria-label, 'Continue')]"],
                'es': ["//button[contains(text(), 'Continuar')]", "//button[contains(text(), 'Siguiente')]", "//button[contains(@aria-label, 'Continuar')]"]
            },
            'publish_btn': {
                'pt': ["//button[contains(text(), 'Publicar')]", "//button[contains(text(), 'Criar campanha')]", "//button[contains(text(), 'Finalizar')]"],
                'en': ["//button[contains(text(), 'Publish')]", "//button[contains(text(), 'Create campaign')]", "//button[contains(text(), 'Finish')]"],
                'es': ["//button[contains(text(), 'Publicar')]", "//button[contains(text(), 'Crear campaña')]", "//button[contains(text(), 'Finalizar')]"]
            },
            'input_fields': {
                'campaign_name': {
                    'pt': ["//input[contains(@aria-label, 'nome')]", "//input[contains(@placeholder, 'nome')]"],
                    'en': ["//input[contains(@aria-label, 'name')]", "//input[contains(@placeholder, 'name')]"],
                    'es': ["//input[contains(@aria-label, 'nombre')]", "//input[contains(@placeholder, 'nombre')]"]
                },
                'budget': {
                    'pt': ["//input[contains(@aria-label, 'orçamento')]", "//input[contains(@placeholder, 'orçamento')]"],
                    'en': ["//input[contains(@aria-label, 'budget')]", "//input[contains(@placeholder, 'budget')]"],
                    'es': ["//input[contains(@aria-label, 'presupuesto')]", "//input[contains(@placeholder, 'presupuesto')]"]
                },
                'location': {
                    'pt': ["//input[contains(@aria-label, 'localização')]", "//input[contains(@placeholder, 'localização')]"],
                    'en': ["//input[contains(@aria-label, 'location')]", "//input[contains(@placeholder, 'location')]"],
                    'es': ["//input[contains(@aria-label, 'ubicación')]", "//input[contains(@placeholder, 'ubicación')]"]
                },
                'keywords': {
                    'pt': ["//textarea[contains(@aria-label, 'palavra')]", "//input[contains(@aria-label, 'palavra')]"],
                    'en': ["//textarea[contains(@aria-label, 'keyword')]", "//input[contains(@aria-label, 'keyword')]"],
                    'es': ["//textarea[contains(@aria-label, 'palabra clave')]", "//input[contains(@aria-label, 'palabra clave')]"]
                },
                'headlines': {
                    'pt': ["//input[contains(@aria-label, 'Título')]", "//input[contains(@placeholder, 'Título')]"],
                    'en': ["//input[contains(@aria-label, 'Headline')]", "//input[contains(@placeholder, 'Headline')]"],
                    'es': ["//input[contains(@aria-label, 'Título')]", "//input[contains(@placeholder, 'Título')]"]
                },
                'descriptions': {
                    'pt': ["//textarea[contains(@aria-label, 'Descrição')]", "//textarea[contains(@placeholder, 'Descrição')]"],
                    'en': ["//textarea[contains(@aria-label, 'Description')]", "//textarea[contains(@placeholder, 'Description')]"],
                    'es': ["//textarea[contains(@aria-label, 'Descripción')]", "//textarea[contains(@placeholder, 'Descripción')]"]
                },
                'url': {
                    'pt': ["//input[contains(@aria-label, 'URL')]", "//input[contains(@placeholder, 'URL')]"],
                    'en': ["//input[contains(@aria-label, 'URL')]", "//input[contains(@placeholder, 'URL')]"],
                    'es': ["//input[contains(@aria-label, 'URL')]", "//input[contains(@placeholder, 'URL')]"]
                }
            }
        }
        
        # Log de inicialização extremamente detalhado (após definir seletores)
        self._log_automation_initialization()
    
    def _create_navigation_retry_manager(self) -> RetryManager:
        """Criar RetryManager específico para operações de navegação"""
        from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException
        
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=15.0,
            exponential_base=1.5,
            jitter=True,
            timeout=45.0,
            circuit_breaker_enabled=False,  # Não usar circuit breaker para navegação
            retry_on_exceptions=(
                WebDriverException,
                TimeoutException,
                NoSuchElementException,
                StaleElementReferenceException,
                ConnectionError,
                OSError
            )
        )
        
        return RetryManager(config, self.logger)
    
    def setup_driver_with_retry(self, browser_info: Dict) -> bool:
        """🔧 Configurar WebDriver APENAS com AdsPower - SEM FALLBACKS LOCAIS"""
        self.logger.info("🚀 INICIANDO setup do WebDriver - REQUER ADSPOWER FUNCIONANDO")
        
        # VERIFICAÇÃO CRÍTICA: AdsPower deve estar rodando
        if not browser_info or not isinstance(browser_info, dict):
            error_msg = (
                "❌ FALHA CRÍTICA: browser_info inválido!\n"
                "🔍 VERIFICAÇÕES NECESSÁRIAS:\n"
                "   1. AdsPower está aberto?\n"
                "   2. Perfil foi iniciado corretamente?\n"
                "   3. API local está habilitada?\n"
                "💡 Este sistema REQUER AdsPower funcionando - não há fallback local!"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if self.enable_advanced_retry and self.webdriver_retry_manager:
            try:
                return self.webdriver_retry_manager.execute_with_retry(
                    self._setup_driver_internal, browser_info
                )
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL no setup do WebDriver após retry: {str(e)}")
                return False
            except Exception as e:
                self.logger.error(f"❌ ERRO INESPERADO no setup do WebDriver: {str(e)}")
                return False
        else:
            # Fallback para método original
            return self._setup_driver_internal(browser_info)
    
    def _setup_driver_internal(self, browser_info: Dict) -> bool:
        """🔧 Método interno para setup do WebDriver APENAS com AdsPower - SEM FALLBACKS"""
        # CORREÇÃO CRÍTICA: Removido fallback_chrome para garantir 100% controle AdsPower
        strategies = [
            ("remote_webdriver", self._setup_remote_webdriver),
            ("direct_chrome", self._setup_direct_chrome)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                self.logger.info(f"🎯 Tentando estratégia: {strategy_name}")
                
                if strategy_func(browser_info):
                    self.logger.info(f"✅ Sucesso com estratégia: {strategy_name}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Estratégia {strategy_name} retornou False")
                    
            except Exception as e:
                self.logger.error(f"❌ Estratégia {strategy_name} falhou: {str(e)}")
                # Continuar com próxima estratégia
                continue
        
        # Se todas as estratégias falharam - FALHA CLARA sem fallback local
        error_msg = (
            "❌ FALHA CRÍTICA: Não foi possível conectar ao AdsPower!\n"
            "🔍 VERIFICAÇÕES NECESSÁRIAS:\n"
            "   1. AdsPower está aberto?\n"
            "   2. API local está habilitada?\n"
            "   3. Perfil foi iniciado corretamente?\n"
            "   4. Porta de debug está disponível?\n"
            "💡 Este sistema REQUER AdsPower funcionando - não há fallback local!"
        )
        self.logger.error(error_msg)
        raise WebDriverException(error_msg)
    
    def _setup_remote_webdriver(self, browser_info: Dict) -> bool:
        """🌐 Estratégia 1: APENAS webdriver.Remote() - SEM Chrome local"""
        try:
            selenium_address = browser_info.get('selenium_address')
            if not selenium_address:
                error_msg = "❌ FALHA: selenium_address não disponível no AdsPower!"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info(f"🎯 Conectando via webdriver.Remote() EXCLUSIVAMENTE: {selenium_address}")
            
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # CORREÇÃO CRÍTICA: Usar APENAS webdriver.Remote() 
            self.driver = webdriver.Remote(
                command_executor=selenium_address,
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            # Aplicar stealth
            stealth(self.driver,
                   languages=["pt-BR", "pt"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True)
            
            # Teste básico
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            self.logger.info("✅ webdriver.Remote() conectado com sucesso ao AdsPower!")
            return True
            
        except Exception as e:
            error_msg = f"❌ FALHA CRÍTICA: webdriver.Remote() não conseguiu conectar ao AdsPower: {str(e)}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    def _setup_direct_chrome(self, browser_info: Dict) -> bool:
        """🔧 Estratégia 2: APENAS webdriver.Remote() com debug port - SEM Chrome local"""
        try:
            debug_port = browser_info.get('debug_port')
            if not debug_port:
                error_msg = "❌ FALHA: debug_port não disponível no AdsPower!"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Construir URL do Remote WebDriver
            remote_url = f"http://localhost:{debug_port}/webdriver"
            self.logger.info(f"🎯 Conectando via webdriver.Remote() com debug port: {remote_url}")
            
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # CORREÇÃO CRÍTICA: Usar APENAS webdriver.Remote() 
            self.driver = webdriver.Remote(
                command_executor=remote_url,
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            # Teste básico
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            self.logger.info("✅ webdriver.Remote() com debug port conectado com sucesso ao AdsPower!")
            return True
            
        except Exception as e:
            error_msg = f"❌ FALHA CRÍTICA: webdriver.Remote() com debug port não conseguiu conectar ao AdsPower: {str(e)}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    # MÉTODO REMOVIDO: _setup_fallback_chrome
    # CORREÇÃO CRÍTICA: Eliminado fallback que criava Chrome local
    # Sistema agora requer 100% AdsPower ou falha claramente
    
    def safe_navigate(self, url: str) -> bool:
        """🧭 Navegação segura com retry robusto"""
        if self.enable_advanced_retry and self.navigation_retry_manager:
            try:
                return self.navigation_retry_manager.execute_with_retry(self._navigate_internal, url)
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL na navegação após retry: {str(e)}")
                return False
        else:
            return self._navigate_internal(url)
    
    def _navigate_internal(self, url: str) -> bool:
        """🧭 Método interno de navegação"""
        if not self.driver:
            raise WebDriverException("Driver não inicializado")
        
        self.logger.info(f"🧭 Navegando para: {url}")
        self.driver.get(url)
        
        # Aguardar carregamento
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        self.logger.info("✅ Navegação concluída com sucesso")
        return True
    
    def safe_find_element(self, selector: str, timeout: int = None) -> Optional[object]:
        """🔍 Busca segura de elemento com retry robusto"""
        if timeout is None:
            timeout = self.default_timeout
        
        if self.enable_advanced_retry and self.navigation_retry_manager:
            try:
                return self.navigation_retry_manager.execute_with_retry(
                    self._find_element_internal, selector, timeout
                )
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL na busca de elemento após retry: {str(e)}")
                return None
        else:
            return self._find_element_internal(selector, timeout)
    
    def _find_element_internal(self, selector: str, timeout: int):
        """🔍 Método interno de busca de elemento"""
        if not self.driver:
            raise WebDriverException("Driver não inicializado")
        
        wait = WebDriverWait(self.driver, timeout)
        
        # Tentar diferentes estratégias de busca
        strategies = [
            (By.XPATH, selector),
            (By.CSS_SELECTOR, selector),
            (By.ID, selector),
            (By.CLASS_NAME, selector)
        ]
        
        for by_method, value in strategies:
            try:
                element = wait.until(EC.presence_of_element_located((by_method, value)))
                self.logger.debug(f"✅ Elemento encontrado com {by_method.upper()}: {value}")
                return element
            except TimeoutException:
                continue
        
        raise NoSuchElementException(f"Elemento não encontrado: {selector}")
    
    def safe_click(self, element_or_selector, timeout: int = None) -> bool:
        """👆 Click seguro com retry robusto"""
        if self.enable_advanced_retry and self.navigation_retry_manager:
            try:
                return self.navigation_retry_manager.execute_with_retry(
                    self._click_internal, element_or_selector, timeout
                )
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL no click após retry: {str(e)}")
                return False
        else:
            return self._click_internal(element_or_selector, timeout)
    
    def _click_internal(self, element_or_selector, timeout: int = None) -> bool:
        """👆 Método interno de click"""
        if timeout is None:
            timeout = self.default_timeout
        
        # Se é um seletor string, encontrar o elemento primeiro
        if isinstance(element_or_selector, str):
            element = self._find_element_internal(element_or_selector, timeout)
        else:
            element = element_or_selector
        
        if not element:
            raise NoSuchElementException("Elemento para click não encontrado")
        
        # Aguardar elemento ser clicável
        wait = WebDriverWait(self.driver, timeout)
        clickable_element = wait.until(EC.element_to_be_clickable(element))
        
        # Scroll para o elemento se necessário
        self.driver.execute_script("arguments[0].scrollIntoView(true);", clickable_element)
        time.sleep(0.5)
        
        # Tentar click
        clickable_element.click()
        time.sleep(1)
        
        self.logger.debug("✅ Click executado com sucesso")
        return True
    
    def cleanup(self):
        """🧹 Limpeza de recursos"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.info("🧹 WebDriver encerrado")
            
            if self.adspower_manager:
                self.adspower_manager.cleanup()
            
            if self.enable_advanced_retry:
                if self.webdriver_retry_manager:
                    self.webdriver_retry_manager.cleanup()
                if self.navigation_retry_manager:
                    self.navigation_retry_manager.cleanup()
                self.logger.info("🧹 Recursos de retry limpos")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {str(e)}")
    
    def _log_automation_initialization(self) -> None:
        """🔍 LOG DETALHADO de inicialização do GoogleAdsAutomation"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*80)
        self.logger.info(f"🚀 INICIALIZANDO GoogleAdsAutomation - {timestamp}")
        self.logger.info(f"📋 Logger configurado: {self.logger.name}")
        self.logger.info(f"⏱️ Timeout padrão: {self.default_timeout}s")
        self.logger.info(f"⏳ Delay padrão: {self.default_delay}s")
        self.logger.info(f"🔄 Max retries: {self.max_retries}")
        self.logger.info(f"⏲️ Retry delay: {self.retry_delay}s")
        self.logger.info(f"🌐 Idioma atual: {self.current_language}")
        self.logger.info(f"🎛️ AdsPowerManager inicializado: {type(self.adspower_manager).__name__}")
        self.logger.info(f"🖥️ WebDriver: {self.driver} (None no início)")
        self.logger.info(f"⏰ WebDriverWait: {self.wait} (None no início)")
        self.logger.info(f"📊 Total de seletores multilíngues carregados: {len(self.multilingual_selectors)}")
        
        # Log dos seletores principais
        for key, selectors in list(self.multilingual_selectors.items())[:3]:  # Primeiros 3 para não sobrecarregar
            self.logger.info(f"   📋 Seletor '{key}': {len(selectors)} idiomas configurados")
        
        self.logger.info("="*80)
    
    def _log_step_start(self, step_name: str, step_number: int = None, details: Dict = None) -> str:
        """🚀 LOG PADRONIZADO de início de etapa com timestamp"""
        timestamp = datetime.now().isoformat()
        step_id = f"STEP_{step_number}" if step_number else "STEP"
        
        self.logger.info("="*60)
        self.logger.info(f"🚀 [{step_id}] INICIANDO: {step_name} - {timestamp}")
        
        if details:
            self.logger.info(f"📋 Detalhes da etapa:")
            for key, value in details.items():
                self.logger.info(f"   📌 {key}: {value}")
        
        return timestamp
    
    def _log_step_success(self, step_name: str, start_timestamp: str, details: Dict = None) -> None:
        """✅ LOG PADRONIZADO de sucesso de etapa"""
        end_timestamp = datetime.now().isoformat()
        start_time = datetime.fromisoformat(start_timestamp)
        end_time = datetime.fromisoformat(end_timestamp)
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(f"✅ SUCESSO: {step_name}")
        self.logger.info(f"⏱️ Duração: {duration:.3f}s")
        
        if details:
            self.logger.info(f"📋 Resultados:")
            for key, value in details.items():
                self.logger.info(f"   ✅ {key}: {value}")
        
        self.logger.info("="*60)
    
    def _log_step_failure(self, step_name: str, start_timestamp: str, error: Exception, details: Dict = None) -> None:
        """❌ LOG PADRONIZADO de falha de etapa"""
        end_timestamp = datetime.now().isoformat()
        start_time = datetime.fromisoformat(start_timestamp)
        end_time = datetime.fromisoformat(end_timestamp)
        duration = (end_time - start_time).total_seconds()
        
        self.logger.error(f"❌ FALHA: {step_name}")
        self.logger.error(f"⏱️ Duração até falha: {duration:.3f}s")
        self.logger.error(f"💥 Tipo do erro: {type(error).__name__}")
        self.logger.error(f"📝 Mensagem: {str(error)}")
        
        if details:
            self.logger.error(f"📋 Contexto da falha:")
            for key, value in details.items():
                self.logger.error(f"   ❌ {key}: {value}")
        
        self.logger.error(f"📚 Traceback completo:")
        self.logger.error(traceback.format_exc())
        self.logger.error("="*60)
    
    def _log_webdriver_state(self, context: str) -> Dict:
        """🔍 LOG DETALHADO do estado atual do WebDriver"""
        state = {
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'driver_available': self.driver is not None,
            'wait_available': self.wait is not None
        }
        
        self.logger.info(f"🔍 ESTADO DO WEBDRIVER ({context}):")
        self.logger.info(f"   📅 Timestamp: {state['timestamp']}")
        self.logger.info(f"   🚗 Driver disponível: {state['driver_available']}")
        self.logger.info(f"   ⏰ Wait disponível: {state['wait_available']}")
        
        if self.driver:
            try:
                # Coletar informações detalhadas do driver
                current_url = self.driver.current_url
                title = self.driver.title or "[Sem título]"
                window_handles = self.driver.window_handles
                window_size = self.driver.get_window_size()
                
                state.update({
                    'current_url': current_url,
                    'page_title': title,
                    'total_windows': len(window_handles),
                    'current_window': self.driver.current_window_handle,
                    'window_size': window_size
                })
                
                self.logger.info(f"   🌐 URL atual: {current_url}")
                self.logger.info(f"   📄 Título: {title}")
                self.logger.info(f"   🪟 Total de janelas: {len(window_handles)}")
                self.logger.info(f"   📐 Tamanho da janela: {window_size}")
                
                # Teste de funcionalidade JavaScript
                try:
                    js_test = self.driver.execute_script("return {ready: document.readyState, url: window.location.href, title: document.title};")
                    state['javascript_test'] = js_test
                    self.logger.info(f"   🧪 Teste JavaScript: {js_test}")
                except Exception as js_error:
                    state['javascript_error'] = str(js_error)
                    self.logger.warning(f"   ⚠️ Erro no teste JavaScript: {str(js_error)}")
                
            except Exception as driver_error:
                state['driver_error'] = str(driver_error)
                self.logger.error(f"   ❌ Erro ao acessar driver: {str(driver_error)}")
        
        return state
    
    def setup_driver(self, browser_info: Dict, headless: bool = False) -> bool:
        """🔧 CONFIGURAR DRIVER com logging EXTREMAMENTE detalhado para conexão WebDriver"""
        step_start = self._log_step_start("Setup WebDriver Driver", 1, {
            'headless_mode': headless,
            'browser_info_provided': browser_info is not None,
            'browser_info_keys': list(browser_info.keys()) if browser_info else None
        })
        
        try:
            # Estado inicial detalhado
            initial_state = self._log_webdriver_state("Before setup_driver")
            
            # VALIDAÇÃO CRÍTICA: Verificar informações do browser
            if not browser_info:
                self._log_step_failure("Setup WebDriver Driver", step_start, 
                                     ValueError("Informações do browser não fornecidas"), {
                    'browser_info': browser_info,
                    'expected_fields': ['debug_port', 'selenium_address', 'webdriver', 'ws']
                })
                return False
            
            self.logger.info(f"📋 ANÁLISE DETALHADA dos dados do AdsPower:")
            self.logger.info(f"   📊 Total de campos: {len(browser_info)}")
            for key, value in browser_info.items():
                self.logger.info(f"   📌 {key}: {value} (tipo: {type(value).__name__})")
            
            # PROCESSO CRÍTICO: Conectar ao AdsPower com retry
            connection_success = self._connect_to_adspower_with_retry(browser_info, max_retries=5)
            
            if connection_success:
                # Validação final detalhada
                final_state = self._log_webdriver_state("After successful setup_driver")
                
                self._log_step_success("Setup WebDriver Driver", step_start, {
                    'connection_method': 'AdsPower Remote',
                    'driver_type': type(self.driver).__name__ if self.driver else 'None',
                    'wait_configured': self.wait is not None,
                    'final_url': self.driver.current_url if self.driver else 'N/A'
                })
                return True
            else:
                self._log_step_failure("Setup WebDriver Driver", step_start,
                                     ConnectionError("Falha na conexão com AdsPower"), {
                    'retry_attempts': 5,
                    'browser_info_summary': {k: str(v)[:100] for k, v in browser_info.items()}
                })
                return False
            
        except Exception as e:
            self._log_step_failure("Setup WebDriver Driver", step_start, e, {
                'browser_info_keys': list(browser_info.keys()) if browser_info else None,
                'driver_state': self.driver is not None,
                'headless_requested': headless
            })
            return False
    
    def _connect_to_adspower_with_retry(self, browser_info: Dict, max_retries: int = 5) -> bool:
        """🔄 SISTEMA ROBUSTO DE RETRY com logging EXTREMAMENTE detalhado para cada tentativa"""
        
        step_start = self._log_step_start("Connect to AdsPower with Retry", 2, {
            'max_retries': max_retries,
            'available_methods': ['selenium_address', 'debug_port', 'chrome_service'],
            'browser_info_fields': list(browser_info.keys())
        })
        
        connection_attempts = []
        
        for attempt in range(max_retries):
            attempt_start = datetime.now().isoformat()
            self.logger.info(f"🔄 ===== TENTATIVA {attempt + 1}/{max_retries} =====")
            
            try:
                attempt_details = {
                    'attempt_number': attempt + 1,
                    'attempt_start': attempt_start,
                    'methods_tried': []
                }
                
                # MÉTODO 1: webdriver.Remote() com selenium_address (PRIORIDADE MÁXIMA)
                if 'selenium_address' in browser_info:
                    method_start = datetime.now().isoformat()
                    self.logger.info(f"🎯 MÉTODO 1: Tentando webdriver.Remote() com selenium_address...")
                    
                    method_success = self._try_webdriver_remote_selenium(browser_info)
                    method_duration = (datetime.now() - datetime.fromisoformat(method_start)).total_seconds()
                    
                    attempt_details['methods_tried'].append({
                        'method': 'webdriver_remote_selenium',
                        'success': method_success,
                        'duration': method_duration,
                        'selenium_address': browser_info.get('selenium_address')
                    })
                    
                    if method_success:
                        self.logger.info(f"✅ MÉTODO 1 SUCESSO - Executando validação robusta...")
                        validation_result = self._execute_comprehensive_validation()
                        if validation_result['all_validations_passed']:
                            self._log_step_success("Connect to AdsPower with Retry", step_start, {
                                'successful_method': 'webdriver_remote_selenium',
                                'attempt_number': attempt + 1,
                                'total_attempts': len(connection_attempts) + 1,
                                'validation_score': validation_result['total_score']
                            })
                            return True
                        else:
                            self.logger.warning(f"⚠️ MÉTODO 1 - Conexão falhou na validação robusta")
                            self._log_validation_failure(validation_result, 'webdriver_remote_selenium')
                
                # MÉTODO 2: webdriver.Remote() com porta debug
                debug_address = self._extract_debug_address(browser_info)
                if debug_address:
                    method_start = datetime.now().isoformat()
                    self.logger.info(f"🎯 MÉTODO 2: Tentando webdriver.Remote() com debug port...")
                    
                    method_success = self._try_webdriver_remote_debug(debug_address, browser_info)
                    method_duration = (datetime.now() - datetime.fromisoformat(method_start)).total_seconds()
                    
                    attempt_details['methods_tried'].append({
                        'method': 'webdriver_remote_debug',
                        'success': method_success,
                        'duration': method_duration,
                        'debug_address': debug_address
                    })
                    
                    if method_success:
                        self.logger.info(f"✅ MÉTODO 2 SUCESSO - Executando validação robusta...")
                        validation_result = self._execute_comprehensive_validation()
                        if validation_result['all_validations_passed']:
                            self._log_step_success("Connect to AdsPower with Retry", step_start, {
                                'successful_method': 'webdriver_remote_debug',
                                'attempt_number': attempt + 1,
                                'debug_address': debug_address,
                                'validation_score': validation_result['total_score']
                            })
                            return True
                        else:
                            self.logger.warning(f"⚠️ MÉTODO 2 - Conexão falhou na validação robusta")
                            self._log_validation_failure(validation_result, 'webdriver_remote_debug')
                
                # MÉTODO 3 REMOVIDO: Chrome Service com debuggerAddress (CRIAVA CHROME LOCAL)
                # CORREÇÃO CRÍTICA: Eliminado método que usava webdriver.Chrome() local
                self.logger.error("🚫 MÉTODO 3 REMOVIDO: Chrome Service criaria Chrome local - PROIBIDO!")
                self.logger.error("💡 Sistema requer 100% webdriver.Remote() com AdsPower funcionando")
                
                # Se chegou aqui, tentativa falhou
                attempt_end = datetime.now().isoformat()
                attempt_duration = (datetime.fromisoformat(attempt_end) - datetime.fromisoformat(attempt_start)).total_seconds()
                
                attempt_details.update({
                    'attempt_end': attempt_end,
                    'attempt_duration': attempt_duration,
                    'success': False
                })
                
                connection_attempts.append(attempt_details)
                
                self.logger.warning(f"⚠️ TENTATIVA {attempt + 1} FALHOU - Todos os métodos falharam")
                self.logger.warning(f"📊 Métodos tentados: {len(attempt_details['methods_tried'])}")
                
                if attempt < max_retries - 1:
                    delay = 2 * (attempt + 1)
                    self.logger.warning(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
                    
            except Exception as e:
                attempt_end = datetime.now().isoformat()
                attempt_duration = (datetime.fromisoformat(attempt_end) - datetime.fromisoformat(attempt_start)).total_seconds()
                
                attempt_details.update({
                    'attempt_end': attempt_end,
                    'attempt_duration': attempt_duration,
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                
                connection_attempts.append(attempt_details)
                
                self.logger.error(f"❌ ERRO CRÍTICO na tentativa {attempt + 1}:")
                self.logger.error(f"   💥 Tipo: {type(e).__name__}")
                self.logger.error(f"   📝 Mensagem: {str(e)}")
                
                if attempt < max_retries - 1:
                    delay = 2 * (attempt + 1)
                    self.logger.error(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                    time.sleep(delay)
        
        # RESUMO FINAL DAS TENTATIVAS
        self.logger.error("💥 RESUMO FINAL - TODAS AS TENTATIVAS FALHARAM:")
        for i, attempt in enumerate(connection_attempts):
            self.logger.error(f"   📋 Tentativa {i+1}: {len(attempt.get('methods_tried', []))} métodos, duração: {attempt.get('attempt_duration', 0):.3f}s")
        
        self._log_step_failure("Connect to AdsPower with Retry", step_start,
                             ConnectionError("Todas as tentativas de conexão falharam"), {
            'total_attempts': len(connection_attempts),
            'methods_available': ['selenium_address' in browser_info, debug_address is not None],
            'final_debug_address': debug_address
        })
        
        return False
    
    def _extract_debug_address(self, browser_info: Dict) -> Optional[str]:
        """🔍 EXTRAIR endereço de debug do AdsPower de forma ROBUSTA"""
        
        # Método 1: debugger_address já processado
        if 'debugger_address' in browser_info:
            address = browser_info['debugger_address']
            self.logger.info(f"✅ Debug address pré-processado: {address}")
            return address
        
        # Método 2: construir de debug_port + debug_host
        if 'debug_port' in browser_info:
            host = browser_info.get('debug_host', '127.0.0.1')
            port = browser_info['debug_port']
            address = f"{host}:{port}"
            self.logger.info(f"✅ Debug address construído: {address}")
            return address
        
        # Método 3: extrair de WebSocket URL
        if 'ws' in browser_info and isinstance(browser_info['ws'], str):
            ws_url = browser_info['ws']
            import re
            match = re.search(r'ws://([^:/]+):(\d+)', ws_url)
            if match:
                host, port = match.groups()
                address = f"{host}:{port}"
                self.logger.info(f"✅ Debug address extraído da WebSocket: {address}")
                return address
        
        # Método 4: testar portas comuns
        self.logger.warning("⚠️ Testando portas comuns do Chrome...")
        import requests
        for port in [9222, 9223, 9224, 9225]:
            try:
                response = requests.get(f"http://127.0.0.1:{port}/json", timeout=2)
                if response.status_code == 200:
                    address = f"127.0.0.1:{port}"
                    self.logger.info(f"✅ Porta funcional encontrada: {address}")
                    return address
            except:
                continue
        
        self.logger.error("💥 FALHA: Não foi possível determinar debug address!")
        return None
    
    def _try_webdriver_remote_selenium(self, browser_info: Dict) -> bool:
        """🎯 MÉTODO 1: webdriver.Remote() com selenium_address do AdsPower"""
        try:
            selenium_address = browser_info['selenium_address']
            self.logger.info(f"🎯 Conectando via webdriver.Remote() ao: {selenium_address}")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Opções para Chrome (compatível com Selenium 4)
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Conectar ao AdsPower via Remote WebDriver
            self.driver = webdriver.Remote(
                command_executor=selenium_address,
                options=options
            )
            
            self.logger.info("✅ SUCESSO: webdriver.Remote() conectado ao AdsPower!")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ webdriver.Remote() selenium falhou: {str(e)}")
            return False
    
    def _try_webdriver_remote_debug(self, debug_address: str, browser_info: Dict) -> bool:
        """🎯 MÉTODO 2: webdriver.Remote() com porta de debug"""
        try:
            # Construir URL do Remote WebDriver com porta debug
            remote_url = f"http://{debug_address}/webdriver"
            self.logger.info(f"🎯 Tentando webdriver.Remote() via debug: {remote_url}")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Opções para Chrome (compatível com Selenium 4)
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Remote(
                command_executor=remote_url,
                options=options
            )
            
            self.logger.info("✅ SUCESSO: webdriver.Remote() via debug conectado!")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ webdriver.Remote() debug falhou: {str(e)}")
            return False
    
    # MÉTODO REMOVIDO: _try_chrome_service_debug
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    # Sistema agora exige 100% webdriver.Remote() com AdsPower ou falha claramente
    
    def _execute_comprehensive_validation(self) -> Dict:
        """🎯 ORQUESTRADOR DE VALIDAÇÃO ROBUSTA - Executa todas as validações em sequência
        
        Esta função coordena a execução de todas as validações robustas implementadas
        e gera um relatório consolidado com sistema de alertas claros.
        
        Returns:
            Dict: Relatório consolidado de todas as validações
        """
        step_start = self._log_step_start("Validação Robusta Consolidada", 100, {
            'validacoes_a_executar': ['validate_adspower_session', 'verify_session_active', 'test_browser_navigation'],
            'objetivo': 'Garantir controle absoluto do navegador AdsPower'
        })
        
        consolidated_report = {
            'all_validations_passed': False,
            'timestamp': datetime.now().isoformat(),
            'total_score': 0,
            'validations': {},
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'summary': ''
        }
        
        try:
            # Configurar WebDriverWait se ainda não existe
            if not self.wait and self.driver:
                self.wait = WebDriverWait(self.driver, self.default_timeout)
                self.logger.info(f"⏱️ WebDriverWait configurado: timeout {self.default_timeout}s")
            
            # VALIDAÇÃO 1: Sessão AdsPower (Teste completo de controle)
            self.logger.info("🎯 ===== EXECUTANDO VALIDAÇÃO 1: SESSÃO ADSPOWER =====")
            session_validation = self.validate_adspower_session()
            consolidated_report['validations']['session_validation'] = session_validation
            
            if session_validation['session_valid']:
                self.logger.info("✅ VALIDAÇÃO 1 APROVADA: Controle do navegador confirmado")
                consolidated_report['total_score'] += session_validation['overall_score']
            else:
                self.logger.error("❌ VALIDAÇÃO 1 REPROVADA: Problemas no controle do navegador")
                consolidated_report['critical_issues'].extend(session_validation['critical_failures'])
                consolidated_report['warnings'].extend(session_validation['warnings'])
            
            # VALIDAÇÃO 2: Verificação de Sessão Ativa (Responsividade)
            self.logger.info("🎯 ===== EXECUTANDO VALIDAÇÃO 2: SESSÃO ATIVA =====")
            active_validation = self.verify_session_active()
            consolidated_report['validations']['active_validation'] = active_validation
            
            if active_validation['session_active'] and active_validation['session_responsive']:
                self.logger.info("✅ VALIDAÇÃO 2 APROVADA: Sessão ativa e responsiva")
                consolidated_report['total_score'] += 30  # Pontos por responsividade
            else:
                self.logger.error("❌ VALIDAÇÃO 2 REPROVADA: Sessão inativa ou lenta")
                if not active_validation['session_active']:
                    consolidated_report['critical_issues'].append("Sessão WebDriver não está ativa")
                if not active_validation['session_responsive']:
                    consolidated_report['critical_issues'].append("Sessão WebDriver não está responsiva")
                consolidated_report['recommendations'].extend(active_validation['recommendations'])
            
            # VALIDAÇÃO 3: Teste Crítico de Navegação (Google.com)
            self.logger.info("🎯 ===== EXECUTANDO VALIDAÇÃO 3: TESTE DE NAVEGAÇÃO =====")
            navigation_validation = self.test_browser_navigation()
            consolidated_report['validations']['navigation_validation'] = navigation_validation
            
            if navigation_validation['navigation_successful']:
                self.logger.info("✅ VALIDAÇÃO 3 APROVADA: Navegação para Google.com bem-sucedida")
                consolidated_report['total_score'] += 20  # Pontos por navegação
            else:
                self.logger.error("❌ VALIDAÇÃO 3 REPROVADA: Falha na navegação para Google.com")
                consolidated_report['critical_issues'].append("Incapaz de navegar para sites externos")
                consolidated_report['warnings'].extend(navigation_validation['warnings'])
                for error in navigation_validation['errors']:
                    consolidated_report['critical_issues'].append(f"Navegação: {error}")
            
            # ANÁLISE FINAL CONSOLIDADA
            max_possible_score = 120  # 70 (sessão) + 30 (ativo) + 20 (navegação)
            score_percentage = (consolidated_report['total_score'] / max_possible_score) * 100
            
            # Critérios para aprovação geral:
            # 1. Score mínimo de 80%
            # 2. Máximo 1 issue crítico
            # 3. Validação de sessão deve ter passado
            critical_issues_count = len(consolidated_report['critical_issues'])
            session_passed = consolidated_report['validations']['session_validation']['session_valid']
            
            consolidated_report['all_validations_passed'] = (
                score_percentage >= 80 and 
                critical_issues_count <= 1 and 
                session_passed
            )
            
            # Gerar resumo personalizado
            if consolidated_report['all_validations_passed']:
                consolidated_report['summary'] = f"✅ CONTROLE VALIDADO COM SUCESSO - Score: {score_percentage:.1f}% ({consolidated_report['total_score']}/{max_possible_score})"
                consolidated_report['recommendations'].append("Sistema pronto para automação do Google Ads")
                
                self._log_step_success("Validação Robusta Consolidada", step_start, {
                    'score_final': f"{consolidated_report['total_score']}/{max_possible_score}",
                    'percentual': f"{score_percentage:.1f}%",
                    'validacoes_aprovadas': sum(1 for v in consolidated_report['validations'].values() 
                                             if v.get('session_valid') or v.get('session_active') or v.get('navigation_successful')),
                    'issues_criticos': critical_issues_count
                })
            else:
                reasons = []
                if score_percentage < 80:
                    reasons.append(f"Score baixo: {score_percentage:.1f}%")
                if critical_issues_count > 1:
                    reasons.append(f"{critical_issues_count} issues críticos")
                if not session_passed:
                    reasons.append("Controle de sessão falhou")
                
                consolidated_report['summary'] = f"❌ VALIDAÇÃO FALHOU - Motivos: {', '.join(reasons)}"
                consolidated_report['recommendations'].append("Reiniciar conexão com AdsPower necessário")
                
                self._log_step_failure("Validação Robusta Consolidada", step_start,
                                     RuntimeError(consolidated_report['summary']), {
                    'score_obtido': f"{consolidated_report['total_score']}/{max_possible_score}",
                    'percentual': f"{score_percentage:.1f}%",
                    'issues_criticos': consolidated_report['critical_issues'],
                    'recomendacoes': consolidated_report['recommendations']
                })
            
            return consolidated_report
            
        except Exception as e:
            consolidated_report['critical_issues'].append(f"Erro crítico na validação consolidada: {str(e)}")
            consolidated_report['summary'] = f"💥 FALHA CRÍTICA NA VALIDAÇÃO: {str(e)}"
            self._log_step_failure("Validação Robusta Consolidada", step_start, e, consolidated_report)
            return consolidated_report
    
    def _log_validation_failure(self, validation_result: Dict, connection_method: str) -> None:
        """🚨 SISTEMA DE ALERTAS CLAROS para falhas de validação
        
        Gera alertas detalhados e específicos sobre exatamente qual aspecto
        do controle do navegador não está funcionando.
        
        Args:
            validation_result: Resultado da validação consolidada
            connection_method: Método de conexão que foi usado
        """
        self.logger.error("🚨" + "="*80)
        self.logger.error(f"🚨 ALERTA DE VALIDAÇÃO: FALHA NO CONTROLE DO NAVEGADOR")
        self.logger.error(f"🚨 Método de Conexão: {connection_method}")
        self.logger.error(f"🚨 Timestamp: {datetime.now().isoformat()}")
        self.logger.error("🚨" + "="*80)
        
        # RESUMO GERAL
        self.logger.error(f"💥 RESUMO: {validation_result.get('summary', 'Falha na validação')}")
        self.logger.error(f"📊 Score Final: {validation_result.get('total_score', 0)}/120 pontos")
        
        # ISSUES CRÍTICOS ESPECÍFICOS
        critical_issues = validation_result.get('critical_issues', [])
        if critical_issues:
            self.logger.error(f"🔥 PROBLEMAS CRÍTICOS DETECTADOS ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues, 1):
                self.logger.error(f"   🔥 {i}. {issue}")
        
        # ANÁLISE DETALHADA POR VALIDAÇÃO
        validations = validation_result.get('validations', {})
        
        # Análise da Validação de Sessão
        if 'session_validation' in validations:
            session = validations['session_validation']
            if not session.get('session_valid', False):
                self.logger.error(f"❌ CONTROLE DE SESSÃO COMPROMETIDO:")
                
                tests = session.get('tests_performed', {})
                for test_name, test_result in tests.items():
                    if test_result.get('status') == 'FALHA':
                        self.logger.error(f"   ❌ {test_name.upper()}: {test_result.get('error', 'Falha desconhecida')}")
                    elif test_result.get('score', 0) == 0:
                        self.logger.error(f"   ⚠️ {test_name.upper()}: Não funcionou adequadamente")
        
        # Análise da Validação de Sessão Ativa
        if 'active_validation' in validations:
            active = validations['active_validation']
            if not active.get('session_active', False):
                self.logger.error(f"❌ SESSÃO INATIVA DETECTADA:")
                health_checks = active.get('health_checks', {})
                for check_name, check_result in health_checks.items():
                    if not check_result:
                        self.logger.error(f"   ❌ {check_name.upper()}: Falhou")
            
            if not active.get('session_responsive', False):
                self.logger.error(f"❌ SESSÃO LENTA/NÃO RESPONSIVA:")
                response_times = active.get('response_times', {})
                for command, time_taken in response_times.items():
                    if time_taken > 3.0:
                        self.logger.error(f"   🐌 {command.upper()}: {time_taken:.3f}s (muito lento)")
        
        # Análise da Validação de Navegação
        if 'navigation_validation' in validations:
            nav = validations['navigation_validation']
            if not nav.get('navigation_successful', False):
                self.logger.error(f"❌ NAVEGAÇÃO PARA GOOGLE.COM FALHOU:")
                
                errors = nav.get('errors', [])
                for error in errors:
                    self.logger.error(f"   ❌ ERRO DE NAVEGAÇÃO: {error}")
                
                steps = nav.get('steps_performed', [])
                for step in steps:
                    if step.get('status') == 'falha':
                        self.logger.error(f"   ❌ ETAPA '{step.get('step', 'desconhecida')}' FALHOU: {step.get('error', 'Erro desconhecido')}")
        
        # RECOMENDAÇÕES DE RESOLUÇÃO
        recommendations = validation_result.get('recommendations', [])
        if recommendations:
            self.logger.error(f"💡 RECOMENDAÇÕES PARA RESOLUÇÃO ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                self.logger.error(f"   💡 {i}. {rec}")
        
        # AÇÕES SUGERIDAS
        self.logger.error(f"🛠️ AÇÕES SUGERIDAS:")
        self.logger.error(f"   🛠️ 1. Verificar se AdsPower está executando corretamente")
        self.logger.error(f"   🛠️ 2. Reiniciar o perfil do AdsPower")
        self.logger.error(f"   🛠️ 3. Verificar conectividade de rede")
        self.logger.error(f"   🛠️ 4. Reiniciar a aplicação de automação")
        self.logger.error(f"   🛠️ 5. Verificar logs detalhados acima para problemas específicos")
        
        self.logger.error("🚨" + "="*80)
        self.logger.error(f"🚨 FIM DO ALERTA DE VALIDAÇÃO")
        self.logger.error("🚨" + "="*80)
    
    def _validate_adspower_connection(self, browser_info: Dict) -> bool:
        """🧪 VALIDAÇÃO EXPLÍCITA DE SESSÃO com logs detalhados - MÉTODO LEGADO
        
        Esta função está mantida para compatibilidade, mas o novo sistema
        usa _execute_comprehensive_validation() que é muito mais robusto.
        """
        if not self.driver:
            self.logger.error("💥 ERRO: Driver está None após conexão!")
            return False
        
        try:
            # Configurar WebDriverWait
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            self.logger.info(f"⏱️ WebDriverWait configurado: timeout {self.default_timeout}s")
            
            # TESTE 1: URL atual
            current_url = self.driver.current_url
            self.logger.info(f"🔍 VALIDAÇÃO 1 - URL atual: {current_url}")
            
            # TESTE 2: Título da página
            title = self.driver.title or "[Sem título]"
            self.logger.info(f"🔍 VALIDAÇÃO 2 - Título: {title}")
            
            # TESTE 3: Window handles (abas)
            windows = self.driver.window_handles
            self.logger.info(f"🔍 VALIDAÇÃO 3 - Abas: {len(windows)} aba(s) detectada(s)")
            
            # TESTE 4: Executar JavaScript básico
            js_result = self.driver.execute_script("return 'ADSPOWER_CONNECTION_OK';")
            if js_result == 'ADSPOWER_CONNECTION_OK':
                self.logger.info("🔍 VALIDAÇÃO 4 - JavaScript: ✅ FUNCIONAL")
            else:
                self.logger.warning(f"🔍 VALIDAÇÃO 4 - JavaScript: ⚠️ Resultado: {js_result}")
            
            # TESTE 5: Verificar se é realmente o AdsPower (não Chrome novo)
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            self.logger.info(f"🔍 VALIDAÇÃO 5 - User Agent: {user_agent[:100]}...")
            
            # TESTE 6: Testar capacidade de controle básico
            window_size = self.driver.get_window_size()
            self.logger.info(f"🔍 VALIDAÇÃO 6 - Tamanho janela: {window_size}")
            
            # RESUMO DE VALIDAÇÃO
            validation_summary = {
                'url': current_url,
                'title': title,
                'tabs_count': len(windows),
                'javascript_ok': js_result == 'ADSPOWER_CONNECTION_OK',
                'window_size': window_size
            }
            
            self.logger.info(f"✅ VALIDAÇÃO COMPLETA - AdsPower conectado com SUCESSO!")
            self.logger.info(f"📊 Resumo da sessão: {validation_summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"💥 FALHA na validação da conexão: {str(e)}")
            return False
    
    def prepare_browser_for_navigation(self) -> bool:
        """🛠️ Preparar browser CALCULADAMENTE para navegação eficaz"""
        try:
            self.logger.info("🛠️ PREPARANDO browser com controle EXTREMAMENTE CALCULADO...")
            
            if not self.driver:
                self.logger.error("❌ Driver não está disponível")
                return False
            
            # ETAPA 1: Verificar estado atual do browser
            self.logger.info("📊 ETAPA 1: Verificando estado atual do browser...")
            
            try:
                current_url = self.driver.current_url
                title = self.driver.title or "Sem título"
                windows = self.driver.window_handles
                
                self.logger.info(f"📍 URL atual: {current_url}")
                self.logger.info(f"📄 Título atual: {title}")
                self.logger.info(f"🪟 Número de abas: {len(windows)}")
                
            except Exception as state_error:
                self.logger.error(f"❌ Erro ao verificar estado: {str(state_error)}")
                return False
            
            # ETAPA 2: Abrir nova aba se necessário (estratégia mais segura)
            self.logger.info("🆕 ETAPA 2: Abrindo nova aba para navegação limpa...")
            
            try:
                # Abrir nova aba usando JavaScript (mais confiável)
                self.driver.execute_script("window.open('about:blank', '_blank');")
                time.sleep(2)  # Aguardar aba abrir
                
                # Mudar para a nova aba
                new_windows = self.driver.window_handles
                if len(new_windows) > len(windows):
                    self.driver.switch_to.window(new_windows[-1])  # Última aba (nova)
                    self.logger.info("✅ Nova aba criada e ativada com sucesso")
                else:
                    self.logger.warning("⚠️ Nova aba não detectada, usando aba atual")
                
            except Exception as tab_error:
                self.logger.warning(f"⚠️ Erro ao criar nova aba: {str(tab_error)}")
                self.logger.info("🔄 Continuando com aba atual...")
            
            # ETAPA 3: Verificar controle da aba ativa
            self.logger.info("🎯 ETAPA 3: Verificando controle da aba ativa...")
            
            try:
                # Executar teste simples de JavaScript
                test_result = self.driver.execute_script("return document.readyState;")
                self.logger.info(f"✅ Estado do documento: {test_result}")
                
                # Verificar se consegue acessar elementos básicos
                body_present = self.driver.execute_script("return document.body !== null;")
                self.logger.info(f"✅ Body presente: {body_present}")
                
            except Exception as control_error:
                self.logger.error(f"❌ Falha no controle da aba: {str(control_error)}")
                return False
            
            # ETAPA 4: Preparar para navegação via barra de endereço
            self.logger.info("🔗 ETAPA 4: Preparando navegação direta...")
            
            try:
                # Focar na janela para garantir que está ativa
                self.driver.switch_to.window(self.driver.current_window_handle)
                
                # Aguardar um pouco para estabilizar
                time.sleep(1)
                
                self.logger.info("✅ Browser preparado para navegação calculada")
                
            except Exception as prep_error:
                self.logger.error(f"❌ Erro na preparação final: {str(prep_error)}")
                return False
            
            self.logger.info("🎉 Browser TOTALMENTE PREPARADO para navegação eficaz!")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na preparação do browser: {str(e)}")
            return False
    
    def navigate_with_extreme_calculation(self, target_url: str) -> bool:
        """🧮 Navegação EXTREMAMENTE CALCULADA e EFICAZ"""
        try:
            self.logger.info(f"🧮 INICIANDO navegação EXTREMAMENTE CALCULADA para: {target_url}")
            
            if not self.driver:
                self.logger.error("❌ Driver não disponível")
                return False
            
            # MÉTODO 1: Navegação direta (mais rápida)
            self.logger.info("🚀 MÉTODO 1: Tentativa de navegação direta...")
            try:
                self.driver.get(target_url)
                time.sleep(3)  # Aguardar carregamento
                
                # Verificar se deu certo
                final_url = self.driver.current_url
                if target_url.replace("https://", "").replace("http://", "") in final_url:
                    self.logger.info("✅ MÉTODO 1 SUCESSO: Navegação direta funcionou")
                    return True
                else:
                    self.logger.warning(f"⚠️ MÉTODO 1 FALHOU: URL esperada não alcançada. Final: {final_url}")
            
            except Exception as method1_error:
                self.logger.warning(f"⚠️ MÉTODO 1 ERRO: {str(method1_error)}")
            
            # MÉTODO 2: Navegação via JavaScript (alternativa)
            self.logger.info("🔧 MÉTODO 2: Tentativa via JavaScript...")
            try:
                js_code = f"window.location.href = '{target_url}';"
                self.driver.execute_script(js_code)
                time.sleep(4)  # Aguardar mais tempo para JS
                
                # Verificar se deu certo
                final_url = self.driver.current_url
                if target_url.replace("https://", "").replace("http://", "") in final_url:
                    self.logger.info("✅ MÉTODO 2 SUCESSO: Navegação via JavaScript funcionou")
                    return True
                else:
                    self.logger.warning(f"⚠️ MÉTODO 2 FALHOU: URL esperada não alcançada. Final: {final_url}")
            
            except Exception as method2_error:
                self.logger.warning(f"⚠️ MÉTODO 2 ERRO: {str(method2_error)}")
            
            # MÉTODO 3: Simular interação com barra de endereço (mais manual)
            self.logger.info("⌨️ MÉTODO 3: Simulando interação manual com barra de endereço...")
            try:
                # Tentar usar Ctrl+L para focar na barra de endereço
                from selenium.webdriver.common.action_chains import ActionChains
                from selenium.webdriver.common.keys import Keys
                
                actions = ActionChains(self.driver)
                actions.key_down(Keys.CONTROL).send_keys('l').key_up(Keys.CONTROL).perform()
                time.sleep(1)
                
                # Digitar URL
                actions = ActionChains(self.driver)
                actions.send_keys(target_url).send_keys(Keys.RETURN).perform()
                time.sleep(5)  # Aguardar navegação
                
                # Verificar se deu certo
                final_url = self.driver.current_url
                if target_url.replace("https://", "").replace("http://", "") in final_url:
                    self.logger.info("✅ MÉTODO 3 SUCESSO: Simulação manual funcionou")
                    return True
                else:
                    self.logger.warning(f"⚠️ MÉTODO 3 FALHOU: URL esperada não alcançada. Final: {final_url}")
            
            except Exception as method3_error:
                self.logger.warning(f"⚠️ MÉTODO 3 ERRO: {str(method3_error)}")
            
            # Se chegou aqui, todos os métodos falharam
            self.logger.error("💥 FALHA TOTAL: Todos os 3 métodos de navegação falharam")
            return False
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na navegação calculada: {str(e)}")
            return False
    
    def navigate_to_google_ads(self) -> bool:
        """🌐 CORREÇÃO 3: Navegação SIMPLIFICADA e DIRETA"""
        try:
            self.logger.info("🌐 INICIANDO navegação SIMPLIFICADA para Google Ads...")
            
            if not self.driver:
                self.logger.error("❌ Driver não está inicializado!")
                return False
            
            # Lista simples de URLs para tentar
            target_urls = [
                "https://ads.google.com/aw/",
                "https://ads.google.com/home/",
                "https://ads.google.com/",
                "https://ads.google.com/aw/campaigns/"
            ]
            
            for i, url in enumerate(target_urls, 1):
                try:
                    self.logger.info(f"🎯 TENTATIVA {i}: Navegando para {url}")
                    
                    # Navegação direta com driver.get()
                    self.driver.get(url)
                    
                    # Aguardar carregamento
                    time.sleep(4)
                    
                    # Verificação clara de sucesso
                    current_url = self.driver.current_url
                    title = self.driver.title or ""
                    
                    self.logger.info(f"📍 URL atual: {current_url}")
                    self.logger.info(f"📄 Título: {title}")
                    
                    # Verificação simples se chegou ao Google Ads
                    if "ads.google.com" in current_url.lower():
                        # Verificar se não é página de login
                        page_source = self.driver.page_source.lower()
                        if not any(login_term in page_source for login_term in ["sign in", "entrar", "login"]):
                            self.logger.info(f"✅ SUCESSO: Chegou ao Google Ads na tentativa {i}")
                            self.take_screenshot("google_ads_sucesso.png")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Página de login detectada - tentativa {i}")
                    else:
                        self.logger.warning(f"⚠️ URL incorreta na tentativa {i}: {current_url}")
                        
                except Exception as nav_error:
                    self.logger.error(f"❌ Erro na tentativa {i}: {str(nav_error)}")
                    continue
            
            # 🔧 CORREÇÃO 4: Navegação com tratamento adequado de erros
            self.logger.error("💥 FALHA CRÍTICA: Todas as tentativas de navegação falharam")
            self.logger.error("🔧 POSSÍVEIS CAUSAS:")
            self.logger.error("   1. Usuário não está logado no Google Ads")
            self.logger.error("   2. Conta Google Ads não tem permissões adequadas")
            self.logger.error("   3. Conexão com internet instável")
            self.logger.error("   4. Google Ads detectou automação e bloqueou")
            self.take_screenshot("navegacao_falha_total.png")
            return False
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na navegação: {str(e)}")
            self.logger.error("🔧 Verifique logs detalhados acima")
            return False
    
    def validate_adspower_session(self) -> Dict:
        """🔍 VALIDAÇÃO EXPLÍCITA E ROBUSTA DE CONTROLE DO NAVEGADOR AdsPower
        
        Esta função realiza uma bateria completa de testes para confirmar com certeza absoluta
        que o Selenium está realmente controlando o AdsPower corretamente.
        
        Returns:
            Dict: Relatório completo de validação com status detalhado de cada teste
        """
        step_start = self._log_step_start("Validação Explícita da Sessão AdsPower", 1, {
            'objetivo': 'Confirmar controle absoluto do navegador',
            'testes_a_executar': ['current_url', 'window_handles', 'title', 'javascript', 'user_agent', 'dimensoes_janela']
        })
        
        validation_report = {
            'session_valid': False,
            'timestamp': datetime.now().isoformat(),
            'driver_available': False,
            'tests_performed': {},
            'critical_failures': [],
            'warnings': [],
            'overall_score': 0,
            'recommendation': ''
        }
        
        try:
            # VALIDAÇÃO PRÉVIA: Driver disponível
            if not self.driver:
                validation_report['critical_failures'].append("Driver não está inicializado")
                self._log_step_failure("Validação Explícita da Sessão AdsPower", step_start,
                                     RuntimeError("Driver não disponível"), validation_report)
                return validation_report
            
            validation_report['driver_available'] = True
            self.logger.info("✅ PRÉ-VALIDAÇÃO: Driver está disponível")
            
            # TESTE 1: Verificação de URL atual (conectividade básica)
            test_start = datetime.now().isoformat()
            try:
                current_url = self.driver.current_url
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['current_url'] = {
                    'status': 'SUCESSO',
                    'value': current_url,
                    'duration': test_duration,
                    'score': 20
                }
                
                self.logger.info(f"✅ TESTE 1 SUCESSO - URL atual: {current_url} (duração: {test_duration:.3f}s)")
                
                # Análise da URL
                if current_url and current_url != "data:,":
                    self.logger.info("   📊 URL válida detectada - conexão funcional")
                else:
                    validation_report['warnings'].append("URL vazia ou inválida detectada")
                    self.logger.warning("   ⚠️ URL vazia ou inválida - possível problema de carregamento")
                    
            except Exception as url_error:
                validation_report['tests_performed']['current_url'] = {
                    'status': 'FALHA',
                    'error': str(url_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste URL falhou: {str(url_error)}")
                self.logger.error(f"❌ TESTE 1 FALHA - URL atual: {str(url_error)}")
            
            # TESTE 2: Verificação de Window Handles (controle de abas)
            test_start = datetime.now().isoformat()
            try:
                window_handles = self.driver.window_handles
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['window_handles'] = {
                    'status': 'SUCESSO',
                    'count': len(window_handles),
                    'handles': window_handles,
                    'current_handle': self.driver.current_window_handle,
                    'duration': test_duration,
                    'score': 15
                }
                
                self.logger.info(f"✅ TESTE 2 SUCESSO - Window Handles: {len(window_handles)} aba(s) (duração: {test_duration:.3f}s)")
                self.logger.info(f"   📋 Handles disponíveis: {window_handles[:3]}{'...' if len(window_handles) > 3 else ''}")
                self.logger.info(f"   🎯 Handle atual: {self.driver.current_window_handle}")
                
                if len(window_handles) == 0:
                    validation_report['critical_failures'].append("Nenhuma aba disponível")
                    self.logger.error("   ❌ CRÍTICO: Nenhuma aba disponível")
                    
            except Exception as handles_error:
                validation_report['tests_performed']['window_handles'] = {
                    'status': 'FALHA',
                    'error': str(handles_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste Window Handles falhou: {str(handles_error)}")
                self.logger.error(f"❌ TESTE 2 FALHA - Window Handles: {str(handles_error)}")
            
            # TESTE 3: Verificação de Título da Página
            test_start = datetime.now().isoformat()
            try:
                page_title = self.driver.title or "[Sem título]"
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['title'] = {
                    'status': 'SUCESSO',
                    'value': page_title,
                    'length': len(page_title),
                    'duration': test_duration,
                    'score': 10
                }
                
                self.logger.info(f"✅ TESTE 3 SUCESSO - Título: '{page_title}' (duração: {test_duration:.3f}s)")
                self.logger.info(f"   📏 Comprimento do título: {len(page_title)} caracteres")
                
                if not page_title or page_title == "[Sem título]":
                    validation_report['warnings'].append("Título da página vazio ou padrão")
                    self.logger.warning("   ⚠️ Título vazio - página pode não ter carregado completamente")
                    
            except Exception as title_error:
                validation_report['tests_performed']['title'] = {
                    'status': 'FALHA',
                    'error': str(title_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste Título falhou: {str(title_error)}")
                self.logger.error(f"❌ TESTE 3 FALHA - Título: {str(title_error)}")
            
            # TESTE 4: Execução de JavaScript (controle avançado)
            test_start = datetime.now().isoformat()
            try:
                # Teste básico de JavaScript
                js_basic = self.driver.execute_script("return 'ADSPOWER_VALIDATION_OK';")
                
                # Teste de propriedades do navegador
                js_properties = self.driver.execute_script("""
                    return {
                        ready_state: document.readyState,
                        location: window.location.href,
                        title: document.title,
                        has_body: document.body !== null,
                        timestamp: new Date().toISOString(),
                        screen_width: screen.width,
                        screen_height: screen.height,
                        inner_width: window.innerWidth,
                        inner_height: window.innerHeight
                    };
                """)
                
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['javascript'] = {
                    'status': 'SUCESSO',
                    'basic_test': js_basic,
                    'properties': js_properties,
                    'duration': test_duration,
                    'score': 25
                }
                
                self.logger.info(f"✅ TESTE 4 SUCESSO - JavaScript: '{js_basic}' (duração: {test_duration:.3f}s)")
                self.logger.info(f"   📊 Estado do documento: {js_properties.get('ready_state', 'N/A')}")
                self.logger.info(f"   🌐 Location via JS: {js_properties.get('location', 'N/A')}")
                self.logger.info(f"   📏 Dimensões da tela: {js_properties.get('screen_width', 'N/A')}x{js_properties.get('screen_height', 'N/A')}")
                self.logger.info(f"   🪟 Dimensões da janela: {js_properties.get('inner_width', 'N/A')}x{js_properties.get('inner_height', 'N/A')}")
                
                if js_basic != 'ADSPOWER_VALIDATION_OK':
                    validation_report['warnings'].append("JavaScript básico retornou valor inesperado")
                    self.logger.warning(f"   ⚠️ JavaScript básico inesperado: {js_basic}")
                    
            except Exception as js_error:
                validation_report['tests_performed']['javascript'] = {
                    'status': 'FALHA',
                    'error': str(js_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste JavaScript falhou: {str(js_error)}")
                self.logger.error(f"❌ TESTE 4 FALHA - JavaScript: {str(js_error)}")
            
            # TESTE 5: User Agent (identificação do navegador)
            test_start = datetime.now().isoformat()
            try:
                user_agent = self.driver.execute_script("return navigator.userAgent;")
                navigator_info = self.driver.execute_script("""
                    return {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        cookieEnabled: navigator.cookieEnabled,
                        onLine: navigator.onLine,
                        vendor: navigator.vendor || 'N/A'
                    };
                """)
                
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['user_agent'] = {
                    'status': 'SUCESSO',
                    'user_agent': user_agent,
                    'navigator_info': navigator_info,
                    'duration': test_duration,
                    'score': 15
                }
                
                self.logger.info(f"✅ TESTE 5 SUCESSO - User Agent (duração: {test_duration:.3f}s)")
                self.logger.info(f"   🌐 User Agent: {user_agent[:100]}{'...' if len(user_agent) > 100 else ''}")
                self.logger.info(f"   💻 Platform: {navigator_info.get('platform', 'N/A')}")
                self.logger.info(f"   🗣️ Language: {navigator_info.get('language', 'N/A')}")
                self.logger.info(f"   🍪 Cookies Enabled: {navigator_info.get('cookieEnabled', 'N/A')}")
                self.logger.info(f"   📡 Online: {navigator_info.get('onLine', 'N/A')}")
                
                # Verificação se é realmente Chrome
                if "chrome" not in user_agent.lower():
                    validation_report['warnings'].append("User Agent não indica Chrome")
                    self.logger.warning("   ⚠️ User Agent não parece ser Chrome")
                    
            except Exception as ua_error:
                validation_report['tests_performed']['user_agent'] = {
                    'status': 'FALHA',
                    'error': str(ua_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste User Agent falhou: {str(ua_error)}")
                self.logger.error(f"❌ TESTE 5 FALHA - User Agent: {str(ua_error)}")
            
            # TESTE 6: Dimensões da Janela (controle físico)
            test_start = datetime.now().isoformat()
            try:
                window_size = self.driver.get_window_size()
                window_position = self.driver.get_window_position()
                
                # Teste de alteração de tamanho para verificar controle
                original_size = window_size.copy()
                self.driver.set_window_size(800, 600)
                time.sleep(0.5)
                test_size = self.driver.get_window_size()
                self.driver.set_window_size(original_size['width'], original_size['height'])
                
                test_duration = (datetime.now() - datetime.fromisoformat(test_start)).total_seconds()
                
                validation_report['tests_performed']['window_dimensions'] = {
                    'status': 'SUCESSO',
                    'original_size': original_size,
                    'position': window_position,
                    'test_size': test_size,
                    'size_control_works': test_size['width'] == 800 and test_size['height'] == 600,
                    'duration': test_duration,
                    'score': 15
                }
                
                self.logger.info(f"✅ TESTE 6 SUCESSO - Dimensões da Janela (duração: {test_duration:.3f}s)")
                self.logger.info(f"   📐 Tamanho original: {original_size['width']}x{original_size['height']}")
                self.logger.info(f"   📍 Posição: x={window_position['x']}, y={window_position['y']}")
                self.logger.info(f"   🧪 Teste de controle: {test_size['width']}x{test_size['height']}")
                
                if not (test_size['width'] == 800 and test_size['height'] == 600):
                    validation_report['warnings'].append("Controle de dimensões da janela pode estar limitado")
                    self.logger.warning("   ⚠️ Controle de dimensões não funcionou completamente")
                    
            except Exception as dim_error:
                validation_report['tests_performed']['window_dimensions'] = {
                    'status': 'FALHA',
                    'error': str(dim_error),
                    'duration': (datetime.now() - datetime.fromisoformat(test_start)).total_seconds(),
                    'score': 0
                }
                validation_report['critical_failures'].append(f"Teste Dimensões falhou: {str(dim_error)}")
                self.logger.error(f"❌ TESTE 6 FALHA - Dimensões: {str(dim_error)}")
            
            # ANÁLISE FINAL E PONTUAÇÃO
            total_score = sum(test.get('score', 0) for test in validation_report['tests_performed'].values())
            validation_report['overall_score'] = total_score
            
            # Determinar se sessão é válida (mínimo 70% de sucesso)
            min_score_required = 70  # De 100 pontos possíveis
            validation_report['session_valid'] = total_score >= min_score_required and len(validation_report['critical_failures']) == 0
            
            # Gerar recomendação
            if validation_report['session_valid']:
                validation_report['recommendation'] = 'SESSÃO VÁLIDA - Controle total do navegador confirmado'
                self._log_step_success("Validação Explícita da Sessão AdsPower", step_start, {
                    'pontuacao_total': total_score,
                    'testes_realizados': len(validation_report['tests_performed']),
                    'falhas_criticas': len(validation_report['critical_failures']),
                    'avisos': len(validation_report['warnings'])
                })
            else:
                if len(validation_report['critical_failures']) > 0:
                    validation_report['recommendation'] = f'SESSÃO INVÁLIDA - Falhas críticas: {len(validation_report["critical_failures"])}'
                else:
                    validation_report['recommendation'] = f'SESSÃO LIMITADA - Pontuação baixa: {total_score}/{min_score_required}'
                
                self._log_step_failure("Validação Explícita da Sessão AdsPower", step_start,
                                     RuntimeError(validation_report['recommendation']), {
                    'pontuacao': f'{total_score}/{min_score_required}',
                    'falhas_criticas': validation_report['critical_failures'],
                    'avisos': validation_report['warnings']
                })
            
            return validation_report
            
        except Exception as e:
            validation_report['critical_failures'].append(f"Erro crítico na validação: {str(e)}")
            validation_report['recommendation'] = 'FALHA TOTAL - Validação não pôde ser concluída'
            self._log_step_failure("Validação Explícita da Sessão AdsPower", step_start, e, validation_report)
            return validation_report
    
    def test_browser_navigation(self) -> Dict:
        """🧭 TESTE CRÍTICO DE NAVEGAÇÃO PARA GOOGLE.COM
        
        Este teste navega para Google.com como validação definitiva de que o controle
        do navegador está funcionando para navegação real na internet.
        
        Returns:
            Dict: Relatório completo do teste de navegação
        """
        step_start = self._log_step_start("Teste Crítico de Navegação - Google.com", 2, {
            'objetivo': 'Confirmar capacidade de navegação real na internet',
            'url_destino': 'https://www.google.com',
            'timeout_maximo': 30
        })
        
        navigation_report = {
            'navigation_successful': False,
            'timestamp': datetime.now().isoformat(),
            'target_url': 'https://www.google.com',
            'steps_performed': [],
            'final_url': None,
            'final_title': None,
            'page_elements_found': {},
            'load_time': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            if not self.driver:
                error_msg = "Driver não está disponível para teste de navegação"
                navigation_report['errors'].append(error_msg)
                self._log_step_failure("Teste Crítico de Navegação - Google.com", step_start,
                                     RuntimeError(error_msg), navigation_report)
                return navigation_report
            
            navigation_start = datetime.now()
            
            # ETAPA 1: Navegação para Google.com
            step_info = {
                'step': 'navegacao_inicial',
                'status': 'em_progresso',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                self.logger.info("🧭 ETAPA 1: Iniciando navegação para Google.com...")
                self.driver.get('https://www.google.com')
                time.sleep(3)  # Aguardar carregamento inicial
                
                step_info['status'] = 'sucesso'
                step_info['duration'] = (datetime.now() - datetime.fromisoformat(step_info['timestamp'])).total_seconds()
                navigation_report['steps_performed'].append(step_info)
                
                self.logger.info(f"✅ ETAPA 1 SUCESSO - Comando de navegação executado (duração: {step_info['duration']:.3f}s)")
                
            except Exception as nav_error:
                step_info['status'] = 'falha'
                step_info['error'] = str(nav_error)
                navigation_report['steps_performed'].append(step_info)
                navigation_report['errors'].append(f"Falha na navegação inicial: {str(nav_error)}")
                self.logger.error(f"❌ ETAPA 1 FALHA - Navegação: {str(nav_error)}")
                
                self._log_step_failure("Teste Crítico de Navegação - Google.com", step_start,
                                     nav_error, navigation_report)
                return navigation_report
            
            # ETAPA 2: Verificação da URL final
            step_info = {
                'step': 'verificacao_url',
                'status': 'em_progresso',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                final_url = self.driver.current_url
                navigation_report['final_url'] = final_url
                
                # Verificar se chegou realmente no Google
                google_domains = ['google.com', 'google.com.br', 'google.pt']
                url_valid = any(domain in final_url.lower() for domain in google_domains)
                
                step_info['status'] = 'sucesso' if url_valid else 'aviso'
                step_info['final_url'] = final_url
                step_info['url_valid'] = url_valid
                step_info['duration'] = (datetime.now() - datetime.fromisoformat(step_info['timestamp'])).total_seconds()
                navigation_report['steps_performed'].append(step_info)
                
                if url_valid:
                    self.logger.info(f"✅ ETAPA 2 SUCESSO - URL válida do Google: {final_url}")
                else:
                    self.logger.warning(f"⚠️ ETAPA 2 AVISO - URL inesperada: {final_url}")
                    navigation_report['warnings'].append(f"URL final não é do Google: {final_url}")
                    
            except Exception as url_error:
                step_info['status'] = 'falha'
                step_info['error'] = str(url_error)
                navigation_report['steps_performed'].append(step_info)
                navigation_report['errors'].append(f"Falha na verificação de URL: {str(url_error)}")
                self.logger.error(f"❌ ETAPA 2 FALHA - Verificação URL: {str(url_error)}")
            
            # ETAPA 3: Verificação do título da página
            step_info = {
                'step': 'verificacao_titulo',
                'status': 'em_progresso',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                final_title = self.driver.title or "[Sem título]"
                navigation_report['final_title'] = final_title
                
                # Verificar se o título indica Google
                google_titles = ['google', 'pesquisa', 'search']
                title_valid = any(term in final_title.lower() for term in google_titles)
                
                step_info['status'] = 'sucesso' if title_valid else 'aviso'
                step_info['final_title'] = final_title
                step_info['title_valid'] = title_valid
                step_info['duration'] = (datetime.now() - datetime.fromisoformat(step_info['timestamp'])).total_seconds()
                navigation_report['steps_performed'].append(step_info)
                
                if title_valid:
                    self.logger.info(f"✅ ETAPA 3 SUCESSO - Título válido do Google: '{final_title}'")
                else:
                    self.logger.warning(f"⚠️ ETAPA 3 AVISO - Título inesperado: '{final_title}'")
                    navigation_report['warnings'].append(f"Título não indica Google: {final_title}")
                    
            except Exception as title_error:
                step_info['status'] = 'falha'
                step_info['error'] = str(title_error)
                navigation_report['steps_performed'].append(step_info)
                navigation_report['errors'].append(f"Falha na verificação de título: {str(title_error)}")
                self.logger.error(f"❌ ETAPA 3 FALHA - Verificação Título: {str(title_error)}")
            
            # ETAPA 4: Verificação de elementos característicos do Google
            step_info = {
                'step': 'verificacao_elementos',
                'status': 'em_progresso',
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                # Procurar elementos típicos do Google
                google_elements = {
                    'search_box': "//input[@name='q'] | //input[@title='Pesquisar'] | //input[@title='Search']",
                    'google_logo': "//img[contains(@alt, 'Google')] | //*[contains(@class, 'logo')]",
                    'search_button': "//input[@value='Pesquisa Google'] | //input[@value='Google Search'] | //button[contains(text(), 'Pesquisa')]",
                    'lucky_button': "//input[contains(@value, 'sorte')] | //input[contains(@value, 'lucky')]"
                }
                
                elements_found = {}
                for element_name, xpath in google_elements.items():
                    try:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        elements_found[element_name] = True
                        self.logger.info(f"   ✅ Elemento encontrado: {element_name}")
                    except:
                        elements_found[element_name] = False
                        self.logger.info(f"   ❌ Elemento não encontrado: {element_name}")
                
                navigation_report['page_elements_found'] = elements_found
                elements_count = sum(1 for found in elements_found.values() if found)
                
                step_info['status'] = 'sucesso' if elements_count >= 2 else 'aviso'
                step_info['elements_found'] = elements_found
                step_info['elements_count'] = elements_count
                step_info['duration'] = (datetime.now() - datetime.fromisoformat(step_info['timestamp'])).total_seconds()
                navigation_report['steps_performed'].append(step_info)
                
                if elements_count >= 2:
                    self.logger.info(f"✅ ETAPA 4 SUCESSO - {elements_count} elementos do Google encontrados")
                else:
                    self.logger.warning(f"⚠️ ETAPA 4 AVISO - Apenas {elements_count} elementos encontrados")
                    navigation_report['warnings'].append(f"Poucos elementos do Google encontrados: {elements_count}")
                    
            except Exception as elements_error:
                step_info['status'] = 'falha'
                step_info['error'] = str(elements_error)
                navigation_report['steps_performed'].append(step_info)
                navigation_report['errors'].append(f"Falha na verificação de elementos: {str(elements_error)}")
                self.logger.error(f"❌ ETAPA 4 FALHA - Verificação Elementos: {str(elements_error)}")
            
            # CÁLCULO FINAL
            navigation_end = datetime.now()
            navigation_report['load_time'] = (navigation_end - navigation_start).total_seconds()
            
            # Determinar sucesso geral
            successful_steps = sum(1 for step in navigation_report['steps_performed'] if step['status'] == 'sucesso')
            total_steps = len(navigation_report['steps_performed'])
            success_rate = (successful_steps / total_steps) if total_steps > 0 else 0
            
            # Considera sucesso se pelo menos 75% das etapas foram bem-sucedidas e sem erros críticos
            navigation_report['navigation_successful'] = (success_rate >= 0.75 and len(navigation_report['errors']) == 0)
            
            if navigation_report['navigation_successful']:
                self._log_step_success("Teste Crítico de Navegação - Google.com", step_start, {
                    'url_final': navigation_report['final_url'],
                    'titulo_final': navigation_report['final_title'],
                    'tempo_carregamento': f"{navigation_report['load_time']:.3f}s",
                    'etapas_sucesso': f"{successful_steps}/{total_steps}",
                    'elementos_encontrados': sum(1 for found in navigation_report.get('page_elements_found', {}).values() if found)
                })
            else:
                error_summary = f"Taxa de sucesso: {success_rate:.1%}, Erros: {len(navigation_report['errors'])}"
                self._log_step_failure("Teste Crítico de Navegação - Google.com", step_start,
                                     RuntimeError(error_summary), {
                    'erros': navigation_report['errors'],
                    'avisos': navigation_report['warnings'],
                    'etapas_realizadas': total_steps
                })
            
            return navigation_report
            
        except Exception as e:
            navigation_report['errors'].append(f"Erro crítico no teste de navegação: {str(e)}")
            self._log_step_failure("Teste Crítico de Navegação - Google.com", step_start, e, navigation_report)
            return navigation_report
    
    def verify_session_active(self) -> Dict:
        """⚡ VERIFICAÇÃO DE SESSÃO ATIVA E RESPONSIVA
        
        Confirma se a sessão WebDriver está ativa, responsiva e pronta para automação.
        
        Returns:
            Dict: Relatório de status da sessão
        """
        step_start = self._log_step_start("Verificação de Sessão Ativa", 3, {
            'objetivo': 'Confirmar que sessão WebDriver está ativa e responsiva',
            'testes': ['disponibilidade_driver', 'responsividade', 'timeout_tests']
        })
        
        session_report = {
            'session_active': False,
            'session_responsive': False,
            'timestamp': datetime.now().isoformat(),
            'response_times': {},
            'health_checks': {},
            'recommendations': []
        }
        
        try:
            # VERIFICAÇÃO 1: Driver disponível
            if not self.driver:
                session_report['health_checks']['driver_available'] = False
                session_report['recommendations'].append("Reinicializar conexão com AdsPower")
                self._log_step_failure("Verificação de Sessão Ativa", step_start,
                                     RuntimeError("Driver não disponível"), session_report)
                return session_report
            
            session_report['health_checks']['driver_available'] = True
            self.logger.info("✅ VERIFICAÇÃO 1: Driver está disponível")
            
            # VERIFICAÇÃO 2: Teste de responsividade básica
            response_start = datetime.now()
            try:
                # Teste simples mas efetivo
                current_url = self.driver.current_url
                response_time = (datetime.now() - response_start).total_seconds()
                
                session_report['response_times']['basic_command'] = response_time
                session_report['health_checks']['basic_responsiveness'] = True
                
                self.logger.info(f"✅ VERIFICAÇÃO 2: Responsividade básica OK (tempo: {response_time:.3f}s)")
                
                if response_time > 5.0:
                    session_report['recommendations'].append("Sessão lenta - considerar reinicialização")
                    self.logger.warning(f"⚠️ Sessão lenta detectada: {response_time:.3f}s")
                
            except Exception as resp_error:
                session_report['health_checks']['basic_responsiveness'] = False
                session_report['recommendations'].append("Sessão não responsiva - reinicialização necessária")
                self.logger.error(f"❌ VERIFICAÇÃO 2 FALHA: {str(resp_error)}")
            
            # VERIFICAÇÃO 3: Teste de comando JavaScript
            response_start = datetime.now()
            try:
                js_result = self.driver.execute_script("return 'SESSION_ACTIVE_CHECK';")
                js_response_time = (datetime.now() - response_start).total_seconds()
                
                session_report['response_times']['javascript_command'] = js_response_time
                session_report['health_checks']['javascript_execution'] = js_result == 'SESSION_ACTIVE_CHECK'
                
                if session_report['health_checks']['javascript_execution']:
                    self.logger.info(f"✅ VERIFICAÇÃO 3: JavaScript responsivo (tempo: {js_response_time:.3f}s)")
                else:
                    self.logger.error(f"❌ VERIFICAÇÃO 3: JavaScript retornou valor inesperado: {js_result}")
                    session_report['recommendations'].append("Execução JavaScript comprometida")
                
            except Exception as js_error:
                session_report['health_checks']['javascript_execution'] = False
                session_report['recommendations'].append("JavaScript não funcional")
                self.logger.error(f"❌ VERIFICAÇÃO 3 FALHA: {str(js_error)}")
            
            # VERIFICAÇÃO 4: Teste de múltiplas operações sequenciais
            response_start = datetime.now()
            try:
                # Sequência de comandos para testar estabilidade
                commands_results = []
                
                # Comando 1: URL
                commands_results.append(self.driver.current_url is not None)
                
                # Comando 2: Título
                commands_results.append(self.driver.title is not None)
                
                # Comando 3: Window handles
                commands_results.append(len(self.driver.window_handles) > 0)
                
                # Comando 4: JavaScript
                test_js = self.driver.execute_script("return window.location.href;")
                commands_results.append(test_js is not None)
                
                sequential_response_time = (datetime.now() - response_start).total_seconds()
                successful_commands = sum(commands_results)
                
                session_report['response_times']['sequential_commands'] = sequential_response_time
                session_report['health_checks']['sequential_stability'] = successful_commands == len(commands_results)
                
                self.logger.info(f"✅ VERIFICAÇÃO 4: Estabilidade sequencial {successful_commands}/{len(commands_results)} (tempo: {sequential_response_time:.3f}s)")
                
                if successful_commands < len(commands_results):
                    session_report['recommendations'].append("Instabilidade detectada em comandos sequenciais")
                
            except Exception as seq_error:
                session_report['health_checks']['sequential_stability'] = False
                session_report['recommendations'].append("Falha crítica em comandos sequenciais")
                self.logger.error(f"❌ VERIFICAÇÃO 4 FALHA: {str(seq_error)}")
            
            # VERIFICAÇÃO 5: Teste de capacidade de interação
            response_start = datetime.now()
            try:
                # Testar se consegue obter informações da página
                page_info = self.driver.execute_script("""
                    return {
                        ready: document.readyState === 'complete',
                        interactive: document.readyState !== 'loading',
                        has_body: document.body !== null,
                        can_focus: typeof window.focus === 'function'
                    };
                """)
                
                interaction_response_time = (datetime.now() - response_start).total_seconds()
                interaction_capable = all(page_info.values())
                
                session_report['response_times']['interaction_test'] = interaction_response_time
                session_report['health_checks']['interaction_capable'] = interaction_capable
                
                if interaction_capable:
                    self.logger.info(f"✅ VERIFICAÇÃO 5: Capacidade de interação OK (tempo: {interaction_response_time:.3f}s)")
                else:
                    self.logger.warning(f"⚠️ VERIFICAÇÃO 5: Limitações de interação detectadas: {page_info}")
                    session_report['recommendations'].append("Capacidade de interação limitada")
                
            except Exception as interact_error:
                session_report['health_checks']['interaction_capable'] = False
                session_report['recommendations'].append("Incapaz de testar interação")
                self.logger.error(f"❌ VERIFICAÇÃO 5 FALHA: {str(interact_error)}")
            
            # ANÁLISE FINAL
            health_checks_passed = sum(1 for check in session_report['health_checks'].values() if check)
            total_checks = len(session_report['health_checks'])
            health_score = (health_checks_passed / total_checks) if total_checks > 0 else 0
            
            # Calcular responsividade média
            response_times = list(session_report['response_times'].values())
            avg_response_time = sum(response_times) / len(response_times) if response_times else float('inf')
            
            # Determinar status da sessão
            session_report['session_active'] = health_score >= 0.8  # 80% dos checks passaram
            session_report['session_responsive'] = avg_response_time < 3.0  # Média abaixo de 3s
            
            overall_session_ok = session_report['session_active'] and session_report['session_responsive']
            
            if overall_session_ok:
                self._log_step_success("Verificação de Sessão Ativa", step_start, {
                    'saude_geral': f"{health_checks_passed}/{total_checks} checks OK",
                    'tempo_resposta_medio': f"{avg_response_time:.3f}s",
                    'sessao_ativa': session_report['session_active'],
                    'sessao_responsiva': session_report['session_responsive']
                })
            else:
                reasons = []
                if not session_report['session_active']:
                    reasons.append(f"Saúde baixa: {health_score:.1%}")
                if not session_report['session_responsive']:
                    reasons.append(f"Lentidão: {avg_response_time:.3f}s")
                
                self._log_step_failure("Verificação de Sessão Ativa", step_start,
                                     RuntimeError(f"Sessão problemática: {', '.join(reasons)}"), {
                    'recomendacoes': session_report['recommendations'],
                    'checks_falharam': total_checks - health_checks_passed,
                    'tempo_resposta_medio': avg_response_time
                })
            
            return session_report
            
        except Exception as e:
            session_report['recommendations'].append("Falha crítica na verificação de sessão")
            self._log_step_failure("Verificação de Sessão Ativa", step_start, e, session_report)
            return session_report
    
    def close_popups(self):
        """Fechar popups e elementos que podem atrapalhar"""
        try:
            # Lista de seletores de popups comuns do Google Ads
            popup_selectors = [
                # Popup de cookies
                "//button[contains(text(), 'Aceitar')] | //button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'OK')] | //button[contains(text(), 'Ok')]",
                "//button[contains(@aria-label, 'Fechar')] | //button[contains(@aria-label, 'Close')]",
                "//div[contains(@class, 'close')] | //button[contains(@class, 'close')]",
                # Popup de tour/introdução
                "//button[contains(text(), 'Pular')] | //button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Não agora')] | //button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Dispensar')] | //button[contains(text(), 'Dismiss')]",
                # Popup de notificações
                "//button[contains(text(), 'Bloquear')] | //button[contains(text(), 'Block')]",
                "//button[contains(text(), 'Permitir')] | //button[contains(text(), 'Allow')]",
                # X para fechar
                "//button[@aria-label='Fechar'] | //button[@aria-label='Close']",
                "//span[text()='×'] | //span[text()='✕']"
            ]
            
            for selector in popup_selectors:
                try:
                    # Tentar encontrar e clicar no popup (timeout curto)
                    if self.driver and self.wait:
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        element.click()
                        self.logger.info(f"Popup fechado: {selector}")
                        time.sleep(1)
                except:
                    continue  # Se não encontrar, continua para o próximo
                    
        except Exception as e:
            self.logger.debug(f"Erro ao fechar popups: {str(e)}")
            # Não é erro crítico, continua a execução
    
    def wait_for_page_load(self, timeout: int | None = None) -> bool:
        """Aguardar carregamento da página"""
        if timeout is None:
            timeout = self.default_timeout or 30
        
        try:
            if self.driver:
                WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Aguardar um pouco mais para elementos dinâmicos
            return True
        except TimeoutException:
            self.logger.warning("Timeout ao aguardar carregamento da página")
            return False
    
    def click_element_safe(self, selector: str, by_type: str = "xpath") -> bool:
        """Clicar em elemento com tratamento de erro"""
        try:
            if not self.wait or not self.driver:
                return False
                
            if by_type == "xpath":
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            else:
                element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # Scroll até o elemento se necessário
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Tentar clicar
            element.click()
            time.sleep(self.default_delay)
            return True
            
        except (TimeoutException, NoSuchElementException):
            self.logger.warning(f"Elemento não encontrado: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao clicar no elemento {selector}: {str(e)}")
            return False
    
    def input_text_safe(self, selector: str, text: str, by_type: str = "css") -> bool:
        """Inserir texto em campo com tratamento de erro"""
        try:
            if not self.wait or not self.driver:
                return False
                
            if by_type == "xpath":
                element = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            else:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            # Limpar campo e inserir texto
            element.clear()
            time.sleep(0.5)
            element.send_keys(text)
            time.sleep(1)
            return True
            
        except (TimeoutException, NoSuchElementException):
            self.logger.warning(f"Campo não encontrado: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao inserir texto no campo {selector}: {str(e)}")
            return False
    
    def create_campaign_step_by_step(self, config: Dict) -> bool:
        """🚀 Criar campanha passo a passo com LOGS SUPER DETALHADOS"""
        try:
            self.logger.info("🚀 INICIANDO criação de campanha step-by-step...")
            
            # PASSO 1: Navegar para campanhas e tentar nova campanha
            self.logger.info("🔍 PASSO 1: Procurando botão 'Nova Campanha'...")
            if not self.try_multilingual_click('new_campaign_btn'):
                self.logger.warning("⚠️ Tentativa 1 falhou, tentando seletores alternativos...")
                
                # Tentar seletores alternativos mais robustos
                alternative_selectors = [
                    "//button[contains(@class, 'new-campaign') or contains(@class, 'create') or contains(@aria-label, 'Nova')]",
                    "//a[contains(text(), 'Nova') or contains(text(), 'New') or contains(text(), 'Create')]",
                    "//button[contains(@data-track, 'create') or contains(@data-action, 'new')]",
                    "//div[@role='button'][contains(text(), '+') or contains(text(), 'Nova')]"
                ]
                
                success = False
                for i, alt_selector in enumerate(alternative_selectors):
                    self.logger.info(f"🔄 Tentativa alternativa {i+1}: {alt_selector[:50]}...")
                    if self.click_element_safe(alt_selector):
                        self.logger.info(f"✅ SUCESSO com seletor alternativo {i+1}!")
                        success = True
                        break
                
                if not success:
                    self.logger.error("💥 FALHA TOTAL: Nenhum botão 'Nova Campanha' encontrado")
                    self.take_screenshot("erro_nova_campanha.png")
                    return False
            else:
                self.logger.info("✅ PASSO 1 CONCLUÍDO: Botão 'Nova Campanha' clicado!")
            
            self.wait_for_page_load()
            self.logger.info("⏳ Aguardando carregamento da página...")
            
            # PASSO 2: Selecionar objetivo (se aparecer)
            self.logger.info("🎯 PASSO 2: Tentando selecionar objetivo da campanha...")
            objective_success = False
            objectives = [
                "//button[contains(text(), 'sem orientação') or contains(text(), 'without goal')]",
                "//div[contains(text(), 'Vendas') or contains(text(), 'Sales')]",
                "//div[contains(text(), 'Leads')]", 
                "//div[contains(text(), 'Tráfego') or contains(text(), 'Traffic')]"
            ]
            
            for i, obj_selector in enumerate(objectives):
                self.logger.info(f"🎯 Tentando objetivo {i+1}...")
                if self.click_element_safe(obj_selector):
                    self.logger.info(f"✅ OBJETIVO SELECIONADO: {obj_selector[:30]}...")
                    objective_success = True
                    break
            
            if not objective_success:
                self.logger.info("ℹ️ Nenhum objetivo selecionado (pode não ser necessário)")
            
            self.wait_for_page_load()
            
            # PASSO 3: Selecionar tipo de campanha (Pesquisa)
            self.logger.info("🔍 PASSO 3: Selecionando tipo 'Pesquisa/Search'...")
            if not self.try_multilingual_click('search_network'):
                self.logger.warning("⚠️ Seletores multilíngues falharam, tentando alternativos...")
                
                search_selectors = [
                    "//div[contains(@class, 'campaign-type')]//*[contains(text(), 'Pesquisa') or contains(text(), 'Search')]",
                    "//button[contains(text(), 'Pesquisa') or contains(text(), 'Search')]",
                    "//div[@role='button'][contains(text(), 'Pesquisa') or contains(text(), 'Search')]",
                    "//label[contains(text(), 'Pesquisa') or contains(text(), 'Search')]/..//input"
                ]
                
                search_success = False
                for i, search_sel in enumerate(search_selectors):
                    self.logger.info(f"🔍 Tentando seletor de pesquisa {i+1}...")
                    if self.click_element_safe(search_sel):
                        self.logger.info(f"✅ PESQUISA SELECIONADA: {search_sel[:30]}...")
                        search_success = True
                        break
                
                if not search_success:
                    self.logger.error("💥 FALHA: Não conseguiu selecionar tipo 'Pesquisa'")
                    self.take_screenshot("erro_tipo_pesquisa.png")
                    return False
            else:
                self.logger.info("✅ PASSO 3 CONCLUÍDO: Tipo 'Pesquisa' selecionado!")
            
            self.wait_for_page_load()
            
            # PASSO 4: Continuar com configuração detalhada
            self.logger.info("➡️ INICIANDO configuração detalhada da campanha...")
            return self.configure_campaign_details(config)
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na criação da campanha: {str(e)}")
            self.take_screenshot("erro_criacao_campanha.png")
            return False
    
    def create_campaign_google_ads_official_flow(self, config: Dict) -> bool:
        """Seguir exatamente o passo a passo oficial do Google Ads"""
        try:
            self.logger.info("🚀 Iniciando criação de campanha seguindo fluxo oficial do Google Ads...")
            
            # PASSO 1-2: Acessar seção Campanhas e iniciar nova campanha
            if not self.step_1_2_start_new_campaign():
                return False
            
            # PASSO 3: Escolher objetivo da campanha
            if not self.step_3_choose_campaign_objective(config):
                return False
            
            # PASSO 4: Selecionar tipo de campanha (Rede de Pesquisa)
            if not self.step_4_select_search_network():
                return False
            
            # PASSO 5: Definir nome da campanha
            if not self.step_5_define_campaign_name(config):
                return False
            
            # PASSO 6: Configurar definições da campanha
            if not self.step_6_configure_campaign_settings(config):
                return False
            
            # PASSO 7: Criar grupos de anúncios
            if not self.step_7_create_ad_groups(config):
                return False
            
            # PASSO 8: Criar anúncios de pesquisa responsivos
            if not self.step_8_create_responsive_search_ads(config):
                return False
            
            # PASSO 9: Adicionar extensões de anúncio
            if not self.step_9_add_ad_extensions(config):
                return False
            
            # PASSO 10: Revisar e publicar campanha
            if not self.step_10_review_and_publish():
                return False
            
            self.logger.info("✅ Campanha criada com sucesso seguindo fluxo oficial!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação da campanha: {str(e)}")
            return False
    
    def step_1_2_start_new_campaign(self) -> bool:
        """PASSO 1-2: 🚀 Navegação SUPER ROBUSTA para Nova Campanha"""
        try:
            self.logger.info("🚀 PASSO 1-2: Navegação multilíngue para Nova Campanha...")
            
            # Detectar idioma da interface automaticamente
            self.detect_interface_language()
            
            # Passo 1: Clicar no menu Campanhas (multilíngue)
            def click_campaigns_menu():
                return self.try_multilingual_click('campaigns_menu')
            
            self.smart_wait_and_retry(click_campaigns_menu, 3, "Clique no menu Campanhas")
            
            # Passo 2: Clicar no botão Nova Campanha (multilíngue)
            def click_new_campaign():
                return self.try_multilingual_click('new_campaign_btn')
            
            if self.smart_wait_and_retry(click_new_campaign, 5, "Clique no botão Nova Campanha"):
                self.logger.info("🎉 PASSO 1-2 COMPLETADO COM SUCESSO!")
                return True
            
            self.logger.error("💥 FALHA TOTAL no PASSO 1-2")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro no PASSO 1-2: {str(e)}")
            return False
    
    def step_3_choose_campaign_objective(self, config: Dict) -> bool:
        """PASSO 3: 🎯 Seleção MULTILÍNGUE dos 4 objetivos que suportam pesquisa"""
        try:
            self.logger.info("🎯 PASSO 3: Seleção multilíngue de objetivo (APENAS pesquisa)...")
            
            # Prioridade 1: SEM ORIENTAÇÃO (conforme instrução do usuário)
            def try_sem_orientacao():
                return self.try_multilingual_click('objectives', 'sem_orientacao')
            
            if self.smart_wait_and_retry(try_sem_orientacao, 3, "Seleção: SEM ORIENTAÇÃO"):
                self.logger.info("🚀 OBJETIVO SELECIONADO: SEM ORIENTAÇÃO (PRIORIDADE)")
                return True
            
            # Prioridade 2: VENDAS
            def try_vendas():
                return self.try_multilingual_click('objectives', 'vendas')
            
            if self.smart_wait_and_retry(try_vendas, 3, "Seleção: VENDAS"):
                self.logger.info("💰 OBJETIVO SELECIONADO: VENDAS")
                return True
            
            # Prioridade 3: LEADS
            def try_leads():
                return self.try_multilingual_click('objectives', 'leads')
            
            if self.smart_wait_and_retry(try_leads, 3, "Seleção: LEADS"):
                self.logger.info("📧 OBJETIVO SELECIONADO: LEADS")
                return True
            
            # Prioridade 4: TRÁFEGO DO SITE
            def try_trafego():
                return self.try_multilingual_click('objectives', 'trafego')
            
            if self.smart_wait_and_retry(try_trafego, 3, "Seleção: TRÁFEGO"):
                self.logger.info("🌐 OBJETIVO SELECIONADO: TRÁFEGO DO SITE")
                return True
            
            # Se não encontrou nenhum dos 4, continuar mesmo assim
            self.logger.warning("⚠️ Nenhum dos 4 objetivos encontrado, mas continuando...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no PASSO 3: {str(e)}")
            return False
    
    def step_4_select_search_network(self) -> bool:
        """PASSO 4: 🔍 Seleção MULTILÍNGUE da Rede de Pesquisa"""
        try:
            self.logger.info("🔍 PASSO 4: Seleção multilíngue da Rede de Pesquisa...")
            
            def select_search_network():
                return self.try_multilingual_click('search_network')
            
            if self.smart_wait_and_retry(select_search_network, 5, "Seleção da Rede de Pesquisa"):
                self.logger.info("🎉 REDE DE PESQUISA SELECIONADA COM SUCESSO!")
                return True
            
            self.logger.error("💥 FALHA TOTAL: Não foi possível selecionar Rede de Pesquisa")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro no PASSO 4: {str(e)}")
            return False
    
    def step_5_define_campaign_name(self, config: Dict) -> bool:
        """PASSO 5: 📝 Definição MULTILÍNGUE do nome da campanha"""
        try:
            self.logger.info("📝 PASSO 5: Definição multilíngue do nome da campanha...")
            
            campaign_name = config.get('campaign_name', '').strip()
            
            # SE NÃO ESTIVER PREENCHIDO, PULAR (conforme instrução)
            if not campaign_name:
                self.logger.info("⚠️ Nome da campanha não preenchido - PULANDO PASSO 5")
                return True
            
            def input_campaign_name():
                return self.try_multilingual_input('campaign_name', campaign_name)
            
            if self.smart_wait_and_retry(input_campaign_name, 3, f"Inserir nome: {campaign_name}"):
                self.logger.info(f"🎉 NOME DA CAMPANHA DEFINIDO: {campaign_name}")
                return True
            
            self.logger.warning("⚠️ Não conseguiu inserir nome, mas continuando...")
            return True  # Não é crítico
            
        except Exception as e:
            self.logger.error(f"❌ Erro no PASSO 5: {str(e)}")
            return True
    
    def step_6_configure_campaign_settings(self, config: Dict) -> bool:
        """PASSO 6: Configurar definições da campanha (redes, localização, idioma, orçamento, lances)"""
        try:
            self.logger.info("⚙️ PASSO 6: Configurando definições da campanha...")
            
            # 6.1: Desmarcar "Incluir parceiros de pesquisa do Google"
            search_partners_selectors = [
                "//input[@type='checkbox'][contains(@aria-label, 'parceiros')] | //input[@type='checkbox'][contains(@aria-label, 'partners')]",
                "//input[@type='checkbox'][contains(@name, 'search-partners')]",
                "//label[contains(text(), 'parceiros')]//input[@type='checkbox']"
            ]
            
            for selector in search_partners_selectors:
                try:
                    if self.driver:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element.is_selected():
                            element.click()
                            self.logger.info("✅ Desmarcou parceiros de pesquisa")
                            time.sleep(1)
                            break
                except:
                    continue
            
            # 6.2: Configurar localização(s)
            locations = config.get('locations', ['Brasil'])
            if isinstance(locations, str):
                locations = [locations]
            
            for location in locations:
                location_selectors = [
                    "//input[contains(@aria-label, 'localização')] | //input[contains(@aria-label, 'location')]",
                    "//input[contains(@placeholder, 'localização')] | //input[contains(@placeholder, 'location')]",
                    "//input[contains(@data-testid, 'location')]"
                ]
                
                for selector in location_selectors:
                    if self.input_text_safe(selector, location, "xpath"):
                        # Aguardar sugestões e selecionar primeira
                        time.sleep(2)
                        try:
                            if self.driver:
                                suggestion = self.driver.find_element(By.XPATH, "//div[contains(@class, 'suggestion')] | //li[contains(@role, 'option')]")
                                suggestion.click()
                        except:
                            pass
                        break
            
            # 6.3: Configurar idioma
            language = config.get('language', 'Português (Brasil)')
            language_selectors = [
                "//input[contains(@aria-label, 'idioma')] | //input[contains(@aria-label, 'language')]",
                "//select[contains(@aria-label, 'idioma')] | //select[contains(@aria-label, 'language')]"
            ]
            
            for selector in language_selectors:
                if self.input_text_safe(selector, language, "xpath"):
                    break
            
            # 6.4: Configurar orçamento diário - MULTILÍNGUE
            budget = config.get('budget', '').strip()
            if budget:
                def input_budget():
                    return self.try_multilingual_input('budget', budget)
                
                if self.smart_wait_and_retry(input_budget, 3, f"Inserir orçamento: R$ {budget}"):
                    self.logger.info(f"💰 ORÇAMENTO DEFINIDO: R$ {budget}")
                else:
                    self.logger.warning("⚠️ Não conseguiu inserir orçamento, mas continuando...")
            else:
                self.logger.info("⚠️ Orçamento não preenchido - PULANDO")
            
            # 6.5: Configurar estratégia de lances (Maximizar cliques por padrão)
            bidding_selectors = [
                "//div[contains(text(), 'Maximizar cliques')] | //div[contains(text(), 'Maximize clicks')]",
                "//button[contains(text(), 'Maximizar cliques')] | //button[contains(text(), 'Maximize clicks')]"
            ]
            
            for selector in bidding_selectors:
                if self.click_element_safe(selector, "xpath"):
                    self.logger.info("✅ Estratégia de lances configurada")
                    break
            
            # Continuar para próximo passo
            continue_selectors = [
                "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Próximo')] | //button[contains(text(), 'Next')]",
                "//button[contains(@aria-label, 'Continuar')] | //button[contains(@aria-label, 'Continue')]"
            ]
            
            for selector in continue_selectors:
                if self.click_element_safe(selector, "xpath"):
                    self.wait_for_page_load()
                    break
            
            self.logger.info("✅ Definições da campanha configuradas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 6: {str(e)}")
            return False
    
    def step_7_create_ad_groups(self, config: Dict) -> bool:
        """PASSO 7: Criar grupos de anúncios"""
        try:
            self.logger.info("📁 PASSO 7: Criando grupos de anúncios...")
            
            # 7.1: Dar nome ao grupo de anúncios
            ad_group_name = f"Grupo de Anúncios - {config.get('campaign_name', 'Principal')}"
            
            ad_group_name_selectors = [
                "//input[contains(@aria-label, 'grupo')] | //input[contains(@aria-label, 'group')]",
                "//input[contains(@placeholder, 'grupo')] | //input[contains(@placeholder, 'group')]",
                "//input[contains(@name, 'ad-group')]"
            ]
            
            for selector in ad_group_name_selectors:
                if self.input_text_safe(selector, ad_group_name, "xpath"):
                    self.logger.info(f"✅ Nome do grupo de anúncios: {ad_group_name}")
                    break
            
            # 7.2: Adicionar palavras-chave
            keywords = config.get('keywords', [])
            if keywords:
                keywords_text = '\\n'.join(keywords)
                
                keyword_selectors = [
                    "//textarea[contains(@aria-label, 'palavra')] | //textarea[contains(@aria-label, 'keyword')]",
                    "//textarea[contains(@placeholder, 'palavra')] | //textarea[contains(@placeholder, 'keyword')]",
                    "//input[contains(@aria-label, 'palavra')] | //input[contains(@aria-label, 'keyword')]"
                ]
                
                for selector in keyword_selectors:
                    if self.input_text_safe(selector, keywords_text, "xpath"):
                        self.logger.info(f"✅ Adicionadas {len(keywords)} palavras-chave")
                        break
            
            # Continuar para anúncios
            continue_selectors = [
                "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Próximo')] | //button[contains(text(), 'Next')]"
            ]
            
            for selector in continue_selectors:
                if self.click_element_safe(selector, "xpath"):
                    self.wait_for_page_load()
                    break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 7: {str(e)}")
            return False
    
    def step_8_create_responsive_search_ads(self, config: Dict) -> bool:
        """PASSO 8: Criar anúncios de pesquisa responsivos (até 15 títulos, 4 descrições)"""
        try:
            self.logger.info("📝 PASSO 8: Criando anúncios de pesquisa responsivos...")
            
            # 8.1: URL final - MULTILÍNGUE
            landing_url = config.get('landing_url', '').strip()
            if landing_url:
                def input_url():
                    return self.try_multilingual_input('url', landing_url)
                
                if self.smart_wait_and_retry(input_url, 3, f"Inserir URL: {landing_url}"):
                    self.logger.info(f"🌐 URL FINAL DEFINIDA: {landing_url}")
                else:
                    self.logger.warning("⚠️ Não conseguiu inserir URL, mas continuando...")
            else:
                self.logger.info("⚠️ URL final não preenchida - PULANDO")
            
            # 8.2: Títulos (até 15, máximo 30 caracteres cada) - PULA se não preenchido
            ad_titles = config.get('ad_titles', [])
            if ad_titles and any(title.strip() for title in ad_titles):  # Verifica se tem títulos preenchidos
                for i, title in enumerate(ad_titles[:15]):  # Máximo 15 títulos
                    title = title.strip()
                    if not title:  # Pula títulos vazios
                        continue
                        
                    if len(title) > 30:
                        title = title[:30]  # Máximo 30 caracteres
                    
                    title_selectors = [
                        f"//input[contains(@aria-label, 'Título {i+1}')] | //input[contains(@aria-label, 'Headline {i+1}')]",
                        f"//input[contains(@placeholder, 'Título {i+1}')] | //input[contains(@placeholder, 'Headline {i+1}')]",
                        f"//input[contains(@name, 'headline-{i}')]"
                    ]
                    
                    for selector in title_selectors:
                        if self.input_text_safe(selector, title, "xpath"):
                            self.logger.info(f"✅ Título {i+1}: {title}")
                            break
            else:
                self.logger.info("⚠️ Títulos não preenchidos - PULANDO configuração de títulos")
            
            # 8.3: Descrições (até 4, máximo 90 caracteres cada) - PULA se não preenchido
            ad_descriptions = config.get('ad_descriptions', [])
            if ad_descriptions and any(desc.strip() for desc in ad_descriptions):  # Verifica se tem descrições preenchidas
                for i, description in enumerate(ad_descriptions[:4]):  # Máximo 4 descrições
                    description = description.strip()
                    if not description:  # Pula descrições vazias
                        continue
                        
                    if len(description) > 90:
                        description = description[:90]  # Máximo 90 caracteres
                    
                    desc_selectors = [
                        f"//textarea[contains(@aria-label, 'Descrição {i+1}')] | //textarea[contains(@aria-label, 'Description {i+1}')]",
                        f"//textarea[contains(@placeholder, 'Descrição {i+1}')] | //textarea[contains(@placeholder, 'Description {i+1}')]",
                        f"//textarea[contains(@name, 'description-{i}')]"
                    ]
                    
                    for selector in desc_selectors:
                        if self.input_text_safe(selector, description, "xpath"):
                            self.logger.info(f"✅ Descrição {i+1}: {description}")
                            break
            else:
                self.logger.info("⚠️ Descrições não preenchidas - PULANDO configuração de descrições")
            
            # 8.4: Caminhos de exibição (até 2, 15 caracteres cada)
            display_paths = ["oferta", "especial"]  # Valores padrão
            for i, path in enumerate(display_paths[:2]):
                if len(path) > 15:
                    path = path[:15]
                
                path_selectors = [
                    f"//input[contains(@aria-label, 'Caminho {i+1}')] | //input[contains(@aria-label, 'Path {i+1}')]",
                    f"//input[contains(@name, 'path-{i}')]"
                ]
                
                for selector in path_selectors:
                    if self.input_text_safe(selector, path, "xpath"):
                        self.logger.info(f"✅ Caminho {i+1}: {path}")
                        break
            
            self.logger.info("✅ Anúncios responsivos criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 8: {str(e)}")
            return False
    
    def step_9_add_ad_extensions(self, config: Dict) -> bool:
        """PASSO 9: Adicionar extensões de anúncio (sitelink, chamada, local)"""
        try:
            self.logger.info("🔗 PASSO 9: Adicionando extensões de anúncio...")
            
            # Tentar clicar em "Adicionar extensões" ou pular se opcional
            extension_selectors = [
                "//button[contains(text(), 'Adicionar extensões')] | //button[contains(text(), 'Add extensions')]",
                "//a[contains(text(), 'extensões')] | //a[contains(text(), 'extensions')]",
                "//button[contains(text(), 'Pular')] | //button[contains(text(), 'Skip')]"
            ]
            
            for selector in extension_selectors:
                if self.click_element_safe(selector, "xpath"):
                    if 'Skip' in selector or 'Pular' in selector:
                        self.logger.info("⚠️ Extensões puladas (opcional)")
                    else:
                        self.logger.info("✅ Extensões de anúncio configuradas")
                    return True
            
            # Se não encontrar, continuar (extensões são opcionais)
            self.logger.info("ℹ️ Seção de extensões não encontrada, continuando...")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 9: {str(e)}")
            return False
    
    def step_10_review_and_publish(self) -> bool:
        """PASSO 10: Revisar todas as configurações e publicar campanha"""
        try:
            self.logger.info("🚀 PASSO 10: Revisando e publicando campanha...")
            
            # Procurar botões de publicar/finalizar
            publish_selectors = [
                "//button[contains(text(), 'Publicar')] | //button[contains(text(), 'Publish')]",
                "//button[contains(text(), 'Criar campanha')] | //button[contains(text(), 'Create campaign')]",
                "//button[contains(text(), 'Finalizar')] | //button[contains(text(), 'Finish')]",
                "//button[contains(@aria-label, 'Publicar')] | //button[contains(@aria-label, 'Publish')]"
            ]
            
            for selector in publish_selectors:
                if self.click_element_safe(selector, "xpath"):
                    self.wait_for_page_load(timeout=30)  # Publicação pode demorar
                    self.logger.info("🎉 CAMPANHA PUBLICADA COM SUCESSO!")
                    return True
            
            self.logger.error("❌ Não foi possível encontrar botão de publicar")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 10: {str(e)}")
            return False
    
    def configure_campaign_details(self, config: Dict) -> bool:
        """📝 Configurar detalhes específicos da campanha com LOGS DETALHADOS"""
        try:
            self.logger.info("📝 INICIANDO configuração de detalhes da campanha...")
            
            # Nome da campanha
            campaign_name = config.get('campaign_name', 'Campanha Teste')
            self.logger.info(f"🏷️ Inserindo nome da campanha: {campaign_name}")
            if not self.try_multilingual_input('campaign_name', campaign_name):
                self.logger.error("❌ FALHA ao inserir nome da campanha")
                return False
            self.logger.info("✅ Nome da campanha inserido com sucesso")
            
            # Orçamento
            budget = str(config.get('daily_budget', 50))
            self.logger.info(f"💰 Inserindo orçamento diário: R$ {budget}")
            if not self.try_multilingual_input('budget', budget):
                self.logger.error("❌ FALHA ao inserir orçamento")
                return False
            self.logger.info("✅ Orçamento inserido com sucesso")
            
            # Localização  
            locations = config.get('target_locations', ['Brasil'])
            location_text = ', '.join(locations)
            self.logger.info(f"🌍 Inserindo localização: {location_text}")
            if not self.try_multilingual_input('location', location_text):
                self.logger.error("❌ FALHA ao inserir localização")
                return False
            self.logger.info("✅ Localização inserida com sucesso")
            
            # Continuar para próxima etapa
            self.logger.info("➡️ Clicando em 'Continuar' para próxima etapa...")
            if not self.try_multilingual_click('continue_btn'):
                self.logger.error("❌ FALHA ao clicar em 'Continuar'")
                return False
            
            self.logger.info("🎉 DETALHES DA CAMPANHA configurados com SUCESSO!")
            self.wait_for_page_load()
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO GRAVE ao configurar detalhes da campanha: {str(e)}")
            return False
    
    def configure_ad_groups_and_keywords(self, config: Dict) -> bool:
        """🔑 Configurar grupos de anúncios e palavras-chave com LOGS DETALHADOS"""
        try:
            self.logger.info("🔑 INICIANDO configuração de palavras-chave...")
            
            # Adicionar palavras-chave
            keywords = config.get('keywords', ['palavra-chave exemplo'])
            keywords_text = '\n'.join(keywords)
            
            self.logger.info(f"🎯 Inserindo {len(keywords)} palavras-chave: {keywords[:3]}...")
            if not self.try_multilingual_input('keywords', keywords_text):
                self.logger.error("❌ FALHA ao inserir palavras-chave")
                return False
            self.logger.info("✅ Palavras-chave inseridas com sucesso")
            
            # Continuar para anúncios
            self.logger.info("➡️ Clicando em 'Continuar' para configurar anúncios...")
            if not self.try_multilingual_click('continue_btn'):
                self.logger.error("❌ FALHA ao clicar em 'Continuar' após palavras-chave")
                return False
            
            self.logger.info("🎉 PALAVRAS-CHAVE configuradas com SUCESSO!")
            self.wait_for_page_load()
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO GRAVE ao configurar palavras-chave: {str(e)}")
            return False
    
    def configure_ads(self, config: Dict) -> bool:
        """📢 Configurar anúncios com LOGS DETALHADOS"""
        try:
            self.logger.info("📢 INICIANDO configuração de anúncios...")
            
            # Títulos do anúncio (até 15 títulos no Google Ads)
            headlines = config.get('ad_headlines', ['Título do Anúncio 1', 'Título do Anúncio 2'])
            self.logger.info(f"📝 Inserindo {len(headlines)} títulos de anúncio...")
            for i, headline in enumerate(headlines[:3]):  # Limitar a 3 por simplicidade
                if not self.try_multilingual_input('headlines', headline):
                    self.logger.warning(f"⚠️ Falha ao inserir título {i+1}: {headline}")
                else:
                    self.logger.info(f"✅ Título {i+1} inserido: {headline}")
            
            # Descrições do anúncio (até 4 descrições no Google Ads)
            descriptions = config.get('ad_descriptions', ['Descrição do anúncio exemplo'])
            self.logger.info(f"📄 Inserindo {len(descriptions)} descrições de anúncio...")
            for i, desc in enumerate(descriptions[:2]):  # Limitar a 2 por simplicidade
                if not self.try_multilingual_input('descriptions', desc):
                    self.logger.warning(f"⚠️ Falha ao inserir descrição {i+1}: {desc}")
                else:
                    self.logger.info(f"✅ Descrição {i+1} inserida: {desc}")
            
            # URL de destino
            final_url = config.get('final_url', 'https://exemplo.com')
            self.logger.info(f"🔗 Inserindo URL de destino: {final_url}")
            if not self.try_multilingual_input('url', final_url):
                self.logger.error("❌ FALHA ao inserir URL de destino")
                return False
            self.logger.info("✅ URL de destino inserida com sucesso")
            
            # Publicar campanha
            self.logger.info("🚀 TENTANDO publicar a campanha...")
            if not self.try_multilingual_click('publish_btn'):
                self.logger.warning("⚠️ Botão 'Publicar' não encontrado, tentando 'Continuar' primeiro...")
                
                # Tentar continuar primeiro
                if self.try_multilingual_click('continue_btn'):
                    self.logger.info("✅ Clicou em 'Continuar', tentando 'Publicar' novamente...")
                    self.wait_for_page_load()
                    
                    if not self.try_multilingual_click('publish_btn'):
                        self.logger.error("❌ FALHA TOTAL ao publicar campanha")
                        return False
                else:
                    self.logger.error("❌ FALHA TOTAL - nem 'Continuar' nem 'Publicar' funcionaram")
                    return False
            
            self.logger.info("🎉 CAMPANHA PUBLICADA COM SUCESSO!")
            self.wait_for_page_load(timeout=30)  # Publicação pode demorar
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO GRAVE ao configurar anúncios: {str(e)}")
            return False
    
    def run(self, profile: Dict, config: Dict) -> bool:
        """🚀 MÉTODO PRINCIPAL que orquestra TODO o fluxo de automação"""
        try:
            self.logger.info(f"🚀 INICIANDO automação COMPLETA para perfil: {profile['name']}")
            
            # ETAPA 1: Iniciar browser no AdsPower (JÁ FOI FEITO)
            self.logger.info("📱 ETAPA 1: Browser AdsPower já foi iniciado pelo main.py")
            
            # ETAPA 2: Configurar e conectar driver Selenium
            self.logger.info("🔧 ETAPA 2: Configurando driver Selenium...")
            from adspower_manager import AdsPowerManager
            adspower_manager = AdsPowerManager()
            
            browser_info = adspower_manager.get_browser_info(profile['user_id'])
            if not browser_info:
                self.logger.error("💥 FALHA na ETAPA 2: Não conseguiu obter info do browser")
                return False
            
            self.logger.info(f"📋 Info do browser: {browser_info}")
            
            if not self.setup_driver(browser_info, config.get('headless', False)):
                self.logger.error("💥 FALHA na ETAPA 2: Não conseguiu configurar driver")
                return False
            
            self.logger.info("✅ ETAPA 2 COMPLETA: Driver configurado e conectado")
            
            # TESTE CRÍTICO: Verificar se consegue controlar o browser
            self.logger.info("🧪 TESTE CRÍTICO: Verificando controle do browser...")
            try:
                if not self.driver:
                    self.logger.error("💥 ERRO: Driver não existe (None)")
                    return False
                    
                current_url = self.driver.current_url
                page_title = self.driver.title
                self.logger.info(f"✅ CONTROLE CONFIRMADO - URL: {current_url}")
                self.logger.info(f"✅ CONTROLE CONFIRMADO - Título: {page_title}")
                
                # Teste básico: navegar para uma página simples
                self.logger.info("🧪 TESTE: Navegando para Google...")
                if self.driver:
                    self.driver.get("https://www.google.com")
                else:
                    self.logger.error("💥 ERRO: Driver não existe para navegar")
                    return False
                
                # Aguardar carregar
                time.sleep(3)
                
                if self.driver:
                    new_url = self.driver.current_url
                    new_title = self.driver.title
                else:
                    self.logger.error("💥 ERRO: Driver não existe para verificar navegação")
                    return False
                self.logger.info(f"✅ NAVEGAÇÃO TESTE - URL: {new_url}")
                self.logger.info(f"✅ NAVEGAÇÃO TESTE - Título: {new_title}")
                
                if "google" in new_url.lower():
                    self.logger.info("🎉 TESTE PASSOU: Browser está sendo controlado corretamente!")
                else:
                    self.logger.error("💥 TESTE FALHOU: Navegação não funcionou")
                    return False
                    
            except Exception as test_error:
                self.logger.error(f"💥 TESTE CRÍTICO FALHOU: {str(test_error)}")
                return False
            
            # ETAPA 3: Navegar para Google Ads
            self.logger.info("🌐 ETAPA 3: Navegando para Google Ads...")
            if not self.navigate_to_google_ads():
                self.logger.error("💥 FALHA na ETAPA 3: Não conseguiu navegar para Google Ads")
                return False
            
            self.logger.info("✅ ETAPA 3 COMPLETA: Navegou para Google Ads com sucesso")
            
            # ETAPA 4: Criar campanha
            self.logger.info("📝 ETAPA 4: Criando campanha...")
            success = self.create_campaign_step_by_step(config)
            
            if success:
                self.logger.info("🎉 ETAPA 4 COMPLETA: Campanha criada com SUCESSO!")
            else:
                self.logger.error("💥 FALHA na ETAPA 4: Criação de campanha falhou")
            
            # ETAPA 5: Limpeza (sem fechar browser AdsPower)
            self.logger.info("🧹 ETAPA 5: Limpeza final...")
            self.cleanup()
            
            return success
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO no fluxo principal: {str(e)}")
            import traceback
            self.logger.error(f"📍 Traceback completo: {traceback.format_exc()}")
            try:
                self.cleanup()
            except:
                pass
            return False
    
    def create_campaign_with_browser(self, profile: Dict, config: Dict, browser_info: Dict) -> bool:
        """🚀 Função principal SUPER ROBUSTA para criar campanha com SCREENSHOTS em CADA ETAPA"""
        try:
            self.logger.info(f"🚀 INICIANDO automação COMPLETA para perfil: {profile['name']}")
            
            # ETAPA 1: Configurar driver do Selenium
            self.logger.info("🔧 ETAPA 1: Configurando driver do Selenium...")
            self.take_screenshot("etapa_1_antes_driver.png")
            
            headless = config.get('headless', False)
            if not self.setup_driver(browser_info, headless):
                self.logger.error("❌ FALHA na ETAPA 1: Não foi possível configurar o driver")
                self.take_screenshot("etapa_1_erro_driver.png")
                return False
            
            self.logger.info("✅ ETAPA 1 COMPLETA: Driver configurado com sucesso")
            self.take_screenshot("etapa_1_driver_ok.png")
            
            # ETAPA 2: Preparar browser para navegação calculada
            self.logger.info("🛠️ ETAPA 2A: Preparando browser para controle total...")
            self.take_screenshot("etapa_2a_antes_preparacao.png")
            
            if not self.prepare_browser_for_navigation():
                self.logger.error("❌ FALHA na ETAPA 2A: Não conseguiu preparar browser")
                self.take_screenshot("etapa_2a_erro_preparacao.png")
                return False
            
            self.logger.info("✅ ETAPA 2A COMPLETA: Browser preparado para controle total")
            self.take_screenshot("etapa_2a_preparacao_ok.png")
            
            # TESTE CRÍTICO: Verificar se consegue controlar o browser
            self.logger.info("🧪 TESTE CRÍTICO: Verificando controle do browser...")
            try:
                if not self.driver:
                    self.logger.error("💥 ERRO: Driver não existe (None)")
                    return False
                    
                current_url = self.driver.current_url
                page_title = self.driver.title
                self.logger.info(f"✅ CONTROLE CONFIRMADO - URL: {current_url}")
                self.logger.info(f"✅ CONTROLE CONFIRMADO - Título: {page_title}")
                
                # Teste básico: navegar para uma página simples
                self.logger.info("🧪 TESTE: Navegando para Google...")
                if self.driver:
                    self.driver.get("https://www.google.com")
                else:
                    self.logger.error("💥 ERRO: Driver não existe para navegar")
                    return False
                
                # Aguardar carregar
                time.sleep(3)
                
                if self.driver:
                    new_url = self.driver.current_url
                    new_title = self.driver.title
                else:
                    self.logger.error("💥 ERRO: Driver não existe para verificar navegação")
                    return False
                self.logger.info(f"✅ NAVEGAÇÃO TESTE - URL: {new_url}")
                self.logger.info(f"✅ NAVEGAÇÃO TESTE - Título: {new_title}")
                
                if "google" in new_url.lower():
                    self.logger.info("🎉 TESTE PASSOU: Browser está sendo controlado corretamente!")
                else:
                    self.logger.error("💥 TESTE FALHOU: Navegação não funcionou")
                    return False
                    
            except Exception as test_error:
                self.logger.error(f"💥 TESTE CRÍTICO FALHOU: {str(test_error)}")
                import traceback
                self.logger.error(f"📍 Traceback: {traceback.format_exc()}")
                return False
            
            # ETAPA 3: Navegar para Google Ads
            self.logger.info("🌐 ETAPA 3: Navegando para Google Ads...")
            if not self.navigate_to_google_ads():
                self.logger.error("💥 FALHA na ETAPA 3: Não conseguiu navegar para Google Ads")
                return False
            
            self.logger.info("✅ ETAPA 3 COMPLETA: Navegou para Google Ads com sucesso")
            
            # ETAPA 4: Criar campanha
            self.logger.info("📝 ETAPA 4: Criando campanha...")
            success = self.create_campaign_step_by_step(config)
            
            if success:
                self.logger.info("🎉 ETAPA 4 COMPLETA: Campanha criada com SUCESSO!")
            else:
                self.logger.error("💥 FALHA na ETAPA 4: Criação de campanha falhou")
            
            # ETAPA 5: Limpeza (sem fechar browser AdsPower)
            self.logger.info("🧹 ETAPA 5: Limpeza final...")
            self.cleanup()
            
            return success
            self.take_screenshot("etapa_3_pagina_carregada.png")
            
            # Verificar se realmente está na página certa
            try:
                if not self.driver:
                    self.logger.error("❌ FALHA na ETAPA 3: Driver não está disponível")
                    return False
                    
                current_url = self.driver.current_url
                title = self.driver.title
                self.logger.info(f"📍 URL atual: {current_url}")
                self.logger.info(f"📄 Título: {title}")
                
                if "ads.google.com" not in current_url.lower():
                    self.logger.error(f"❌ FALHA na ETAPA 3: URL incorreta: {current_url}")
                    self.take_screenshot("etapa_3_url_incorreta.png")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ FALHA na ETAPA 3: Erro ao verificar estado: {str(e)}")
                self.take_screenshot("etapa_3_erro_verificacao.png")
                return False
            
            self.logger.info("✅ ETAPA 3 COMPLETA: Estado da página verificado")
            
            # ETAPA 4: Iniciar criação de campanha
            self.logger.info("📝 ETAPA 4: INICIANDO criação de campanha step-by-step...")
            self.take_screenshot("etapa_4_antes_campanha.png")
            
            success = self.create_campaign_step_by_step(config)
            
            if success:
                self.logger.info("🎉 ETAPA 4 COMPLETA: Campanha criada com SUCESSO!")
                self.take_screenshot("etapa_4_campanha_sucesso.png")
                self.logger.info(f"✅ Campanha '{config.get('campaign_name', 'Sem nome')}' criada com sucesso no perfil {profile['name']}")
            else:
                self.logger.error("❌ FALHA na ETAPA 4: Criação de campanha falhou")
                self.take_screenshot("etapa_4_campanha_erro.png")
                self.logger.error(f"❌ Falha ao criar campanha no perfil {profile['name']}")
            
            # ETAPA 5: Verificação final e limpeza
            self.logger.info("🧹 ETAPA 5: Verificação final e limpeza...")
            self.take_screenshot("etapa_5_final.png")
            
            return success
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na automação do perfil {profile['name']}: {str(e)}")
            self.take_screenshot("erro_critico_geral.png")
            return False
            
        finally:
            # 🔧 CORREÇÃO 4: Não fechar browser, apenas desconectar driver
            try:
                if self.driver:
                    self.logger.info("🔌 Desconectando driver (mantendo browser aberto)...")
                    self.driver.quit()
                    self.driver = None
                    self.logger.info("✅ Driver desconectado com sucesso")
            except Exception as disconnect_error:
                self.logger.warning(f"⚠️ Erro ao desconectar driver: {str(disconnect_error)}")
    
    def create_campaign(self, profile: Dict, config: Dict) -> bool:
        """Método legado - mantido para compatibilidade"""
        self.logger.warning("Método create_campaign é legado. Use create_campaign_with_browser.")
        browser_info = self.adspower_manager.start_browser(profile['user_id'])
        if not browser_info:
            return False
        try:
            return self.create_campaign_with_browser(profile, config, browser_info)
        finally:
            self.adspower_manager.stop_browser(profile['user_id'])
    
    def cleanup(self):
        """Limpar recursos do driver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.info("Driver limpo com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao limpar driver: {str(e)}")
    
    def take_screenshot(self, filename: str | None = None) -> str | None:
        """Tirar screenshot para debugging"""
        try:
            if not self.driver:
                return None
                
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot salvo: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Erro ao tirar screenshot: {str(e)}")
            return None
    
    def get_page_source(self) -> str:
        """Obter código fonte da página para debugging"""
        try:
            if self.driver:
                return self.driver.page_source
            return ""
        except Exception as e:
            self.logger.error(f"Erro ao obter código fonte: {str(e)}")
            return ""
    
    def detect_interface_language(self) -> str:
        """🌐 Detectar automaticamente o idioma da interface do Google Ads"""
        try:
            self.logger.info("🔍 Detectando idioma da interface do Google Ads...")
            
            # Palavras-chave para detectar idioma
            detection_words = {
                'pt': ['Campanhas', 'Nova campanha', 'Orçamento', 'Publicar', 'Continuar'],
                'en': ['Campaigns', 'New campaign', 'Budget', 'Publish', 'Continue'],
                'es': ['Campañas', 'Nueva campaña', 'Presupuesto', 'Publicar', 'Continuar']
            }
            
            if not self.driver:
                return 'pt'  # Padrão português
            
            page_text = self.driver.page_source.lower()
            
            # Contar ocorrências para cada idioma
            scores = {}
            for lang, words in detection_words.items():
                scores[lang] = sum(1 for word in words if word.lower() in page_text)
            
            # Detectar idioma com maior pontuação
            detected_lang = max(scores.keys(), key=lambda k: scores[k])
            
            if scores[detected_lang] > 0:
                self.current_language = detected_lang
                self.logger.info(f"🌐 Idioma detectado: {detected_lang.upper()} (Score: {scores[detected_lang]})")
                return detected_lang
            else:
                self.logger.info("⚠️ Não foi possível detectar idioma, usando português como padrão")
                self.current_language = 'pt'
                return 'pt'
                
        except Exception as e:
            self.logger.error(f"Erro ao detectar idioma: {str(e)}")
            self.current_language = 'pt'
            return 'pt'
    
    def try_multilingual_click(self, selector_group: str, selector_key: str | None = None) -> bool:
        """🔄 Tentar clique em múltiplos idiomas com várias tentativas"""
        
        # Se idioma for auto, detectar primeiro
        if self.current_language == 'auto':
            self.detect_interface_language()
        
        languages = [self.current_language, 'pt', 'en', 'es']  # Prioridade: detectado, pt, en, es
        languages = list(dict.fromkeys(languages))  # Remover duplicatas
        
        for lang in languages:
            self.logger.info(f"🔄 Tentando seletores em {lang.upper()}...")
            
            # Obter seletores para este idioma
            if selector_key:
                selectors = self.multilingual_selectors.get(selector_group, {}).get(selector_key, {}).get(lang, [])
            else:
                selectors = self.multilingual_selectors.get(selector_group, {}).get(lang, [])
            
            if not selectors:
                continue
            
            # Tentar cada seletor para este idioma
            for selector in selectors:
                if self.click_element_safe(selector):
                    self.logger.info(f"✅ SUCESSO com seletor {lang.upper()}: {selector}")
                    return True
        
        self.logger.error(f"❌ FALHA TOTAL: Nenhum seletor funcionou para {selector_group}")
        return False
    
    def try_multilingual_input(self, selector_group: str, text: str) -> bool:
        """📝 Tentar inserir texto em campos usando seletores multilíngues"""
        
        # Se idioma for auto, detectar primeiro
        if self.current_language == 'auto':
            self.detect_interface_language()
        
        languages = [self.current_language, 'pt', 'en', 'es']
        languages = list(dict.fromkeys(languages))
        
        for lang in languages:
            self.logger.info(f"🔄 Tentando campos de input em {lang.upper()}...")
            
            selectors = self.multilingual_selectors.get('input_fields', {}).get(selector_group, {}).get(lang, [])
            
            if not selectors:
                continue
            
            for selector in selectors:
                if self.input_text_safe(selector, text, "xpath"):
                    self.logger.info(f"✅ SUCESSO input {lang.upper()}: {text[:30]}...")
                    return True
        
        self.logger.error(f"❌ FALHA TOTAL: Nenhum campo de input funcionou para {selector_group}")
        return False
    
    def smart_wait_and_retry(self, action_func, max_attempts: int = 5, description: str = "ação") -> bool:
        """🧠 Sistema inteligente de espera e retry para qualquer ação"""
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"🔄 Tentativa {attempt + 1}/{max_attempts}: {description}")
                
                # Aguardar carregamento da página
                self.wait_for_page_load()
                
                # Fechar popups que podem atrapalhar
                self.close_popups()
                
                # Executar ação
                if action_func():
                    self.logger.info(f"✅ SUCESSO na tentativa {attempt + 1}: {description}")
                    return True
                
                # Se falhou, aguardar mais um pouco e tentar novamente
                wait_time = self.retry_delay * (attempt + 1)  # Aumentar tempo progressivamente
                self.logger.warning(f"⚠️ Tentativa {attempt + 1} falhou, aguardando {wait_time}s...")
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"❌ Erro na tentativa {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        self.logger.error(f"💥 FALHA COMPLETA após {max_attempts} tentativas: {description}")
        return False
    
    # SISTEMA REMOVIDO: _setup_chrome_driver_smart
    # CORREÇÃO CRÍTICA: Eliminado sistema completo que criava Chrome local
    # Sistema agora exige 100% webdriver.Remote() com AdsPower ou falha claramente
    
    def _detect_chrome_version(self, browser_info: Dict) -> str:
        """🔍 Detectar versão do Chrome no AdsPower"""
        try:
            # Método 1: Verificar se AdsPower retorna versão
            for key in ['chrome_version', 'browser_version', 'version']:
                if key in browser_info:
                    version = browser_info[key]
                    self.logger.info(f"✅ Versão do Chrome encontrada: {version}")
                    return version
            
            # Método 2: Tentar obter via debugger port
            debugger_address = browser_info.get('debugger_address')
            if debugger_address:
                import requests
                try:
                    version_url = f"http://{debugger_address}/json/version"
                    response = requests.get(version_url, timeout=5)
                    if response.status_code == 200:
                        version_data = response.json()
                        browser_str = version_data.get('Browser', '')
                        # Extrair versão (ex: "Chrome/120.0.6099.109")
                        import re
                        match = re.search(r'Chrome/(\d+\.\d+)', browser_str)
                        if match:
                            version = match.group(1)
                            self.logger.info(f"✅ Versão do Chrome via API: {version}")
                            return version
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao detectar versão via API: {str(e)}")
            
            # Método 3: Fallback para versão comum
            self.logger.warning("⚠️ Não foi possível detectar versão específica, usando padrão")
            return "120.0"  # Versão comum recente
            
        except Exception as e:
            self.logger.error(f"💥 Erro ao detectar versão do Chrome: {str(e)}")
            return "120.0"
    
    # MÉTODO REMOVIDO: _try_adspower_chromedriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    
    # MÉTODO REMOVIDO: _try_path_chromedriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    
    # MÉTODO REMOVIDO: _try_specific_version_chromedriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    
    # MÉTODO REMOVIDO: _try_multiple_versions_chromedriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    
    # MÉTODO REMOVIDO: _try_latest_chromedriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Chrome() local
    
    # SISTEMA REMOVIDO: _setup_firefox_driver
    # CORREÇÃO CRÍTICA: Eliminado sistema Firefox que criava drivers locais
    # Sistema agora requer 100% webdriver.Remote() com AdsPower ou falha claramente
    
    # MÉTODO REMOVIDO: _try_adspower_geckodriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Firefox() local
    
    # MÉTODO REMOVIDO: _try_path_geckodriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Firefox() local
    
    # MÉTODO REMOVIDO: _try_auto_install_geckodriver
    # CORREÇÃO CRÍTICA: Eliminado método que criava webdriver.Firefox() local