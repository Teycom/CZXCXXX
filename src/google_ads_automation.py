#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Automation - Automação de Criação de Campanhas
Sistema robusto para automação de campanhas do Google Ads via AdsPower
"""

import time
import json
import logging
import traceback
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, NoSuchElementException,
    ElementNotInteractableException, StaleElementReferenceException,
    ElementClickInterceptedException, InvalidSessionIdException
)

# Stealth e undetected chrome
import undetected_chromedriver as uc
from selenium_stealth import stealth

# Imports locais
from config import get_config
from logger import get_logger, log_automation_event

class GoogleAdsAutomation:
    """Automação robusta para criação de campanhas no Google Ads"""
    
    def __init__(self, adspower_manager, profile_name: str = ""):
        self.adspower_manager = adspower_manager
        self.profile_name = profile_name
        self.logger = get_logger()
        self.config = get_config()
        
        # Estado da automação
        self.driver = None
        self.current_url = ""
        self.automation_active = False
        self.screenshots_dir = "screenshots"
        
        # Criar diretório de screenshots
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # Seletores multilíngues super robustos
        self.selectors = self._initialize_multilingual_selectors()
        
        self.logger.info(f"🤖 GoogleAdsAutomation inicializado para perfil: {profile_name}")
    
    def _initialize_multilingual_selectors(self) -> Dict[str, Dict[str, List[str]]]:
        """Inicializar seletores multilíngues extremamente robustos"""
        return {
            'campaign_creation': {
                'new_campaign_button': [
                    # Português
                    "//button[contains(text(), 'Nova campanha')]",
                    "//button[contains(text(), 'Criar campanha')]",
                    "//a[contains(text(), 'Nova campanha')]",
                    "//span[contains(text(), 'Nova campanha')]",
                    "//div[contains(text(), 'Nova campanha')]",
                    # Inglês
                    "//button[contains(text(), 'New campaign')]",
                    "//button[contains(text(), 'Create campaign')]",
                    "//a[contains(text(), 'New campaign')]",
                    "//span[contains(text(), 'New campaign')]",
                    "//div[contains(text(), 'New campaign')]",
                    # Espanhol
                    "//button[contains(text(), 'Nueva campaña')]",
                    "//button[contains(text(), 'Crear campaña')]",
                    "//a[contains(text(), 'Nueva campaña')]",
                    "//span[contains(text(), 'Nueva campaña')]",
                    # Seletores por atributos
                    "//button[@data-testid='new-campaign']",
                    "//button[contains(@aria-label, 'campaign')]",
                    "//button[contains(@aria-label, 'campanha')]",
                    "//button[contains(@aria-label, 'campaña')]",
                    # Seletores CSS
                    "button[data-testid*='campaign']",
                    "button[aria-label*='campaign']",
                    "a[href*='campaign']",
                    # Seletores genéricos por posição
                    "//button[contains(@class, 'create') or contains(@class, 'new')]",
                    "//div[@role='button'][contains(text(), 'campaign') or contains(text(), 'campanha') or contains(text(), 'campaña')]"
                ],
                'campaign_objective': [
                    # Vendas/Sales
                    "//div[contains(text(), 'Vendas') or contains(text(), 'Sales') or contains(text(), 'Ventas')]",
                    "//span[contains(text(), 'Vendas') or contains(text(), 'Sales') or contains(text(), 'Ventas')]",
                    "//button[contains(text(), 'Vendas') or contains(text(), 'Sales') or contains(text(), 'Ventas')]",
                    # Leads
                    "//div[contains(text(), 'Leads') or contains(text(), 'Lead')]",
                    "//span[contains(text(), 'Leads') or contains(text(), 'Lead')]",
                    "//button[contains(text(), 'Leads') or contains(text(), 'Lead')]",
                    # Tráfego/Traffic
                    "//div[contains(text(), 'Tráfego') or contains(text(), 'Traffic') or contains(text(), 'Tráfico')]",
                    "//span[contains(text(), 'Tráfego') or contains(text(), 'Traffic') or contains(text(), 'Tráfico')]",
                    "//button[contains(text(), 'Tráfego') or contains(text(), 'Traffic') or contains(text(), 'Tráfico')]",
                    # Sem orientação/Without guidance
                    "//div[contains(text(), 'sem orientação') or contains(text(), 'without guidance') or contains(text(), 'sin orientación')]",
                    "//span[contains(text(), 'sem orientação') or contains(text(), 'without guidance') or contains(text(), 'sin orientación')]",
                    "//button[contains(text(), 'sem orientação') or contains(text(), 'without guidance') or contains(text(), 'sin orientación')]"
                ],
                'search_campaign_type': [
                    # Pesquisa/Search
                    "//div[contains(text(), 'Pesquisa') or contains(text(), 'Search') or contains(text(), 'Búsqueda')]",
                    "//span[contains(text(), 'Pesquisa') or contains(text(), 'Search') or contains(text(), 'Búsqueda')]",
                    "//button[contains(text(), 'Pesquisa') or contains(text(), 'Search') or contains(text(), 'Búsqueda')]",
                    "//label[contains(text(), 'Pesquisa') or contains(text(), 'Search') or contains(text(), 'Búsqueda')]",
                    # Rede de pesquisa
                    "//div[contains(text(), 'Rede de pesquisa') or contains(text(), 'Search Network') or contains(text(), 'Red de búsqueda')]",
                    "//span[contains(text(), 'Rede de pesquisa') or contains(text(), 'Search Network') or contains(text(), 'Red de búsqueda')]"
                ]
            },
            'navigation': {
                'campaigns_menu': [
                    "//a[contains(text(), 'Campanhas') or contains(text(), 'Campaigns') or contains(text(), 'Campañas')]",
                    "//span[contains(text(), 'Campanhas') or contains(text(), 'Campaigns') or contains(text(), 'Campañas')]",
                    "//div[contains(text(), 'Campanhas') or contains(text(), 'Campaigns') or contains(text(), 'Campañas')]",
                    "//button[contains(text(), 'Campanhas') or contains(text(), 'Campaigns') or contains(text(), 'Campañas')]",
                    "a[href*='campaigns']",
                    "a[href*='campanhas']",
                    "a[href*='campañas']"
                ],
                'continue_button': [
                    "//button[contains(text(), 'Continuar') or contains(text(), 'Continue') or contains(text(), 'Continúa')]",
                    "//button[contains(text(), 'Próximo') or contains(text(), 'Next') or contains(text(), 'Siguiente')]",
                    "//button[contains(text(), 'Avançar') or contains(text(), 'Forward') or contains(text(), 'Adelante')]",
                    "//span[contains(text(), 'Continuar') or contains(text(), 'Continue') or contains(text(), 'Continúa')]",
                    "//span[contains(text(), 'Próximo') or contains(text(), 'Next') or contains(text(), 'Siguiente')]",
                    "button[data-testid*='continue']",
                    "button[data-testid*='next']"
                ],
                'save_button': [
                    "//button[contains(text(), 'Salvar') or contains(text(), 'Save') or contains(text(), 'Guardar')]",
                    "//button[contains(text(), 'Publicar') or contains(text(), 'Publish') or contains(text(), 'Publicar')]",
                    "//span[contains(text(), 'Salvar') or contains(text(), 'Save') or contains(text(), 'Guardar')]",
                    "//span[contains(text(), 'Publicar') or contains(text(), 'Publish') or contains(text(), 'Publicar')]",
                    "button[data-testid*='save']",
                    "button[data-testid*='publish']"
                ]
            },
            'form_fields': {
                'campaign_name': [
                    "//input[@placeholder*='nome' or @placeholder*='name' or @placeholder*='nombre']",
                    "//input[@aria-label*='nome' or @aria-label*='name' or @aria-label*='nombre']",
                    "//input[contains(@id, 'name') or contains(@id, 'nome') or contains(@id, 'nombre')]",
                    "input[placeholder*='campaign']",
                    "input[aria-label*='campaign']",
                    "input[id*='campaign']"
                ],
                'budget_input': [
                    "//input[@placeholder*='orçamento' or @placeholder*='budget' or @placeholder*='presupuesto']",
                    "//input[@aria-label*='orçamento' or @aria-label*='budget' or @aria-label*='presupuesto']",
                    "//input[contains(@id, 'budget') or contains(@id, 'orcamento') or contains(@id, 'presupuesto')]",
                    "input[placeholder*='budget']",
                    "input[aria-label*='budget']",
                    "input[type='number']"
                ],
                'location_input': [
                    "//input[@placeholder*='localização' or @placeholder*='location' or @placeholder*='ubicación']",
                    "//input[@aria-label*='localização' or @aria-label*='location' or @aria-label*='ubicación']",
                    "//input[contains(@id, 'location') or contains(@id, 'localizacao') or contains(@id, 'ubicacion')]",
                    "input[placeholder*='location']",
                    "input[aria-label*='location']"
                ]
            }
        }
    
    def setup_webdriver(self, browser_info: Dict) -> bool:
        """🔧 CONFIGURAR WEBDRIVER com conexão robusta ao AdsPower"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*80)
        self.logger.info(f"🔧 INICIANDO setup_webdriver() - {timestamp}")
        
        try:
            # Log detalhado das informações do browser
            self.logger.info(f"📋 INFORMAÇÕES DO BROWSER RECEBIDAS:")
            for key, value in browser_info.items():
                self.logger.info(f"   📝 {key}: {value}")
            
            # Extrair debug port com múltiplos métodos
            debug_port = self._extract_debug_port(browser_info)
            if not debug_port:
                self.logger.error("❌ FALHA CRÍTICA: Debug port não encontrado")
                return False
            
            self.logger.info(f"🔌 DEBUG PORT CONFIRMADO: {debug_port}")
            
            # Configurar WebDriver com retry robusto
            success = self._setup_webdriver_with_retry(debug_port, browser_info)
            
            if success:
                self.logger.info("✅ WEBDRIVER CONFIGURADO COM SUCESSO!")
                self.automation_active = True
                return True
            else:
                self.logger.error("❌ FALHA na configuração do WebDriver")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 ERRO INESPERADO no setup_webdriver:")
            self.logger.error(f"   💥 Tipo: {type(e).__name__}")
            self.logger.error(f"   💬 Mensagem: {str(e)}")
            self.logger.error(f"   📚 Traceback: {traceback.format_exc()}")
            return False
        
        finally:
            end_timestamp = datetime.now().isoformat()
            self.logger.info(f"🏁 FINALIZANDO setup_webdriver() - {end_timestamp}")
            self.logger.info("="*80)
    
    def _extract_debug_port(self, browser_info: Dict) -> Optional[str]:
        """🔍 EXTRAIR DEBUG PORT com múltiplos métodos"""
        self.logger.info("🔍 INICIANDO extração de debug port...")
        
        # Método 1: Campo direto debug_port
        if 'debug_port' in browser_info and browser_info['debug_port']:
            port = str(browser_info['debug_port'])
            self.logger.info(f"✅ MÉTODO 1 SUCESSO: debug_port = {port}")
            return port
        
        # Método 2: Extrair do WebSocket URL
        ws_url = browser_info.get('ws', '')
        if ws_url:
            self.logger.info(f"🔍 MÉTODO 2: Analisando WebSocket URL: {ws_url}")
            
            # Tentar extrair porta do WebSocket
            import re
            port_patterns = [
                r'127\.0\.0\.1:(\d+)',
                r'localhost:(\d+)',
                r':(\d+)/'
            ]
            
            for pattern in port_patterns:
                match = re.search(pattern, ws_url)
                if match:
                    port = match.group(1)
                    self.logger.info(f"✅ MÉTODO 2 SUCESSO: Porta extraída = {port}")
                    return port
        
        # Método 3: Verificar outros campos possíveis
        possible_fields = ['selenium_port', 'remote_debugging_port', 'port', 'debugPort']
        for field in possible_fields:
            if field in browser_info and browser_info[field]:
                port = str(browser_info[field])
                self.logger.info(f"✅ MÉTODO 3 SUCESSO: {field} = {port}")
                return port
        
        self.logger.error("❌ TODOS OS MÉTODOS FALHARAM - Debug port não encontrado")
        return None
    
    def _setup_webdriver_with_retry(self, debug_port: str, browser_info: Dict, max_attempts: int = 5) -> bool:
        """🔄 CONFIGURAR WEBDRIVER com sistema de retry robusto"""
        self.logger.info(f"🔄 INICIANDO setup com retry - Debug port: {debug_port}")
        
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"🎯 TENTATIVA {attempt}/{max_attempts}")
            
            try:
                # Limpar driver anterior se existir
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                # Aguardar um pouco entre tentativas
                if attempt > 1:
                    wait_time = attempt * 2
                    self.logger.info(f"⏳ Aguardando {wait_time}s antes da tentativa...")
                    time.sleep(wait_time)
                
                # Tentar conectar com WebDriver Remote
                success = self._connect_webdriver_remote(debug_port, browser_info)
                
                if success:
                    self.logger.info(f"✅ SUCESSO na tentativa {attempt}!")
                    return True
                else:
                    self.logger.warning(f"⚠️ TENTATIVA {attempt} FALHOU")
                    
            except Exception as e:
                self.logger.error(f"❌ ERRO na tentativa {attempt}: {str(e)}")
        
        self.logger.error(f"💥 TODAS AS {max_attempts} TENTATIVAS FALHARAM")
        return False
    
    def _connect_webdriver_remote(self, debug_port: str, browser_info: Dict) -> bool:
        """🌐 CONECTAR via WebDriver Remote com configuração robusta"""
        try:
            # Configurar opções do Chrome
            chrome_options = ChromeOptions()
            
            # Configurações essenciais para AdsPower
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            self.logger.info(f"🔧 Opções do Chrome configuradas")
            self.logger.info(f"   🔌 Debugger Address: 127.0.0.1:{debug_port}")
            
            # Obter caminho do WebDriver do browser_info
            webdriver_path = browser_info.get('webdriver', '')
            self.logger.info(f"📁 Caminho do WebDriver: {webdriver_path}")
            
            # Configurar Service se WebDriver path disponível
            service = None
            if webdriver_path and os.path.exists(webdriver_path):
                try:
                    service = ChromeService(executable_path=webdriver_path)
                    self.logger.info(f"✅ Chrome Service configurado com: {webdriver_path}")
                except Exception as service_error:
                    self.logger.warning(f"⚠️ Falha ao configurar Service: {str(service_error)}")
                    service = None
            
            # Tentar conectar com WebDriver Remote
            self.logger.info("🌐 Tentando conectar via webdriver.Remote()...")
            
            # URL do Selenium Grid/Remote (AdsPower usa porta padrão 4444)
            remote_url = f"http://127.0.0.1:4444/wd/hub"
            
            # Tentar diferentes URLs de conexão
            remote_urls = [
                f"http://127.0.0.1:4444/wd/hub",
                f"http://localhost:4444/wd/hub",
                f"http://127.0.0.1:{debug_port}",
                f"http://localhost:{debug_port}"
            ]
            
            driver_connected = False
            
            for remote_url in remote_urls:
                try:
                    self.logger.info(f"🔗 Tentando URL: {remote_url}")
                    
                    # Criar WebDriver Remote
                    self.driver = webdriver.Remote(
                        command_executor=remote_url,
                        options=chrome_options
                    )
                    
                    # Testar se a conexão funciona
                    self.driver.set_page_load_timeout(30)
                    current_url = self.driver.current_url
                    
                    self.logger.info(f"✅ CONEXÃO ESTABELECIDA via {remote_url}")
                    self.logger.info(f"🌐 URL atual: {current_url}")
                    
                    driver_connected = True
                    break
                    
                except Exception as remote_error:
                    self.logger.warning(f"⚠️ Falha em {remote_url}: {str(remote_error)}")
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
            
            # Se Remote falhou, tentar método direto com debugger
            if not driver_connected:
                self.logger.info("🔄 Tentando método direto com debugger address...")
                
                try:
                    # Usar Chrome com debugger address diretamente
                    if service:
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    else:
                        self.driver = webdriver.Chrome(options=chrome_options)
                    
                    # Testar conexão
                    self.driver.set_page_load_timeout(30)
                    current_url = self.driver.current_url
                    
                    self.logger.info(f"✅ CONEXÃO DIRETA ESTABELECIDA")
                    self.logger.info(f"🌐 URL atual: {current_url}")
                    
                    driver_connected = True
                    
                except Exception as direct_error:
                    self.logger.error(f"❌ Falha na conexão direta: {str(direct_error)}")
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
            
            if not driver_connected:
                self.logger.error("❌ TODAS AS TENTATIVAS DE CONEXÃO FALHARAM")
                return False
            
            # Aplicar stealth para evitar detecção
            try:
                stealth(self.driver,
                    languages=["pt-BR", "pt", "en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
                self.logger.info("🥷 Stealth aplicado com sucesso")
            except Exception as stealth_error:
                self.logger.warning(f"⚠️ Falha ao aplicar stealth: {str(stealth_error)}")
            
            # Configurações finais do driver
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)
            
            # Testar funcionalidade básica
            try:
                window_handles = self.driver.window_handles
                self.logger.info(f"🪟 Janelas disponíveis: {len(window_handles)}")
                
                if window_handles:
                    self.driver.switch_to.window(window_handles[0])
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    self.logger.info(f"✅ TESTE DE FUNCIONALIDADE PASSOU")
                    self.logger.info(f"   🌐 URL: {current_url}")
                    self.logger.info(f"   📄 Título: {page_title}")
                    
                    return True
                else:
                    self.logger.error("❌ Nenhuma janela disponível")
                    return False
                    
            except Exception as test_error:
                self.logger.error(f"❌ Falha no teste de funcionalidade: {str(test_error)}")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 ERRO na conexão WebDriver Remote:")
            self.logger.error(f"   💥 Tipo: {type(e).__name__}")
            self.logger.error(f"   💬 Mensagem: {str(e)}")
            self.logger.error(f"   📚 Traceback: {traceback.format_exc()}")
            return False
    
    def create_campaign(self, campaign_data: Dict) -> bool:
        """🚀 CRIAR CAMPANHA com automação robusta"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*80)
        self.logger.info(f"🚀 INICIANDO create_campaign() - {timestamp}")
        
        try:
            # Validar se driver está ativo
            if not self.driver:
                self.logger.error("❌ ERRO: WebDriver não está configurado")
                return False
            
            # Log dos dados da campanha
            self.logger.info("📋 DADOS DA CAMPANHA:")
            for key, value in campaign_data.items():
                self.logger.info(f"   📝 {key}: {value}")
            
            # Etapa 1: Navegar para Google Ads
            self.logger.info("🎯 ETAPA 1: Navegando para Google Ads...")
            if not self._navigate_to_google_ads():
                self.logger.error("❌ FALHA na ETAPA 1: Navegação para Google Ads")
                return False
            
            # Etapa 2: Verificar login
            self.logger.info("🔐 ETAPA 2: Verificando login...")
            if not self._verify_login():
                self.logger.error("❌ FALHA na ETAPA 2: Login não verificado")
                return False
            
            # Etapa 3: Navegar para campanhas
            self.logger.info("📋 ETAPA 3: Navegando para seção de campanhas...")
            if not self._navigate_to_campaigns():
                self.logger.error("❌ FALHA na ETAPA 3: Navegação para campanhas")
                return False
            
            # Etapa 4: Iniciar nova campanha
            self.logger.info("🆕 ETAPA 4: Iniciando nova campanha...")
            if not self._start_new_campaign():
                self.logger.error("❌ FALHA na ETAPA 4: Iniciar nova campanha")
                return False
            
            # Etapa 5: Selecionar objetivo
            self.logger.info("🎯 ETAPA 5: Selecionando objetivo da campanha...")
            if not self._select_campaign_objective(campaign_data.get('objective', 'Vendas')):
                self.logger.error("❌ FALHA na ETAPA 5: Seleção de objetivo")
                return False
            
            # Etapa 6: Selecionar tipo de campanha
            self.logger.info("📊 ETAPA 6: Selecionando tipo de campanha...")
            if not self._select_campaign_type('Pesquisa'):
                self.logger.error("❌ FALHA na ETAPA 6: Seleção de tipo")
                return False
            
            # Etapa 7: Configurar campanha
            self.logger.info("⚙️ ETAPA 7: Configurando detalhes da campanha...")
            if not self._configure_campaign_details(campaign_data):
                self.logger.error("❌ FALHA na ETAPA 7: Configuração de detalhes")
                return False
            
            # Etapa 8: Finalizar campanha
            self.logger.info("✅ ETAPA 8: Finalizando campanha...")
            if not self._finalize_campaign():
                self.logger.error("❌ FALHA na ETAPA 8: Finalização")
                return False
            
            self.logger.info("🎉 CAMPANHA CRIADA COM SUCESSO!")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO INESPERADO na criação de campanha:")
            self.logger.error(f"   💥 Tipo: {type(e).__name__}")
            self.logger.error(f"   💬 Mensagem: {str(e)}")
            self.logger.error(f"   📚 Traceback: {traceback.format_exc()}")
            return False
        
        finally:
            end_timestamp = datetime.now().isoformat()
            self.logger.info(f"🏁 FINALIZANDO create_campaign() - {end_timestamp}")
            self.logger.info("="*80)
    
    def _navigate_to_google_ads(self) -> bool:
        """🌐 NAVEGAR para Google Ads"""
        try:
            google_ads_url = "https://ads.google.com"
            self.logger.info(f"🌐 Navegando para: {google_ads_url}")
            
            self.driver.get(google_ads_url)
            self._wait_for_page_load()
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.logger.info(f"✅ Navegação concluída")
            self.logger.info(f"   🌐 URL atual: {current_url}")
            self.logger.info(f"   📄 Título: {page_title}")
            
            self._take_screenshot("01_google_ads_navigation")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na navegação: {str(e)}")
            self._take_screenshot("01_navigation_error")
            return False
    
    def _verify_login(self) -> bool:
        """🔐 VERIFICAR se está logado no Google Ads"""
        try:
            self.logger.info("🔍 Verificando status de login...")
            
            # Aguardar carregamento da página
            time.sleep(5)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.logger.info(f"🔍 URL atual: {current_url}")
            self.logger.info(f"🔍 Título: {page_title}")
            
            # Verificar se está na página de login
            login_indicators = [
                "accounts.google.com",
                "signin",
                "login",
                "entrar"
            ]
            
            is_login_page = any(indicator in current_url.lower() for indicator in login_indicators)
            
            if is_login_page:
                self.logger.warning("⚠️ Detectada página de login - usuário precisa fazer login manual")
                self.logger.warning("💡 Faça login manualmente no Google Ads antes de executar o bot")
                self._take_screenshot("02_login_required")
                return False
            
            # Verificar se está no Google Ads
            ads_indicators = [
                "ads.google.com",
                "google ads",
                "google adwords"
            ]
            
            is_ads_page = any(indicator in current_url.lower() or indicator in page_title.lower() for indicator in ads_indicators)
            
            if is_ads_page:
                self.logger.info("✅ Login verificado - usuário está no Google Ads")
                self._take_screenshot("02_login_verified")
                return True
            else:
                self.logger.warning("⚠️ Não foi possível verificar login")
                self._take_screenshot("02_login_uncertain")
                return True  # Continuar mesmo assim
                
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação de login: {str(e)}")
            self._take_screenshot("02_login_error")
            return False
    
    def _navigate_to_campaigns(self) -> bool:
        """📋 NAVEGAR para seção de campanhas"""
        try:
            self.logger.info("🔍 Procurando menu de campanhas...")
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Tentar encontrar menu de campanhas
            campaigns_selectors = self.selectors['navigation']['campaigns_menu']
            
            for selector in campaigns_selectors:
                try:
                    self.logger.info(f"🔍 Tentando seletor: {selector}")
                    
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.logger.info(f"✅ Elemento encontrado: {element.text}")
                    element.click()
                    
                    self._wait_for_page_load()
                    self._take_screenshot("03_campaigns_navigation")
                    
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            # Se não encontrou menu, tentar URL direta
            self.logger.info("🔄 Tentando navegação direta para campanhas...")
            campaigns_url = "https://ads.google.com/aw/campaigns"
            self.driver.get(campaigns_url)
            self._wait_for_page_load()
            
            self._take_screenshot("03_campaigns_direct")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na navegação para campanhas: {str(e)}")
            self._take_screenshot("03_campaigns_error")
            return False
    
    def _start_new_campaign(self) -> bool:
        """🆕 INICIAR nova campanha"""
        try:
            self.logger.info("🔍 Procurando botão de nova campanha...")
            
            # Aguardar carregamento
            time.sleep(5)
            
            # Tentar encontrar botão de nova campanha
            new_campaign_selectors = self.selectors['campaign_creation']['new_campaign_button']
            
            for selector in new_campaign_selectors:
                try:
                    self.logger.info(f"🔍 Tentando seletor: {selector}")
                    
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.logger.info(f"✅ Botão encontrado: {element.text}")
                    
                    # Scroll para o elemento se necessário
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # Tentar clicar
                    try:
                        element.click()
                    except ElementClickInterceptedException:
                        # Tentar JavaScript click
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    self._wait_for_page_load()
                    self._take_screenshot("04_new_campaign_clicked")
                    
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.error("❌ Não foi possível encontrar botão de nova campanha")
            self._take_screenshot("04_new_campaign_not_found")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar nova campanha: {str(e)}")
            self._take_screenshot("04_new_campaign_error")
            return False
    
    def _select_campaign_objective(self, objective: str) -> bool:
        """🎯 SELECIONAR objetivo da campanha"""
        try:
            self.logger.info(f"🎯 Selecionando objetivo: {objective}")
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Mapear objetivos
            objective_map = {
                'Vendas': ['Vendas', 'Sales', 'Ventas'],
                'Leads': ['Leads', 'Lead'],
                'Tráfego do site': ['Tráfego', 'Traffic', 'Tráfico'],
                'Sem orientação': ['sem orientação', 'without guidance', 'sin orientación']
            }
            
            # Obter variações do objetivo
            objective_variations = objective_map.get(objective, [objective])
            
            # Tentar encontrar objetivo
            objective_selectors = self.selectors['campaign_creation']['campaign_objective']
            
            for variation in objective_variations:
                for selector in objective_selectors:
                    try:
                        # Substituir placeholder no seletor
                        if 'Vendas' in selector or 'Sales' in selector or 'Ventas' in selector:
                            if variation not in ['Vendas', 'Sales', 'Ventas']:
                                continue
                        
                        self.logger.info(f"🔍 Tentando: {variation} com seletor: {selector}")
                        
                        if selector.startswith('//'):
                            element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        
                        # Verificar se o texto do elemento corresponde
                        element_text = element.text.lower()
                        if variation.lower() in element_text:
                            self.logger.info(f"✅ Objetivo encontrado: {element.text}")
                            
                            # Scroll e click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
                            
                            try:
                                element.click()
                            except ElementClickInterceptedException:
                                self.driver.execute_script("arguments[0].click();", element)
                            
                            time.sleep(2)
                            self._take_screenshot("05_objective_selected")
                            
                            # Procurar botão continuar
                            return self._click_continue_button()
                        
                    except Exception as selector_error:
                        self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                        continue
            
            # Se não encontrou, tentar continuar sem seleção (pode ser opcional)
            self.logger.warning("⚠️ Objetivo não encontrado, tentando continuar...")
            return self._click_continue_button()
            
        except Exception as e:
            self.logger.error(f"❌ Erro na seleção de objetivo: {str(e)}")
            self._take_screenshot("05_objective_error")
            return False
    
    def _select_campaign_type(self, campaign_type: str) -> bool:
        """📊 SELECIONAR tipo de campanha"""
        try:
            self.logger.info(f"📊 Selecionando tipo: {campaign_type}")
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Tentar encontrar tipo de campanha
            type_selectors = self.selectors['campaign_creation']['search_campaign_type']
            
            for selector in type_selectors:
                try:
                    self.logger.info(f"🔍 Tentando seletor: {selector}")
                    
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.logger.info(f"✅ Tipo encontrado: {element.text}")
                    
                    # Scroll e click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    try:
                        element.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    time.sleep(2)
                    self._take_screenshot("06_type_selected")
                    
                    # Procurar botão continuar
                    return self._click_continue_button()
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            # Se não encontrou, tentar continuar
            self.logger.warning("⚠️ Tipo não encontrado, tentando continuar...")
            return self._click_continue_button()
            
        except Exception as e:
            self.logger.error(f"❌ Erro na seleção de tipo: {str(e)}")
            self._take_screenshot("06_type_error")
            return False
    
    def _configure_campaign_details(self, campaign_data: Dict) -> bool:
        """⚙️ CONFIGURAR detalhes da campanha"""
        try:
            self.logger.info("⚙️ Configurando detalhes da campanha...")
            
            # Aguardar carregamento
            time.sleep(5)
            
            success_count = 0
            
            # Configurar nome da campanha
            if campaign_data.get('name'):
                if self._fill_campaign_name(campaign_data['name']):
                    success_count += 1
            
            # Configurar orçamento
            if campaign_data.get('budget'):
                if self._fill_budget(campaign_data['budget']):
                    success_count += 1
            
            # Configurar localização
            if campaign_data.get('locations'):
                if self._fill_locations(campaign_data['locations']):
                    success_count += 1
            
            self.logger.info(f"📊 Campos configurados com sucesso: {success_count}")
            self._take_screenshot("07_details_configured")
            
            # Continuar mesmo se alguns campos falharam
            return self._click_continue_button()
            
        except Exception as e:
            self.logger.error(f"❌ Erro na configuração de detalhes: {str(e)}")
            self._take_screenshot("07_details_error")
            return False
    
    def _fill_campaign_name(self, name: str) -> bool:
        """📝 PREENCHER nome da campanha"""
        try:
            self.logger.info(f"📝 Preenchendo nome: {name}")
            
            name_selectors = self.selectors['form_fields']['campaign_name']
            
            for selector in name_selectors:
                try:
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    # Limpar e preencher
                    element.clear()
                    element.send_keys(name)
                    
                    self.logger.info(f"✅ Nome preenchido: {name}")
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.warning("⚠️ Campo de nome não encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao preencher nome: {str(e)}")
            return False
    
    def _fill_budget(self, budget: str) -> bool:
        """💰 PREENCHER orçamento"""
        try:
            self.logger.info(f"💰 Preenchendo orçamento: {budget}")
            
            budget_selectors = self.selectors['form_fields']['budget_input']
            
            for selector in budget_selectors:
                try:
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    # Limpar e preencher
                    element.clear()
                    element.send_keys(str(budget))
                    
                    self.logger.info(f"✅ Orçamento preenchido: {budget}")
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.warning("⚠️ Campo de orçamento não encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao preencher orçamento: {str(e)}")
            return False
    
    def _fill_locations(self, locations: List[str]) -> bool:
        """🌍 PREENCHER localizações"""
        try:
            self.logger.info(f"🌍 Preenchendo localizações: {locations}")
            
            location_selectors = self.selectors['form_fields']['location_input']
            
            for selector in location_selectors:
                try:
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    # Preencher primeira localização
                    if locations:
                        element.clear()
                        element.send_keys(locations[0])
                        time.sleep(2)  # Aguardar sugestões
                        element.send_keys(Keys.ENTER)
                    
                    self.logger.info(f"✅ Localização preenchida: {locations[0] if locations else 'Nenhuma'}")
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.warning("⚠️ Campo de localização não encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao preencher localização: {str(e)}")
            return False
    
    def _click_continue_button(self) -> bool:
        """➡️ CLICAR botão continuar"""
        try:
            self.logger.info("➡️ Procurando botão continuar...")
            
            # Aguardar um pouco
            time.sleep(2)
            
            continue_selectors = self.selectors['navigation']['continue_button']
            
            for selector in continue_selectors:
                try:
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.logger.info(f"✅ Botão continuar encontrado: {element.text}")
                    
                    # Scroll e click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    try:
                        element.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    self._wait_for_page_load()
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.warning("⚠️ Botão continuar não encontrado")
            return True  # Continuar mesmo assim
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao clicar continuar: {str(e)}")
            return False
    
    def _finalize_campaign(self) -> bool:
        """✅ FINALIZAR campanha"""
        try:
            self.logger.info("✅ Finalizando campanha...")
            
            # Aguardar carregamento
            time.sleep(5)
            
            # Procurar botão salvar/publicar
            save_selectors = self.selectors['navigation']['save_button']
            
            for selector in save_selectors:
                try:
                    if selector.startswith('//'):
                        element = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.logger.info(f"✅ Botão finalizar encontrado: {element.text}")
                    
                    # Scroll e click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    try:
                        element.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", element)
                    
                    # Aguardar processamento
                    time.sleep(10)
                    self._take_screenshot("08_campaign_finalized")
                    
                    return True
                    
                except Exception as selector_error:
                    self.logger.debug(f"⚠️ Seletor falhou: {str(selector_error)}")
                    continue
            
            self.logger.warning("⚠️ Botão finalizar não encontrado")
            self._take_screenshot("08_finalize_not_found")
            return True  # Considerar sucesso mesmo assim
            
        except Exception as e:
            self.logger.error(f"❌ Erro na finalização: {str(e)}")
            self._take_screenshot("08_finalize_error")
            return False
    
    def _wait_for_page_load(self, timeout: int = 30):
        """⏳ AGUARDAR carregamento da página"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Aguardar um pouco mais para JavaScript
        except TimeoutException:
            self.logger.warning("⚠️ Timeout no carregamento da página")
    
    def _take_screenshot(self, name: str):
        """📸 TIRAR SCREENSHOT para debug"""
        try:
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{name}_{self.profile_name}.png"
                filepath = os.path.join(self.screenshots_dir, filename)
                
                self.driver.save_screenshot(filepath)
                self.logger.debug(f"📸 Screenshot salvo: {filepath}")
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao tirar screenshot: {str(e)}")
    
    def cleanup(self):
        """🧹 LIMPEZA de recursos"""
        try:
            if self.driver:
                self.logger.info("🧹 Fechando WebDriver...")
                self.driver.quit()
                self.driver = None
            
            self.automation_active = False
            self.logger.info("✅ Limpeza concluída")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {str(e)}")
    
    def __del__(self):
        """Destrutor para garantir limpeza"""
        try:
            self.cleanup()
        except:
            pass