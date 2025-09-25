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
        """Obter lista de perfis do AdsPower"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/user/list")
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                profiles = data.get('data', {}).get('list', [])
                self.logger.info(f"Encontrados {len(profiles)} perfis no AdsPower")
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
        """Iniciar browser para um perfil específico"""
        try:
            # Verificar se já existe um browser ativo para este perfil
            if user_id in self.active_browsers:
                self.logger.info(f"Browser já ativo para perfil {user_id}")
                return self.active_browsers[user_id]
            
            params = {
                'user_id': user_id,
                'open_tabs': 1
            }
            
            response = requests.get(f"{self.api_url}/api/v1/browser/start", params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                browser_info = data.get('data', {})
                self.active_browsers[user_id] = browser_info
                self.logger.info(f"Browser iniciado para perfil {user_id}")
                return browser_info
            else:
                self.logger.error(f"Erro ao iniciar browser: {data.get('msg', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao iniciar browser para perfil {user_id}: {str(e)}")
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