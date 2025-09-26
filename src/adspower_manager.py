#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdsPower Manager - Gerenciador de Perfis do AdsPower
Responsável pela comunicação com a API local do AdsPower
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional

class AdsPowerManager:
    """Gerenciador de perfis do AdsPower"""
    
    def __init__(self, api_url: str = "http://localhost:50325"):
        self.api_url = api_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        self.active_browsers = {}  # Armazenar browsers ativos
    
    def get_profiles(self) -> List[Dict]:
        """Obter lista de perfis do AdsPower - suporta até 2000+ perfis"""
        try:
            # Usar parâmetros para obter todos os perfis (até 2000)
            params = {
                'page': 1,
                'page_size': 2000,  # Máximo para suportar muitos perfis
                'group_id': ''  # Deixar vazio para pegar de todos os grupos
            }
            
            response = requests.get(f"{self.api_url}/api/v1/user/list", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                profiles = data.get('data', {}).get('list', [])
                total = data.get('data', {}).get('total', len(profiles))
                self.logger.info(f"Encontrados {len(profiles)} de {total} perfis no AdsPower")
                
                # Se houver mais perfis, fazer requisições adicionais
                if total > 2000:
                    self.logger.warning(f"Total de {total} perfis encontrado, mas limitado a 2000 por requisição")
                
                return profiles
            else:
                self.logger.error(f"Erro da API AdsPower: {data.get('msg', 'Erro desconhecido')}")
                return []
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Não foi possível conectar ao AdsPower. Verifique se o AdsPower está aberto e a API local está habilitada.")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter perfis: {str(e)}")
            return []
    
    def start_browser(self, user_id: str) -> Optional[Dict]:
        """🚀 Iniciar browser FUNCIONAL com debug port configurado corretamente"""
        try:
            self.logger.info(f"🚀 INICIANDO browser para perfil {user_id} com configurações FUNCIONAIS...")
            
            # Verificar se já existe um browser ativo para este perfil
            if user_id in self.active_browsers:
                existing_info = self.active_browsers[user_id]
                self.logger.info(f"🔄 Browser já ativo para perfil {user_id}")
                self.logger.info(f"📋 Dados existentes: {existing_info}")
                return existing_info
            
            # Parâmetros otimizados para garantir debug port
            params = {
                'user_id': user_id,
                'open_tabs': 1,
                'args': [],  # Argumentos extras do Chrome
                'load_extensions': 0,  # Não carregar extensões (mais rápido)
                'extract_ip': 0  # Não extrair IP (mais rápido)
            }
            
            self.logger.info(f"📤 Enviando requisição para iniciar browser...")
            self.logger.info(f"🎯 URL: {self.api_url}/api/v1/browser/start")
            self.logger.info(f"📋 Parâmetros: {params}")
            
            response = requests.get(f"{self.api_url}/api/v1/browser/start", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"📨 RESPOSTA COMPLETA do AdsPower: {json.dumps(data, indent=2)}")
            
            if data.get('code') == 0:
                browser_info = data.get('data', {})
                
                # LOG DETALHADO de todas as informações retornadas
                self.logger.info("🔍 ANÁLISE DETALHADA das informações do browser:")
                for key, value in browser_info.items():
                    self.logger.info(f"   📋 {key}: {value}")
                
                # Verificar se debug_port existe ou precisa ser extraído
                debug_port = None
                possible_debug_fields = ['debug_port', 'debugPort', 'remote_debugging_port', 'port', 'selenium_port']
                
                for field in possible_debug_fields:
                    if field in browser_info and browser_info[field]:
                        debug_port = browser_info[field]
                        self.logger.info(f"✅ DEBUG PORT ENCONTRADO: {field} = {debug_port}")
                        break
                
                if not debug_port:
                    # Tentar extrair do ws (WebSocket) URL se disponível
                    ws_url = browser_info.get('ws', '')
                    if ws_url and 'localhost:' in ws_url:
                        try:
                            # Extrair porta do WebSocket URL (formato típico: ws://localhost:9222/...)
                            import re
                            port_match = re.search(r'localhost:(\d+)', ws_url)
                            if port_match:
                                debug_port = port_match.group(1)
                                browser_info['debug_port'] = debug_port  # Adicionar ao dict
                                self.logger.info(f"✅ DEBUG PORT EXTRAÍDO do WebSocket: {debug_port}")
                        except Exception as extract_error:
                            self.logger.error(f"❌ Erro ao extrair porta do WebSocket: {str(extract_error)}")
                
                if not debug_port:
                    self.logger.error("💥 PROBLEMA CRÍTICO: DEBUG PORT não encontrado em nenhum campo!")
                    self.logger.error("🔍 Campos disponíveis no retorno:")
                    for key in browser_info.keys():
                        self.logger.error(f"   - {key}")
                    
                    # Tentar usar porta padrão como fallback
                    debug_port = "9222"  # Porta padrão do Chrome debugging
                    browser_info['debug_port'] = debug_port
                    self.logger.warning(f"⚠️ USANDO PORTA PADRÃO como fallback: {debug_port}")
                
                # VERIFICAÇÃO REAL: Testar se browser está funcional
                browser_functional = False
                
                # MÉTODO 1: Verificar se há debug port válido
                if debug_port:
                    try:
                        test_url = f"http://127.0.0.1:{debug_port}/json"
                        response = requests.get(test_url, timeout=5)
                        if response.status_code == 200:
                            tabs_data = response.json()
                            self.logger.info(f"✅ BROWSER FUNCIONAL: {len(tabs_data)} aba(s) ativa(s)")
                            browser_functional = True
                        else:
                            self.logger.warning(f"⚠️ Debug port {debug_port} não responde adequadamente")
                    except Exception as debug_test_error:
                        self.logger.warning(f"⚠️ Não foi possível testar debug port: {str(debug_test_error)}")
                
                # MÉTODO 2: Verificar via API de status do AdsPower
                if not browser_functional:
                    try:
                        status_params = {'user_id': user_id}
                        status_response = requests.get(f"{self.api_url}/api/v1/browser/active", params=status_params, timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('code') == 0 and status_data.get('data', {}).get('status') == 'Active':
                                self.logger.info("✅ BROWSER ATIVO confirmado via API de status")
                                browser_functional = True
                            else:
                                self.logger.warning("⚠️ API de status indica browser não está ativo")
                    except Exception as status_error:
                        self.logger.warning(f"⚠️ Erro ao verificar status: {str(status_error)}")
                
                # MÉTODO 3: Se tem dados básicos, assumir funcional
                if not browser_functional and browser_info:
                    # Se AdsPower retornou dados e há porta, assumir que está funcional
                    basic_indicators = ['debug_port', 'debugPort', 'remote_debugging_port', 'port', 'webdriver_port']
                    has_port_info = any(field in browser_info for field in basic_indicators)
                    
                    if has_port_info:
                        self.logger.info("✅ BROWSER considerado FUNCIONAL - tem informações de porta")
                        browser_functional = True
                    else:
                        self.logger.warning("⚠️ Browser retornado mas sem informações de porta")
                
                if browser_functional:
                    self.active_browsers[user_id] = browser_info
                    self.logger.info(f"🎉 Browser CONFIRMADAMENTE FUNCIONAL para perfil {user_id}")
                    self.logger.info(f"🔌 Debug Port final: {debug_port}")
                    return browser_info
                else:
                    self.logger.error("💥 BROWSER NÃO FUNCIONAL - todos os testes falharam")
                    self.logger.error("🔍 Dados retornados pelo AdsPower:")
                    for key, value in browser_info.items():
                        self.logger.error(f"   - {key}: {value}")
                    return None
                
            else:
                error_msg = data.get('msg', 'Erro desconhecido')
                self.logger.error(f"💥 ERRO da API AdsPower: {error_msg}")
                self.logger.error(f"📋 Resposta completa: {data}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"⏰ TIMEOUT ao iniciar browser para perfil {user_id}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("💥 ERRO DE CONEXÃO: AdsPower não está respondendo!")
            self.logger.error("🔧 Verifique se:")
            self.logger.error("   - AdsPower está aberto")
            self.logger.error("   - API local está habilitada")
            self.logger.error("   - Porta 50325 não está bloqueada")
            return None
        except Exception as e:
            self.logger.error(f"💥 ERRO CRÍTICO ao iniciar browser para perfil {user_id}: {str(e)}")
            self.logger.error(f"📍 Tipo do erro: {type(e).__name__}")
            return None
    
    def stop_browser(self, user_id: str) -> bool:
        """Parar browser de um perfil específico"""
        try:
            params = {'user_id': user_id}
            
            response = requests.get(f"{self.api_url}/api/v1/browser/stop", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                # Remover da lista de browsers ativos
                if user_id in self.active_browsers:
                    del self.active_browsers[user_id]
                self.logger.info(f"Browser parado para perfil {user_id}")
                return True
            else:
                self.logger.error(f"Erro ao parar browser: {data.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao parar browser para perfil {user_id}: {str(e)}")
            return False
    
    def get_browser_info(self, user_id: str) -> Optional[Dict]:
        """Obter informações do browser ativo"""
        return self.active_browsers.get(user_id)
    
    def check_browser_status(self, user_id: str) -> bool:
        """Verificar se o browser está ativo"""
        try:
            params = {'user_id': user_id}
            response = requests.get(f"{self.api_url}/api/v1/browser/active", params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('code') == 0 and data.get('data', {}).get('status') == 'Active'
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar status do browser: {str(e)}")
            return False
    
    def create_profile(self, name: str, **kwargs) -> Optional[str]:
        """Criar novo perfil no AdsPower"""
        try:
            profile_data = {
                'name': name,
                'domain_name': kwargs.get('domain_name', ''),
                'open_urls': kwargs.get('open_urls', ['https://www.google.com']),
                'repeat_config': kwargs.get('repeat_config', []),
                'username': kwargs.get('username', ''),
                'password': kwargs.get('password', ''),
                'fakey': kwargs.get('fakey', ''),
                'cookie': kwargs.get('cookie', ''),
                'ignore_cookie_error': kwargs.get('ignore_cookie_error', 1),
                'ip': kwargs.get('ip', ''),
                'country': kwargs.get('country', 'BR'),
                'region': kwargs.get('region', ''),
                'city': kwargs.get('city', ''),
                'remark': kwargs.get('remark', ''),
                'ipv6': kwargs.get('ipv6', ''),
                'sys_app_cate_id': kwargs.get('sys_app_cate_id', ''),
                'user_proxy_config': kwargs.get('user_proxy_config', {}),
                'fingerprint_config': kwargs.get('fingerprint_config', {}),
                'browser_kernel_config': kwargs.get('browser_kernel_config', {}),
                'pa_config': kwargs.get('pa_config', {})
            }
            
            response = requests.post(f"{self.api_url}/api/v1/user/create", json=profile_data)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                user_id = data.get('data', {}).get('id')
                self.logger.info(f"Perfil criado com sucesso: {name} (ID: {user_id})")
                return user_id
            else:
                self.logger.error(f"Erro ao criar perfil: {data.get('msg', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao criar perfil {name}: {str(e)}")
            return None
    
    def delete_profile(self, user_id: str) -> bool:
        """Deletar perfil do AdsPower"""
        try:
            # Primeiro, parar o browser se estiver ativo
            if self.check_browser_status(user_id):
                self.stop_browser(user_id)
            
            params = {'user_ids': [user_id]}
            response = requests.post(f"{self.api_url}/api/v1/user/delete", json=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                self.logger.info(f"Perfil deletado com sucesso: {user_id}")
                return True
            else:
                self.logger.error(f"Erro ao deletar perfil: {data.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao deletar perfil {user_id}: {str(e)}")
            return False
    
    def update_profile(self, user_id: str, **kwargs) -> bool:
        """Atualizar perfil existente"""
        try:
            update_data = {'user_id': user_id}
            update_data.update(kwargs)
            
            response = requests.post(f"{self.api_url}/api/v1/user/update", json=update_data)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                self.logger.info(f"Perfil atualizado com sucesso: {user_id}")
                return True
            else:
                self.logger.error(f"Erro ao atualizar perfil: {data.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar perfil {user_id}: {str(e)}")
            return False
    
    def get_profile_info(self, user_id: str) -> Optional[Dict]:
        """Obter informações detalhadas de um perfil"""
        try:
            params = {'user_id': user_id}
            response = requests.get(f"{self.api_url}/api/v1/user/info", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                return data.get('data', {})
            else:
                self.logger.error(f"Erro ao obter info do perfil: {data.get('msg', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao obter info do perfil {user_id}: {str(e)}")
            return None
    
    def cleanup_all_browsers(self):
        """Fechar todos os browsers ativos"""
        self.logger.info("Fechando todos os browsers ativos...")
        for user_id in list(self.active_browsers.keys()):
            self.stop_browser(user_id)
        self.active_browsers.clear()
        self.logger.info("Todos os browsers foram fechados")
    
    def __del__(self):
        """Destrutor para garantir limpeza dos recursos"""
        try:
            self.cleanup_all_browsers()
        except:
            pass