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
        
        # Seletores CSS/XPath para elementos do Google Ads
        self.selectors = {
            'new_campaign_btn': "//button[contains(text(), 'Nova campanha')] | //button[contains(text(), 'New campaign')]",
            'campaign_objective': "//div[contains(@class, 'campaign-objective')]",
            'campaign_type_search': "//div[contains(text(), 'Pesquisa')] | //div[contains(text(), 'Search')]",
            'campaign_name_input': "input[data-test-id='campaign-name-input']",
            'budget_input': "input[data-test-id='budget-input']",
            'location_input': "input[data-test-id='location-input']",
            'keyword_input': "input[data-test-id='keyword-input']",
            'ad_headline_input': "input[data-test-id='headline-input']",
            'ad_description_input': "textarea[data-test-id='description-input']",
            'final_url_input': "input[data-test-id='final-url-input']",
            'save_continue_btn': "//button[contains(text(), 'Salvar e continuar')] | //button[contains(text(), 'Save and continue')]",
            'publish_btn': "//button[contains(text(), 'Publicar')] | //button[contains(text(), 'Publish')]"
        }
    
    def setup_driver(self, browser_info: Dict, headless: bool = False) -> bool:
        """Configurar driver do Selenium com informações do browser AdsPower"""
        try:
            if not browser_info:
                self.logger.error("Informações do browser não fornecidas")
                return False
            
            chrome_options = Options()
            
            # Configurações anti-detecção
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # Conectar ao browser AdsPower existente via debug port
            debug_port = browser_info.get('debug_port')
            if not debug_port:
                self.logger.error("Porta de debug não encontrada nas informações do browser")
                return False
            
            # Conectar ao browser existente via debugger address
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            
            # Usar webdriver regular para conectar ao browser existente
            from selenium import webdriver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Configurar WebDriverWait
            if self.driver:
                self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            # Maximizar janela
            self.driver.maximize_window()
            
            self.logger.info("Driver configurado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar driver: {str(e)}")
            return False
    
    def navigate_to_google_ads(self) -> bool:
        """Navegar para o Google Ads"""
        try:
            # URL correta do Google Ads conforme especificado
            if self.driver:
                self.driver.get("https://ads.google.com/aw/")
            time.sleep(self.default_delay)
            
            # Verificar se chegou na página correta
            if self.wait:
                self.wait.until(lambda d: "ads.google.com" in d.current_url.lower())
            
            # Fechar popups que podem aparecer
            self.close_popups()
            
            self.logger.info("Navegou para Google Ads com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Google Ads: {str(e)}")
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
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Aguardar carregamento da página"""
        if timeout is None:
            timeout = self.default_timeout
        
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
        """Criar campanha passo a passo"""
        try:
            self.logger.info("Iniciando criação de campanha...")
            
            # Passo 1: Clicar em "Nova Campanha"
            if not self.click_element_safe(self.selectors['new_campaign_btn']):
                # Tentar seletores alternativos
                alternative_selectors = [
                    "//button[contains(@class, 'new-campaign')]",
                    "//a[contains(text(), 'Nova campanha')]",
                    "//button[contains(@aria-label, 'Nova campanha')]"
                ]
                
                success = False
                for alt_selector in alternative_selectors:
                    if self.click_element_safe(alt_selector):
                        success = True
                        break
                
                if not success:
                    self.logger.error("Não foi possível encontrar botão 'Nova Campanha'")
                    return False
            
            self.wait_for_page_load()
            
            # Passo 2: Selecionar objetivo da campanha (se necessário)
            # Muitas vezes o Google Ads pede para selecionar um objetivo primeiro
            try:
                # Procurar por objetivos comuns
                objectives = [
                    "//div[contains(text(), 'Vendas')]",
                    "//div[contains(text(), 'Leads')]", 
                    "//div[contains(text(), 'Tráfego do website')]",
                    "//button[contains(text(), 'Criar campanha sem orientação de objetivo')]"
                ]
                
                for obj_selector in objectives:
                    if self.click_element_safe(obj_selector):
                        break
                        
                self.wait_for_page_load()
            except:
                pass  # Nem sempre é necessário
            
            # Passo 3: Selecionar tipo de campanha (Pesquisa)
            if not self.click_element_safe(self.selectors['campaign_type_search']):
                # Seletores alternativos para campanha de pesquisa
                search_selectors = [
                    "//div[contains(@class, 'campaign-type')]//div[contains(text(), 'Pesquisa')]",
                    "//button[contains(text(), 'Pesquisa')]",
                    "//div[contains(text(), 'Search')]"
                ]
                
                for search_sel in search_selectors:
                    if self.click_element_safe(search_sel):
                        break
            
            self.wait_for_page_load()
            
            # Passo 4: Usar novo fluxo oficial
            return self.create_campaign_google_ads_official_flow(config)
            
        except Exception as e:
            self.logger.error(f"Erro na criação da campanha: {str(e)}")
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
        """PASSO 1-2: Clicar em Campanhas no menu lateral e no botão (+) Nova campanha"""
        try:
            self.logger.info("📋 PASSO 1-2: Navegando para seção Campanhas...")
            
            # Primeiro, clicar no menu Campanhas (se necessário)
            campaigns_menu_selectors = [
                "//span[contains(text(), 'Campanhas')]",
                "//a[contains(text(), 'Campanhas')]",
                "//div[contains(@data-value, 'campaigns')]",
                "//button[contains(@aria-label, 'Campanhas')]"
            ]
            
            for selector in campaigns_menu_selectors:
                if self.click_element_safe(selector):
                    self.logger.info("✅ Clicou na seção Campanhas")
                    break
            
            time.sleep(2)
            
            # Clicar no botão de adição (+) para Nova campanha
            new_campaign_selectors = [
                "//button[contains(@aria-label, 'Nova campanha')] | //button[contains(@aria-label, 'New campaign')]",
                "//button[contains(text(), '+')]",
                "//button[contains(@data-value, 'new-campaign')]",
                "//div[contains(@class, 'create-button')]//button",
                "//button[contains(@class, 'mdc-fab')]",
                "//button[contains(@class, 'create')]"
            ]
            
            for selector in new_campaign_selectors:
                if self.click_element_safe(selector):
                    self.logger.info("✅ Clicou no botão (+) Nova campanha")
                    self.wait_for_page_load()
                    return True
            
            self.logger.error("❌ Não foi possível encontrar botão Nova Campanha")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 1-2: {str(e)}")
            return False
    
    def step_3_choose_campaign_objective(self, config: Dict) -> bool:
        """PASSO 3: Escolher o objetivo da campanha - PRIORIZAR 'sem orientação de objetivo' conforme instrução"""
        try:
            self.logger.info("🎯 PASSO 3: Escolhendo objetivo da campanha (priorizando sem orientação)...")
            
            # PRIORIDADE: Criar campanha sem orientação de objetivo (conforme instrução do usuário)
            priority_selectors = [
                "//button[contains(text(), 'Criar campanha sem orientação de objetivo')] | //button[contains(text(), 'Create campaign without goal guidance')]",
                "//div[contains(text(), 'sem orientação')] | //div[contains(text(), 'without goal')]",
                "//a[contains(text(), 'sem orientação')] | //a[contains(text(), 'without goal')]"
            ]
            
            # Primeiro tentar a opção sem orientação
            for selector in priority_selectors:
                if self.click_element_safe(selector):
                    self.logger.info("✅ Campanha sem orientação de objetivo selecionada (PRIORIDADE)")
                    self.wait_for_page_load()
                    return True
            
            # Se não encontrar a opção sem orientação, usar objetivos tradicionais como fallback
            fallback_selectors = [
                "//div[contains(text(), 'Vendas')] | //div[contains(text(), 'Sales')]",
                "//div[contains(text(), 'Leads')] | //div[contains(text(), 'Leads')]", 
                "//div[contains(text(), 'Tráfego do website')] | //div[contains(text(), 'Website traffic')]"
            ]
            
            for selector in fallback_selectors:
                if self.click_element_safe(selector):
                    self.logger.info("✅ Objetivo da campanha selecionado (fallback)")
                    self.wait_for_page_load()
                    return True
            
            # Se nenhum objetivo foi encontrado, continuar (talvez não seja necessário)
            self.logger.info("ℹ️ Nenhum objetivo específico encontrado, continuando...")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 3: {str(e)}")
            return False
    
    def step_4_select_search_network(self) -> bool:
        """PASSO 4: Selecionar o tipo de campanha 'Rede de Pesquisa'"""
        try:
            self.logger.info("🔍 PASSO 4: Selecionando Rede de Pesquisa...")
            
            search_network_selectors = [
                "//div[contains(text(), 'Pesquisa')] | //div[contains(text(), 'Search')]",
                "//button[contains(text(), 'Pesquisa')] | //button[contains(text(), 'Search')]",
                "//div[contains(@class, 'campaign-type')]//div[contains(text(), 'Pesquisa')]",
                "//div[contains(@data-value, 'search')]"
            ]
            
            for selector in search_network_selectors:
                if self.click_element_safe(selector):
                    self.logger.info("✅ Rede de Pesquisa selecionada")
                    self.wait_for_page_load()
                    return True
            
            self.logger.error("❌ Não foi possível selecionar Rede de Pesquisa")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 4: {str(e)}")
            return False
    
    def step_5_define_campaign_name(self, config: Dict) -> bool:
        """PASSO 5: Definir nome descritivo da campanha - PULA se não estiver preenchido"""
        try:
            self.logger.info("📝 PASSO 5: Definindo nome da campanha...")
            
            campaign_name = config.get('campaign_name', '').strip()
            
            # SE NÃO ESTIVER PREENCHIDO, PULAR (conforme instrução)
            if not campaign_name:
                self.logger.info("⚠️ Nome da campanha não preenchido - PULANDO PASSO 5")
                return True  # Continua mesmo sem preencher
            
            name_selectors = [
                "//input[contains(@aria-label, 'nome')] | //input[contains(@aria-label, 'name')]",
                "//input[contains(@placeholder, 'nome')] | //input[contains(@placeholder, 'name')]",
                "//input[contains(@id, 'campaign-name')]",
                "//input[contains(@data-testid, 'campaign-name')]"
            ]
            
            for selector in name_selectors:
                if self.input_text_safe(selector, campaign_name, "xpath"):
                    self.logger.info(f"✅ Nome da campanha definido: {campaign_name}")
                    return True
            
            self.logger.warning("⚠️ Não foi possível inserir nome da campanha, mas continuando...")
            return True  # Não falha, apenas continua
            
        except Exception as e:
            self.logger.error(f"Erro no PASSO 5: {str(e)}")
            return True  # Continua mesmo com erro
    
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
            
            # 6.4: Configurar orçamento diário - PULA se não preenchido
            budget = config.get('budget', '').strip()
            if budget:  # Só configura se estiver preenchido
                budget_selectors = [
                    "//input[contains(@aria-label, 'orçamento')] | //input[contains(@aria-label, 'budget')]",
                    "//input[contains(@placeholder, 'orçamento')] | //input[contains(@placeholder, 'budget')]",
                    "//input[@type='number'][contains(@name, 'budget')]"
                ]
                
                for selector in budget_selectors:
                    if self.input_text_safe(selector, budget, "xpath"):
                        self.logger.info(f"✅ Orçamento definido: R$ {budget}")
                        break
            else:
                self.logger.info("⚠️ Orçamento não preenchido - PULANDO configuração de orçamento")
            
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
            
            # 8.1: URL final - PULA se não preenchido (conforme instrução)
            landing_url = config.get('landing_url', '').strip()
            if landing_url:
                url_selectors = [
                    "//input[contains(@aria-label, 'URL')] | //input[contains(@aria-label, 'url')]",
                    "//input[contains(@placeholder, 'URL')] | //input[contains(@placeholder, 'url')]",
                    "//input[contains(@name, 'final-url')]"
                ]
                
                for selector in url_selectors:
                    if self.input_text_safe(selector, landing_url, "xpath"):
                        self.logger.info(f"✅ URL final definida: {landing_url}")
                        break
            else:
                self.logger.info("⚠️ URL final não preenchida - PULANDO configuração de URL")
            
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
        """Configurar detalhes específicos da campanha"""
        try:
            # Nome da campanha
            if config.get('campaign_name'):
                name_selectors = [
                    self.selectors['campaign_name_input'],
                    "input[placeholder*='nome']",
                    "input[placeholder*='name']",
                    "//input[contains(@aria-label, 'nome')]"
                ]
                
                for name_sel in name_selectors:
                    if self.input_text_safe(name_sel, config['campaign_name']):
                        break
            
            # Orçamento
            if config.get('budget'):
                budget_selectors = [
                    self.selectors['budget_input'],
                    "input[placeholder*='orçamento']",
                    "input[placeholder*='budget']",
                    "//input[contains(@aria-label, 'orçamento')]"
                ]
                
                for budget_sel in budget_selectors:
                    if self.input_text_safe(budget_sel, config['budget']):
                        break
            
            # Localização
            if config.get('location'):
                location_selectors = [
                    self.selectors['location_input'],
                    "input[placeholder*='localização']",
                    "input[placeholder*='location']",
                    "//input[contains(@aria-label, 'local')]"
                ]
                
                for loc_sel in location_selectors:
                    if self.input_text_safe(loc_sel, config['location']):
                        time.sleep(2)
                        # Pressionar Enter ou clicar na primeira sugestão
                        try:
                            suggestion = self.driver.find_element(By.XPATH, "//div[contains(@class, 'suggestion')]")
                            suggestion.click()
                        except:
                            pass
                        break
            
            # Continuar para próxima etapa
            if self.click_element_safe(self.selectors['save_continue_btn']):
                self.wait_for_page_load()
                return self.configure_ad_groups_and_keywords(config)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar detalhes da campanha: {str(e)}")
            return False
    
    def configure_ad_groups_and_keywords(self, config: Dict) -> bool:
        """Configurar grupos de anúncios e palavras-chave"""
        try:
            # Adicionar palavras-chave
            keywords = config.get('keywords', [])
            if keywords:
                keyword_selectors = [
                    self.selectors['keyword_input'],
                    "textarea[placeholder*='palavra']",
                    "textarea[placeholder*='keyword']",
                    "//textarea[contains(@aria-label, 'palavra')]"
                ]
                
                keywords_text = '\n'.join(keywords)
                
                for kw_sel in keyword_selectors:
                    if self.input_text_safe(kw_sel, keywords_text):
                        break
            
            # Continuar para anúncios
            if self.click_element_safe(self.selectors['save_continue_btn']):
                self.wait_for_page_load()
                return self.configure_ads(config)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar palavras-chave: {str(e)}")
            return False
    
    def configure_ads(self, config: Dict) -> bool:
        """Configurar anúncios"""
        try:
            # Título do anúncio
            if config.get('ad_title'):
                title_selectors = [
                    self.selectors['ad_headline_input'],
                    "input[placeholder*='título']",
                    "input[placeholder*='headline']",
                    "//input[contains(@aria-label, 'título')]"
                ]
                
                for title_sel in title_selectors:
                    if self.input_text_safe(title_sel, config['ad_title']):
                        break
            
            # Descrição do anúncio
            if config.get('ad_description'):
                desc_selectors = [
                    self.selectors['ad_description_input'],
                    "textarea[placeholder*='descrição']",
                    "textarea[placeholder*='description']",
                    "//textarea[contains(@aria-label, 'descrição')]"
                ]
                
                for desc_sel in desc_selectors:
                    if self.input_text_safe(desc_sel, config['ad_description']):
                        break
            
            # URL de destino
            if config.get('landing_url'):
                url_selectors = [
                    self.selectors['final_url_input'],
                    "input[placeholder*='URL']",
                    "input[placeholder*='url']",
                    "//input[contains(@aria-label, 'URL')]"
                ]
                
                for url_sel in url_selectors:
                    if self.input_text_safe(url_sel, config['landing_url']):
                        break
            
            # Publicar campanha
            if self.click_element_safe(self.selectors['publish_btn']):
                self.wait_for_page_load()
                self.logger.info("Campanha publicada com sucesso!")
                return True
            
            # Se não encontrar botão publicar, tentar salvar e continuar
            if self.click_element_safe(self.selectors['save_continue_btn']):
                self.wait_for_page_load()
                # Tentar publicar novamente
                if self.click_element_safe(self.selectors['publish_btn']):
                    self.logger.info("Campanha publicada com sucesso!")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar anúncios: {str(e)}")
            return False
    
    def create_campaign_with_browser(self, profile: Dict, config: Dict, browser_info: Dict) -> bool:
        """Função principal para criar campanha usando browser AdsPower já iniciado"""
        try:
            # Configurar driver do Selenium para conectar ao browser existente
            headless = config.get('headless', False)
            if not self.setup_driver(browser_info, headless):
                return False
            
            # Navegar para Google Ads
            if not self.navigate_to_google_ads():
                return False
            
            # Aguardar página carregar completamente
            self.wait_for_page_load()
            
            # Criar campanha passo a passo
            success = self.create_campaign_step_by_step(config)
            
            if success:
                self.logger.info(f"✅ Campanha '{config.get('campaign_name', 'Sem nome')}' criada com sucesso no perfil {profile['name']}")
            else:
                self.logger.error(f"❌ Falha ao criar campanha no perfil {profile['name']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro geral ao criar campanha no perfil {profile['name']}: {str(e)}")
            return False
            
        finally:
            # Limpar recursos do driver (mas não fechar browser do AdsPower)
            self.cleanup()
    
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
    
    def take_screenshot(self, filename: str = None) -> str:
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