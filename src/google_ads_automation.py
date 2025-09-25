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
            self.driver.get("https://ads.google.com")
            time.sleep(self.default_delay)
            
            # Verificar se chegou na página correta
            self.wait.until(lambda d: "ads.google.com" in d.current_url.lower())
            
            self.logger.info("Navegou para Google Ads com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Google Ads: {str(e)}")
            return False
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Aguardar carregamento da página"""
        if timeout is None:
            timeout = self.default_timeout
        
        try:
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
            
            # Passo 4: Configurar detalhes da campanha
            return self.configure_campaign_details(config)
            
        except Exception as e:
            self.logger.error(f"Erro na criação da campanha: {str(e)}")
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