# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter as ctk
import socket, os, sys, threading, time, requests, re, json

try:
    import FPGA
except ImportError:
    pass

# ========== PREMIUM AESTHETIC CONFIGURATION ==========
COLORS = {
    "bg_base": "#0D1117",        
    "bg_panel": "#161B22",       
    "bg_input": "#010409",       
    "accent_primary": "#2F81F7", 
    "accent_hover": "#388BFD",
    "success": "#238636",        
    "success_hover": "#2EA043",
    "warning": "#D29922",        
    "error_bg": "#2C1414",       
    "error_fg": "#F85149",
    "text_main": "#E6EDF3",
    "text_muted": "#8B949E",
    "border": "#30363D",
    "stepper_inactive": "#484F58",
    "sidebar": "#010409"
}

ctk.set_appearance_mode("Dark")

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ========== MAIN APPLICATION CLASS ==========
class GranjaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title('Remote FPGA Farm Orchestrator')
        self.geometry('1150x850')
        self.minsize(1050, 750)
        self.configure(fg_color=COLORS["bg_base"])
        
        try:
            self.iconbitmap(resource_path("micro.ico"))
        except:
            pass

        self.fonts = {
            "h1": ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            "h2": ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            "h3": ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            "body": ctk.CTkFont(family="Segoe UI", size=13),
            "body_mono": ctk.CTkFont(family="Consolas", size=12)
        }

        self.modo_netbird = ctk.BooleanVar(value=False)
        self.usar_ia = ctk.BooleanVar(value=False)
        self.check_value = ctk.BooleanVar(value=False)
        
        self.build_login_gateway()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # -------------------------------------------------------------------------
    # 1. LOGIN GATEWAY
    # -------------------------------------------------------------------------
    def build_login_gateway(self):
        self.login_container = ctk.CTkFrame(self, fg_color="transparent")
        self.login_container.place(relx=0.5, rely=0.5, anchor="center")
        
        self.login_card = ctk.CTkFrame(self.login_container, fg_color=COLORS["bg_panel"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        self.login_card.pack(ipadx=40, ipady=30)
        
        ctk.CTkLabel(self.login_card, text="FPGA FARM", font=self.fonts["h1"], text_color=COLORS["text_main"]).pack(pady=(20, 5))
        ctk.CTkLabel(self.login_card, text="Secure Authentication Required", font=self.fonts["body"], text_color=COLORS["text_muted"]).pack(pady=(0, 30))
        
        self.pass_entry = ctk.CTkEntry(self.login_card, placeholder_text="Enter secret key...", show="•", width=260, height=40, font=self.fonts["body"], fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.pass_entry.pack(pady=10)
        self.pass_entry.bind("<Return>", lambda e: self.verify_login())
        
        self.login_btn = ctk.CTkButton(self.login_card, text="Initialize Session", command=self.verify_login, fg_color=COLORS["accent_primary"], hover_color=COLORS["accent_hover"], font=self.fonts["h3"], height=40, width=260)
        self.login_btn.pack(pady=(20, 20))

    def verify_login(self):
        if self.pass_entry.get() == "Dronelab4.0": 
            self.login_container.destroy()
            self.build_app_shell()
        else:
            self.pass_entry.configure(border_color=COLORS["error_fg"]) 

    # -------------------------------------------------------------------------
    # 2. APP SHELL & NAVIGATION
    # -------------------------------------------------------------------------
    def build_app_shell(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="LAB 4.0 FPGA FARM", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=COLORS["accent_primary"]).pack(pady=(30, 40), padx=20)

        self.btn_nav_deploy = self.create_nav_button("🚀 Deploy Hub", "deploy")
        self.btn_nav_farm = self.create_nav_button("📡 Farm Telemetry", "farm")
        self.btn_nav_settings = self.create_nav_button("⚙️ Settings", "settings")

        self.view_deploy = ctk.CTkFrame(self, fg_color="transparent")
        self.view_farm = ctk.CTkFrame(self, fg_color="transparent")
        self.view_settings = ctk.CTkFrame(self, fg_color="transparent")

        self.build_view_deploy()
        self.build_view_farm()
        self.build_view_settings()

        threading.Thread(target=self.update_dashboard_loop, daemon=True).start()
        self.select_view("deploy")

    def create_nav_button(self, text, view_name):
        btn = ctk.CTkButton(
            self.sidebar, text=text, font=self.fonts["h3"], text_color=COLORS["text_muted"],
            fg_color="transparent", hover_color=COLORS["bg_panel"], anchor="w", height=45,
            command=lambda: self.select_view(view_name)
        )
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def select_view(self, view_name):
        for btn in [self.btn_nav_deploy, self.btn_nav_farm, self.btn_nav_settings]:
            btn.configure(fg_color="transparent", text_color=COLORS["text_muted"])
        
        self.view_deploy.grid_forget()
        self.view_farm.grid_forget()
        self.view_settings.grid_forget()

        if view_name == "deploy":
            self.btn_nav_deploy.configure(fg_color=COLORS["bg_panel"], text_color=COLORS["text_main"])
            self.view_deploy.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        elif view_name == "farm":
            self.btn_nav_farm.configure(fg_color=COLORS["bg_panel"], text_color=COLORS["text_main"])
            self.view_farm.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        elif view_name == "settings":
            self.btn_nav_settings.configure(fg_color=COLORS["bg_panel"], text_color=COLORS["text_main"])
            self.view_settings.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    # -------------------------------------------------------------------------
    # 3. VIEW: DEPLOY HUB
    # -------------------------------------------------------------------------
    def build_view_deploy(self):
        ctk.CTkLabel(self.view_deploy, text="Deployment Canvas", font=self.fonts["h1"]).pack(anchor="w", pady=(0, 20))

        self.deploy_panel = ctk.CTkFrame(self.view_deploy, fg_color=COLORS["bg_panel"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        self.deploy_panel.pack(fill="x", pady=(0, 20))

        toggles_frame = ctk.CTkFrame(self.deploy_panel, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.ia_switch = ctk.CTkSwitch(toggles_frame, text="AI Auto-Routing", variable=self.usar_ia, command=self.toggle_ia, progress_color=COLORS["warning"], font=self.fonts["h3"])
        self.ia_switch.pack(side="left")

        route_frame = ctk.CTkFrame(self.deploy_panel, fg_color="transparent")
        route_frame.pack(fill="x", padx=20, pady=10)
        
        self.routetxt = ctk.CTkEntry(route_frame, placeholder_text="Select Quartus Project (.qpf)", state='readonly', fg_color=COLORS["bg_input"], border_color=COLORS["border"], height=40)
        self.routetxt.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.programtxt = ctk.CTkOptionMenu(route_frame, values=["Empty"], fg_color=COLORS["bg_input"], button_color=COLORS["border"], height=40)
        
        self.btn_examinar_proyecto = ctk.CTkButton(route_frame, text="Browse", command=self.get_route, fg_color=COLORS["border"], hover_color=COLORS["bg_base"], text_color=COLORS["text_main"], width=90, height=40)
        self.btn_examinar_proyecto.pack(side="right")

        opts_frame = ctk.CTkFrame(self.deploy_panel, fg_color="transparent")
        opts_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.fpgatxt = ctk.CTkOptionMenu(opts_frame, values=["No FPGAs detected"], fg_color=COLORS["bg_input"], button_color=COLORS["border"], height=40)
        self.fpgatxt.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.carreratxt = ctk.CTkOptionMenu(opts_frame, values=['Mechatronics', 'Physics', 'Software', 'Computing', 'Other'], fg_color=COLORS["bg_input"], button_color=COLORS["border"], height=40)
        self.carreratxt.pack(side="right", fill="x", expand=True)

        self.program_button = ctk.CTkButton(self.deploy_panel, text="COMPILE & DEPLOY", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), fg_color=COLORS["success"], text_color="#FFFFFF", hover_color=COLORS["success_hover"], command=self.ejecutar_programacion, height=55)
        self.program_button.pack(fill="x", padx=20, pady=(0, 20))

        self.stepper_container = ctk.CTkFrame(self.view_deploy, fg_color="transparent")
        self.stepper_container.pack(fill="x", pady=(10, 20))
        
        stepper_labels = ctk.CTkFrame(self.stepper_container, fg_color="transparent")
        stepper_labels.pack(pady=(0, 10))
        
        self.step1_lbl = ctk.CTkLabel(stepper_labels, text="[ ] Parse Metrics", font=self.fonts["h3"], text_color=COLORS["stepper_inactive"])
        self.step1_lbl.pack(side="left", padx=10)
        self.step2_lbl = ctk.CTkLabel(stepper_labels, text=" ➔  [ ] AI Allocation", font=self.fonts["h3"], text_color=COLORS["stepper_inactive"])
        self.step2_lbl.pack(side="left", padx=10)
        self.step3_lbl = ctk.CTkLabel(stepper_labels, text=" ➔  [ ] SSH Deploying", font=self.fonts["h3"], text_color=COLORS["stepper_inactive"])
        self.step3_lbl.pack(side="left", padx=10)

        self.deploy_progress = ctk.CTkProgressBar(self.stepper_container, mode="indeterminate", progress_color=COLORS["accent_primary"], fg_color=COLORS["bg_input"], height=6)
        self.deploy_progress.pack(fill="x", padx=20)
        self.deploy_progress.set(0)

        self.termf = ctk.CTkTextbox(self.view_deploy, font=self.fonts["body_mono"], fg_color=COLORS["bg_panel"], text_color=COLORS["text_muted"], wrap="word", border_width=1, border_color=COLORS["border"])
        self.termf.pack(fill="both", expand=True)

        sys.stdout = Redirigir(self.termf)
        sys.stderr = Redirigir(self.termf)

    # -------------------------------------------------------------------------
    # 4. VIEW: FARM TELEMETRY
    # -------------------------------------------------------------------------
    def build_view_farm(self):
        header_frame = ctk.CTkFrame(self.view_farm, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Live Hardware Monitor", font=self.fonts["h1"]).pack(side="left")

        telemetry_frame = ctk.CTkFrame(self.view_farm, fg_color=COLORS["bg_panel"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        telemetry_frame.pack(fill="both", expand=True)

        self.style_treeview()
        columns = ("board", "status", "power", "ping")
        self.status_tree = ttk.Treeview(telemetry_frame, columns=columns, show="headings", style="Custom.Treeview")
        self.status_tree.heading("board", text="Hardware Instance")
        self.status_tree.heading("status", text="Status")
        self.status_tree.heading("power", text="Power")
        self.status_tree.heading("ping", text="Execution Time (s)")
        
        self.status_tree.column("board", width=250, anchor="w")
        self.status_tree.column("status", width=120, anchor="center")
        self.status_tree.column("power", width=120, anchor="center")
        self.status_tree.column("ping", width=120, anchor="center")
        self.status_tree.pack(fill="both", expand=True, padx=20, pady=20)

        self.status_tree.tag_configure("busy", foreground=COLORS["warning"])
        self.status_tree.tag_configure("idle", foreground=COLORS["success"])
        self.status_tree.tag_configure("error", foreground=COLORS["error_fg"], background=COLORS["error_bg"])
        self.status_tree.tag_configure("quarantined", foreground="#FFFFFF", background="#8B0000")

    # -------------------------------------------------------------------------
    # 5. VIEW: ENVIRONMENT SETTINGS
    # -------------------------------------------------------------------------
    def build_view_settings(self):
        ctk.CTkLabel(self.view_settings, text="Environment Configuration", font=self.fonts["h1"]).pack(anchor="w", pady=(0, 20))

        settings_panel = ctk.CTkFrame(self.view_settings, fg_color=COLORS["bg_panel"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        settings_panel.pack(fill="x")

        ctk.CTkLabel(settings_panel, text="Network & Connectivity", font=self.fonts["h2"]).pack(anchor="w", padx=30, pady=(30, 10))
        self.netbird_switch = ctk.CTkSwitch(settings_panel, text="Enable NetBird Remote Mesh", variable=self.modo_netbird, font=self.fonts["body"], progress_color=COLORS["accent_primary"])
        self.netbird_switch.pack(anchor="w", padx=30, pady=10)

        ctk.CTkLabel(settings_panel, text="Server Project Mode", font=self.fonts["body"]).pack(anchor="w", padx=30, pady=(10, 0))
        self.srv_switch = ctk.CTkSwitch(settings_panel, text="Target Server Directly", variable=self.check_value, command=self.check_button, font=self.fonts["body"])
        self.srv_switch.pack(anchor="w", padx=30, pady=(5, 10))

        ctk.CTkLabel(settings_panel, text="Authentication", font=self.fonts["h2"]).pack(anchor="w", padx=30, pady=(30, 10))
        ctk.CTkLabel(settings_panel, text="OpenSSH Identity File Path", font=self.fonts["body"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=30, pady=(0, 5))
        
        key_frame = ctk.CTkFrame(settings_panel, fg_color="transparent")
        key_frame.pack(fill="x", padx=30, pady=(0, 30))
        
        self.keytxt = ctk.CTkEntry(key_frame, state='readonly', fg_color=COLORS["bg_input"], border_color=COLORS["border"], font=self.fonts["body"], height=40)
        self.keytxt.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_key = ctk.CTkButton(key_frame, text="Browse", command=self.get_key, fg_color=COLORS["border"], hover_color=COLORS["bg_base"], text_color=COLORS["text_main"], font=self.fonts["body"], height=40)
        self.btn_key.pack(side="right")

    # -------------------------------------------------------------------------
    # 6. CORE LOGIC
    # -------------------------------------------------------------------------
    def set_focus_mode(self, active: bool):
        state = "disabled" if active else "normal"
        self.ia_switch.configure(state=state)
        self.btn_examinar_proyecto.configure(state=state)
        self.fpgatxt.configure(state=state)
        self.carreratxt.configure(state=state)
        self.program_button.configure(state=state)
        
        if active:
            self.deploy_progress.start()
            self.reset_stepper()
        else:
            self.deploy_progress.stop()

    def reset_stepper(self):
        self.step1_lbl.configure(text="[ ] Parse Metrics", text_color=COLORS["stepper_inactive"])
        self.step2_lbl.configure(text=" ➔  [ ] AI Allocation", text_color=COLORS["stepper_inactive"])
        self.step3_lbl.configure(text=" ➔  [ ] SSH Deploying", text_color=COLORS["stepper_inactive"])

    def update_stepper(self, step: int, status: str):
        def _update():
            if step == 1:
                self.step1_lbl.configure(text=f"[✓] {status}", text_color=COLORS["success"])
                self.step2_lbl.configure(text_color=COLORS["accent_primary"]) 
            elif step == 2:
                self.step2_lbl.configure(text=f" ➔  [✓] {status}", text_color=COLORS["success"])
                self.step3_lbl.configure(text_color=COLORS["accent_primary"])
            elif step == 3:
                self.step3_lbl.configure(text=f" ➔  [✓] {status}", text_color=COLORS["success"])
        self.after(0, _update)

    def extract_hardware_metrics(self, ruta_local_qpf):
        hardware_data = {"family": "Unknown", "total_alms": 0, "dsp_blocks": 0}
        if not ruta_local_qpf or not os.path.exists(ruta_local_qpf): return hardware_data
        base_name = os.path.basename(ruta_local_qpf).replace('.qpf', '')
        dir_name = os.path.dirname(ruta_local_qpf)
        report_paths = [os.path.join(dir_name, "output_files", f"{base_name}.flow.rpt"), os.path.join(dir_name, f"{base_name}.flow.rpt")]
        target_file = next((path for path in report_paths if os.path.exists(path)), None)
        if not target_file: return hardware_data
        try:
            with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                fam = re.search(r';\s*Family\s*;\s*([^;]+)\s*;', content)
                alm = re.search(r';\s*Logic utilization.*?\s*;\s*([\d,]+)\s*/', content, re.IGNORECASE)
                dsp = re.search(r';\s*Total DSP Blocks\s*;\s*([\d,]+)\s*/', content, re.IGNORECASE)
                if fam: hardware_data["family"] = fam.group(1).strip()
                if alm: hardware_data["total_alms"] = int(alm.group(1).replace(',', ''))
                if dsp: hardware_data["dsp_blocks"] = int(dsp.group(1).replace(',', ''))
        except: pass
        return hardware_data

    def toggle_ia(self):
        if self.usar_ia.get():
            self.fpgatxt.set("🤖 AI Auto-Routing Enabled")
            self.fpgatxt.configure(state='disabled')
        else:
            self.fpgatxt.configure(state='normal')
            self.actualizar_lista_fpgas()

    def get_key(self):
        path = filedialog.askopenfilename(title="Select SSH Key", filetypes=(("Keys", "*.*"),))
        if path:
            self.keytxt.configure(state='normal')
            self.keytxt.delete(0, 'end')
            self.keytxt.insert(0, path)
            self.keytxt.configure(state='readonly')
            self.actualizar_lista_fpgas()

    def get_route(self):
        path = filedialog.askopenfilename(filetypes=(("Quartus Project", "*.qpf"),))
        if path:
            self.routetxt.configure(state='normal')
            self.routetxt.delete(0, 'end')
            self.routetxt.insert(0, path)
            self.routetxt.configure(state='readonly')

    def actualizar_lista_fpgas(self):
        key = self.keytxt.get()
        if not key: return
        self.fpgatxt.set("Scanning mesh...")
        
        def tarea():
            # This network call takes a few seconds
            lista = FPGA.detectar_fpgas_disponibles(key, self.modo_netbird.get())
            
            def update_ui():
                # CRITICAL FIX: Check if the user turned AI mode back on while the scan was running
                if self.usar_ia.get():
                    return
                
                # Only update the dropdown if AI mode is still OFF
                self.fpgatxt.configure(values=lista)
                self.fpgatxt.set(lista[0] if lista else "No FPGAs detected")
                
            self.after(0, update_ui)
            
        threading.Thread(target=tarea, daemon=True).start()

    def check_button(self):
        if self.check_value.get():
            self.routetxt.pack_forget()
            self.programtxt.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_examinar_proyecto.configure(state='disabled')
            def cargar():
                p = FPGA.pgmlist(self.keytxt.get(), self.modo_netbird.get())
                self.after(0, lambda: (self.programtxt.configure(values=p), self.programtxt.set(p[0] if p else "Empty")))
            threading.Thread(target=cargar, daemon=True).start()
        else:
            self.programtxt.pack_forget()
            self.routetxt.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_examinar_proyecto.configure(state='normal')

    def bundle_verilog_sources(self, ruta_local_qpf):
        verilog_payload = ""
        if not ruta_local_qpf: return verilog_payload
        base_dir = os.path.dirname(ruta_local_qpf)
        base_name = os.path.basename(ruta_local_qpf).replace('.qpf', '')
        qsf_path = os.path.join(base_dir, f"{base_name}.qsf")
        if os.path.exists(qsf_path):
            try:
                with open(qsf_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if "_FILE" in line and (".v" in line or ".sv" in line):
                            parts = line.split()
                            src_file = parts[-1].strip('"')
                            src_path = os.path.join(base_dir, src_file)
                            if os.path.exists(src_path):
                                with open(src_path, 'r', encoding='utf-8', errors='ignore') as src:
                                    verilog_payload += f"\n// --- {src_file} ---\n"
                                    verilog_payload += src.read()
            except Exception as e:
                print(f"[WARNING] Could not parse Verilog sources: {e}")
        return verilog_payload

    def show_bypass_dialog(self, title, message, original_payload, api_ip, callback_continue):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("500x250")
        dialog.attributes("-topmost", True)
        dialog.grab_set() 

        ctk.CTkLabel(dialog, text=title, font=self.fonts["h2"], text_color=COLORS["warning"]).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=message, font=self.fonts["body"], wraplength=450, justify="center").pack(pady=(0, 20), padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=20)

        def on_cancel():
            print(" -> [CANCELLED] Deployment aborted by user.")
            dialog.destroy()
            self.set_focus_mode(active=False)

        def on_bypass():
            print("\n -> [BYPASS] Overriding Gatekeeper. Forcing deployment...")
            dialog.destroy()
            original_payload["force_bypass"] = True
            threading.Thread(target=callback_continue, args=(original_payload, api_ip), daemon=True).start()

        ctk.CTkButton(btn_frame, text="Cancel Deployment", command=on_cancel, fg_color=COLORS["bg_panel"], hover_color=COLORS["border"]).pack(side="left", expand=True, padx=10)
        ctk.CTkButton(btn_frame, text="Deploy Anyway", command=on_bypass, fg_color=COLORS["error_fg"], hover_color="#C93C37").pack(side="right", expand=True, padx=10)

    def ejecutar_programacion(self):
        key = self.keytxt.get()
        if not key:
            print("[ERROR] Configure your SSH key in the Settings tab first.")
            return

        fpga_sel = self.fpgatxt.get()
        proy_sel = self.programtxt.get()
        carrera_sel = self.carreratxt.get()
        ruta_qpf = self.routetxt.get()
        is_srv = self.check_value.get()
        m_nb = self.modo_netbird.get()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_alumno = s.getsockname()[0]
            s.close()
        except: ip_alumno = "127.0.0.1"

        self.set_focus_mode(active=True)

        def tarea_ssh():
            target_fpga = fpga_sel
            api_ip = "100.66.246.67" if m_nb else "192.168.1.95"
            try:
                print("\n" + "-"*50)
                print("[STEP 1] Parsing Hardware Requirements...")
                time.sleep(0.5) 
                nombre_archivo = proy_sel if is_srv else os.path.basename(ruta_qpf)
                if is_srv:
                    familia, alms, dsps = ("Agilex" if "agilex" in nombre_archivo.lower() else "Cyclone V"), 0, 0
                    verilog_code = ""
                else:
                    metrics = self.extract_hardware_metrics(ruta_qpf)
                    familia, alms, dsps = metrics["family"], metrics["total_alms"], metrics["dsp_blocks"]
                    verilog_code = self.bundle_verilog_sources(ruta_qpf)
                
                print(f" -> Family: {familia} | ALMs: {alms} | DSPs: {dsps}")
                self.update_stepper(1, "Metrics Parsed")

                # ---------------------------------------------------------
                # 1. DEPLOYMENT FUNCTION & TAMPER LOCK
                # ---------------------------------------------------------
                def proceed_with_deployment(final_fpga):
                    print(f" -> [OK] Assigned: {final_fpga}")
                    self.update_stepper(2, "Board Allocated")

                    stop_hb = threading.Event()
                    def heartbeat(board):
                        while not stop_hb.is_set():
                            try: requests.post(f"http://{api_ip}:5000/heartbeat", json={"physical_instance": board}, timeout=5)
                            except: pass
                            stop_hb.wait(300)

                    if self.usar_ia.get(): threading.Thread(target=heartbeat, args=(final_fpga,), daemon=True).start()

                    print("\n[STEP 3] Initiating SSH Deployment to Target...")
                    self.update_stepper(3, "Deploying...")
                    
                    if is_srv:
                        FPGA.ssh_conection(ip_alumno, final_fpga, proy_sel, key, socket.gethostname(), carrera_sel, m_nb)
                    else:
                        if not ruta_qpf or not os.path.exists(ruta_qpf):
                            print(" -> [FAIL] Invalid local .qpf file.")
                            if self.usar_ia.get(): stop_hb.set()
                            self.after(0, lambda: self.set_focus_mode(active=False))
                            return
                        FPGA.dse(ip_alumno, key, os.path.dirname(ruta_qpf), ruta_qpf, final_fpga, socket.gethostname(), carrera_sel, m_nb)

                    print("\n[SUCCESS] Pipeline Completed.")
                    self.update_stepper(3, "Deployed Successfully")

                    if self.usar_ia.get():
                        stop_hb.set()
                        
                        # --- 2-MINUTE TAMPER LOCK ---
                        def delayed_release():
                            print(f" -> [LOCK] Board {final_fpga} secured for 120s. No other users can tamper with it.")
                            time.sleep(120)
                            try:
                                requests.post(f"http://{api_ip}:5000/release_board", json={"physical_instance": final_fpga}, timeout=5)
                                print(f" -> [INFO] Board {final_fpga} lock expired. Released to pool.")
                            except: pass
                            
                        threading.Thread(target=delayed_release, daemon=True).start()
                        
                    self.after(0, lambda: self.set_focus_mode(active=False))

                # ---------------------------------------------------------
                # 2. AI ROUTING & QUEUE WATCHER (Wrapped in function)
                # ---------------------------------------------------------
                def run_routing_and_deployment():
                    if self.usar_ia.get():
                        print("\n[STEP 2] Requesting AI Node Allocation & Security Check...")
                        initial_payload = {
                            "task_id": nombre_archivo, 
                            "family": familia, 
                            "total_alms": alms, 
                            "dsp_blocks": dsps,
                            "verilog_source": verilog_code,
                            "force_bypass": False
                        }
                        
                        def handle_api_request(current_payload, target_ip):
                            headers = {"X-Admin-Token": "UADY_RESEARCH_ADMIN_2026"} 
                            res = requests.post(
                                f"http://{target_ip}:5000/route_task", 
                                json=current_payload, 
                                headers=headers, 
                                timeout=90
                            )
                            
                            if res.status_code == 403: 
                                data = res.json()
                                print(f" -> [SECURITY ALERT] Task Blocked:\n{data.get('reasoning')}")
                                self.after(0, lambda: self.set_focus_mode(active=False))
                                return None
                                
                            elif res.status_code == 202: 
                                data = res.json()
                                recc_type = data.get("recommendation_type")
                                reasoning = data.get('reasoning')
                                remote_debug = data.get('debug_gatekeeper')
                                
                                if remote_debug:
                                    print("\n" + "="*40)
                                    print("[SERVER DEBUG] RAW GATEKEEPER DECISION:")
                                    print(json.dumps(remote_debug, indent=2))
                                    print("="*40 + "\n")
                                
                                title = "High-End Hardware Required" if recc_type == "recompile_for_agilex" else "Optimization Suggestion"
                                print(f" -> [INTERVENTION] {title}:\n{reasoning}")
                                
                                self.after(0, lambda: self.show_bypass_dialog(
                                    title=title, 
                                    message=reasoning + "\n\nAre you sure you want to bypass this warning and deploy?", 
                                    original_payload=current_payload, 
                                    api_ip=target_ip, 
                                    callback_continue=handle_api_request
                                ))
                                return "PAUSED"
                                
                            elif res.status_code == 200: 
                                data = res.json()
                                if current_payload.get("force_bypass"):
                                    print(" -> [OK] Bypass accepted. Routing via Qwen...")
                                    proceed_with_deployment(data["physical_instance"]) 
                                else:
                                    print(" -> [OK] Gatekeeper passed.")
                                    return data["physical_instance"]
                            
                            else:
                                print(f" -> [FAIL] API Error: {res.status_code}")
                                self.after(0, lambda: self.set_focus_mode(active=False))
                                return None

                        # --- QUEUE WATCHER ---
                        allocation_status = {"done": False}
                        
                        def queue_watcher():
                            time.sleep(15) 
                            if not allocation_status["done"]:
                                self.update_stepper(2, "⏳ Waiting in Server Queue...")
                                print(" -> [QUEUE] Farm is full. Task is holding in line...")
                                
                        threading.Thread(target=queue_watcher, daemon=True).start()
                        
                        target_fpga = handle_api_request(initial_payload, api_ip)
                        allocation_status["done"] = True 
                        
                        if target_fpga == "PAUSED":
                            return 
                            
                        if target_fpga is None:
                            return 
                            
                        proceed_with_deployment(target_fpga)
                        
                    else:
                        print("\n[STEP 2] Bypassing AI (Manual Selection)...")
                        time.sleep(0.5)
                        proceed_with_deployment(fpga_sel)

                # ---------------------------------------------------------
                # 3. MISSING COMPILE REPORT INTERVENTION
                # ---------------------------------------------------------
                if not is_srv and familia == "Unknown":
                    print(" -> [WARNING] Hardware metrics report missing. Deployment blocked.")
                    def show_compile_error():
                        dialog = ctk.CTkToplevel(self)
                        dialog.title("Compilation Required")
                        dialog.geometry("500x250")
                        dialog.attributes("-topmost", True)
                        dialog.grab_set() 

                        ctk.CTkLabel(dialog, text="Compile Report Missing", font=self.fonts["h2"], text_color=COLORS["error_fg"]).pack(pady=(20, 5))
                        ctk.CTkLabel(dialog, text="The .flow.rpt file was not found. This indicates the Quartus project has not been fully compiled yet.\n\nPlease compile your project in Quartus before attempting to deploy to the farm.", font=self.fonts["body"], wraplength=450, justify="center").pack(pady=(0, 20), padx=20)

                        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
                        btn_frame.pack(fill="x", pady=10, padx=20)

                        def on_acknowledge():
                            print(" -> [ABORTED] Deployment stopped. User must compile first.")
                            dialog.destroy()
                            self.set_focus_mode(active=False)

                        ctk.CTkButton(btn_frame, text="Okay", command=on_acknowledge, fg_color=COLORS["bg_panel"], hover_color=COLORS["border"]).pack(expand=True, padx=10)
                        
                    self.after(0, show_compile_error)
                else:
                    run_routing_and_deployment()

            except Exception as e: 
                print(f"\n[ERROR] Pipeline Failed: {e}")
            finally:
                self.after(0, lambda: self.set_focus_mode(active=False))

        threading.Thread(target=tarea_ssh, daemon=True).start()

    def update_dashboard_loop(self):
        while True:
            api_ip = "100.66.246.67" if self.modo_netbird.get() else "192.168.1.95"
            try:
                res = requests.get(f"http://{api_ip}:5000/status", timeout=2)
                if res.status_code == 200:
                    data = res.json().get("farm_state", {})
                    self.status_tree.delete(*self.status_tree.get_children())
                    for board, info in data.items():
                        status = info["status"].upper()
                        power = "ON" if info.get("powered") else "OFF"
                        ping = info.get("seconds_since_last_ping", 0)
                        
                        ping_str = f"{ping}s [TIMEOUT]" if status == "BUSY" and ping > 50 else f"{ping}s" if status == "BUSY" else "-"
                        
                        tag = "idle"
                        if status == "QUARANTINED":
                            tag = "quarantined"
                            ping_str = "LOCKED"
                        elif status == "BUSY":
                            tag = "error" if ping > 50 else "busy"

                        self.status_tree.insert("", "end", values=(board, status, power, ping_str), tags=(tag,))
            except:
                self.status_tree.delete(*self.status_tree.get_children())
                self.status_tree.insert("", "end", values=("⚠️ API OFFLINE", "Disconn", "-", "-"), tags=("error",))
            time.sleep(2)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Increased rowheight to 55 and data font size to 16
        style.configure("Custom.Treeview", background=COLORS["bg_input"], foreground=COLORS["text_main"], fieldbackground=COLORS["bg_input"], rowheight=55, borderwidth=0, font=("Segoe UI", 16))
        
        # Increased heading font size to 18
        style.configure("Custom.Treeview.Heading", background=COLORS["bg_panel"], foreground=COLORS["text_muted"], font=("Segoe UI", 18, 'bold'), borderwidth=0, relief="flat")
        
        style.map("Custom.Treeview", background=[('selected', COLORS["border"])], foreground=[('selected', '#FFFFFF')])
        style.layout("Custom.Treeview.Heading", [("Treeheading.cell", {'sticky': 'nswe'}), ("Treeheading.border", {'sticky':'nswe', 'children': [("Treeheading.padding", {'sticky':'nswe', 'children': [("Treeheading.image", {'side':'right', 'sticky':''}), ("Treeheading.text", {'sticky':'we'})]})]})])

    def on_closing(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.destroy()

class Redirigir:
    def __init__(self, textbox):
        self.textbox = textbox
    def write(self, text):
        try:
            self.textbox.insert("end", text)
            self.textbox.see("end")
        except: pass
    def flush(self): pass

if __name__ == "__main__":
    app = GranjaApp()
    app.mainloop()