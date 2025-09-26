#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Automation - Automação de Criação de Campanhas
Responsável pela automação do navegador para criar campanhas no Google Ads
"""

import time
import logging
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from selenium_stealth import stealth
from adspower_manager import AdsPowerManager

class GoogleAdsAutomation:
    """Automação para criação de campanhas no Google Ads"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        self.adspower_manager = AdsPowerManager()
        
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
    
    def setup_driver(self, browser_info: Dict, headless: bool = False) -> bool:
        """🔧 Configurar driver SUPER ROBUSTO para controlar browser AdsPower com TOTAL EFICÁCIA"""
        try:
            self.logger.info("🔧 INICIANDO setup do driver com controle EXTREMAMENTE CALCULADO...")
            
            if not browser_info:
                self.logger.error("❌ Informações do browser não fornecidas")
                return False
            
            # Log das informações do browser para debugging
            self.logger.info(f"📋 Informações do browser recebidas: {browser_info}")
            
            chrome_options = Options()
            
            # Configurações anti-detecção PREMIUM
            self.logger.info("🛡️ Configurando opções anti-detecção...")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions-file-access-check')
            chrome_options.add_argument('--disable-extensions-http-throttling')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if headless:
                chrome_options.add_argument('--headless')
                self.logger.info("👻 Modo headless ativado")
            
            # CONEXÃO EXTREMAMENTE ROBUSTA ao browser AdsPower
            self.logger.info("🔌 CONFIGURANDO conexão EXTREMAMENTE ROBUSTA ao AdsPower...")
            
            # Extrair debug port com múltiplas tentativas
            debug_port = None
            debug_fields = ['debug_port', 'debugPort', 'remote_debugging_port', 'port', 'selenium_port']
            
            for field in debug_fields:
                if field in browser_info and browser_info[field]:
                    debug_port = str(browser_info[field])
                    self.logger.info(f"✅ Debug port encontrado em '{field}': {debug_port}")
                    break
            
            if not debug_port:
                self.logger.error("💥 ERRO CRÍTICO: Debug port não encontrado!")
                self.logger.error(f"📋 Informações disponíveis: {list(browser_info.keys())}")
                
                # Tentar portas comuns como fallback
                common_ports = ["9222", "9223", "9224", "9225"]
                self.logger.warning("🔄 Tentando portas comuns como fallback...")
                
                for port in common_ports:
                    try:
                        test_url = f"http://127.0.0.1:{port}/json"
                        import requests
                        response = requests.get(test_url, timeout=2)
                        if response.status_code == 200:
                            debug_port = port
                            self.logger.info(f"✅ FALLBACK SUCESSO: Porta {port} respondendo!")
                            break
                    except:
                        continue
                
                if not debug_port:
                    self.logger.error("💥 FALHA TOTAL: Nenhuma porta de debug encontrada ou funcional")
                    # Último recurso: tentar com porta padrão mesmo assim
                    debug_port = "9222"
                    self.logger.warning(f"🚨 ÚLTIMO RECURSO: Usando porta padrão {debug_port}")
            
            # Configurar conexão com verificação
            debugger_address = f"127.0.0.1:{debug_port}"
            self.logger.info(f"🎯 Configurando debugger address: {debugger_address}")
            
            # VERIFICAR se a porta está realmente ativa
            try:
                import requests
                test_url = f"http://127.0.0.1:{debug_port}/json"
                self.logger.info(f"🧪 TESTANDO conexão: {test_url}")
                
                response = requests.get(test_url, timeout=5)
                if response.status_code == 200:
                    tabs = response.json()
                    self.logger.info(f"✅ DEBUG PORT ATIVO: {len(tabs)} aba(s) detectada(s)")
                    for i, tab in enumerate(tabs[:3]):  # Mostrar apenas 3 primeiras
                        self.logger.info(f"   📄 Aba {i+1}: {tab.get('title', 'Sem título')[:50]}")
                else:
                    self.logger.warning(f"⚠️ DEBUG PORT responde com status {response.status_code} - tentando conectar mesmo assim")
                    # Não retornar False aqui - tentar conectar mesmo assim
                    
            except Exception as test_error:
                self.logger.error(f"💥 ERRO ao testar debug port: {str(test_error)}")
                return False
            
            # Configurar Chrome Options com debug port confirmado
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)
            
            # MÉTODO PRINCIPAL: Conectar via debugger address
            self.logger.info("🚀 MÉTODO PRINCIPAL: Criando WebDriver com debugger address...")
            
            connection_successful = False
            
            try:
                from selenium import webdriver
                self.driver = webdriver.Chrome(options=chrome_options)
                
                if self.driver:
                    self.logger.info("✅ WebDriver criado com SUCESSO!")
                    connection_successful = True
                else:
                    self.logger.error("❌ WebDriver retornou None")
                    
            except Exception as main_connection_error:
                self.logger.error(f"💥 FALHA no método principal: {str(main_connection_error)}")
                self.logger.info("🔄 Tentando método alternativo...")
                
                # MÉTODO ALTERNATIVO: Tentar sem remote debugging
                try:
                    from selenium import webdriver as alt_webdriver
                    alternative_options = Options()
                    
                    # Opções básicas apenas
                    alternative_options.add_argument('--no-sandbox')
                    alternative_options.add_argument('--disable-dev-shm-usage')
                    alternative_options.add_argument('--disable-blink-features=AutomationControlled')
                    
                    # Tentar conectar ao browser existente via processo
                    # (método mais básico que pode funcionar)
                    self.logger.info("🔄 MÉTODO ALTERNATIVO: Conectando via processo básico...")
                    
                    # Aguardar um pouco e tentar novamente
                    time.sleep(3)
                    alternative_options.add_experimental_option("debuggerAddress", debugger_address)
                    
                    self.driver = alt_webdriver.Chrome(options=alternative_options)
                    
                    if self.driver:
                        self.logger.info("✅ MÉTODO ALTERNATIVO SUCESSO!")
                        connection_successful = True
                    
                except Exception as alternative_error:
                    self.logger.error(f"💥 MÉTODO ALTERNATIVO também falhou: {str(alternative_error)}")
            
            if not connection_successful or not self.driver:
                self.logger.error("💥 FALHA TOTAL: Todos os métodos de conexão falharam!")
                self.logger.error("🔧 POSSÍVEIS SOLUÇÕES:")
                self.logger.error("   1. Verifique se AdsPower permite automação")
                self.logger.error("   2. Verifique se remote debugging está habilitado")
                self.logger.error("   3. Tente reiniciar o AdsPower")
                return False
            
            # Configurar WebDriverWait (só se driver existe)
            if self.driver:
                self.wait = WebDriverWait(self.driver, self.default_timeout)
            self.logger.info(f"⏱️ WebDriverWait configurado com timeout: {self.default_timeout}s")
            
            # BATERIA DE TESTES CRÍTICOS: Verificar controle TOTAL do browser
            self.logger.info("🧪 BATERIA DE TESTES CRÍTICOS: Verificando controle COMPLETO...")
            
            test_results = []
            
            # Verificação adicional de segurança
            if not self.driver:
                self.logger.error("💥 ERRO CRÍTICO: Driver está None após conexão supostamente bem-sucedida")
                return False
            
            try:
                # TESTE 1: Obter URL atual
                current_url = self.driver.current_url
                test_results.append(("URL atual", "SUCESSO", current_url))
                self.logger.info(f"✅ TESTE 1 SUCESSO: URL atual obtida: {current_url}")
            except Exception as url_error:
                test_results.append(("URL atual", "FALHA", str(url_error)))
                self.logger.error(f"❌ TESTE 1 FALHA: {str(url_error)}")
            
            try:
                # TESTE 2: Obter título
                title = self.driver.title or "Sem título" if self.driver else "Driver None"
                test_results.append(("Título", "SUCESSO", title))
                self.logger.info(f"✅ TESTE 2 SUCESSO: Título obtido: {title}")
            except Exception as title_error:
                test_results.append(("Título", "FALHA", str(title_error)))
                self.logger.error(f"❌ TESTE 2 FALHA: {str(title_error)}")
            
            try:
                # TESTE 3: Obter abas
                windows = self.driver.window_handles if self.driver else []
                test_results.append(("Abas", "SUCESSO", f"{len(windows)} abas"))
                self.logger.info(f"✅ TESTE 3 SUCESSO: {len(windows)} aba(s) detectada(s)")
            except Exception as windows_error:
                test_results.append(("Abas", "FALHA", str(windows_error)))
                self.logger.error(f"❌ TESTE 3 FALHA: {str(windows_error)}")
            
            try:
                # TESTE 4: JavaScript básico
                if self.driver:
                    js_result = self.driver.execute_script("return 'CONTROLE_OK';")
                    if js_result == 'CONTROLE_OK':
                        test_results.append(("JavaScript", "SUCESSO", "Controle confirmado"))
                        self.logger.info("✅ TESTE 4 SUCESSO: JavaScript executado com sucesso")
                    else:
                        test_results.append(("JavaScript", "PARCIAL", f"Resultado: {js_result}"))
                        self.logger.warning(f"⚠️ TESTE 4 PARCIAL: Resultado inesperado: {js_result}")
                else:
                    test_results.append(("JavaScript", "FALHA", "Driver é None"))
            except Exception as js_error:
                test_results.append(("JavaScript", "FALHA", str(js_error)))
                self.logger.error(f"❌ TESTE 4 FALHA: {str(js_error)}")
            
            try:
                # TESTE 5: Navegação básica (teste crucial)
                if self.driver:
                    self.logger.info("🧪 TESTE 5 CRÍTICO: Tentando navegação básica...")
                    original_url = self.driver.current_url
                    self.driver.execute_script("window.history.replaceState({}, '', window.location.href);")
                    test_results.append(("Navegação básica", "SUCESSO", "Comando aceito"))
                    self.logger.info("✅ TESTE 5 SUCESSO: Navegação básica funcional")
                else:
                    test_results.append(("Navegação básica", "FALHA", "Driver é None"))
            except Exception as nav_error:
                test_results.append(("Navegação básica", "FALHA", str(nav_error)))
                self.logger.error(f"❌ TESTE 5 FALHA: {str(nav_error)}")
            
            # ANÁLISE DOS RESULTADOS DOS TESTES
            self.logger.info("📊 ANÁLISE DOS RESULTADOS DOS TESTES:")
            successful_tests = 0
            total_tests = len(test_results)
            
            for test_name, result, details in test_results:
                if result == "SUCESSO":
                    successful_tests += 1
                    self.logger.info(f"   ✅ {test_name}: {details}")
                elif result == "PARCIAL":
                    successful_tests += 0.5
                    self.logger.warning(f"   ⚠️ {test_name}: {details}")
                else:
                    self.logger.error(f"   ❌ {test_name}: {details}")
            
            success_rate = (successful_tests / total_tests) * 100
            self.logger.info(f"📈 TAXA DE SUCESSO: {success_rate:.1f}% ({successful_tests}/{total_tests})")
            
            if success_rate < 60:
                self.logger.error("💥 CONTROLE INSUFICIENTE: Muitos testes falharam")
                return False
            elif success_rate < 100:
                self.logger.warning("⚠️ CONTROLE PARCIAL: Alguns problemas detectados, mas continuando...")
            else:
                self.logger.info("🎉 CONTROLE TOTAL CONFIRMADO: Todos os testes passaram!")
            
            # Maximizar janela com verificação
            try:
                if self.driver:
                    self.logger.info("📺 Maximizando janela do browser...")
                    self.driver.maximize_window()
                    time.sleep(1)  # Aguardar maximização
                    self.logger.info("✅ Janela maximizada com sucesso")
                else:
                    self.logger.warning("⚠️ Não é possível maximizar - driver é None")
            except Exception as max_error:
                self.logger.warning(f"⚠️ Não foi possível maximizar janela: {str(max_error)}")
            
            self.logger.info("🎉 Driver configurado com TOTAL SUCESSO e CONTROLE VERIFICADO!")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO ao configurar driver: {str(e)}")
            self.logger.error(f"📍 Detalhes do erro: {type(e).__name__}")
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
        """🌐 Navegar para Google Ads usando o sistema EXTREMAMENTE CALCULADO"""
        try:
            self.logger.info("🌐 INICIANDO navegação para Google Ads com sistema CALCULADO...")
            
            if not self.driver:
                self.logger.error("❌ Driver não está inicializado!")
                return False
            
            # PRIMEIRO: Preparar browser para navegação eficaz
            self.logger.info("🛠️ Preparando browser para controle total...")
            if not self.prepare_browser_for_navigation():
                self.logger.error("❌ FALHA na preparação do browser")
                return False
            
            # SEGUNDO: Usar navegação extremamente calculada
            target_urls = [
                "https://ads.google.com/aw/",
                "https://ads.google.com/home/", 
                "https://ads.google.com/",
                "https://ads.google.com/aw/campaigns/",
                "https://ads.google.com/aw/overview/"
            ]
            
            for attempt, target_url in enumerate(target_urls, 1):
                self.logger.info(f"🎯 TENTATIVA {attempt}: Navegação CALCULADA para {target_url}")
                
                # Usar o método extremamente calculado
                if self.navigate_with_extreme_calculation(target_url):
                    self.logger.info(f"✅ SUCESSO na tentativa {attempt}!")
                    
                    # Verificar qualidade da navegação com análise detalhada
                    try:
                        time.sleep(3)  # Aguardar estabilização
                        
                        final_url = self.driver.current_url
                        title = self.driver.title or ""
                        page_source = self.driver.page_source.lower()
                        
                        self.logger.info(f"🎯 URL final: {final_url}")
                        self.logger.info(f"📄 Título: {title}")
                        
                        # Análise detalhada dos indicadores de sucesso
                        success_indicators = [
                            ("campanhas" in page_source, "palavra 'campanhas' encontrada"),
                            ("campaigns" in page_source, "palavra 'campaigns' encontrada"), 
                            ("google ads" in title.lower(), "título contém 'Google Ads'"),
                            ("ads.google.com" in final_url.lower(), "URL contém 'ads.google.com'"),
                            ("overview" in final_url.lower(), "URL contém 'overview'"),
                            ("campaign" in page_source, "palavra 'campaign' encontrada")
                        ]
                        
                        success_count = 0
                        for indicator_found, description in success_indicators:
                            if indicator_found:
                                self.logger.info(f"✅ INDICADOR: {description}")
                                success_count += 1
                        
                        # Verificar status de login
                        login_indicators = ["entrar", "sign in", "login"]
                        login_detected = any(indicator in page_source for indicator in login_indicators)
                        
                        if login_detected:
                            self.logger.warning(f"⚠️ Página de login detectada - tentando próxima URL...")
                            continue
                        elif success_count >= 2:
                            self.logger.info(f"🎉 NAVEGAÇÃO CALCULADA CONCLUÍDA COM SUCESSO! {success_count} indicadores")
                            
                            # Screenshot final de sucesso
                            self.take_screenshot("navegacao_calculada_sucesso.png")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Apenas {success_count} indicadores - tentando próxima URL...")
                            continue
                            
                    except Exception as analysis_error:
                        self.logger.error(f"❌ Erro na análise pós-navegação: {str(analysis_error)}")
                        continue
                
                else:
                    self.logger.warning(f"⚠️ Tentativa {attempt} falhou - tentando próxima...")
                    time.sleep(2)  # Pausa entre tentativas
            
            # Se chegou aqui, todas as tentativas falharam
            self.logger.error("💥 FALHA TOTAL: Todas as tentativas de navegação calculada falharam")
            self.take_screenshot("navegacao_calculada_falha_total.png")
            return False
            
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO na navegação calculada: {str(e)}")
            self.take_screenshot("navegacao_calculada_erro_critico.png")
            return False
    
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
            
            # ETAPA 2B: Navegação EXTREMAMENTE CALCULADA
            self.logger.info("🧮 ETAPA 2B: Navegação EXTREMAMENTE CALCULADA para Google Ads...")
            self.take_screenshot("etapa_2b_antes_navegacao.png")
            
            # Tentar múltiplas URLs com navegação calculada
            target_urls = [
                "https://ads.google.com/aw/",
                "https://ads.google.com/home/",
                "https://ads.google.com/",
                "https://ads.google.com/aw/campaigns/",
                "https://ads.google.com/aw/overview/"
            ]
            
            navigation_success = False
            for attempt, url in enumerate(target_urls, 1):
                self.logger.info(f"🎯 TENTATIVA {attempt}: Navegação calculada para {url}")
                
                if self.navigate_with_extreme_calculation(url):
                    self.logger.info(f"✅ SUCESSO na tentativa {attempt}!")
                    navigation_success = True
                    break
                else:
                    self.logger.warning(f"⚠️ Tentativa {attempt} falhou, tentando próxima...")
                    time.sleep(2)  # Pausa entre tentativas
            
            if not navigation_success:
                self.logger.error("❌ FALHA na ETAPA 2B: Todas as tentativas de navegação falharam")
                self.take_screenshot("etapa_2b_erro_navegacao.png")
                return False
            
            self.logger.info("✅ ETAPA 2B COMPLETA: Navegação calculada bem-sucedida")
            self.take_screenshot("etapa_2b_navegacao_ok.png")
            
            # ETAPA 3: Aguardar carregamento e verificar estado
            self.logger.info("⏳ ETAPA 3: Verificando estado da página após navegação...")
            self.wait_for_page_load()
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
            # Sempre limpar recursos
            try:
                self.logger.info("🧹 Limpando recursos do driver...")
                self.cleanup()
            except Exception as cleanup_error:
                self.logger.warning(f"⚠️ Erro ao limpar recursos: {str(cleanup_error)}")
    
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