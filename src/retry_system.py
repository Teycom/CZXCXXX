#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avançado de Retry para AdsPower
Sistema extremamente robusto para lidar com instabilidades de conexão e problemas intermitentes
"""

import time
import random
import logging
import requests
import threading
from typing import Callable, Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

class RetryState(Enum):
    """Estados do sistema de retry"""
    IDLE = "idle"
    RETRYING = "retrying"
    SUCCESS = "success"
    FAILED = "failed"
    CIRCUIT_OPEN = "circuit_open"

class CircuitState(Enum):
    """Estados do Circuit Breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Muitas falhas - rejeitando chamadas
    HALF_OPEN = "half_open"  # Testando se voltou a funcionar

@dataclass
class RetryAttempt:
    """Informações de uma tentativa de retry"""
    attempt_number: int
    timestamp: datetime
    duration: float
    error: Optional[Exception] = None
    success: bool = False
    backoff_delay: float = 0.0
    strategy_used: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetryConfig:
    """Configuração do sistema de retry"""
    max_attempts: int = 10
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    timeout: float = 30.0
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: int = 30
    health_check_interval: int = 10
    retry_on_exceptions: Tuple = (requests.ConnectionError, requests.Timeout, requests.HTTPError)

class CircuitBreaker:
    """Implementação do padrão Circuit Breaker"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, logger: Optional[logging.Logger] = None):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.logger = logger or logging.getLogger(__name__)
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.RLock()
        
        self.logger.info(f"🔧 CircuitBreaker inicializado - Threshold: {failure_threshold}, Recovery: {recovery_timeout}s")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executar função através do circuit breaker"""
        with self.lock:
            current_time = datetime.now()
            
            # Verificar se circuit está OPEN e se passou o tempo de recovery
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (current_time - self.last_failure_time).seconds >= self.recovery_timeout:
                    self.logger.info("🔄 CircuitBreaker: Transitando para HALF_OPEN - Tentando recuperação")
                    self.state = CircuitState.HALF_OPEN
                else:
                    self.logger.warning("⚡ CircuitBreaker OPEN - Rejeitando chamada sem executar")
                    raise CircuitOpenException("Circuit breaker está OPEN - muitas falhas detectadas")
            
            try:
                # Executar função
                self.logger.debug(f"🔧 CircuitBreaker: Executando função {func.__name__}")
                result = func(*args, **kwargs)
                
                # Sucesso - resetar contador de falhas
                if self.state == CircuitState.HALF_OPEN:
                    self.logger.info("✅ CircuitBreaker: HALF_OPEN → CLOSED - Recuperação bem-sucedida")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.last_failure_time = None
                elif self.failure_count > 0:
                    self.logger.info(f"✅ CircuitBreaker: Sucesso detectado - Reset counter de {self.failure_count} → 0")
                    self.failure_count = 0
                    self.last_failure_time = None
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = current_time
                
                self.logger.error(f"❌ CircuitBreaker: Falha #{self.failure_count} detectada - {str(e)}")
                
                # Verificar se deve abrir o circuit
                if self.failure_count >= self.failure_threshold:
                    if self.state != CircuitState.OPEN:
                        self.logger.critical(f"⚡ CircuitBreaker: ABRINDO CIRCUIT - {self.failure_count} falhas consecutivas")
                        self.state = CircuitState.OPEN
                
                raise
    
    def get_state_info(self) -> Dict[str, Any]:
        """Obter informações do estado atual"""
        with self.lock:
            return {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'failure_threshold': self.failure_threshold,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'recovery_timeout': self.recovery_timeout,
                'is_operational': self.state != CircuitState.OPEN
            }

class ExponentialBackoff:
    """Implementação de Exponential Backoff com Jitter"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, exponential_base: float = 2.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay para uma tentativa específica"""
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Aplicar limite máximo
        delay = min(delay, self.max_delay)
        
        # Adicionar jitter para evitar thundering herd
        if self.jitter:
            jitter_range = delay * 0.1  # 10% de variação
            jitter_value = random.uniform(-jitter_range, jitter_range)
            delay += jitter_value
        
        return max(0.1, delay)  # Mínimo de 100ms

