#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger - Sistema de Logging para o Bot
Configuração centralizada de logging para todo o projeto
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "GoogleAdsCampaignBot", level: int = logging.INFO) -> logging.Logger:
    """Configurar sistema de logging"""
    
    # Criar logger principal
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Criar diretório de logs se não existir
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Formato das mensagens de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo (com rotação)
    log_file = os.path.join(logs_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log inicial
    logger.info("="*50)
    logger.info("Google Ads Campaign Bot - Sistema de Logging Iniciado")
    logger.info(f"Nível de log: {logging.getLevelName(level)}")
    logger.info(f"Arquivo de log: {log_file}")
    logger.info("="*50)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Obter logger existente ou criar novo"""
    if name is None:
        name = "GoogleAdsCampaignBot"
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

class BotLoggerAdapter(logging.LoggerAdapter):
    """Adapter personalizado para adicionar contexto aos logs"""
    
    def __init__(self, logger, extra):
        super().__init__(logger, extra)
    
    def process(self, msg, kwargs):
        return f"[{self.extra['context']}] {msg}", kwargs

def get_profile_logger(profile_name: str) -> BotLoggerAdapter:
    """Obter logger com contexto de perfil específico"""
    base_logger = get_logger()
    return BotLoggerAdapter(base_logger, {'context': f"Profile:{profile_name}"})

def get_campaign_logger(campaign_name: str) -> BotLoggerAdapter:
    """Obter logger com contexto de campanha específica"""
    base_logger = get_logger()
    return BotLoggerAdapter(base_logger, {'context': f"Campaign:{campaign_name}"})

# Configurar logging para bibliotecas externas
def configure_external_loggers():
    """Configurar nível de log para bibliotecas externas"""
    
    # Reduzir verbosidade do Selenium
    selenium_logger = logging.getLogger('selenium')
    selenium_logger.setLevel(logging.WARNING)
    
    # Reduzir verbosidade do urllib3
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)
    
    # Reduzir verbosidade do requests
    requests_logger = logging.getLogger('requests')
    requests_logger.setLevel(logging.WARNING)
    
    # Reduzir verbosidade do undetected_chromedriver
    uc_logger = logging.getLogger('undetected_chromedriver')
    uc_logger.setLevel(logging.WARNING)

# Executar configuração automática
configure_external_loggers()

# Função para logging de performance
def log_performance(func):
    """Decorator para logging de performance de funções"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = datetime.now()
        
        logger.debug(f"Iniciando execução de {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.debug(f"Função {func.__name__} executada com sucesso em {duration:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Erro na função {func.__name__} após {duration:.2f}s: {str(e)}")
            raise
    
    return wrapper

# Função para logging estruturado de eventos
def log_event(event_type: str, message: str, details: dict = None, level: int = logging.INFO):
    """Log estruturado de eventos importantes"""
    logger = get_logger()
    
    log_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    # Formatar mensagem estruturada
    structured_msg = f"[{event_type}] {message}"
    if details:
        details_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        structured_msg += f" | {details_str}"
    
    logger.log(level, structured_msg)

# Funções de conveniência para tipos específicos de eventos
def log_profile_event(profile_name: str, event: str, message: str, success: bool = True):
    """Log evento relacionado a perfil"""
    level = logging.INFO if success else logging.ERROR
    log_event(
        'PROFILE_EVENT', 
        message, 
        {'profile': profile_name, 'event': event, 'success': success},
        level
    )

def log_campaign_event(campaign_name: str, event: str, message: str, success: bool = True):
    """Log evento relacionado a campanha"""
    level = logging.INFO if success else logging.ERROR
    log_event(
        'CAMPAIGN_EVENT', 
        message, 
        {'campaign': campaign_name, 'event': event, 'success': success},
        level
    )

def log_automation_event(action: str, message: str, success: bool = True, details: dict = None):
    """Log evento de automação"""
    level = logging.INFO if success else logging.ERROR
    event_details = {'action': action, 'success': success}
    if details:
        event_details.update(details)
    
    log_event('AUTOMATION_EVENT', message, event_details, level)

# Função para gerar relatório de logs
def generate_log_summary(log_file_path: str = None) -> dict:
    """Gerar resumo dos logs para relatório"""
    if not log_file_path:
        logs_dir = "logs"
        log_file_path = os.path.join(logs_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    
    summary = {
        'total_lines': 0,
        'errors': 0,
        'warnings': 0,
        'infos': 0,
        'profile_events': 0,
        'campaign_events': 0,
        'automation_events': 0
    }
    
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    summary['total_lines'] += 1
                    
                    if 'ERROR' in line:
                        summary['errors'] += 1
                    elif 'WARNING' in line:
                        summary['warnings'] += 1
                    elif 'INFO' in line:
                        summary['infos'] += 1
                    
                    if 'PROFILE_EVENT' in line:
                        summary['profile_events'] += 1
                    elif 'CAMPAIGN_EVENT' in line:
                        summary['campaign_events'] += 1
                    elif 'AUTOMATION_EVENT' in line:
                        summary['automation_events'] += 1
    
    except Exception as e:
        logger = get_logger()
        logger.error(f"Erro ao gerar resumo dos logs: {str(e)}")
    
    return summary