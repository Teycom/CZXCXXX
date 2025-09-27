#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Campaign Bot - Interface Principal
Bot para automação de criação de campanhas no Google Ads via AdsPower
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback

# Imports locais
from adspower_manager import AdsPowerManager
from google_ads_automation import GoogleAdsAutomation
from config import get_config
from logger import setup_logger, get_logger

class GoogleAdsCampaignBot:
    """Interface principal do bot de campanhas do Google Ads"""
    
    def __init__(self):
        # Configurar logging
        self.logger = setup_logger()
        self.config = get_config()
        
        # Inicializar componentes
        self.adspower_manager = AdsPowerManager(
            api_url=self.config.adspower.api_url,
            enable_advanced_retry=self.config.adspower.advanced_retry_enabled
        )
        
        # Estado da aplicação
        self.profiles = []
        self.selected_profiles = []
        self.automation_running = False
        self.automation_thread = None
        
        # Configurações da campanha
        self.campaign_config = {
            'name': '',
            'objective': 'Vendas',
            'budget': '50',
            'locations': ['Brasil'],
            'titles': [],
            'descriptions': [],
            'keywords': [],
            'final_url': ''
        }
        
        # Criar interface
        self.setup_gui()
        
        # Carregar perfis automaticamente
        self.load_profiles()
        
        self.logger.info("🚀 Google Ads Campaign Bot inicializado com sucesso!")
    
    def setup_gui(self):
        """🎨 CONFIGURAR interface gráfica moderna"""
        self.root = tk.Tk()
        self.root.title("Google Ads Campaign Bot v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores modernas
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Modern.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#28a745', foreground='white')
        style.configure('Danger.TButton', background='#dc3545', foreground='white')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🚀 Google Ads Campaign Bot", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de configuração da campanha
        self.setup_campaign_config_frame(main_frame)
        
        # Frame de seleção de perfis
        self.setup_profiles_frame(main_frame)
        
        # Frame de controles
        self.setup_controls_frame(main_frame)
        
        # Frame de status
        self.setup_status_frame(main_frame)
    
    def setup_campaign_config_frame(self, parent):
        """⚙️ CONFIGURAR frame de configuração da campanha"""
        config_frame = ttk.LabelFrame(parent, text="📋 Configuração da Campanha", padding="15")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        
        # Nome da campanha
        ttk.Label(config_frame, text="Nome da Campanha:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.campaign_name_var = tk.StringVar(value="Campanha Teste")
        ttk.Entry(config_frame, textvariable=self.campaign_name_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        
        # Objetivo
        ttk.Label(config_frame, text="Objetivo:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.objective_var = tk.StringVar(value="Vendas")
        objective_combo = ttk.Combobox(config_frame, textvariable=self.objective_var, width=25)
        objective_combo['values'] = ('Vendas', 'Leads', 'Tráfego do site', 'Sem orientação')
        objective_combo.grid(row=0, column=3, sticky=(tk.W, tk.E))
        objective_combo.state(['readonly'])
        
        # Orçamento
        ttk.Label(config_frame, text="Orçamento Diário (R$):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.budget_var = tk.StringVar(value="50")
        ttk.Entry(config_frame, textvariable=self.budget_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 20), pady=(10, 0))
        
        # URL final
        ttk.Label(config_frame, text="URL Final:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.final_url_var = tk.StringVar(value="https://exemplo.com")
        ttk.Entry(config_frame, textvariable=self.final_url_var, width=25).grid(row=1, column=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Localizações
        ttk.Label(config_frame, text="Localizações:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.locations_var = tk.StringVar(value="Brasil")
        ttk.Entry(config_frame, textvariable=self.locations_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 20), pady=(10, 0))
        
        # Títulos dos anúncios
        ttk.Label(config_frame, text="Títulos (separados por ;):").grid(row=2, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.titles_var = tk.StringVar(value="Título 1; Título 2; Título 3")
        ttk.Entry(config_frame, textvariable=self.titles_var, width=25).grid(row=2, column=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def setup_profiles_frame(self, parent):
        """👥 CONFIGURAR frame de seleção de perfis"""
        profiles_frame = ttk.LabelFrame(parent, text="👥 Seleção de Perfis AdsPower", padding="15")
        profiles_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        profiles_frame.columnconfigure(0, weight=1)
        profiles_frame.rowconfigure(1, weight=1)
        
        # Controles superiores
        controls_frame = ttk.Frame(profiles_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(2, weight=1)
        
        # Botões de controle
        ttk.Button(controls_frame, text="🔄 Recarregar Perfis", command=self.load_profiles).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(controls_frame, text="✅ Selecionar Todos", command=self.select_all_profiles).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(controls_frame, text="❌ Desmarcar Todos", command=self.deselect_all_profiles).grid(row=0, column=2, padx=(0, 10))
        
        # Campo de busca
        ttk.Label(controls_frame, text="🔍 Buscar:").grid(row=0, column=3, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_profiles)
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=4, padx=(0, 10))
        
        # Contador de selecionados
        self.selected_count_var = tk.StringVar(value="Selecionados: 0")
        ttk.Label(controls_frame, textvariable=self.selected_count_var, font=('Arial', 10, 'bold')).grid(row=0, column=5, padx=(20, 0))
        
        # Lista de perfis com scrollbar
        list_frame = ttk.Frame(profiles_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview para perfis
        columns = ('select', 'name', 'id', 'group', 'status')
        self.profiles_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar colunas
        self.profiles_tree.heading('select', text='✓')
        self.profiles_tree.heading('name', text='Nome do Perfil')
        self.profiles_tree.heading('id', text='ID')
        self.profiles_tree.heading('group', text='Grupo')
        self.profiles_tree.heading('status', text='Status')
        
        self.profiles_tree.column('select', width=50, anchor='center')
        self.profiles_tree.column('name', width=300)
        self.profiles_tree.column('id', width=100)
        self.profiles_tree.column('group', width=150)
        self.profiles_tree.column('status', width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profiles_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.profiles_tree.xview)
        self.profiles_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid dos componentes
        self.profiles_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind para seleção
        self.profiles_tree.bind('<Button-1>', self.on_profile_click)
        self.profiles_tree.bind('<Double-1>', self.on_profile_double_click)
    
    def setup_controls_frame(self, parent):
        """🎮 CONFIGURAR frame de controles"""
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=3, column=0, columnspan=3, pady=(0, 15))
        
        # Botões principais
        self.start_button = ttk.Button(
            controls_frame, 
            text="🚀 Iniciar Automação", 
            command=self.start_automation,
            style='Success.TButton'
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            controls_frame, 
            text="⏹️ Parar Automação", 
            command=self.stop_automation,
            style='Danger.TButton',
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # Botões auxiliares
        ttk.Button(controls_frame, text="💾 Salvar Configuração", command=self.save_config).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(controls_frame, text="📂 Carregar Configuração", command=self.load_config).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(controls_frame, text="📊 Ver Logs", command=self.show_logs).grid(row=0, column=4, padx=(0, 10))
    
    def setup_status_frame(self, parent):
        """📊 CONFIGURAR frame de status"""
        status_frame = ttk.LabelFrame(parent, text="📊 Status da Automação", padding="15")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 0))
        status_frame.columnconfigure(0, weight=1)
        
        # Área de texto para logs
        text_frame = ttk.Frame(status_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(text_frame, height=10, wrap=tk.WORD, font=('Consolas', 9))
        status_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Status atual
        self.current_status_var = tk.StringVar(value="Pronto para iniciar")
        ttk.Label(status_frame, textvariable=self.current_status_var, font=('Arial', 10, 'bold')).grid(row=2, column=0, pady=(5, 0))
    
    def load_profiles(self):
        """📋 CARREGAR perfis do AdsPower"""
        self.log_status("🔄 Carregando perfis do AdsPower...")
        
        def load_in_thread():
            try:
                profiles = self.adspower_manager.get_profiles()
                
                # Atualizar interface na thread principal
                self.root.after(0, self.update_profiles_list, profiles)
                
            except Exception as e:
                error_msg = f"❌ Erro ao carregar perfis: {str(e)}"
                self.root.after(0, self.log_status, error_msg)
                self.logger.error(error_msg)
        
        # Executar em thread separada
        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def update_profiles_list(self, profiles: List[Dict]):
        """📋 ATUALIZAR lista de perfis na interface"""
        try:
            self.profiles = profiles
            
            # Limpar lista atual
            for item in self.profiles_tree.get_children():
                self.profiles_tree.delete(item)
            
            # Adicionar perfis
            for profile in profiles:
                profile_id = profile.get('user_id', 'N/A')
                profile_name = profile.get('name', 'Sem nome')
                group_name = profile.get('group_name', 'Sem grupo')
                status = 'Ativo' if profile.get('status') == 'Active' else 'Inativo'
                
                # Inserir na árvore
                item_id = self.profiles_tree.insert('', 'end', values=(
                    '☐',  # Checkbox vazio
                    profile_name,
                    profile_id,
                    group_name,
                    status
                ))
                
                # Armazenar dados do perfil no item
                self.profiles_tree.set(item_id, 'profile_data', json.dumps(profile))
            
            self.log_status(f"✅ {len(profiles)} perfis carregados com sucesso!")
            self.update_selected_count()
            
        except Exception as e:
            error_msg = f"❌ Erro ao atualizar lista: {str(e)}"
            self.log_status(error_msg)
            self.logger.error(error_msg)
    
    def on_profile_click(self, event):
        """🖱️ MANIPULAR clique em perfil"""
        try:
            item = self.profiles_tree.identify('item', event.x, event.y)
            column = self.profiles_tree.identify('column', event.x, event.y)
            
            if item and column == '#1':  # Coluna de seleção
                current_value = self.profiles_tree.item(item, 'values')[0]
                
                if current_value == '☐':
                    # Marcar como selecionado
                    values = list(self.profiles_tree.item(item, 'values'))
                    values[0] = '☑'
                    self.profiles_tree.item(item, values=values)
                    
                    # Adicionar à lista de selecionados
                    profile_data = json.loads(self.profiles_tree.set(item, 'profile_data'))
                    if profile_data not in self.selected_profiles:
                        self.selected_profiles.append(profile_data)
                else:
                    # Desmarcar
                    values = list(self.profiles_tree.item(item, 'values'))
                    values[0] = '☐'
                    self.profiles_tree.item(item, values=values)
                    
                    # Remover da lista de selecionados
                    profile_data = json.loads(self.profiles_tree.set(item, 'profile_data'))
                    if profile_data in self.selected_profiles:
                        self.selected_profiles.remove(profile_data)
                
                self.update_selected_count()
                
        except Exception as e:
            self.logger.error(f"Erro no clique do perfil: {str(e)}")
    
    def on_profile_double_click(self, event):
        """🖱️ MANIPULAR duplo clique em perfil"""
        try:
            item = self.profiles_tree.identify('item', event.x, event.y)
            if item:
                profile_data = json.loads(self.profiles_tree.set(item, 'profile_data'))
                profile_name = profile_data.get('name', 'Sem nome')
                profile_id = profile_data.get('user_id', 'N/A')
                
                messagebox.showinfo(
                    "Informações do Perfil",
                    f"Nome: {profile_name}\n"
                    f"ID: {profile_id}\n"
                    f"Grupo: {profile_data.get('group_name', 'Sem grupo')}\n"
                    f"Status: {profile_data.get('status', 'Desconhecido')}"
                )
        except Exception as e:
            self.logger.error(f"Erro no duplo clique: {str(e)}")
    
    def select_all_profiles(self):
        """✅ SELECIONAR todos os perfis"""
        try:
            self.selected_profiles.clear()
            
            for item in self.profiles_tree.get_children():
                # Marcar como selecionado
                values = list(self.profiles_tree.item(item, 'values'))
                values[0] = '☑'
                self.profiles_tree.item(item, values=values)
                
                # Adicionar à lista
                profile_data = json.loads(self.profiles_tree.set(item, 'profile_data'))
                self.selected_profiles.append(profile_data)
            
            self.update_selected_count()
            self.log_status("✅ Todos os perfis selecionados")
            
        except Exception as e:
            self.logger.error(f"Erro ao selecionar todos: {str(e)}")
    
    def deselect_all_profiles(self):
        """❌ DESMARCAR todos os perfis"""
        try:
            self.selected_profiles.clear()
            
            for item in self.profiles_tree.get_children():
                # Desmarcar
                values = list(self.profiles_tree.item(item, 'values'))
                values[0] = '☐'
                self.profiles_tree.item(item, values=values)
            
            self.update_selected_count()
            self.log_status("❌ Todos os perfis desmarcados")
            
        except Exception as e:
            self.logger.error(f"Erro ao desmarcar todos: {str(e)}")
    
    def filter_profiles(self, *args):
        """🔍 FILTRAR perfis por busca"""
        try:
            search_term = self.search_var.get().lower()
            
            for item in self.profiles_tree.get_children():
                values = self.profiles_tree.item(item, 'values')
                profile_name = values[1].lower()
                profile_id = values[2].lower()
                
                if search_term in profile_name or search_term in profile_id:
                    self.profiles_tree.reattach(item, '', 'end')
                else:
                    self.profiles_tree.detach(item)
                    
        except Exception as e:
            self.logger.error(f"Erro no filtro: {str(e)}")
    
    def update_selected_count(self):
        """📊 ATUALIZAR contador de selecionados"""
        count = len(self.selected_profiles)
        self.selected_count_var.set(f"Selecionados: {count}")
    
    def start_automation(self):
        """🚀 INICIAR automação"""
        try:
            # Validações
            if not self.selected_profiles:
                messagebox.showwarning("Aviso", "Selecione pelo menos um perfil!")
                return
            
            if not self.campaign_name_var.get().strip():
                messagebox.showwarning("Aviso", "Digite um nome para a campanha!")
                return
            
            # Preparar configuração da campanha
            self.campaign_config = {
                'name': self.campaign_name_var.get().strip(),
                'objective': self.objective_var.get(),
                'budget': self.budget_var.get().strip(),
                'locations': [loc.strip() for loc in self.locations_var.get().split(',')],
                'titles': [title.strip() for title in self.titles_var.get().split(';')],
                'final_url': self.final_url_var.get().strip()
            }
            
            # Atualizar interface
            self.automation_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.progress_var.set(0)
            self.current_status_var.set("Iniciando automação...")
            
            # Iniciar thread de automação
            self.automation_thread = threading.Thread(target=self.run_automation, daemon=True)
            self.automation_thread.start()
            
            self.log_status("🚀 Automação iniciada!")
            
        except Exception as e:
            error_msg = f"❌ Erro ao iniciar automação: {str(e)}"
            self.log_status(error_msg)
            self.logger.error(error_msg)
    
    def stop_automation(self):
        """⏹️ PARAR automação"""
        try:
            self.automation_running = False
            self.current_status_var.set("Parando automação...")
            self.log_status("⏹️ Parando automação...")
            
            # Aguardar thread terminar
            if self.automation_thread and self.automation_thread.is_alive():
                self.automation_thread.join(timeout=5)
            
            # Resetar interface
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.current_status_var.set("Automação parada")
            
            self.log_status("✅ Automação parada com sucesso!")
            
        except Exception as e:
            error_msg = f"❌ Erro ao parar automação: {str(e)}"
            self.log_status(error_msg)
            self.logger.error(error_msg)
    
    def run_automation(self):
        """🤖 EXECUTAR automação principal"""
        try:
            total_profiles = len(self.selected_profiles)
            successful_campaigns = 0
            failed_campaigns = 0
            
            self.root.after(0, self.log_status, f"🎯 Iniciando automação para {total_profiles} perfis...")
            
            for i, profile in enumerate(self.selected_profiles):
                if not self.automation_running:
                    break
                
                profile_name = profile.get('name', 'Sem nome')
                profile_id = profile.get('user_id', 'N/A')
                
                # Atualizar progresso
                progress = (i / total_profiles) * 100
                self.root.after(0, self.progress_var.set, progress)
                self.root.after(0, self.current_status_var.set, f"Processando: {profile_name}")
                self.root.after(0, self.log_status, f"🔄 Processando perfil: {profile_name} ({i+1}/{total_profiles})")
                
                try:
                    # Iniciar browser no AdsPower
                    self.root.after(0, self.log_status, f"🚀 Iniciando browser para: {profile_name}")
                    browser_info = self.adspower_manager.start_browser(profile_id)
                    
                    if not browser_info:
                        self.root.after(0, self.log_status, f"❌ Falha ao iniciar browser: {profile_name}")
                        failed_campaigns += 1
                        continue
                    
                    # Criar automação
                    automation = GoogleAdsAutomation(self.adspower_manager, profile_name)
                    
                    # Configurar WebDriver
                    self.root.after(0, self.log_status, f"🔧 Configurando WebDriver: {profile_name}")
                    if not automation.setup_webdriver(browser_info):
                        self.root.after(0, self.log_status, f"❌ Falha na configuração do WebDriver: {profile_name}")
                        failed_campaigns += 1
                        continue
                    
                    # Criar campanha
                    self.root.after(0, self.log_status, f"📋 Criando campanha: {profile_name}")
                    if automation.create_campaign(self.campaign_config):
                        self.root.after(0, self.log_status, f"✅ Campanha criada com sucesso: {profile_name}")
                        successful_campaigns += 1
                    else:
                        self.root.after(0, self.log_status, f"❌ Falha na criação da campanha: {profile_name}")
                        failed_campaigns += 1
                    
                    # Limpeza
                    automation.cleanup()
                    
                    # Aguardar entre perfis
                    if i < total_profiles - 1:  # Não aguardar no último
                        self.root.after(0, self.log_status, f"⏳ Aguardando 5s antes do próximo perfil...")
                        time.sleep(5)
                
                except Exception as profile_error:
                    error_msg = f"❌ Erro no perfil {profile_name}: {str(profile_error)}"
                    self.root.after(0, self.log_status, error_msg)
                    self.logger.error(f"Erro no perfil {profile_name}: {traceback.format_exc()}")
                    failed_campaigns += 1
            
            # Finalizar automação
            self.root.after(0, self.progress_var.set, 100)
            self.root.after(0, self.current_status_var.set, "Automação concluída")
            
            # Relatório final
            final_report = f"🎉 AUTOMAÇÃO CONCLUÍDA!\n"
            final_report += f"✅ Sucessos: {successful_campaigns}\n"
            final_report += f"❌ Falhas: {failed_campaigns}\n"
            final_report += f"📊 Total processado: {successful_campaigns + failed_campaigns}/{total_profiles}"
            
            self.root.after(0, self.log_status, final_report)
            
            # Resetar interface
            self.root.after(0, self.reset_automation_interface)
            
        except Exception as e:
            error_msg = f"💥 Erro crítico na automação: {str(e)}"
            self.root.after(0, self.log_status, error_msg)
            self.logger.error(f"Erro crítico: {traceback.format_exc()}")
            self.root.after(0, self.reset_automation_interface)
    
    def reset_automation_interface(self):
        """🔄 RESETAR interface após automação"""
        self.automation_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.current_status_var.set("Pronto para nova automação")
    
    def log_status(self, message: str):
        """📝 ADICIONAR mensagem ao log de status"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            
            self.status_text.insert(tk.END, formatted_message)
            self.status_text.see(tk.END)
            
            # Limitar tamanho do log
            lines = self.status_text.get("1.0", tk.END).split('\n')
            if len(lines) > 1000:
                self.status_text.delete("1.0", f"{len(lines)-500}.0")
            
            # Log também no arquivo
            self.logger.info(message)
            
        except Exception as e:
            self.logger.error(f"Erro no log de status: {str(e)}")
    
    def save_config(self):
        """💾 SALVAR configuração"""
        try:
            config_data = {
                'campaign_name': self.campaign_name_var.get(),
                'objective': self.objective_var.get(),
                'budget': self.budget_var.get(),
                'locations': self.locations_var.get(),
                'titles': self.titles_var.get(),
                'final_url': self.final_url_var.get(),
                'selected_profiles': [p.get('user_id') for p in self.selected_profiles]
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                self.log_status(f"💾 Configuração salva: {filename}")
                messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
                
        except Exception as e:
            error_msg = f"❌ Erro ao salvar configuração: {str(e)}"
            self.log_status(error_msg)
            messagebox.showerror("Erro", error_msg)
    
    def load_config(self):
        """📂 CARREGAR configuração"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Aplicar configurações
                self.campaign_name_var.set(config_data.get('campaign_name', ''))
                self.objective_var.set(config_data.get('objective', 'Vendas'))
                self.budget_var.set(config_data.get('budget', '50'))
                self.locations_var.set(config_data.get('locations', 'Brasil'))
                self.titles_var.set(config_data.get('titles', ''))
                self.final_url_var.set(config_data.get('final_url', ''))
                
                self.log_status(f"📂 Configuração carregada: {filename}")
                messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")
                
        except Exception as e:
            error_msg = f"❌ Erro ao carregar configuração: {str(e)}"
            self.log_status(error_msg)
            messagebox.showerror("Erro", error_msg)
    
    def show_logs(self):
        """📊 MOSTRAR logs detalhados"""
        try:
            logs_dir = "logs"
            if os.path.exists(logs_dir):
                # Abrir pasta de logs
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(["explorer", logs_dir])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", logs_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", logs_dir])
                
                self.log_status("📊 Pasta de logs aberta")
            else:
                messagebox.showinfo("Info", "Pasta de logs não encontrada")
                
        except Exception as e:
            error_msg = f"❌ Erro ao abrir logs: {str(e)}"
            self.log_status(error_msg)
            messagebox.showerror("Erro", error_msg)
    
    def run(self):
        """🏃 EXECUTAR aplicação"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Erro na execução: {str(e)}")
    
    def on_closing(self):
        """🚪 MANIPULAR fechamento da aplicação"""
        try:
            if self.automation_running:
                if messagebox.askokcancel("Sair", "Automação em andamento. Deseja realmente sair?"):
                    self.stop_automation()
                    self.root.destroy()
            else:
                self.root.destroy()
        except Exception as e:
            self.logger.error(f"Erro no fechamento: {str(e)}")
            self.root.destroy()

def main():
    """🚀 FUNÇÃO PRINCIPAL"""
    try:
        # Configurar logging
        logger = setup_logger()
        logger.info("="*50)
        logger.info("🚀 INICIANDO Google Ads Campaign Bot")
        logger.info("="*50)
        
        # Criar e executar aplicação
        app = GoogleAdsCampaignBot()
        app.run()
        
        logger.info("👋 Aplicação finalizada")
        
    except Exception as e:
        print(f"💥 Erro crítico na inicialização: {str(e)}")
        print(f"📚 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()