class HealthChecker:
    """Monitor contínuo de saúde da conexão AdsPower"""
    
    def __init__(self, check_url: str, check_interval: int = 10, logger: Optional[logging.Logger] = None):
        self.check_url = check_url
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self.is_running = False
        self.last_check_time = None
        self.last_check_success = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.total_checks = 0
        self.total_successes = 0
        
        self.health_history: List[Dict[str, Any]] = []
        self.max_history = 100  # Manter últimas 100 verificações
        
        self.check_thread = None
        self.lock = threading.RLock()
        
        self.logger.info(f"💚 HealthChecker inicializado - URL: {check_url}, Intervalo: {check_interval}s")
    
    def start_monitoring(self):
        """Iniciar monitoramento contínuo"""
        with self.lock:
            if self.is_running:
                self.logger.warning("⚠️ HealthChecker: Monitor já está rodando")
                return
            
            self.is_running = True
            self.check_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.check_thread.start()
            
            self.logger.info("🚀 HealthChecker: Monitoramento iniciado")
    
    def stop_monitoring(self):
        """Parar monitoramento"""
        with self.lock:
            if not self.is_running:
                return
            
            self.is_running = False
            if self.check_thread:
                self.check_thread.join(timeout=5)
            
            self.logger.info("🛑 HealthChecker: Monitoramento parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        self.logger.info("🔄 HealthChecker: Loop de monitoramento iniciado")
        
        while self.is_running:
            try:
                self.perform_health_check()
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ HealthChecker: Erro no loop de monitoramento - {str(e)}")
                time.sleep(self.check_interval)
    
    def perform_health_check(self) -> bool:
        """Realizar uma verificação de saúde"""
        check_start = time.time()
        success = False
        error_details = None
        
        try:
            # Tentar conectar com timeout reduzido
            response = requests.get(
                f"{self.check_url}/status",
                timeout=5,
                headers={'User-Agent': 'AdsPower-HealthChecker'}
            )
            
            success = response.status_code == 200
            check_duration = time.time() - check_start
            
            if success:
                self.logger.debug(f"💚 HealthChecker: OK - {check_duration:.2f}s")
            else:
                error_details = f"HTTP {response.status_code}"
                self.logger.warning(f"⚠️ HealthChecker: HTTP {response.status_code} - {check_duration:.2f}s")
                
        except Exception as e:
            check_duration = time.time() - check_start
            error_details = str(e)
            self.logger.warning(f"❌ HealthChecker: FALHA - {error_details} - {check_duration:.2f}s")
        
        # Atualizar estatísticas
        with self.lock:
            self.last_check_time = datetime.now()
            self.last_check_success = success
            self.total_checks += 1
            
            if success:
                self.total_successes += 1
                self.consecutive_successes += 1
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                self.consecutive_successes = 0
            
            # Adicionar ao histórico
            health_record = {
                'timestamp': self.last_check_time.isoformat(),
                'success': success,
                'duration': check_duration,
                'error': error_details,
                'consecutive_failures': self.consecutive_failures,
                'consecutive_successes': self.consecutive_successes
            }
            
            self.health_history.append(health_record)
            
            # Manter apenas as últimas N verificações
            if len(self.health_history) > self.max_history:
                self.health_history = self.health_history[-self.max_history:]
        
        return success
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obter status atual de saúde"""
        with self.lock:
            if self.total_checks == 0:
                success_rate = 0.0
            else:
                success_rate = (self.total_successes / self.total_checks) * 100
            
            return {
                'is_monitoring': self.is_running,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'last_check_success': self.last_check_success,
                'consecutive_failures': self.consecutive_failures,
                'consecutive_successes': self.consecutive_successes,
                'total_checks': self.total_checks,
                'total_successes': self.total_successes,
                'success_rate': round(success_rate, 2),
                'is_healthy': self.consecutive_failures < 3,  # Saudável se menos de 3 falhas seguidas
                'check_interval': self.check_interval
            }
    
    def get_health_history(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Obter histórico de verificações"""
        with self.lock:
            return self.health_history[-last_n:] if self.health_history else []

class RetryManager:
    """Gerenciador principal do sistema de retry avançado"""
    
    def __init__(self, config: RetryConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Componentes do sistema
        self.backoff = ExponentialBackoff(
            base_delay=config.base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter
        )
        
        self.circuit_breaker = None
        if config.circuit_breaker_enabled:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=config.circuit_failure_threshold,
                recovery_timeout=config.circuit_recovery_timeout,
                logger=self.logger
            )
        
        self.health_checker = None
        self.retry_history: List[RetryAttempt] = []
        self.max_history = 1000
        
        self.logger.info(f"🚀 RetryManager inicializado - Max tentativas: {config.max_attempts}")
        self.logger.info(f"   📊 Backoff: {config.base_delay}s → {config.max_delay}s (base {config.exponential_base})")
        self.logger.info(f"   ⚡ Circuit Breaker: {'Ativado' if config.circuit_breaker_enabled else 'Desativado'}")
    
    def setup_health_monitoring(self, check_url: str):
        """Configurar monitoramento de saúde"""
        if self.health_checker:
            self.health_checker.stop_monitoring()
        
        self.health_checker = HealthChecker(
            check_url=check_url,
            check_interval=self.config.health_check_interval,
            logger=self.logger
        )
        
        self.health_checker.start_monitoring()
        self.logger.info(f"💚 Health monitoring configurado para {check_url}")
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Executar função com retry robusto"""
        start_time = datetime.now()
        last_exception = None
        
        self.logger.info(f"🔄 INICIANDO RETRY - Função: {func.__name__}")
        self.logger.info(f"   📋 Config: {self.config.max_attempts} tentativas, timeout {self.config.timeout}s")
        
        for attempt in range(1, self.config.max_attempts + 1):
            attempt_start = time.time()
            
            self.logger.info(f"🎯 TENTATIVA {attempt}/{self.config.max_attempts} - {func.__name__}")
            
            try:
                # Executar através do circuit breaker se habilitado
                if self.circuit_breaker:
                    result = self.circuit_breaker.call(func, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Sucesso!
                attempt_duration = time.time() - attempt_start
                total_duration = (datetime.now() - start_time).total_seconds()
                
                success_attempt = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    duration=attempt_duration,
                    success=True,
                    strategy_used="standard_retry",
                    details={'total_duration': total_duration}
                )
                
                self.retry_history.append(success_attempt)
                self._cleanup_history()
                
                self.logger.info(f"✅ SUCESSO na tentativa {attempt} - {attempt_duration:.2f}s")
                self.logger.info(f"🏁 RETRY CONCLUÍDO - Tempo total: {total_duration:.2f}s")
                
                return result
                
            except self.config.retry_on_exceptions as e:
                attempt_duration = time.time() - attempt_start
                last_exception = e
                
                # Log detalhado da falha
                self.logger.error(f"❌ FALHA na tentativa {attempt}/{self.config.max_attempts}")
                self.logger.error(f"   💥 Erro: {type(e).__name__}: {str(e)}")
                self.logger.error(f"   ⏱️ Duração: {attempt_duration:.2f}s")
                
                # Registrar tentativa falhada
                failed_attempt = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    duration=attempt_duration,
                    error=e,
                    success=False,
                    strategy_used="standard_retry",
                    details={'error_type': type(e).__name__}
                )
                
                # Se não é a última tentativa, calcular backoff
                if attempt < self.config.max_attempts:
                    backoff_delay = self.backoff.calculate_delay(attempt - 1)
                    failed_attempt.backoff_delay = backoff_delay
                    
                    self.logger.warning(f"⏳ Aguardando {backoff_delay:.2f}s antes da próxima tentativa...")
                    self.logger.warning(f"   📊 Estratégia: Exponential backoff (tentativa {attempt})")
                    
                    time.sleep(backoff_delay)
                
                self.retry_history.append(failed_attempt)
                self._cleanup_history()
                
            except Exception as e:
                # Exceção não configurada para retry
                attempt_duration = time.time() - attempt_start
                
                self.logger.error(f"💥 ERRO NÃO RECUPERÁVEL na tentativa {attempt}")
                self.logger.error(f"   🚫 Tipo: {type(e).__name__}: {str(e)}")
                self.logger.error(f"   ⏱️ Duração: {attempt_duration:.2f}s")
                self.logger.error(f"   ❌ Não está configurado para retry - Abortando")
                
                error_attempt = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    duration=attempt_duration,
                    error=e,
                    success=False,
                    strategy_used="no_retry",
                    details={'error_type': type(e).__name__, 'non_retryable': True}
                )
                
                self.retry_history.append(error_attempt)
                self._cleanup_history()
                
                raise
        
        # Se chegou aqui, todas as tentativas falharam
        total_duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.error(f"💀 RETRY ESGOTADO - {self.config.max_attempts} tentativas falharam")
        self.logger.error(f"   ⏱️ Tempo total: {total_duration:.2f}s")
        self.logger.error(f"   💥 Último erro: {type(last_exception).__name__}: {str(last_exception)}")
        
        # Incluir histórico de tentativas no erro
        if last_exception:
            raise RetryExhaustedException(
                f"Todas as {self.config.max_attempts} tentativas falharam após {total_duration:.2f}s. "
                f"Último erro: {str(last_exception)}"
            ) from last_exception
        else:
            raise RetryExhaustedException(
                f"Todas as {self.config.max_attempts} tentativas falharam após {total_duration:.2f}s"
            )
    
    def _cleanup_history(self):
        """Limpar histórico antigo"""
        if len(self.retry_history) > self.max_history:
            self.retry_history = self.retry_history[-self.max_history:]
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de retry"""
        if not self.retry_history:
            return {
                'total_attempts': 0,
                'successful_attempts': 0,
                'failed_attempts': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'total_backoff_time': 0.0
            }
        
        total_attempts = len(self.retry_history)
        successful_attempts = sum(1 for attempt in self.retry_history if attempt.success)
        failed_attempts = total_attempts - successful_attempts
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0.0
        
        total_duration = sum(attempt.duration for attempt in self.retry_history)
        average_duration = total_duration / total_attempts if total_attempts > 0 else 0.0
        
        total_backoff_time = sum(attempt.backoff_delay for attempt in self.retry_history)
        
        return {
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'failed_attempts': failed_attempts,
            'success_rate': round(success_rate, 2),
            'average_duration': round(average_duration, 2),
            'total_backoff_time': round(total_backoff_time, 2),
            'last_attempts': [
                {
                    'attempt': attempt.attempt_number,
                    'timestamp': attempt.timestamp.isoformat(),
                    'success': attempt.success,
                    'duration': round(attempt.duration, 2),
                    'error': str(attempt.error) if attempt.error else None,
                    'backoff_delay': round(attempt.backoff_delay, 2)
                }
                for attempt in self.retry_history[-10:]  # Últimas 10 tentativas
            ]
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obter status completo do sistema"""
        status = {
            'retry_manager': {
                'config': {
                    'max_attempts': self.config.max_attempts,
                    'base_delay': self.config.base_delay,
                    'max_delay': self.config.max_delay,
                    'timeout': self.config.timeout
                },
                'stats': self.get_retry_stats()
            }
        }
        
        if self.circuit_breaker:
            status['circuit_breaker'] = self.circuit_breaker.get_state_info()
        
        if self.health_checker:
            status['health_checker'] = self.health_checker.get_health_status()
        
        return status
    
    def cleanup(self):
        """Limpeza de recursos"""
        if self.health_checker:
            self.health_checker.stop_monitoring()
        
        self.logger.info("🧹 RetryManager: Limpeza de recursos concluída")

# Exceções customizadas
class RetryException(Exception):
    """Exceção base do sistema de retry"""
    pass

class RetryExhaustedException(RetryException):
    """Exceção quando todas as tentativas de retry foram esgotadas"""
    pass

class CircuitOpenException(RetryException):
    """Exceção quando circuit breaker está aberto"""
    pass

# Decorator para retry automático
def with_retry(config: Optional[RetryConfig] = None, logger: Optional[logging.Logger] = None):
    """Decorator para adicionar retry automático a funções"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_config = config or RetryConfig()
            retry_manager = RetryManager(retry_config, logger)
            
            try:
                return retry_manager.execute_with_retry(func, *args, **kwargs)
            finally:
                retry_manager.cleanup()
        
        return wrapper
    return decorator

# Funções utilitárias
def create_adspower_retry_manager(api_url: str = "http://localhost:50325", logger: Optional[logging.Logger] = None) -> RetryManager:
    """Criar RetryManager configurado especificamente para AdsPower"""
    config = RetryConfig(
        max_attempts=10,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        timeout=30.0,
        circuit_breaker_enabled=True,
        circuit_failure_threshold=5,
        circuit_recovery_timeout=30,
        health_check_interval=10,
        retry_on_exceptions=(
            requests.ConnectionError,
            requests.Timeout,
            requests.HTTPError,
            ConnectionRefusedError,
            OSError
        )
    )
    
    retry_manager = RetryManager(config, logger)
    retry_manager.setup_health_monitoring(api_url)
    
    return retry_manager

def create_webdriver_retry_manager(logger: Optional[logging.Logger] = None) -> RetryManager:
    """Criar RetryManager configurado para operações do WebDriver"""
    from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
    
    config = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=20.0,
        exponential_base=1.5,
        jitter=True,
        timeout=60.0,
        circuit_breaker_enabled=False,  # Não usar circuit breaker para WebDriver
        retry_on_exceptions=(
            WebDriverException,
            TimeoutException,
            NoSuchElementException,
            ConnectionRefusedError
        )
    )
    
    return RetryManager(config, logger)