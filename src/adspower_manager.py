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
from typing import List, Dict, Optional, Any
from datetime import datetime
import traceback
import sys
from retry_system import (
    RetryManager, RetryConfig, CircuitBreaker, HealthChecker,
    create_adspower_retry_manager, RetryExhaustedException, CircuitOpenException
)

class AdsPowerManager:
    """Gerenciador de perfis do AdsPower com sistema de retry extremamente robusto"""
    
    def __init__(self, api_url: str = "http://localhost:50325", enable_advanced_retry: bool = True):
        self.base_url = api_url.rstrip('/')  # Corrigir nome da variável
        self.logger = logging.getLogger(__name__)
        self.active_browsers = {}  # Armazenar browsers ativos
        self.enable_advanced_retry = enable_advanced_retry
        
        # Sistema de retry robusto
        if self.enable_advanced_retry:
            self.retry_manager = create_adspower_retry_manager(api_url, self.logger)
            self.logger.info("🚀 Sistema de retry avançado ATIVADO")
        else:
            self.retry_manager = None
            self.logger.info("⚠️ Sistema de retry avançado DESATIVADO - usando retry básico")
        
        # Log de inicialização extremamente detalhado
        self._log_initialization(api_url)
    
    def _log_initialization(self, api_url: str) -> None:
        """🔍 LOG DETALHADO de inicialização do AdsPowerManager"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*80)
        self.logger.info(f"🚀 INICIALIZANDO AdsPowerManager - {timestamp}")
        self.logger.info(f"📋 URL da API configurada: {api_url}")
        self.logger.info(f"🔧 URL base processada: {self.base_url}")
        self.logger.info(f"💾 Cache de browsers ativos inicializado: {self.active_browsers}")
        self.logger.info(f"🔍 Logger configurado: {self.logger.name}")
        self.logger.info(f"🌐 Testando conectividade com AdsPower...")
        
        # Teste inicial de conectividade com retry robusto
        if self.enable_advanced_retry and self.retry_manager:
            try:
                self.logger.info("🔄 Testando conectividade com sistema de retry robusto...")
                self._test_connectivity_with_retry()
            except Exception as conn_error:
                self.logger.error(f"❌ Teste de conectividade com retry falhou: {str(conn_error)}")
        else:
            # Teste básico sem retry
            try:
                test_response = requests.get(f"{self.base_url}/status", timeout=5)
                if test_response.status_code == 200:
                    self.logger.info("✅ CONECTIVIDADE OK: AdsPower respondendo")
                else:
                    self.logger.warning(f"⚠️ Status HTTP inesperado: {test_response.status_code}")
            except Exception as conn_error:
                self.logger.warning(f"⚠️ Teste de conectividade falhou: {str(conn_error)}")
        
        self.logger.info("="*80)
    
    def _test_connectivity_with_retry(self):
        """🧪 Testar conectividade usando sistema de retry robusto"""
        def test_connection():
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ CONECTIVIDADE ROBUSTA OK: AdsPower respondendo")
                return True
            else:
                raise requests.HTTPError(f"Status HTTP inesperado: {response.status_code}")
        
        try:
            self.retry_manager.execute_with_retry(test_connection)
        except Exception as e:
            self.logger.error(f"❌ Falha na conectividade mesmo com retry robusto: {str(e)}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """📊 Obter status completo do sistema de retry"""
        if self.retry_manager:
            return self.retry_manager.get_system_status()
        else:
            return {
                'retry_manager': {'enabled': False, 'message': 'Sistema de retry básico'},
                'circuit_breaker': {'enabled': False},
                'health_checker': {'enabled': False}
            }
    
    def cleanup(self):
        """🧹 Limpeza de recursos do sistema de retry"""
        if self.retry_manager:
            self.retry_manager.cleanup()
            self.logger.info("🧹 Recursos do RetryManager limpos")
    
    def get_profiles(self) -> List[Dict]:
        """🔍 OBTER LISTA DE PERFIS com sistema de retry extremamente robusto"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*60)
        self.logger.info(f"📋 INICIANDO get_profiles() COM RETRY ROBUSTO - {timestamp}")
        
        if self.enable_advanced_retry and self.retry_manager:
            # Usar sistema de retry avançado
            try:
                return self.retry_manager.execute_with_retry(self._get_profiles_internal)
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL no get_profiles após retry robusto: {str(e)}")
                return []
            except Exception as e:
                self.logger.error(f"❌ ERRO INESPERADO no get_profiles: {str(e)}")
                return []
        else:
            # Fallback para método original
            return self._get_profiles_internal()
    
    def _get_profiles_internal(self) -> List[Dict]:
        """📋 Método interno para obter perfis (usado pelo retry manager)"""
        try:
            # Log detalhado dos parâmetros
            params = {
                'page': 1,
                'page_size': 2000,  # Máximo para suportar muitos perfis
                'group_id': ''  # Deixar vazio para pegar de todos os grupos
            }
            
            url = f"{self.base_url}/api/v1/user/list"
            self.logger.debug(f"🌐 URL de requisição: {url}")
            self.logger.debug(f"📋 Parâmetros da requisição: {json.dumps(params, indent=2)}")
            
            # Log da tentativa de conexão
            self.logger.debug(f"🔄 Enviando requisição GET para AdsPower...")
            request_start = time.time()
            
            response = requests.get(url, params=params, timeout=30)
            
            request_duration = time.time() - request_start
            self.logger.info(f"⏱️ Tempo de resposta: {request_duration:.3f}s")
            self.logger.info(f"📊 Status HTTP: {response.status_code}")
            self.logger.info(f"📏 Tamanho da resposta: {len(response.content)} bytes")
            self.logger.info(f"🏷️ Headers da resposta: {dict(response.headers)}")
            
            # Verificar status HTTP
            response.raise_for_status()
            
            # Log do conteúdo da resposta
            try:
                data = response.json()
                self.logger.info(f"✅ JSON parseado com sucesso")
                self.logger.info(f"📋 Estrutura da resposta: {list(data.keys())}")
                self.logger.info(f"📊 Resposta completa: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}...")
            except json.JSONDecodeError as json_error:
                self.logger.error(f"❌ ERRO ao parsear JSON: {str(json_error)}")
                self.logger.error(f"📄 Resposta bruta: {response.text[:500]}...")
                return []
            
            # Análise detalhada da resposta
            api_code = data.get('code')
            api_message = data.get('msg', 'Sem mensagem')
            self.logger.info(f"🔍 Código da API: {api_code}")
            self.logger.info(f"💬 Mensagem da API: {api_message}")
            
            if api_code == 0:
                # Sucesso - extrair dados dos perfis
                data_section = data.get('data', {})
                profiles = data_section.get('list', [])
                total = data_section.get('total', len(profiles))
                
                self.logger.info(f"✅ SUCESSO na obtenção de perfis!")
                self.logger.info(f"📊 Total de perfis no sistema: {total}")
                self.logger.info(f"📋 Perfis retornados nesta requisição: {len(profiles)}")
                
                # Log detalhado de cada perfil
                if profiles:
                    self.logger.info(f"🔍 ANÁLISE DETALHADA DOS PERFIS:")
                    for i, profile in enumerate(profiles[:5]):  # Log apenas os primeiros 5 para não sobrecarregar
                        self.logger.info(f"   📋 Perfil {i+1}: {json.dumps(profile, indent=4, ensure_ascii=False)}")
                    
                    if len(profiles) > 5:
                        self.logger.info(f"   ... e mais {len(profiles) - 5} perfis (logs resumidos)")
                    
                    # Análise dos campos disponíveis nos perfis
                    if profiles:
                        sample_profile = profiles[0]
                        profile_fields = list(sample_profile.keys())
                        self.logger.info(f"🔧 Campos disponíveis nos perfis: {profile_fields}")
                        
                        # Verificar campos críticos
                        critical_fields = ['user_id', 'name', 'group_id', 'domain_name']
                        for field in critical_fields:
                            if field in sample_profile:
                                self.logger.info(f"   ✅ Campo crítico presente: {field} = {sample_profile[field]}")
                            else:
                                self.logger.warning(f"   ⚠️ Campo crítico ausente: {field}")
                
                # Verificar se há mais perfis
                if total > 2000:
                    self.logger.warning(f"⚠️ ATENÇÃO: Total de {total} perfis encontrado, mas limitado a 2000 por requisição")
                    self.logger.warning(f"💡 Considere implementar paginação para obter todos os perfis")
                
                self.logger.info(f"📋 RETORNANDO {len(profiles)} perfis para processamento")
                return profiles
                
            else:
                # Erro da API
                self.logger.error(f"❌ ERRO DA API AdsPower:")
                self.logger.error(f"   📊 Código: {api_code}")
                self.logger.error(f"   💬 Mensagem: {api_message}")
                self.logger.error(f"   📋 Dados completos: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return []
                
        except requests.exceptions.ConnectionError as conn_error:
            self.logger.error(f"❌ ERRO DE CONEXÃO com AdsPower:")
            self.logger.error(f"   💥 Erro: {str(conn_error)}")
            self.logger.error(f"   🌐 URL tentada: {self.base_url}")
            self.logger.error(f"   🔧 Verificações necessárias:")
            self.logger.error(f"      1. AdsPower está aberto?")
            self.logger.error(f"      2. API local está habilitada?")
            self.logger.error(f"      3. Porta 50325 está disponível?")
            self.logger.error(f"      4. Firewall bloqueando conexão?")
            return []
            
        except requests.exceptions.Timeout as timeout_error:
            self.logger.error(f"❌ TIMEOUT na requisição para AdsPower:")
            self.logger.error(f"   ⏱️ Erro: {str(timeout_error)}")
            self.logger.error(f"   🔧 AdsPower pode estar sobrecarregado ou lento")
            return []
            
        except requests.exceptions.HTTPError as http_error:
            self.logger.error(f"❌ ERRO HTTP da API AdsPower:")
            self.logger.error(f"   📊 Status: {http_error.response.status_code if http_error.response else 'Unknown'}")
            self.logger.error(f"   💬 Erro: {str(http_error)}")
            if http_error.response:
                self.logger.error(f"   📄 Resposta: {http_error.response.text[:500]}")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ ERRO INESPERADO ao obter perfis:")
            self.logger.error(f"   💥 Tipo do erro: {type(e).__name__}")
            self.logger.error(f"   💬 Mensagem: {str(e)}")
            self.logger.error(f"   📋 Traceback completo:")
            self.logger.error(traceback.format_exc())
            return []
        
        finally:
            end_timestamp = datetime.now().isoformat()
            self.logger.info(f"🏁 FINALIZANDO get_profiles() - {end_timestamp}")
            self.logger.info("="*60)
    
    def start_browser(self, user_id: str) -> Optional[Dict]:
        """🚀 INICIAR BROWSER com sistema de retry extremamente robusto"""
        timestamp = datetime.now().isoformat()
        self.logger.info("="*80)
        self.logger.info(f"🚀 INICIANDO start_browser() COM RETRY ROBUSTO para perfil {user_id} - {timestamp}")
        
        # Validações básicas antes do retry
        if not user_id or not str(user_id).strip():
            self.logger.error(f"❌ ERRO: user_id inválido ou vazio: '{user_id}'")
            return None
        
        # Verificar se já existe um browser ativo para este perfil
        self.logger.info(f"🔍 VERIFICANDO se browser já está ativo para perfil {user_id}...")
        if user_id in self.active_browsers:
            existing_info = self.active_browsers[user_id]
            self.logger.info(f"✅ BROWSER JÁ ATIVO encontrado para perfil {user_id}")
            
            # Validar se o browser ainda está funcional
            self.logger.info(f"🧪 VALIDANDO se browser existente ainda está funcional...")
            if self._validate_existing_browser(user_id, existing_info):
                self.logger.info(f"✅ BROWSER EXISTENTE VÁLIDO - retornando dados cached")
                return existing_info
            else:
                self.logger.warning(f"⚠️ BROWSER EXISTENTE INVÁLIDO - removendo do cache e iniciando novo")
                del self.active_browsers[user_id]
        else:
            self.logger.info(f"🆕 NENHUM BROWSER ATIVO encontrado para perfil {user_id} - iniciando novo browser")
        
        # Usar sistema de retry robusto
        if self.enable_advanced_retry and self.retry_manager:
            try:
                return self.retry_manager.execute_with_retry(self._start_browser_internal, user_id)
            except (RetryExhaustedException, CircuitOpenException) as e:
                self.logger.error(f"💀 FALHA TOTAL no start_browser após retry robusto: {str(e)}")
                return None
            except Exception as e:
                self.logger.error(f"❌ ERRO INESPERADO no start_browser: {str(e)}")
                return None
        else:
            # Fallback para método original
            return self._start_browser_internal(user_id)
    
    def _start_browser_internal(self, user_id: str) -> Optional[Dict]:
        """🚀 Método interno para iniciar browser (usado pelo retry manager)"""
        try:
            # LOG DETALHADO: Verificação de entrada
            self.logger.debug(f"📋 PARÂMETROS DE ENTRADA:")
            self.logger.debug(f"   📝 user_id: {user_id}")
            self.logger.debug(f"   🔍 Tipo do user_id: {type(user_id)}")
            self.logger.debug(f"   📊 Comprimento do user_id: {len(str(user_id))}")
            
            # LOG DETALHADO: Preparação dos parâmetros
            self.logger.info(f"⚙️ PREPARANDO parâmetros para iniciar browser...")
            params = {
                'user_id': user_id,
                'open_tabs': 1,
                'args': [],  # Argumentos extras do Chrome
                'load_extensions': 0,  # Não carregar extensões (mais rápido)
                'extract_ip': 0  # Não extrair IP (mais rápido)
            }
            
            url = f"{self.base_url}/api/v1/browser/start"
            self.logger.info(f"📤 CONFIGURAÇÃO DA REQUISIÇÃO:")
            self.logger.info(f"   🎯 URL completa: {url}")
            self.logger.info(f"   📋 Parâmetros completos: {json.dumps(params, indent=2)}")
            self.logger.info(f"   ⏱️ Timeout configurado: 30s")
            
            # LOG: Tentativa de requisição
            self.logger.info(f"🌐 ENVIANDO requisição GET para AdsPower...")
            request_start = time.time()
            
            response = requests.get(url, params=params, timeout=30)
            
            request_duration = time.time() - request_start
            self.logger.info(f"📨 RESPOSTA RECEBIDA:")
            self.logger.info(f"   ⏱️ Tempo de resposta: {request_duration:.3f}s")
            self.logger.info(f"   📊 Status HTTP: {response.status_code}")
            self.logger.info(f"   📏 Tamanho: {len(response.content)} bytes")
            self.logger.info(f"   🏷️ Headers: {dict(response.headers)}")
            
            # Verificar status HTTP
            response.raise_for_status()
            
            # Parsear JSON com logging detalhado
            try:
                data = response.json()
                self.logger.info(f"✅ JSON parseado com sucesso")
                self.logger.info(f"📨 RESPOSTA COMPLETA do AdsPower: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as json_error:
                self.logger.error(f"❌ ERRO ao parsear JSON da resposta:")
                self.logger.error(f"   💥 Erro: {str(json_error)}")
                self.logger.error(f"   📄 Resposta bruta: {response.text[:1000]}...")
                return None
            
            # Análise detalhada da resposta da API
            api_code = data.get('code')
            api_message = data.get('msg', 'Sem mensagem')
            
            self.logger.info(f"🔍 ANÁLISE DA RESPOSTA DA API:")
            self.logger.info(f"   📊 Código da API: {api_code}")
            self.logger.info(f"   💬 Mensagem da API: {api_message}")
            
            if api_code == 0:
                browser_info = data.get('data', {})
                
                self.logger.info(f"✅ SUCESSO - Browser iniciado com sucesso!")
                self.logger.info(f"🔍 ANÁLISE DETALHADA das informações do browser retornadas:")
                self.logger.info(f"   📊 Número de campos retornados: {len(browser_info)}")
                
                for key, value in browser_info.items():
                    self.logger.info(f"   📋 {key}: {value} (tipo: {type(value).__name__})")
                
                # Análise específica de campos críticos
                self.logger.info(f"🔍 ANÁLISE DE CAMPOS CRÍTICOS:")
                critical_fields = ['selenium_address', 'debug_port', 'webdriver', 'ws', 'user_id']
                for field in critical_fields:
                    if field in browser_info:
                        self.logger.info(f"   ✅ {field}: {browser_info[field]}")
                    else:
                        self.logger.warning(f"   ⚠️ {field}: AUSENTE")
                
                # PROCESSO DETALHADO: Extrair debug port
                self.logger.info(f"🔍 PROCESSO DE EXTRAÇÃO DO DEBUG PORT:")
                debug_port = None
                possible_debug_fields = ['debug_port', 'debugPort', 'remote_debugging_port', 'port', 'selenium_port']
                
                self.logger.info(f"   🔍 Verificando campos possíveis: {possible_debug_fields}")
                
                for field in possible_debug_fields:
                    field_value = browser_info.get(field)
                    self.logger.info(f"   🔍 Campo '{field}': {field_value} (presente: {field in browser_info})")
                    
                    if field in browser_info and browser_info[field]:
                        debug_port = str(browser_info[field])  # Garantir que seja string
                        self.logger.info(f"   ✅ DEBUG PORT ENCONTRADO no campo '{field}': {debug_port}")
                        break
                    else:
                        self.logger.info(f"   ❌ Campo '{field}' não utilizável")
                
                if not debug_port:
                    self.logger.warning(f"⚠️ DEBUG PORT não encontrado nos campos diretos")
                    
                    # MÉTODO ALTERNATIVO: Extrair do WebSocket URL
                    self.logger.info(f"🔍 TENTATIVA ALTERNATIVA: Extrair do WebSocket URL...")
                    ws_url = browser_info.get('ws', '')
                    self.logger.info(f"   🌐 WebSocket URL disponível: '{ws_url}'")
                    
                    if ws_url and 'localhost:' in ws_url:
                        try:
                            import re
                            self.logger.info(f"   🔍 Aplicando regex para extrair porta...")
                            port_match = re.search(r'localhost:(\d+)', ws_url)
                            
                            if port_match:
                                debug_port = port_match.group(1)
                                browser_info['debug_port'] = debug_port  # Adicionar ao dict
                                self.logger.info(f"   ✅ DEBUG PORT EXTRAÍDO do WebSocket: {debug_port}")
                            else:
                                self.logger.warning(f"   ⚠️ Regex não encontrou porta no WebSocket URL")
                                
                        except Exception as extract_error:
                            self.logger.error(f"   ❌ Erro ao extrair porta do WebSocket:")
                            self.logger.error(f"      💥 Erro: {str(extract_error)}")
                            self.logger.error(f"      📊 Tipo: {type(extract_error).__name__}")
                    else:
                        self.logger.warning(f"   ⚠️ WebSocket URL não utilizável para extração")
                
                if not debug_port:
                    self.logger.error(f"💥 PROBLEMA CRÍTICO: DEBUG PORT não encontrado em nenhum método!")
                    self.logger.error(f"🔍 RESUMO DOS CAMPOS DISPONÍVEIS NO RETORNO:")
                    for key in sorted(browser_info.keys()):
                        self.logger.error(f"   - {key}: {browser_info[key]}")
                    
                    # FALLBACK: Tentar usar porta padrão
                    self.logger.warning(f"🔄 APLICANDO FALLBACK: Tentando porta padrão do Chrome...")
                    debug_port = "9222"  # Porta padrão do Chrome debugging
                    browser_info['debug_port'] = debug_port
                    self.logger.warning(f"   ⚠️ USANDO PORTA PADRÃO como fallback: {debug_port}")
                    self.logger.warning(f"   ⚠️ ESTA PODE NÃO SER A PORTA CORRETA!")
                
                # VERIFICAÇÃO FUNCIONAL COMPLETA
                self.logger.info(f"🧪 INICIANDO BATERIA DE TESTES DE FUNCIONALIDADE:")
                browser_functional = False
                test_results = []
                
                # TESTE 1: Verificar debug port via Chrome DevTools Protocol
                if debug_port:
                    self.logger.info(f"🧪 TESTE 1: Verificando debug port {debug_port} via Chrome DevTools...")
                    try:
                        test_url = f"http://127.0.0.1:{debug_port}/json"
                        self.logger.info(f"   🌐 URL de teste: {test_url}")
                        
                        test_start = time.time()
                        response = requests.get(test_url, timeout=5)
                        test_duration = time.time() - test_start
                        
                        self.logger.info(f"   ⏱️ Tempo de resposta: {test_duration:.3f}s")
                        self.logger.info(f"   📊 Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            tabs_data = response.json()
                            self.logger.info(f"   ✅ TESTE 1 SUCESSO: {len(tabs_data)} aba(s) ativa(s)")
                            self.logger.info(f"   📋 Dados das abas: {json.dumps(tabs_data[:2], indent=2)}...")  # Primeiras 2 abas
                            browser_functional = True
                            test_results.append(("Chrome DevTools", "SUCESSO", f"{len(tabs_data)} abas"))
                        else:
                            self.logger.warning(f"   ⚠️ TESTE 1 FALHA: Status {response.status_code}")
                            test_results.append(("Chrome DevTools", "FALHA", f"Status {response.status_code}"))
                            
                    except Exception as debug_test_error:
                        self.logger.error(f"   ❌ TESTE 1 ERRO: {str(debug_test_error)}")
                        self.logger.error(f"      💥 Tipo: {type(debug_test_error).__name__}")
                        test_results.append(("Chrome DevTools", "ERRO", str(debug_test_error)))
                else:
                    self.logger.error(f"   ❌ TESTE 1 PULADO: Debug port não disponível")
                    test_results.append(("Chrome DevTools", "PULADO", "Debug port ausente"))
                
                # TESTE 2: Verificar via API de status do AdsPower
                self.logger.info(f"🧪 TESTE 2: Verificando status via API do AdsPower...")
                try:
                    status_params = {'user_id': user_id}
                    status_url = f"{self.base_url}/api/v1/browser/active"
                    
                    self.logger.info(f"   🌐 URL de status: {status_url}")
                    self.logger.info(f"   📋 Parâmetros: {status_params}")
                    
                    test_start = time.time()
                    status_response = requests.get(status_url, params=status_params, timeout=10)
                    test_duration = time.time() - test_start
                    
                    self.logger.info(f"   ⏱️ Tempo de resposta: {test_duration:.3f}s")
                    self.logger.info(f"   📊 Status HTTP: {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        self.logger.info(f"   📨 Resposta da API: {json.dumps(status_data, indent=2)}")
                        
                        api_code = status_data.get('code')
                        browser_status = status_data.get('data', {}).get('status')
                        
                        if api_code == 0 and browser_status == 'Active':
                            self.logger.info(f"   ✅ TESTE 2 SUCESSO: Browser confirmado ativo via API")
                            browser_functional = True
                            test_results.append(("API Status", "SUCESSO", "Browser ativo"))
                        else:
                            self.logger.warning(f"   ⚠️ TESTE 2 FALHA: API code={api_code}, status={browser_status}")
                            test_results.append(("API Status", "FALHA", f"code={api_code}, status={browser_status}"))
                    else:
                        self.logger.warning(f"   ⚠️ TESTE 2 FALHA: Status HTTP {status_response.status_code}")
                        test_results.append(("API Status", "FALHA", f"HTTP {status_response.status_code}"))
                        
                except Exception as status_error:
                    self.logger.error(f"   ❌ TESTE 2 ERRO: {str(status_error)}")
                    self.logger.error(f"      💥 Tipo: {type(status_error).__name__}")
                    test_results.append(("API Status", "ERRO", str(status_error)))
                
                # TESTE 3: Verificar versão do Chrome via debug port
                if debug_port:
                    self.logger.info(f"🧪 TESTE 3: Verificando versão do Chrome via debug port...")
                    try:
                        version_url = f"http://127.0.0.1:{debug_port}/json/version"
                        self.logger.info(f"   🌐 URL de versão: {version_url}")
                        
                        test_start = time.time()
                        version_response = requests.get(version_url, timeout=3)
                        test_duration = time.time() - test_start
                        
                        self.logger.info(f"   ⏱️ Tempo de resposta: {test_duration:.3f}s")
                        self.logger.info(f"   📊 Status: {version_response.status_code}")
                        
                        if version_response.status_code == 200:
                            version_data = version_response.json()
                            chrome_version = version_data.get('Browser', 'Desconhecida')
                            user_agent = version_data.get('User-Agent', 'Desconhecido')
                            
                            self.logger.info(f"   ✅ TESTE 3 SUCESSO: Chrome funcional")
                            self.logger.info(f"      🌐 Versão: {chrome_version}")
                            self.logger.info(f"      👤 User Agent: {user_agent[:100]}...")
                            
                            browser_functional = True
                            test_results.append(("Chrome Version", "SUCESSO", chrome_version))
                        else:
                            self.logger.warning(f"   ⚠️ TESTE 3 FALHA: Status {version_response.status_code}")
                            test_results.append(("Chrome Version", "FALHA", f"Status {version_response.status_code}"))
                            
                    except Exception as version_error:
                        self.logger.error(f"   ❌ TESTE 3 ERRO: {str(version_error)}")
                        self.logger.error(f"      💥 Tipo: {type(version_error).__name__}")
                        test_results.append(("Chrome Version", "ERRO", str(version_error)))
                
                # RESUMO DOS TESTES
                self.logger.info(f"📊 RESUMO DOS TESTES DE FUNCIONALIDADE:")
                successful_tests = 0
                total_tests = len(test_results)
                
                for test_name, result, details in test_results:
                    if result == "SUCESSO":
                        successful_tests += 1
                        self.logger.info(f"   ✅ {test_name}: {details}")
                    elif result == "FALHA":
                        self.logger.warning(f"   ⚠️ {test_name}: {details}")
                    elif result == "ERRO":
                        self.logger.error(f"   ❌ {test_name}: {details}")
                    else:
                        self.logger.info(f"   ⏭️ {test_name}: {details}")
                
                success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
                self.logger.info(f"📈 TAXA DE SUCESSO: {success_rate:.1f}% ({successful_tests}/{total_tests})")
                
                # Decisão final sobre funcionalidade
                if not browser_functional:
                    self.logger.error(f"💥 FALHA DEFINITIVA: Browser não passou em nenhum teste de funcionalidade")
                    self.logger.error(f"🔍 DADOS COMPLETOS DO BROWSER para debug:")
                    for key, value in browser_info.items():
                        self.logger.error(f"   📋 {key}: {value}")
                    return None
                
                # RESULTADO FINAL
                if browser_functional:
                    # Sucesso - armazenar no cache e retornar
                    self.active_browsers[user_id] = browser_info
                    
                    self.logger.info(f"🎉 BROWSER TOTALMENTE FUNCIONAL para perfil {user_id}!")
                    self.logger.info(f"💾 Browser armazenado no cache de browsers ativos")
                    self.logger.info(f"🔌 Debug Port final confirmado: {debug_port}")
                    self.logger.info(f"📊 Taxa de sucesso dos testes: {success_rate:.1f}%")
                    
                    return browser_info
                else:
                    self.logger.error(f"💥 BROWSER NÃO FUNCIONAL - falhou em todos os testes")
                    self.logger.error(f"📊 Taxa de sucesso: {success_rate:.1f}% (insuficiente)")
                    return None
                
            else:
                # Erro da API
                error_msg = data.get('msg', 'Erro desconhecido')
                self.logger.error(f"💥 ERRO DA API AdsPower ao iniciar browser:")
                self.logger.error(f"   📊 Código da API: {api_code}")
                self.logger.error(f"   💬 Mensagem: {error_msg}")
                self.logger.error(f"   📋 Resposta completa: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Análise específica de erros comuns
                if api_code == 10001:
                    self.logger.error(f"   🔍 ERRO ESPECÍFICO: Perfil não encontrado")
                elif api_code == 10002:
                    self.logger.error(f"   🔍 ERRO ESPECÍFICO: Browser já em execução")
                elif api_code == 10003:
                    self.logger.error(f"   🔍 ERRO ESPECÍFICO: Limite de browsers atingido")
                else:
                    self.logger.error(f"   🔍 ERRO DESCONHECIDO: Verificar documentação da API")
                
                return None
                
        except requests.exceptions.Timeout as timeout_error:
            self.logger.error(f"⏰ TIMEOUT ao iniciar browser para perfil {user_id}:")
            self.logger.error(f"   💥 Erro: {str(timeout_error)}")
            self.logger.error(f"   ⏱️ Tempo limite: 30 segundos")
            self.logger.error(f"   🔧 AdsPower pode estar sobrecarregado ou lento")
            return None
            
        except requests.exceptions.ConnectionError as conn_error:
            self.logger.error(f"💥 ERRO DE CONEXÃO ao iniciar browser:")
            self.logger.error(f"   💥 Erro: {str(conn_error)}")
            self.logger.error(f"   🌐 URL tentada: {self.base_url}")
            self.logger.error(f"   🔧 CHECKLIST DE VERIFICAÇÕES:")
            self.logger.error(f"      ✓ AdsPower está aberto?")
            self.logger.error(f"      ✓ API local está habilitada nas configurações?")
            self.logger.error(f"      ✓ Porta 50325 não está bloqueada por firewall?")
            self.logger.error(f"      ✓ Antivírus não está bloqueando a conexão?")
            return None
            
        except requests.exceptions.HTTPError as http_error:
            self.logger.error(f"💥 ERRO HTTP ao iniciar browser:")
            self.logger.error(f"   📊 Status: {http_error.response.status_code if http_error.response else 'Unknown'}")
            self.logger.error(f"   💥 Erro: {str(http_error)}")
            if http_error.response:
                self.logger.error(f"   📄 Resposta: {http_error.response.text[:500]}")
            return None
            
        except Exception as e:
            self.logger.error(f"💥 ERRO INESPERADO ao iniciar browser para perfil {user_id}:")
            self.logger.error(f"   💥 Tipo do erro: {type(e).__name__}")
            self.logger.error(f"   💬 Mensagem: {str(e)}")
            self.logger.error(f"   📋 Traceback completo:")
            self.logger.error(traceback.format_exc())
            return None
        
        finally:
            end_timestamp = datetime.now().isoformat()
            self.logger.info(f"🏁 FINALIZANDO start_browser() para perfil {user_id} - {end_timestamp}")
            self.logger.info("="*80)
    
    def _validate_existing_browser(self, user_id: str, browser_info: Dict) -> bool:
        """🧪 VALIDAR se browser existente ainda está funcional"""
        self.logger.info(f"🧪 VALIDANDO browser existente para perfil {user_id}...")
        
        try:
            debug_port = browser_info.get('debug_port')
            if not debug_port:
                self.logger.warning(f"⚠️ Debug port não encontrado nos dados existentes")
                return False
            
            # Teste rápido de conectividade
            test_url = f"http://127.0.0.1:{debug_port}/json/version"
            response = requests.get(test_url, timeout=3)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Browser existente ainda está funcional")
                return True
            else:
                self.logger.warning(f"⚠️ Browser existente não responde (status: {response.status_code})")
                return False
                
        except Exception as validate_error:
            self.logger.warning(f"⚠️ Erro ao validar browser existente: {str(validate_error)}")
            return False
    
    def stop_browser(self, user_id: str) -> bool:
        """Parar browser de um perfil específico"""
        try:
            params = {'user_id': user_id}
            
            response = requests.get(f"{self.base_url}/api/v1/browser/stop", params=params)
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
            response = requests.get(f"{self.base_url}/api/v1/browser/active", params=params)
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
            
            response = requests.post(f"{self.base_url}/api/v1/user/create", json=profile_data)
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
            response = requests.post(f"{self.base_url}/api/v1/user/delete", json=params)
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
            
            response = requests.post(f"{self.base_url}/api/v1/user/update", json=update_data)
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
            response = requests.get(f"{self.base_url}/api/v1/user/info", params=params)
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