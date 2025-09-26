#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads Campaign Automation Bot with AdsPower Integration
Aplicativo Desktop para Automação de Campanhas do Google Ads

Este é o arquivo principal que executa a interface gráfica do usuário.
Para executar: python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import os
import time
from datetime import datetime
import logging

from adspower_manager import AdsPowerManager
from google_ads_automation import GoogleAdsAutomation
from logger import setup_logger
from config import Config

class GoogleAdsCampaignBot:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Google Ads Campaign Bot - AdsPower Integration")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a2e')
        
        # Maximizar janela (multiplataforma)
        try:
            self.root.state('zoomed')  # Windows
        except:
            # Linux/Mac - definir tamanho máximo
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        # Cores modernas
        self.colors = {
            'primary': '#16213e',
            'secondary': '#0f3460', 
            'accent': '#53a8b6',
            'success': '#5cb85c',
            'warning': '#f0ad4e',
            'danger': '#d9534f',
            'light': '#ffffff',
            'dark': '#1a1a2e',
            'muted': '#6c757d'
        }
        
        # Inicializar componentes
        self.config = Config()
        self.logger = setup_logger()
        self.adspower_manager = AdsPowerManager(enable_advanced_retry=self.config.adspower.advanced_retry_enabled)
        self.automation = GoogleAdsAutomation(enable_advanced_retry=self.config.adspower.advanced_retry_enabled)
        
        # Variáveis de estado
        self.profiles = []
        self.selected_profiles = []
        self.campaign_config = {}
        self.is_running = False
        self.config_file = 'selected_profiles.json'  # Arquivo para persistir seleções
        
        self.setup_ui()
        self.refresh_profiles()
    
    def setup_ui(self):
        """Configurar a interface do usuário"""
        
        # Header moderno com gradiente visual
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        # Logo e título
        title_container = tk.Frame(title_frame, bg=self.colors['primary'])
        title_container.pack(expand=True, fill='both')
        
        title_label = tk.Label(title_container, text="🚀 Google Ads Campaign Bot", 
                              font=('Segoe UI', 24, 'bold'), 
                              fg=self.colors['light'], bg=self.colors['primary'])
        title_label.pack(side='left', padx=20, pady=20)
        
        subtitle_label = tk.Label(title_container, text="Automação Profissional com AdsPower", 
                                 font=('Segoe UI', 12), 
                                 fg=self.colors['accent'], bg=self.colors['primary'])
        subtitle_label.pack(side='left', padx=(0, 20), pady=20)
        
        # Status de conexão
        self.connection_status = tk.Label(title_container, text="🔄 Verificando conexão...", 
                                         font=('Segoe UI', 10), 
                                         fg=self.colors['warning'], bg=self.colors['primary'])
        self.connection_status.pack(side='right', padx=20, pady=20)
        
        # Configurar estilo moderno das abas
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Modern.TNotebook', background=self.colors['dark'], borderwidth=0)
        style.configure('Modern.TNotebook.Tab', 
                       background=self.colors['secondary'], 
                       foreground=self.colors['light'],
                       padding=[20, 10],
                       font=('Segoe UI', 11, 'bold'))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['accent']),
                           ('active', self.colors['primary'])],
                 foreground=[('selected', self.colors['light'])])
        
        # Frame principal com abas
        notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        notebook.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Aba 1: Configuração de Perfis
        self.setup_profiles_tab(notebook)
        
        # Aba 2: Configuração de Campanhas
        self.setup_campaign_tab(notebook)
        
        # Aba 3: Execução e Logs
        self.setup_execution_tab(notebook)
        
        # Aba 4: Configurações
        self.setup_settings_tab(notebook)
    
    def setup_profiles_tab(self, notebook):
        """Configurar aba de perfis do AdsPower - MODERNA E RESPONSIVA"""
        profiles_frame = ttk.Frame(notebook)
        notebook.add(profiles_frame, text="👥 Perfis AdsPower")
        
        # Container principal moderno
        main_container = tk.Frame(profiles_frame, bg=self.colors['dark'])
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header moderno com ações
        header_frame = tk.Frame(main_container, bg=self.colors['primary'], height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Título e informações
        info_container = tk.Frame(header_frame, bg=self.colors['primary'])
        info_container.pack(side='left', fill='y', padx=20, pady=15)
        
        header_label = tk.Label(info_container, text="👥 Gerenciamento de Perfis", 
                               font=('Segoe UI', 16, 'bold'), fg=self.colors['light'], bg=self.colors['primary'])
        header_label.pack(anchor='w')
        
        self.profiles_info_label = tk.Label(info_container, text="Carregando perfis...", 
                                           font=('Segoe UI', 10), fg=self.colors['accent'], bg=self.colors['primary'])
        self.profiles_info_label.pack(anchor='w')
        
        # Botões de ação modernos
        action_container = tk.Frame(header_frame, bg=self.colors['primary'])
        action_container.pack(side='right', padx=20, pady=15)
        
        # Botão Atualizar
        refresh_btn = tk.Button(action_container, text="🔄 Atualizar", 
                               command=self.refresh_profiles,
                               bg=self.colors['accent'], fg=self.colors['light'], 
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat', padx=20, pady=8, cursor='hand2',
                               borderwidth=0)
        refresh_btn.pack(side='right', padx=5)
        
        # Botão Salvar Seleção
        save_btn = tk.Button(action_container, text="💾 Salvar Seleção", 
                            command=self.save_profile_selection,
                            bg=self.colors['success'], fg=self.colors['light'], 
                            font=('Segoe UI', 10, 'bold'),
                            relief='flat', padx=20, pady=8, cursor='hand2',
                            borderwidth=0)
        save_btn.pack(side='right', padx=5)
        
        # Botão Carregar Seleção
        load_btn = tk.Button(action_container, text="📁 Carregar", 
                            command=self.load_profile_selection,
                            bg=self.colors['warning'], fg=self.colors['light'], 
                            font=('Segoe UI', 10, 'bold'),
                            relief='flat', padx=20, pady=8, cursor='hand2',
                            borderwidth=0)
        load_btn.pack(side='right', padx=5)
        
        # Barra de busca moderna
        search_frame = tk.Frame(main_container, bg=self.colors['secondary'], height=60)
        search_frame.pack(fill='x', padx=0, pady=0)
        search_frame.pack_propagate(False)
        
        search_container = tk.Frame(search_frame, bg=self.colors['secondary'])
        search_container.pack(expand=True, fill='both', padx=20, pady=15)
        
        # Ícone de busca
        search_icon = tk.Label(search_container, text="🔍", font=('Segoe UI', 14), 
                              fg=self.colors['accent'], bg=self.colors['secondary'])
        search_icon.pack(side='left', padx=(0, 10))
        
        # Campo de busca estilizado
        self.search_entry = tk.Entry(search_container, font=('Segoe UI', 12), width=40,
                                    bg=self.colors['light'], fg=self.colors['dark'],
                                    relief='flat', bd=8)
        self.search_entry.pack(side='left', padx=5, ipady=5)
        self.search_entry.bind('<KeyRelease>', self.filter_profiles)
        self.search_entry.insert(0, "Digite para buscar perfis...")
        self.search_entry.bind('<FocusIn>', self.clear_search_placeholder)
        self.search_entry.bind('<FocusOut>', self.restore_search_placeholder)
        
        # Botões de seleção em massa modernos
        buttons_container = tk.Frame(search_container, bg=self.colors['secondary'])
        buttons_container.pack(side='right', padx=10)
        
        select_all_btn = tk.Button(buttons_container, text="✅ Todos", 
                                  command=self.select_all_profiles,
                                  bg=self.colors['success'], fg=self.colors['light'], 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', padx=15, pady=6, cursor='hand2',
                                  borderwidth=0)
        select_all_btn.pack(side='left', padx=3)
        
        deselect_all_btn = tk.Button(buttons_container, text="❌ Limpar", 
                                    command=self.deselect_all_profiles,
                                    bg=self.colors['danger'], fg=self.colors['light'], 
                                    font=('Segoe UI', 10, 'bold'),
                                    relief='flat', padx=15, pady=6, cursor='hand2',
                                    borderwidth=0)
        deselect_all_btn.pack(side='left', padx=3)
        
        # Container de perfis com design moderno
        profiles_container = tk.Frame(main_container, bg=self.colors['light'])
        profiles_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Frame principal com scrollbar para checkboxes
        main_frame = tk.Frame(profiles_container, bg=self.colors['light'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas e scrollbar modernos para muitos perfis
        self.profiles_canvas = tk.Canvas(main_frame, bg=self.colors['light'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(main_frame, orient='vertical', command=self.profiles_canvas.yview,
                                bg=self.colors['secondary'], troughcolor=self.colors['light'],
                                activebackground=self.colors['accent'])
        self.profiles_scrollable_frame = tk.Frame(self.profiles_canvas, bg=self.colors['light'])
        
        self.profiles_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.profiles_canvas.configure(scrollregion=self.profiles_canvas.bbox("all"))
        )
        
        self.profiles_canvas.create_window((0, 0), window=self.profiles_scrollable_frame, anchor="nw")
        self.profiles_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.profiles_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Variáveis para checkboxes dos perfis
        self.profile_vars = {}
        self.profile_checkboxes = {}
        
        # Status no rodapé moderno
        status_frame = tk.Frame(main_container, bg=self.colors['primary'], height=50)
        status_frame.pack(fill='x', padx=0, pady=0)
        status_frame.pack_propagate(False)
        
        status_container = tk.Frame(status_frame, bg=self.colors['primary'])
        status_container.pack(expand=True, fill='both', padx=20, pady=12)
        
        self.profiles_status_label = tk.Label(status_container, text="🔄 Aguardando carregamento de perfis...", 
                                             font=('Segoe UI', 11, 'bold'), fg=self.colors['accent'], bg=self.colors['primary'])
        self.profiles_status_label.pack(side='left')
        
        # Contador de selecionados no canto direito
        self.selected_count_label = tk.Label(status_container, text="0 selecionados", 
                                           font=('Segoe UI', 11, 'bold'), fg=self.colors['success'], bg=self.colors['primary'])
        self.selected_count_label.pack(side='right')
    
    def on_profile_selected(self):
        """Callback quando um perfil é selecionado/deselecionado"""
        self.update_selected_profiles()
        self.update_display_count()
    
    def update_display_count(self):
        """Atualizar apenas a exibição do contador"""
        count = len(self.selected_profiles)
        
        if count > 0:
            self.selected_count_label.config(text=f"🎯 {count} selecionados", fg=self.colors['success'])
            self.profiles_status_label.config(text=f"✅ {len(self.profiles)} perfis carregados")
        else:
            self.selected_count_label.config(text="Nenhum selecionado", fg=self.colors['warning'])
            self.profiles_status_label.config(text=f"✅ {len(self.profiles)} perfis carregados")
    
    def save_profile_selection(self):
        """💾 Salvar seleção atual de perfis"""
        try:
            self.update_selected_profiles()
            selected_ids = [profile['user_id'] for profile in self.selected_profiles]
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(selected_ids, f, indent=2)
            
            messagebox.showinfo("✅ Sucesso", f"Seleção de {len(selected_ids)} perfis salva com sucesso!")
            self.logger.info(f"Seleção de {len(selected_ids)} perfis salva em {self.config_file}")
            
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao salvar seleção: {str(e)}")
            self.logger.error(f"Erro ao salvar seleção: {str(e)}")
    
    def load_profile_selection(self):
        """📁 Carregar seleção salva de perfis"""
        try:
            if not os.path.exists(self.config_file):
                messagebox.showinfo("ℹ️ Informação", "Nenhuma seleção salva encontrada.")
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                selected_ids = json.load(f)
            
            # Desmarcar todos primeiro
            self.deselect_all_profiles()
            
            # Marcar os salvos
            loaded_count = 0
            for user_id in selected_ids:
                if user_id in self.profile_vars:
                    self.profile_vars[user_id].set(True)
                    loaded_count += 1
            
            self.update_selected_profiles()
            self.update_display_count()
            messagebox.showinfo("✅ Sucesso", f"Seleção de {loaded_count} perfis carregada com sucesso!")
            self.logger.info(f"Seleção de {loaded_count} perfis carregada de {self.config_file}")
            
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao carregar seleção: {str(e)}")
            self.logger.error(f"Erro ao carregar seleção: {str(e)}")
    
    def load_profile_selection_auto(self):
        """🔄 Carregar seleção automaticamente (silencioso)"""
        try:
            if not os.path.exists(self.config_file):
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                selected_ids = json.load(f)
            
            # Marcar os salvos
            for user_id in selected_ids:
                if user_id in self.profile_vars:
                    self.profile_vars[user_id].set(True)
            
            self.update_selected_profiles()
            self.update_display_count()
            self.logger.info(f"Seleção automática carregada: {len(selected_ids)} perfis")
            
        except Exception as e:
            self.logger.warning(f"Não foi possível carregar seleção automática: {str(e)}")
    
    def clear_search_placeholder(self, event):
        """Limpar placeholder do campo de busca"""
        if self.search_entry.get() == "Digite para buscar perfis...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=self.colors['dark'])
    
    def restore_search_placeholder(self, event):
        """Restaurar placeholder se campo estiver vazio"""
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Digite para buscar perfis...")
            self.search_entry.config(fg=self.colors['muted'])
    
    def setup_campaign_tab(self, notebook):
        """Configurar aba de configuração de campanhas"""
        campaign_frame = ttk.Frame(notebook)
        notebook.add(campaign_frame, text="📈 Configuração de Campanha")
        
        # Frame com scroll
        canvas = tk.Canvas(campaign_frame)
        scrollbar = ttk.Scrollbar(campaign_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configurações básicas da campanha
        basic_frame = tk.LabelFrame(scrollable_frame, text="📋 Configurações Básicas", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        basic_frame.pack(fill='x', padx=10, pady=5)
        
        # Nome da campanha
        tk.Label(basic_frame, text="Nome da Campanha:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.campaign_name_entry = tk.Entry(basic_frame, width=50, font=('Arial', 10))
        self.campaign_name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Orçamento diário
        tk.Label(basic_frame, text="Orçamento Diário (R$):", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.budget_entry = tk.Entry(basic_frame, width=20, font=('Arial', 10))
        self.budget_entry.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        # Tipo de campanha (apenas pesquisa)
        tk.Label(basic_frame, text="Tipo de Campanha:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.campaign_type_label = tk.Label(basic_frame, text="🔍 Pesquisa (Google Search)", 
                                           font=('Arial', 10, 'bold'), fg='#2c3e50')
        self.campaign_type_label.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        # Palavras-chave
        keywords_frame = tk.LabelFrame(scrollable_frame, text="🎯 Palavras-chave", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        keywords_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(keywords_frame, text="Palavras-chave (uma por linha):", font=('Arial', 10)).pack(anchor='w')
        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=8, width=80, font=('Arial', 10))
        self.keywords_text.pack(fill='x', padx=5, pady=5)
        
        # Idioma e Localização
        location_frame = tk.LabelFrame(scrollable_frame, text="🌍 Segmentação Geográfica e Idioma", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        location_frame.pack(fill='x', padx=10, pady=5)
        
        # Idioma
        tk.Label(location_frame, text="Idioma da Campanha:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.language_combo = ttk.Combobox(location_frame, width=30, 
                                          values=["Português (Brasil)", "Português (Portugal)", "Inglês (EUA)", 
                                                 "Inglês (Reino Unido)", "Espanhol", "Francês", "Italiano", "Alemão"])
        self.language_combo.set("Português (Brasil)")
        self.language_combo.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        # Localizações (múltiplas)
        tk.Label(location_frame, text="Localizações (uma por linha):", font=('Arial', 10)).grid(row=1, column=0, sticky='nw', pady=5)
        self.locations_text = scrolledtext.ScrolledText(location_frame, height=4, width=50, font=('Arial', 10))
        self.locations_text.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.locations_text.insert(1.0, "Brasil\nSão Paulo, Brasil\nRio de Janeiro, Brasil")
        
        location_frame.grid_columnconfigure(1, weight=1)
        
        # Anúncios com múltiplos títulos
        ads_frame = tk.LabelFrame(scrollable_frame, text="📝 Configuração dos Anúncios (Até 15 Títulos)", 
                                 font=('Arial', 12, 'bold'), padx=10, pady=10)
        ads_frame.pack(fill='x', padx=10, pady=5)
        
        # Títulos dos anúncios (até 15)
        tk.Label(ads_frame, text="Títulos dos Anúncios (um por linha, até 15):", font=('Arial', 10)).grid(row=0, column=0, sticky='nw', pady=5)
        self.ad_titles_text = scrolledtext.ScrolledText(ads_frame, height=8, width=60, font=('Arial', 10))
        self.ad_titles_text.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        self.ad_titles_text.insert(1.0, "Seu Produto Incrivel Aqui\nOferta Especial Limitada\nSolução Perfeita Para Você")
        
        # Descrições (até 4)
        tk.Label(ads_frame, text="Descrições (uma por linha, até 4):", font=('Arial', 10)).grid(row=1, column=0, sticky='nw', pady=5)
        self.ad_descriptions_text = scrolledtext.ScrolledText(ads_frame, height=4, width=60, font=('Arial', 10))
        self.ad_descriptions_text.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.ad_descriptions_text.insert(1.0, "Descubra a melhor solução do mercado. Qualidade garantida!\nCompre agora e economize até 50%. Entrega rápida em todo Brasil.")
        
        # URL de destino
        tk.Label(ads_frame, text="URL de Destino:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.landing_url_entry = tk.Entry(ads_frame, width=60, font=('Arial', 10))
        self.landing_url_entry.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
        
        ads_frame.grid_columnconfigure(1, weight=1)
        
        # Botões de ação
        action_frame = tk.Frame(scrollable_frame)
        action_frame.pack(fill='x', padx=10, pady=20)
        
        save_config_btn = tk.Button(action_frame, text="💾 Salvar Configuração", 
                                   command=self.save_campaign_config,
                                   bg='#f39c12', fg='white', font=('Arial', 11, 'bold'))
        save_config_btn.pack(side='left', padx=5)
        
        load_config_btn = tk.Button(action_frame, text="📂 Carregar Configuração", 
                                   command=self.load_campaign_config,
                                   bg='#9b59b6', fg='white', font=('Arial', 11, 'bold'))
        load_config_btn.pack(side='left', padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_execution_tab(self, notebook):
        """🚀 Configurar aba de execução MODERNA com botão no canto direito SEMPRE"""
        execution_frame = ttk.Frame(notebook)
        notebook.add(execution_frame, text="▶️ Execução")
        
        # Container principal moderno
        main_container = tk.Frame(execution_frame, bg=self.colors['dark'])
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header de controle MODERNO
        control_frame = tk.Frame(main_container, bg=self.colors['primary'], height=120)
        control_frame.pack(fill='x', padx=0, pady=0)
        control_frame.pack_propagate(False)
        
        # Container interno flexível
        control_container = tk.Frame(control_frame, bg=self.colors['primary'])
        control_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # LADO ESQUERDO - Status e informações
        left_section = tk.Frame(control_container, bg=self.colors['primary'])
        left_section.pack(side='left', fill='y')
        
        # Status atual
        tk.Label(left_section, text="Status da Automação:", 
                font=('Segoe UI', 14, 'bold'), fg=self.colors['light'], bg=self.colors['primary']).pack(anchor='w')
        self.status_label = tk.Label(left_section, text="🟡 Aguardando Inicialização", 
                                    font=('Segoe UI', 12), bg=self.colors['primary'], fg=self.colors['warning'])
        self.status_label.pack(anchor='w', pady=(5, 15))
        
        # Informações de progresso
        tk.Label(left_section, text="Progresso Geral:", 
                font=('Segoe UI', 12, 'bold'), fg=self.colors['light'], bg=self.colors['primary']).pack(anchor='w')
        self.progress_info_label = tk.Label(left_section, text="0 de 0 perfis processados", 
                                          font=('Segoe UI', 10), bg=self.colors['primary'], fg=self.colors['accent'])
        self.progress_info_label.pack(anchor='w')
        
        # CENTRO - Barra de progresso moderna
        center_section = tk.Frame(control_container, bg=self.colors['primary'])
        center_section.pack(side='left', fill='both', expand=True, padx=30)
        
        progress_container = tk.Frame(center_section, bg=self.colors['primary'])
        progress_container.pack(expand=True, fill='y')
        
        # Estilo moderno da barra de progresso
        style = ttk.Style()
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['success'],
                       troughcolor=self.colors['secondary'],
                       borderwidth=0,
                       lightcolor=self.colors['success'],
                       darkcolor=self.colors['success'])
        
        tk.Label(progress_container, text="Progresso da Execução:", 
                font=('Segoe UI', 12, 'bold'), fg=self.colors['light'], bg=self.colors['primary']).pack(pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(progress_container, 
                                          style='Modern.Horizontal.TProgressbar',
                                          mode='determinate', length=300)
        self.progress_bar.pack(pady=10)
        
        self.progress_percentage = tk.Label(progress_container, text="0%", 
                                           font=('Segoe UI', 12, 'bold'), 
                                           fg=self.colors['success'], bg=self.colors['primary'])
        self.progress_percentage.pack()
        
        # LADO DIREITO - Botões de controle (SEMPRE NO CANTO DIREITO)
        right_section = tk.Frame(control_container, bg=self.colors['primary'])
        right_section.pack(side='right', fill='y')
        
        # Container dos botões fixo no canto direito
        buttons_container = tk.Frame(right_section, bg=self.colors['primary'])
        buttons_container.pack(expand=True, fill='y')
        
        # BOTÃO INICIAR - SEMPRE VISÍVEL NO CANTO DIREITO
        self.start_btn = tk.Button(buttons_container, text="▶️ INICIAR AUTOMAÇÃO", 
                                  command=self.start_automation,
                                  bg=self.colors['success'], fg=self.colors['light'], 
                                  font=('Segoe UI', 14, 'bold'),
                                  relief='flat', padx=30, pady=15, cursor='hand2',
                                  borderwidth=0, width=20)
        self.start_btn.pack(pady=(10, 5))
        
        # Botão Parar
        self.stop_btn = tk.Button(buttons_container, text="⏹️ PARAR", 
                                 command=self.stop_automation,
                                 bg=self.colors['danger'], fg=self.colors['light'], 
                                 font=('Segoe UI', 12, 'bold'),
                                 relief='flat', padx=30, pady=10, cursor='hand2',
                                 borderwidth=0, width=20, state='disabled')
        self.stop_btn.pack(pady=5)
        
        # Botão Limpar Logs
        clear_logs_btn = tk.Button(buttons_container, text="🗑️ Limpar Logs", 
                                  command=self.clear_logs,
                                  bg=self.colors['muted'], fg=self.colors['light'], 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', padx=20, pady=8, cursor='hand2',
                                  borderwidth=0, width=20)
        clear_logs_btn.pack(pady=5)
        
        # ÁREA DE LOGS MODERNA
        log_container = tk.Frame(main_container, bg=self.colors['light'])
        log_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header dos logs
        log_header = tk.Frame(log_container, bg=self.colors['secondary'], height=40)
        log_header.pack(fill='x', padx=0, pady=0)
        log_header.pack_propagate(False)
        
        log_title = tk.Label(log_header, text="📋 Logs de Execução em Tempo Real", 
                            font=('Segoe UI', 12, 'bold'), 
                            fg=self.colors['light'], bg=self.colors['secondary'])
        log_title.pack(side='left', padx=15, pady=10)
        
        # Timestamp dos logs
        self.log_timestamp = tk.Label(log_header, text="Última atualização: --:--:--", 
                                     font=('Segoe UI', 9), 
                                     fg=self.colors['accent'], bg=self.colors['secondary'])
        self.log_timestamp.pack(side='right', padx=15, pady=10)
        
        # Área de logs com estilo moderno
        log_frame = tk.Frame(log_container, bg=self.colors['light'])
        log_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, 
                                                 font=('Consolas', 10),
                                                 bg=self.colors['dark'], 
                                                 fg=self.colors['light'],
                                                 insertbackground=self.colors['accent'],
                                                 selectbackground=self.colors['accent'],
                                                 wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configurar handler personalizado para logs
        self.setup_log_handler()
        
        # Configurar cores para logs
        self.setup_log_colors()
    
    def clear_logs(self):
        """Limpar logs da interface"""
        self.log_text.delete(1.0, tk.END)
        self.log_timestamp.config(text="Logs limpos")
        self.logger.info("🗑️ Logs da interface limpos pelo usuário")
    
    def setup_log_colors(self):
        """Configurar cores para diferentes tipos de log"""
        self.log_text.tag_configure('INFO', foreground=self.colors['light'])
        self.log_text.tag_configure('WARNING', foreground=self.colors['warning'])
        self.log_text.tag_configure('ERROR', foreground=self.colors['danger'])
        self.log_text.tag_configure('SUCCESS', foreground=self.colors['success'])
        self.log_text.tag_configure('DEBUG', foreground=self.colors['muted'])
    
    def setup_settings_tab(self, notebook):
        """Configurar aba de configurações"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Configurações")
        
        # Configurações do AdsPower
        adspower_frame = tk.LabelFrame(settings_frame, text="AdsPower API", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        adspower_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(adspower_frame, text="URL da API:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.api_url_entry = tk.Entry(adspower_frame, width=40, font=('Arial', 10))
        self.api_url_entry.insert(0, "http://localhost:50325")
        self.api_url_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Configurações de automação
        automation_frame = tk.LabelFrame(settings_frame, text="Automação", 
                                        font=('Arial', 12, 'bold'), padx=10, pady=10)
        automation_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(automation_frame, text="Delay entre ações (segundos):", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.delay_entry = tk.Entry(automation_frame, width=10, font=('Arial', 10))
        self.delay_entry.insert(0, "3")
        self.delay_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        tk.Label(automation_frame, text="Timeout de página (segundos):", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.timeout_entry = tk.Entry(automation_frame, width=10, font=('Arial', 10))
        self.timeout_entry.insert(0, "30")
        self.timeout_entry.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        # Modo headless
        self.headless_var = tk.BooleanVar()
        headless_check = tk.Checkbutton(automation_frame, text="Executar em modo invisível (headless)", 
                                       variable=self.headless_var, font=('Arial', 10))
        headless_check.grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
    
    def setup_log_handler(self):
        """Configurar handler personalizado para exibir logs na interface"""
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                self.text_widget.after(0, append)
        
        gui_handler = GuiLogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(gui_handler)
    
    def refresh_profiles(self):
        """Atualizar lista de perfis do AdsPower com checkboxes"""
        try:
            profiles = self.adspower_manager.get_profiles()
            self.profiles = profiles
            
            # Limpar checkboxes anteriores
            for widget in self.profiles_scrollable_frame.winfo_children():
                widget.destroy()
            
            self.profile_vars.clear()
            self.profile_checkboxes.clear()
            
            # Criar checkboxes para cada perfil
            for i, profile in enumerate(profiles):
                # Criar variável para checkbox
                var = tk.BooleanVar()
                self.profile_vars[profile['user_id']] = var
                
                # Criar frame moderno para cada perfil
                profile_frame = tk.Frame(self.profiles_scrollable_frame, bg=self.colors['light'], 
                                       relief='solid', bd=1, highlightbackground=self.colors['accent'])
                profile_frame.pack(fill='x', padx=8, pady=3)
                
                # Hover effect
                def on_enter(event, frame=profile_frame):
                    frame.config(bg=self.colors['accent'], relief='raised')
                def on_leave(event, frame=profile_frame):
                    frame.config(bg=self.colors['light'], relief='solid')
                
                profile_frame.bind('<Enter>', on_enter)
                profile_frame.bind('<Leave>', on_leave)
                
                # Checkbox moderno
                checkbox = tk.Checkbutton(profile_frame, 
                                        text=f"👤 {profile['name']} (ID: {profile['user_id']})",
                                        variable=var,
                                        bg=self.colors['light'],
                                        fg=self.colors['dark'],
                                        font=('Segoe UI', 11),
                                        anchor='w',
                                        activebackground=self.colors['accent'],
                                        activeforeground=self.colors['light'],
                                        selectcolor=self.colors['success'],
                                        command=self.on_profile_selected,
                                        cursor='hand2')
                checkbox.pack(fill='x', padx=15, pady=8)
                
                # Bind hover para checkbox também
                checkbox.bind('<Enter>', on_enter)
                checkbox.bind('<Leave>', on_leave)
                
                self.profile_checkboxes[profile['user_id']] = checkbox
            
            # Atualizar status e informações
            self.profiles_status_label.config(text=f"✅ {len(profiles)} perfis carregados do AdsPower")
            self.profiles_info_label.config(text=f"{len(profiles)} perfis disponíveis")
            self.connection_status.config(text="✅ Conectado ao AdsPower", fg=self.colors['success'])
            self.logger.info(f"Carregados {len(profiles)} perfis do AdsPower")
            
            # Carregar seleção salva automaticamente
            self.load_profile_selection_auto()
            
        except Exception as e:
            self.profiles_status_label.config(text="❌ Erro ao carregar perfis")
            self.profiles_info_label.config(text="Erro na conexão")
            self.connection_status.config(text="❌ Desconectado", fg=self.colors['danger'])
            messagebox.showerror("Erro", f"Erro ao carregar perfis: {str(e)}")
            self.logger.error(f"Erro ao carregar perfis: {str(e)}")
    
    def update_selected_profiles(self):
        """Atualizar perfis selecionados baseado nos checkboxes"""
        self.selected_profiles = []
        
        for profile in self.profiles:
            if self.profile_vars.get(profile['user_id'], tk.BooleanVar()).get():
                self.selected_profiles.append(profile)
    
    def update_selected_count(self):
        """Atualizar contador de perfis selecionados"""
        # CORREÇÃO: Não chamar update_selected_profiles() aqui para evitar recursão
        self.update_selected_profiles()  # Atualizar uma única vez
        count = len(self.selected_profiles)
        
        # Atualizar contador no canto direito
        if count > 0:
            self.selected_count_label.config(text=f"🎯 {count} selecionados", fg=self.colors['success'])
            self.profiles_status_label.config(text=f"✅ {len(self.profiles)} perfis carregados")
        else:
            self.selected_count_label.config(text="Nenhum selecionado", fg=self.colors['warning'])
            self.profiles_status_label.config(text=f"✅ {len(self.profiles)} perfis carregados")
    
    def filter_profiles(self, event=None):
        """Filtrar perfis com base na busca"""
        search_term = self.search_entry.get().lower()
        
        for profile in self.profiles:
            checkbox = self.profile_checkboxes.get(profile['user_id'])
            if checkbox:
                profile_name = profile['name'].lower()
                if search_term in profile_name or search_term in profile['user_id'].lower():
                    checkbox.master.pack(fill='x', padx=5, pady=2)
                else:
                    checkbox.master.pack_forget()
    
    def select_all_profiles(self):
        """Selecionar todos os perfis visíveis"""
        for user_id, var in self.profile_vars.items():
            checkbox = self.profile_checkboxes.get(user_id)
            if checkbox and checkbox.master.winfo_viewable():
                var.set(True)
        self.update_selected_profiles()
        self.update_display_count()
    
    def deselect_all_profiles(self):
        """Deselecionar todos os perfis"""
        for var in self.profile_vars.values():
            var.set(False)
        self.update_selected_profiles()
        self.update_display_count()
    
    def save_campaign_config(self):
        """Salvar configuração da campanha"""
        config = self.get_campaign_config()
        
        filename = filedialog.asksaveasfilename(
            title="Salvar Configuração de Campanha",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
                self.logger.info(f"Configuração salva em: {filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")
    
    def load_campaign_config(self):
        """Carregar configuração da campanha"""
        filename = filedialog.askopenfilename(
            title="Carregar Configuração de Campanha",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.set_campaign_config(config)
                messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")
                self.logger.info(f"Configuração carregada de: {filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar: {str(e)}")
    
    def get_campaign_config(self):
        """Obter configuração atual da campanha"""
        keywords = [k.strip() for k in self.keywords_text.get(1.0, tk.END).strip().split('\n') if k.strip()]
        locations = [l.strip() for l in self.locations_text.get(1.0, tk.END).strip().split('\n') if l.strip()]
        ad_titles = [t.strip() for t in self.ad_titles_text.get(1.0, tk.END).strip().split('\n') if t.strip()][:15]  # Máximo 15 títulos
        ad_descriptions = [d.strip() for d in self.ad_descriptions_text.get(1.0, tk.END).strip().split('\n') if d.strip()][:4]  # Máximo 4 descrições
        
        return {
            'campaign_name': self.campaign_name_entry.get(),
            'budget': self.budget_entry.get(),
            'campaign_type': 'Pesquisa',  # Sempre pesquisa
            'language': self.language_combo.get(),
            'keywords': keywords,
            'locations': locations,
            'ad_titles': ad_titles,
            'ad_descriptions': ad_descriptions,
            'landing_url': self.landing_url_entry.get(),
            'delay': self.delay_entry.get(),
            'timeout': self.timeout_entry.get(),
            'headless': self.headless_var.get()
        }
    
    def set_campaign_config(self, config):
        """Definir configuração da campanha"""
        self.campaign_name_entry.delete(0, tk.END)
        self.campaign_name_entry.insert(0, config.get('campaign_name', ''))
        
        self.budget_entry.delete(0, tk.END)
        self.budget_entry.insert(0, config.get('budget', ''))
        
        # Idioma
        self.language_combo.set(config.get('language', 'Português (Brasil)'))
        
        # Palavras-chave
        self.keywords_text.delete(1.0, tk.END)
        self.keywords_text.insert(1.0, '\n'.join(config.get('keywords', [])))
        
        # Localizações múltiplas
        self.locations_text.delete(1.0, tk.END)
        locations = config.get('locations', config.get('location', 'Brasil'))  # Compatibilidade com versão antiga
        if isinstance(locations, str):
            self.locations_text.insert(1.0, locations)
        else:
            self.locations_text.insert(1.0, '\n'.join(locations))
        
        # Títulos múltiplos
        self.ad_titles_text.delete(1.0, tk.END)
        ad_titles = config.get('ad_titles', [config.get('ad_title', '')])  # Compatibilidade com versão antiga
        if isinstance(ad_titles, str):
            self.ad_titles_text.insert(1.0, ad_titles)
        else:
            self.ad_titles_text.insert(1.0, '\n'.join(ad_titles))
        
        # Descrições múltiplas
        self.ad_descriptions_text.delete(1.0, tk.END)
        ad_descriptions = config.get('ad_descriptions', [config.get('ad_description', '')])  # Compatibilidade com versão antiga
        if isinstance(ad_descriptions, str):
            self.ad_descriptions_text.insert(1.0, ad_descriptions)
        else:
            self.ad_descriptions_text.insert(1.0, '\n'.join(ad_descriptions))
        
        # URL de destino
        self.landing_url_entry.delete(0, tk.END)
        self.landing_url_entry.insert(0, config.get('landing_url', ''))
    
    def start_automation(self):
        """Iniciar automação"""
        # CORREÇÃO DO BUG: Atualizar perfis selecionados antes da verificação
        self.update_selected_profiles()
        
        if not self.selected_profiles:
            messagebox.showwarning("⚠️ Aviso", "Selecione pelo menos um perfil do AdsPower!")
            return
        
        config = self.get_campaign_config()
        if not config['campaign_name'] or not config['keywords']:
            messagebox.showwarning("Aviso", "Preencha pelo menos o nome da campanha e palavras-chave!")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="🟢 Executando", fg='#27ae60')
        
        # Executar automação em thread separada
        automation_thread = threading.Thread(target=self.run_automation, args=(config,))
        automation_thread.daemon = True
        automation_thread.start()
    
    def stop_automation(self):
        """Parar automação"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="🔴 Parado", fg='#e74c3c')
        self.logger.info("Automação interrompida pelo usuário")
    
    def run_automation(self, config):
        """Executar automação em todos os perfis selecionados"""
        total_profiles = len(self.selected_profiles)
        
        try:
            for i, profile in enumerate(self.selected_profiles):
                if not self.is_running:
                    break
                
                self.logger.info(f"Iniciando automação no perfil: {profile['name']}")
                
                # Atualizar progresso
                progress = (i / total_profiles) * 100
                self.progress_bar.config(value=progress)
                
                browser_info = None
                try:
                    # 1. Iniciar browser do AdsPower para este perfil
                    self.logger.info(f"Iniciando browser AdsPower para perfil: {profile['name']}")
                    browser_info = self.adspower_manager.start_browser(profile['user_id'])
                    
                    if not browser_info:
                        self.logger.error(f"Falha ao iniciar browser para perfil: {profile['name']}")
                        continue
                    
                    # 2. Aguardar browser inicializar e LOG DETALHADO
                    self.logger.info(f"📋 INFORMAÇÕES DETALHADAS do browser: {browser_info}")
                    time.sleep(5)
                    
                    # 3. EXECUTAR AUTOMAÇÃO com logs detalhados
                    self.logger.info(f"🚀 INICIANDO automação para perfil: {profile['name']}")
                    success = self.automation.create_campaign_with_browser(profile, config, browser_info)
                    self.logger.info(f"📊 RESULTADO da automação: {'SUCESSO' if success else 'FALHA'}")
                    
                    if success:
                        self.logger.info(f"🎉 SUCESSO TOTAL: Campanha criada no perfil: {profile['name']}")
                    else:
                        self.logger.error(f"💥 FALHA CRÍTICA: Não foi possível criar campanha no perfil: {profile['name']}")
                        self.logger.error(f"🔍 Verifique os logs detalhados acima para identificar o problema")
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro no perfil {profile['name']}: {str(e)}")
                
                finally:
                    # 4. Sempre fechar o browser do perfil ao final
                    if browser_info:
                        try:
                            self.adspower_manager.stop_browser(profile['user_id'])
                            self.logger.info(f"Browser fechado para perfil: {profile['name']}")
                        except Exception as e:
                            self.logger.warning(f"Erro ao fechar browser do perfil {profile['name']}: {str(e)}")
                
                # Atualizar progresso final para este perfil
                progress = ((i + 1) / total_profiles) * 100
                self.progress_bar.config(value=progress)
            
            if self.is_running:
                self.logger.info("🎉 Automação concluída em todos os perfis!")
                messagebox.showinfo("Concluído", "Automação finalizada com sucesso!")
            
        except Exception as e:
            self.logger.error(f"Erro geral na automação: {str(e)}")
            messagebox.showerror("Erro", f"Erro na automação: {str(e)}")
        
        finally:
            # Resetar interface
            self.is_running = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="🟡 Aguardando", fg='#f39c12')
            if self.progress_bar['value'] == 100:
                self.progress_bar.config(value=0)

def main():
    """Função principal"""
    root = tk.Tk()
    app = GoogleAdsCampaignBot(root)
    
    # Configurar ícone da janela (se disponível)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()