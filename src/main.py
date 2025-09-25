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
        self.root.title("Google Ads Campaign Bot - AdsPower Integration")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar componentes
        self.config = Config()
        self.logger = setup_logger()
        self.adspower_manager = AdsPowerManager()
        self.automation = GoogleAdsAutomation()
        
        # Variáveis de estado
        self.profiles = []
        self.selected_profiles = []
        self.campaign_config = {}
        self.is_running = False
        
        self.setup_ui()
        self.refresh_profiles()
    
    def setup_ui(self):
        """Configurar a interface do usuário"""
        
        # Título principal
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🚀 Google Ads Campaign Bot", 
                              font=('Arial', 18, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=15)
        
        # Frame principal com abas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Aba 1: Configuração de Perfis
        self.setup_profiles_tab(notebook)
        
        # Aba 2: Configuração de Campanhas
        self.setup_campaign_tab(notebook)
        
        # Aba 3: Execução e Logs
        self.setup_execution_tab(notebook)
        
        # Aba 4: Configurações
        self.setup_settings_tab(notebook)
    
    def setup_profiles_tab(self, notebook):
        """Configurar aba de perfis do AdsPower"""
        profiles_frame = ttk.Frame(notebook)
        notebook.add(profiles_frame, text="👥 Perfis AdsPower")
        
        # Frame superior - controles
        control_frame = tk.Frame(profiles_frame, bg='#ecf0f1', height=80)
        control_frame.pack(fill='x', padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        tk.Label(control_frame, text="Perfis do AdsPower:", 
                font=('Arial', 12, 'bold'), bg='#ecf0f1').pack(side='left', pady=20)
        
        refresh_btn = tk.Button(control_frame, text="🔄 Atualizar Perfis", 
                               command=self.refresh_profiles,
                               bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        refresh_btn.pack(side='right', padx=10, pady=20)
        
        # Lista de perfis com checkboxes
        list_frame = tk.Frame(profiles_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbar para lista
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.profiles_listbox = tk.Listbox(list_frame, selectmode='multiple',
                                          yscrollcommand=scrollbar.set,
                                          font=('Arial', 10))
        self.profiles_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=self.profiles_listbox.yview)
        
        # Frame inferior - perfis selecionados
        selected_frame = tk.Frame(profiles_frame, bg='#ecf0f1', height=100)
        selected_frame.pack(fill='x', padx=10, pady=5)
        selected_frame.pack_propagate(False)
        
        tk.Label(selected_frame, text="Perfis Selecionados:", 
                font=('Arial', 10, 'bold'), bg='#ecf0f1').pack(anchor='w', padx=10, pady=5)
        
        self.selected_label = tk.Label(selected_frame, text="Nenhum perfil selecionado", 
                                      bg='#ecf0f1', fg='#7f8c8d')
        self.selected_label.pack(anchor='w', padx=10)
        
        select_btn = tk.Button(selected_frame, text="✓ Confirmar Seleção", 
                              command=self.update_selected_profiles,
                              bg='#27ae60', fg='white', font=('Arial', 10, 'bold'))
        select_btn.pack(side='right', padx=10, pady=5)
    
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
        
        # Tipo de campanha
        tk.Label(basic_frame, text="Tipo de Campanha:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.campaign_type_combo = ttk.Combobox(basic_frame, width=30, 
                                               values=["Pesquisa", "Display", "Shopping", "Vídeo"])
        self.campaign_type_combo.set("Pesquisa")
        self.campaign_type_combo.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        # Palavras-chave
        keywords_frame = tk.LabelFrame(scrollable_frame, text="🎯 Palavras-chave", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        keywords_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(keywords_frame, text="Palavras-chave (uma por linha):", font=('Arial', 10)).pack(anchor='w')
        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=8, width=80, font=('Arial', 10))
        self.keywords_text.pack(fill='x', padx=5, pady=5)
        
        # Localização
        location_frame = tk.LabelFrame(scrollable_frame, text="📍 Segmentação Geográfica", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        location_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(location_frame, text="Localização:", font=('Arial', 10)).pack(anchor='w')
        self.location_entry = tk.Entry(location_frame, width=50, font=('Arial', 10))
        self.location_entry.pack(fill='x', padx=5, pady=5)
        self.location_entry.insert(0, "Brasil")
        
        # Anúncios
        ads_frame = tk.LabelFrame(scrollable_frame, text="📝 Configuração dos Anúncios", 
                                 font=('Arial', 12, 'bold'), padx=10, pady=10)
        ads_frame.pack(fill='x', padx=10, pady=5)
        
        # Título do anúncio
        tk.Label(ads_frame, text="Título do Anúncio:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.ad_title_entry = tk.Entry(ads_frame, width=50, font=('Arial', 10))
        self.ad_title_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Descrição
        tk.Label(ads_frame, text="Descrição:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.ad_description_entry = tk.Entry(ads_frame, width=50, font=('Arial', 10))
        self.ad_description_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # URL de destino
        tk.Label(ads_frame, text="URL de Destino:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.landing_url_entry = tk.Entry(ads_frame, width=50, font=('Arial', 10))
        self.landing_url_entry.grid(row=2, column=1, padx=10, pady=5)
        
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
        """Configurar aba de execução e logs"""
        execution_frame = ttk.Frame(notebook)
        notebook.add(execution_frame, text="▶️ Execução e Logs")
        
        # Frame de controle
        control_frame = tk.Frame(execution_frame, bg='#ecf0f1', height=100)
        control_frame.pack(fill='x', padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        # Status
        status_frame = tk.Frame(control_frame, bg='#ecf0f1')
        status_frame.pack(side='left', fill='y', padx=10, pady=10)
        
        tk.Label(status_frame, text="Status:", font=('Arial', 12, 'bold'), bg='#ecf0f1').pack(anchor='w')
        self.status_label = tk.Label(status_frame, text="🟡 Aguardando", 
                                    font=('Arial', 10), bg='#ecf0f1', fg='#f39c12')
        self.status_label.pack(anchor='w')
        
        # Progresso
        progress_frame = tk.Frame(control_frame, bg='#ecf0f1')
        progress_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(progress_frame, text="Progresso:", font=('Arial', 12, 'bold'), bg='#ecf0f1').pack(anchor='w')
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # Botões de controle
        button_frame = tk.Frame(control_frame, bg='#ecf0f1')
        button_frame.pack(side='right', padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="▶️ Iniciar Automação", 
                                  command=self.start_automation,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'))
        self.start_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Parar", 
                                 command=self.stop_automation,
                                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                 state='disabled')
        self.stop_btn.pack(pady=5)
        
        # Área de logs
        log_frame = tk.LabelFrame(execution_frame, text="📋 Logs de Execução", 
                                 font=('Arial', 12, 'bold'))
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Adicionar handler personalizado para logs
        self.setup_log_handler()
    
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
        """Atualizar lista de perfis do AdsPower"""
        try:
            profiles = self.adspower_manager.get_profiles()
            self.profiles = profiles
            
            self.profiles_listbox.delete(0, tk.END)
            for profile in profiles:
                display_text = f"{profile['name']} (ID: {profile['user_id']})"
                self.profiles_listbox.insert(tk.END, display_text)
            
            self.logger.info(f"Carregados {len(profiles)} perfis do AdsPower")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar perfis: {str(e)}")
            self.logger.error(f"Erro ao carregar perfis: {str(e)}")
    
    def update_selected_profiles(self):
        """Atualizar perfis selecionados"""
        selected_indices = self.profiles_listbox.curselection()
        self.selected_profiles = [self.profiles[i] for i in selected_indices]
        
        if self.selected_profiles:
            profile_names = [p['name'] for p in self.selected_profiles]
            self.selected_label.config(text=f"{len(profile_names)} perfis: {', '.join(profile_names[:3])}")
            if len(profile_names) > 3:
                self.selected_label.config(text=self.selected_label.cget('text') + f" e mais {len(profile_names) - 3}")
        else:
            self.selected_label.config(text="Nenhum perfil selecionado")
    
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
        
        return {
            'campaign_name': self.campaign_name_entry.get(),
            'budget': self.budget_entry.get(),
            'campaign_type': self.campaign_type_combo.get(),
            'keywords': keywords,
            'location': self.location_entry.get(),
            'ad_title': self.ad_title_entry.get(),
            'ad_description': self.ad_description_entry.get(),
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
        
        self.campaign_type_combo.set(config.get('campaign_type', 'Pesquisa'))
        
        self.keywords_text.delete(1.0, tk.END)
        self.keywords_text.insert(1.0, '\n'.join(config.get('keywords', [])))
        
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, config.get('location', 'Brasil'))
        
        self.ad_title_entry.delete(0, tk.END)
        self.ad_title_entry.insert(0, config.get('ad_title', ''))
        
        self.ad_description_entry.delete(0, tk.END)
        self.ad_description_entry.insert(0, config.get('ad_description', ''))
        
        self.landing_url_entry.delete(0, tk.END)
        self.landing_url_entry.insert(0, config.get('landing_url', ''))
    
    def start_automation(self):
        """Iniciar automação"""
        if not self.selected_profiles:
            messagebox.showwarning("Aviso", "Selecione pelo menos um perfil do AdsPower!")
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
                    
                    # 2. Aguardar browser inicializar
                    time.sleep(5)
                    
                    # 3. Executar automação para este perfil
                    success = self.automation.create_campaign_with_browser(profile, config, browser_info)
                    
                    if success:
                        self.logger.info(f"✅ Campanha criada com sucesso no perfil: {profile['name']}")
                    else:
                        self.logger.error(f"❌ Falha ao criar campanha no perfil: {profile['name']}")
                        
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