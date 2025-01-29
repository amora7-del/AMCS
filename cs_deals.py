import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
import threading
import time

# Load environment variables
load_dotenv()

class CSDealsBot:
    def __init__(self):
        self.api_key = os.getenv('CS_DEALS_API_KEY')
        self.steam_id = os.getenv('STEAM_ID')
        self.api_base_url = 'https://cs.deals/api/v2'
        self.current_language = 'ar'
        self.translations = self.load_translations()
        
        self.root = tk.Tk()
        self.root.title("CS.DEALS Auto-Buy Bot")
        self.root.geometry("1200x800")
        
        # Configure styles
        style = ttk.Style()
        style.configure("Active.TLabel", foreground="green")
        style.configure("Inactive.TLabel", foreground="red")
        
        self.setup_ui()
        self.orders = []
        
        # Start background refresh thread
        self.refresh_thread = threading.Thread(target=self.background_refresh, daemon=True)
        self.refresh_thread.start()

    def load_translations(self):
        return {
            'ar': {
                'title': 'بوت CS.DEALS للشراء التلقائي',
                'skin_name': 'اسم السكين',
                'min_price': 'السعر الأدنى',
                'max_price': 'السعر الأقصى',
                'quantity': 'الكمية',
                'status': 'الحالة',
                'note': 'الملاحظة',
                'submit': 'إضافة أمر شراء',
                'active': 'نشط',
                'inactive': 'غير نشط',
                'waiting': 'قيد الانتظار',
                'success': 'تم الشراء بنجاح',
                'delete': 'حذف',
                'language': 'EN'
            },
            'en': {
                'title': 'CS.DEALS Auto-Buy Bot',
                'skin_name': 'Skin Name',
                'min_price': 'Min Price',
                'max_price': 'Max Price',
                'quantity': 'Quantity',
                'status': 'Status',
                'note': 'Note',
                'submit': 'Add Buy Order',
                'active': 'Active',
                'inactive': 'Inactive',
                'waiting': 'Waiting',
                'success': 'Purchase Successful',
                'delete': 'Delete',
                'language': 'ع'
            }
        }

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header with title and language toggle
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.title_label = ttk.Label(
            header_frame, 
            text=self.translations[self.current_language]['title'],
            font=('Arial', 16, 'bold')
        )
        self.title_label.grid(row=0, column=0, sticky=tk.W)
        
        self.language_button = ttk.Button(
            header_frame,
            text=self.translations[self.current_language]['language'],
            command=self.toggle_language,
            width=5
        )
        self.language_button.grid(row=0, column=1, sticky=tk.E)
        
        # Input form
        form_frame = ttk.LabelFrame(main_frame, padding="10")
        form_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Form fields
        self.skin_name_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        
        # Skin name
        self.skin_name_label = ttk.Label(form_frame, text=self.translations[self.current_language]['skin_name'])
        self.skin_name_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.skin_name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Min price
        self.min_price_label = ttk.Label(form_frame, text=self.translations[self.current_language]['min_price'])
        self.min_price_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.min_price_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Max price
        self.max_price_label = ttk.Label(form_frame, text=self.translations[self.current_language]['max_price'])
        self.max_price_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.max_price_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Quantity
        self.quantity_label = ttk.Label(form_frame, text=self.translations[self.current_language]['quantity'])
        self.quantity_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.quantity_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Submit button
        self.submit_button = ttk.Button(
            form_frame,
            text=self.translations[self.current_language]['submit'],
            command=self.create_buy_order
        )
        self.submit_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Orders table
        self.setup_orders_table(main_frame)

    def setup_orders_table(self, parent):
        # Table frame
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create Treeview
        columns = ('skin_name', 'min_price', 'max_price', 'quantity', 'status', 'note')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Configure columns
        self.tree.heading('skin_name', text=self.translations[self.current_language]['skin_name'])
        self.tree.heading('min_price', text=self.translations[self.current_language]['min_price'])
        self.tree.heading('max_price', text=self.translations[self.current_language]['max_price'])
        self.tree.heading('quantity', text=self.translations[self.current_language]['quantity'])
        self.tree.heading('status', text=self.translations[self.current_language]['status'])
        self.tree.heading('note', text=self.translations[self.current_language]['note'])
        
        # Column widths
        self.tree.column('skin_name', width=200)
        self.tree.column('min_price', width=100)
        self.tree.column('max_price', width=100)
        self.tree.column('quantity', width=80)
        self.tree.column('status', width=100)
        self.tree.column('note', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid table and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind delete action
        self.tree.bind('<Delete>', self.delete_selected_order)
        
        # Configure grid weights
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

    def toggle_language(self):
        self.current_language = 'en' if self.current_language == 'ar' else 'ar'
        self.update_ui_text()

    def update_ui_text(self):
        t = self.translations[self.current_language]
        
        # Update all UI text
        self.title_label.config(text=t['title'])
        self.language_button.config(text=t['language'])
        self.skin_name_label.config(text=t['skin_name'])
        self.min_price_label.config(text=t['min_price'])
        self.max_price_label.config(text=t['max_price'])
        self.quantity_label.config(text=t['quantity'])
        self.submit_button.config(text=t['submit'])
        
        # Update table headers
        self.tree.heading('skin_name', text=t['skin_name'])
        self.tree.heading('min_price', text=t['min_price'])
        self.tree.heading('max_price', text=t['max_price'])
        self.tree.heading('quantity', text=t['quantity'])
        self.tree.heading('status', text=t['status'])
        self.tree.heading('note', text=t['note'])

    def create_buy_order(self):
        try:
            order = {
                'name': self.skin_name_var.get(),
                'minPrice': float(self.min_price_var.get()),
                'maxPrice': float(self.max_price_var.get()),
                'quantity': int(self.quantity_var.get())
            }
            
            response = self.api_request('POST', '/market/buy-orders', order)
            
            if response.get('success'):
                self.refresh_orders()
                self.clear_form()
            else:
                messagebox.showerror("Error", response.get('error', {}).get('message', 'Unknown error'))
                
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numbers for prices and quantity")

    def delete_selected_order(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        order_id = self.tree.item(selected_item[0])['values'][0]
        response = self.api_request('DELETE', f'/market/buy-orders/{order_id}')
        
        if response.get('success'):
            self.refresh_orders()
        else:
            messagebox.showerror("Error", response.get('error', {}).get('message', 'Unknown error'))

    def api_request(self, method, endpoint, data=None):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Steam-ID': self.steam_id
        }
        
        try:
            response = requests.request(
                method,
                f"{self.api_base_url}{endpoint}",
                headers=headers,
                json=data
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': {'message': str(e)}}

    def refresh_orders(self):
        response = self.api_request('GET', '/market/buy-orders')
        if response.get('success'):
            self.orders = response.get('data', [])
            self.update_orders_table()

    def update_orders_table(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add orders to table
        for order in self.orders:
            self.tree.insert('', 'end', values=(
                order['skinName'],
                f"${order['minPrice']}",
                f"${order['maxPrice']}",
                order['quantity'],
                self.translations[self.current_language]['active' if order['status'] == 'active' else 'inactive'],
                order.get('note', self.translations[self.current_language]['waiting'])
            ))

    def clear_form(self):
        self.skin_name_var.set('')
        self.min_price_var.set('')
        self.max_price_var.set('')
        self.quantity_var.set('')

    def background_refresh(self):
        while True:
            self.refresh_orders()
            time.sleep(30)  # Refresh every 30 seconds

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    bot = CSDealsBot()
    bot.run()