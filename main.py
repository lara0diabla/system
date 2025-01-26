import customtkinter as ctk
from tkinter import ttk, Listbox
import sqlite3
from modules.sales import SalesModule
from modules.customers import CustomersModule
from modules.reports import ReportsModule
from modules.suppliers import SuppliersModule
from modules.cashier import CashierModule
from modules.purchases import PurchasesModule
from PyQt5.QtWidgets import QApplication
import threading
from modules.cashier2 import Cashier2Module
from modules.cashier3 import Cashier3Module
from modules.barcode_reader import read_barcode  # Corrected import statement

class AddItemDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Add New Item")
        self.geometry("400x350")  # Size of the Add Item dialog
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.name_input = ctk.CTkEntry(form_layout, placeholder_text="Name")
        self.name_input.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Name:").grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.barcode_input = ctk.CTkEntry(form_layout, placeholder_text="Barcode")
        self.barcode_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Barcode:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.sale_price_input = ctk.CTkEntry(form_layout, placeholder_text="Sale Price")
        self.sale_price_input.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Sale Price:").grid(row=2, column=0, pady=5, padx=5, sticky="w")

        self.purchase_price_input = ctk.CTkEntry(form_layout, placeholder_text="Purchase Price")
        self.purchase_price_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Purchase Price:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.note_input = ctk.CTkEntry(form_layout, placeholder_text="Note")
        self.note_input.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Note:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.weight_checkbox = ctk.CTkCheckBox(form_layout, text="Contains Weight")
        self.weight_checkbox.grid(row=5, column=1, pady=5, padx=5, sticky="w")

        self.category_combo = ttk.Combobox(form_layout)
        self.category_combo.grid(row=6, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Category:").grid(row=6, column=0, pady=5, padx=5, sticky="w")
        self.load_categories()

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_item)
        save_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def load_categories(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories WHERE visible = 1')
        categories = cursor.fetchall()
        conn.close()
        self.category_combo['values'] = [category[0] for category in categories]

    def save_item(self):
        name = self.name_input.get()
        barcode = self.barcode_input.get()
        sale_price_text = self.sale_price_input.get()
        purchase_price_text = self.purchase_price_input.get()
        note = self.note_input.get()
        contains_weight = self.weight_checkbox.get()
        category = self.category_combo.get()
        quantity = 0  # Default quantity value

        if not name or not barcode or not sale_price_text or not purchase_price_text or not category:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            sale_price = float(sale_price_text)
            purchase_price = float(purchase_price_text)
        except ValueError:
            self.error_label.configure(text="Error: Sale Price and Purchase Price must be valid numbers")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        self.create_table(cursor)

        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'note' not in columns:
            cursor.execute('''
                ALTER TABLE items ADD COLUMN note TEXT
            ''')

        cursor.execute('SELECT * FROM items WHERE name = ? OR barcode = ?', (name, barcode))
        if cursor.fetchone():
            self.error_label.configure(text="Error: Duplicate name or barcode")
            conn.close()
            return

        cursor.execute('''
            INSERT INTO items (name, barcode, sale_price, purchase_price, note, contains_weight, category, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, barcode, sale_price, purchase_price, note, contains_weight, category, quantity))
        conn.commit()
        conn.close()

        print("Item saved to the database")
        self.destroy()

    def create_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                barcode TEXT UNIQUE,
                sale_price REAL,
                purchase_price REAL,
                note TEXT,
                contains_weight BOOLEAN,
                category TEXT
            )
        ''')
        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'contains_weight' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN contains_weight BOOLEAN')
        if 'category' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN category TEXT')

class EditItemDialog(ctk.CTkToplevel):
    def __init__(self, item_name, parent=None):
        super().__init__(parent)
        self.title("Edit Item")
        self.geometry("400x350")  # Size of the Edit Item dialog
        self.item_name = item_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.name_input = ctk.CTkEntry(form_layout, placeholder_text="Name")
        self.name_input.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Name:").grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.barcode_input = ctk.CTkEntry(form_layout, placeholder_text="Barcode")
        self.barcode_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Barcode:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.sale_price_input = ctk.CTkEntry(form_layout, placeholder_text="Sale Price")
        self.sale_price_input.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Sale Price:").grid(row=2, column=0, pady=5, padx=5, sticky="w")

        self.purchase_price_input = ctk.CTkEntry(form_layout, placeholder_text="Purchase Price")
        self.purchase_price_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Purchase Price:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.note_input = ctk.CTkEntry(form_layout, placeholder_text="Note")
        self.note_input.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Note:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.weight_checkbox = ctk.CTkCheckBox(form_layout, text="Contains Weight")
        self.weight_checkbox.grid(row=5, column=1, pady=5, padx=5, sticky="w")

        self.category_combo = ttk.Combobox(form_layout)
        self.category_combo.grid(row=6, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Category:").grid(row=6, column=0, pady=5, padx=5, sticky="w")
        self.load_categories()

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        update_button = ctk.CTkButton(button_frame, text="Update Item", command=self.update_item)
        update_button.pack(side="left", padx=5)

        update_stock_button = ctk.CTkButton(button_frame, text="Update Stock", command=self.update_stock)
        update_stock_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

        self.load_item_data()

    def load_categories(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories WHERE visible = 1')
        categories = cursor.fetchall()
        conn.close()
        self.category_combo['values'] = [category[0] for category in categories]

    def load_item_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        self.create_table(cursor)
        cursor.execute('SELECT name, barcode, sale_price, purchase_price, note, contains_weight, category FROM items WHERE name = ?', (self.item_name,))
        item = cursor.fetchone()
        conn.close()

        if item:
            self.name_input.insert(0, item[0])
            self.barcode_input.insert(0, item[1])
            self.sale_price_input.insert(0, item[2])
            self.purchase_price_input.insert(0, item[3])
            self.note_input.insert(0, item[4])
            self.weight_checkbox.select() if item[5] else self.weight_checkbox.deselect()
            self.category_combo.set(item[6])

    def update_item(self):
        name = self.name_input.get()
        barcode = self.barcode_input.get()
        sale_price_text = self.sale_price_input.get()
        purchase_price_text = self.purchase_price_input.get()
        note = self.note_input.get()
        contains_weight = self.weight_checkbox.get()
        category = self.category_combo.get()

        if not name or not barcode or not sale_price_text or not purchase_price_text or not category:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            sale_price = float(self.sale_price_input.get())
            purchase_price = float(self.purchase_price_input.get())
        except ValueError:
            self.error_label.configure(text="Error: Sale Price and Purchase Price must be valid numbers")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        self.create_table(cursor)

        cursor.execute('''
            UPDATE items
            SET name = ?, barcode = ?, sale_price = ?, purchase_price = ?, note = ?, contains_weight = ?, category = ?
            WHERE name = ?
        ''', (name, barcode, sale_price, purchase_price, note, contains_weight, category, self.item_name))
        conn.commit()
        conn.close()

        print("Item updated in the database")
        self.destroy()

    def update_stock(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM items WHERE name = ?', (self.item_name,))
        current_quantity = cursor.fetchone()[0]

        # Assuming you have an input field for updating stock quantity
        new_quantity_text = self.quantity_input.get()
        try:
            new_quantity = int(new_quantity_text)
        except ValueError:
            self.error_label.configure(text="Error: Quantity must be a valid number")
            return

        updated_quantity = current_quantity + new_quantity
        if updated_quantity < 0:
            updated_quantity = -abs(updated_quantity)

        cursor.execute('''
            UPDATE items
            SET quantity = ?
            WHERE name = ?
        ''', (updated_quantity, self.item_name))
        conn.commit()
        conn.close()

        print("Stock updated in the database")
        self.destroy()

    def create_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                barcode TEXT UNIQUE,
                sale_price REAL,
                purchase_price REAL,
                note TEXT,
                contains_weight BOOLEAN,
                category TEXT
            )
        ''')
        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'contains_weight' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN contains_weight BOOLEAN')
        if 'category' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN category TEXT')

class ManageCategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Manage Categories")
        self.geometry("400x300")
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.category_list = Listbox(layout)
        self.category_list.pack(pady=10)
        self.category_list.bind("<<ListboxSelect>>", self.open_edit_category_dialog)

        self.load_categories()

        add_button = ctk.CTkButton(layout, text="Add Category", command=self.open_add_category_dialog)
        add_button.pack(pady=5)

        delete_button = ctk.CTkButton(layout, text="Delete Category", command=self.delete_category)
        delete_button.pack(pady=5)

    def load_categories(self):
        self.category_list.delete(0, ctk.END)
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories')
        categories = cursor.fetchall()
        conn.close()
        for category in categories:
            self.category_list.insert(ctk.END, category[0])

    def open_add_category_dialog(self):
        dialog = AddCategoryDialog(self)
        dialog.grab_set()
        self.load_categories()

    def open_edit_category_dialog(self, event):
        selected_item = self.category_list.get(self.category_list.curselection())
        dialog = AddCategoryDialog(self, selected_item)
        dialog.grab_set()
        self.load_categories()

    def delete_category(self):
        selected_item = self.category_list.get(self.category_list.curselection())
        if selected_item:
            reply = ctk.CTkMessageBox.askyesno("Delete Category", f"Are you sure you want to delete the category '{selected_item}'?")
            if reply:
                conn = sqlite3.connect('sqlite3.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM categories WHERE name = ?', (selected_item,))
                conn.commit()
                conn.close()
                self.load_categories()

class AddCategoryDialog(ctk.CTkToplevel):
    def __init__(self, parent, category_name=None):
        super().__init__(parent)
        self.title("Add Category" if category_name is None else "Edit Category")
        self.geometry("400x250")
        self.category_name = category_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.name_input = ctk.CTkEntry(layout, placeholder_text="Category Name")
        self.name_input.pack(pady=5)

        self.number_input = ctk.CTkEntry(layout, placeholder_text="Category Number")
        self.number_input.pack(pady=5)

        self.visible_checkbox = ctk.CTkCheckBox(layout, text="Visible in Items")
        self.visible_checkbox.pack(pady=5)

        if self.category_name:
            self.load_category_data()

        save_button = ctk.CTkButton(layout, text="Save", command=self.save_category)
        save_button.pack(pady=5)

        exit_button = ctk.CTkButton(layout, text="Exit", command=self.destroy)
        exit_button.pack(pady=5)

    def load_category_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, number, visible FROM categories WHERE name = ?', (self.category_name,))
        category = cursor.fetchone()
        conn.close()
        if category:
            self.name_input.insert(0, category[0])
            self.number_input.insert(0, category[1])
            self.visible_checkbox.select() if category[2] else self.visible_checkbox.deselect()

    def save_category(self):
        name = self.name_input.get()
        number = self.number_input.get()
        visible = self.visible_checkbox.get()

        if not name or not number:
            ctk.CTkMessageBox.show_warning("Input Error", "Both fields must be filled")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        if self.category_name:
            cursor.execute('UPDATE categories SET name = ?, number = ?, visible = ? WHERE name = ?', (name, number, visible, self.category_name))
        else:
            cursor.execute('INSERT INTO categories (name, number, visible) VALUES (?, ?, ?)', (name, number, visible))
        conn.commit()
        conn.close()
        self.destroy()

class ERPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('ERP and POS System')
        self.geometry("1200x700")
        self.search_timer = None
        self.initUI()

    def create_tables(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                sale_price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                contains_weight BOOLEAN,
                category TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                number INTEGER UNIQUE NOT NULL,
                visible BOOLEAN NOT NULL DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                note TEXT,
                outstanding_balance REAL NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                note TEXT,
                outstanding_balance REAL NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT NOT NULL,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                date TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                amount_bought REAL NOT NULL,
                amount_paid REAL NOT NULL,
                date TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'quantity' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0')
        if 'contains_weight' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN contains_weight BOOLEAN')
        if 'category' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN category TEXT')
        conn.commit()
        conn.close()

    def initUI(self):
        self.create_tables()

        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.pack(side="top", fill="x")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        self.sales_module = SalesModule(self)
        self.customers_module = CustomersModule(self)
        self.reports_module = ReportsModule(self)
        self.suppliers_module = SuppliersModule(self)
        self.purchases_module = PurchasesModule(self)
        self.cashier2_module = Cashier2Module(self)
        self.cashier3 = Cashier3Module(self)  # Ensure Cashier3Module is used
        self.tabs.add(self.cashier3, text="Cashier 3")  # Add Cashier 3 tab

        self.tabs.add(self.create_items_tab(), text="Items")
        self.tabs.add(self.sales_module.get_widget(), text="Sales")
        self.tabs.add(self.customers_module.get_widget(), text="Customers")
        self.tabs.add(self.reports_module.get_widget(), text="Reports")
        self.tabs.add(self.suppliers_module.get_widget(), text="Suppliers")
        self.tabs.add(self.purchases_module.get_widget(), text="Purchases")
        self.tabs.add(self.cashier2_module, text="Cashier 2")  # Add Cashier 2 tab
        self.tabs.add(self.create_customers_tab(), text="Customers")

        self.create_toolbar_buttons()

        # Configure resizing behavior
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.tabs.rowconfigure(0, weight=1)
        self.tabs.columnconfigure(0, weight=1)

    def create_toolbar_buttons(self):
        items_button = ctk.CTkButton(self.toolbar, text="Items", command=self.show_items_tab)
        items_button.pack(side="left", padx=5, pady=5)

        sale_button = ctk.CTkButton(self.toolbar, text="Sale", command=self.show_sales_tab)
        sale_button.pack(side="left", padx=5, pady=5)

        cashier_button = ctk.CTkButton(self.toolbar, text="Cashier", command=self.open_cashier_module)
        cashier_button.pack(side="left", padx=5, pady=5)

        cashier2_button = ctk.CTkButton(self.toolbar, text="Cashier 2", command=self.show_cashier2_tab)  # Add Cashier 2 button
        cashier2_button.pack(side="left", padx=5, pady=5)

        cashier3_button = ctk.CTkButton(self.toolbar, text="Cashier 3", command=self.show_cashier3_tab)  # Add Cashier 3 button
        cashier3_button.pack(side="left", padx=5, pady=5)

        customers_button = ctk.CTkButton(self.toolbar, text="Customers", command=self.show_customers_tab)
        customers_button.pack(side="left", padx=5, pady=5)

        reports_button = ctk.CTkButton(self.toolbar, text="Reports", command=self.show_reports_tab)
        reports_button.pack(side="left", padx=5, pady=5)

        suppliers_button = ctk.CTkButton(self.toolbar, text="Suppliers", command=self.show_suppliers_tab)
        suppliers_button.pack(side="left", padx=5, pady=5)

        barcode_reader_button = ctk.CTkButton(self.toolbar, text="Barcode Reader", command=self.open_barcode_reader)
        barcode_reader_button.pack(side="left", padx=5, pady=5)

        purchases_button = ctk.CTkButton(self.toolbar, text="Purchases", command=self.show_purchases_tab)
        purchases_button.pack(side="left", padx=5, pady=5)

    def open_barcode_reader(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Barcode Reader")
        dialog.geometry("300x150")

        barcode_entry = ctk.CTkEntry(dialog, placeholder_text="Enter Barcode")
        barcode_entry.pack(pady=10, padx=10)
        
        error_label = ctk.CTkLabel(dialog, text="")
        error_label.pack()

        def handle_scan():
          barcode_text = barcode_entry.get()
          result = read_barcode(barcode_text)
          if result:
             product_code, weight = result
             product = self.find_product_by_product_code(product_code)
             if product:
                  product_name, product_quantity, product_price, product_barcode = product
                  print(f"Adding Item from Barcode: {product_name}, price: {product_price}")
                  # Add the product to whatever you are doing with the cashier module.
             else:
                  error_label.configure(text="لا يوجد منتج بهذا الباركود.")
          else:
              error_label.configure(text="لا يمكن قراءة الباركود أو تنسيق الباركود خاطئ")
          
          dialog.destroy() #Close dialog after reading.
        scan_button = ctk.CTkButton(dialog, text="Scan", command=handle_scan)
        scan_button.pack()

    def show_items_tab(self):
        self.tabs.select(0)

    def show_sales_tab(self):
        self.tabs.select(1)

    def show_customers_tab(self):
        self.tabs.select(2)

    def show_reports_tab(self):
        self.tabs.select(3)

    def show_suppliers_tab(self):
        self.tabs.select(4)

    def show_purchases_tab(self):
        self.tabs.select(5)

    def show_cashier2_tab(self):
        self.tabs.select(6)

    def show_cashier3_tab(self):
        self.tabs.select(7)

    def create_items_tab(self):
        widget = ctk.CTkFrame(self.tabs)
        layout = ctk.CTkFrame(widget)
        layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(layout)
        top_section.pack(fill="x", pady=10)

        self.search_box = ctk.CTkEntry(top_section, placeholder_text="Search...")
        self.search_box.pack(side="left", padx=5, fill="x", expand=True)  # Adjusted to fill the remaining space
        self.search_box.bind("<KeyRelease>", self.on_search_key_release)

        add_item_button = ctk.CTkButton(top_section, text="Add New Item", command=self.open_add_item_dialog)
        add_item_button.pack(side="left", padx=5)

        manage_categories_button = ctk.CTkButton(top_section, text="Manage Categories", command=self.open_manage_categories_dialog)
        manage_categories_button.pack(side="left", padx=5)

        self.middle_layout = ctk.CTkFrame(layout)
        self.middle_layout.pack(fill="both", expand=True)

        self.table = ttk.Treeview(self.middle_layout, columns=("Name", "Quantity"), show="headings")
        self.table.heading("Name", text="Name")
        self.table.heading("Quantity", text="Quantity")
        self.table.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        self.table.bind("<Double-1>", self.open_edit_item_dialog)

        # Increase row height and add spacing
        style = ttk.Style()
        style.configure("Treeview", rowheight=60)  # 3 times larger than the default
        style.layout("Treeview.Item", [('Treeitem.padding', {'sticky': 'nswe', 'children': [('Treeitem.text', {'sticky': 'nswe'})]})])
        style.configure("Treeview.Item", padding=(0, 5))  # Add 10 units spacing

        # Bind mouse enter and leave events
        self.table.bind("<Motion>", self.on_mouse_enter)
        self.table.bind("<Leave>", self.on_mouse_leave)

        self.categories_layout = ctk.CTkFrame(self.middle_layout)
        self.categories_layout.pack(side="left", fill="y", padx=10)

        self.categories_canvas = ctk.CTkCanvas(self.categories_layout)
        self.categories_canvas.pack(side="left", fill="both", expand=True)

        self.categories_frame = ctk.CTkFrame(self.categories_canvas)
        self.categories_canvas.create_window((0, 0), window=self.categories_frame, anchor="nw")

        self.categories_frame.bind("<Configure>", lambda e: self.categories_canvas.configure(scrollregion=self.categories_canvas.bbox("all")))
        self.categories_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        self.load_visible_categories()
        return widget

    def on_mouse_wheel(self, event):
        self.categories_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_visible_categories(self):
        for widget in self.categories_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories WHERE visible = 1')
        categories = cursor.fetchall()
        conn.close()

        for category in categories:
            category_name = category[0]
            category_button = ctk.CTkButton(self.categories_frame, text=category_name, command=lambda name=category_name: self.show_items_in_category(name), height=90, width=290)  # Adjust the height and width as needed
            category_button.pack(pady=5)

    def clear_items_table(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items')
        conn.commit()
        conn.close()
        self.search_items('')

    def search_items(self, event=None):
        text = self.search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        if text.isdigit():
            cursor.execute('SELECT name, quantity FROM items WHERE barcode LIKE ?', ('%' + text + '%',))
        else:
            cursor.execute('SELECT name, quantity FROM items WHERE name LIKE ?', ('%' + text + '%',))
        items = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for item in items:
            self.table.insert("", "end", values=(item[0], item[1]))

    def on_search_key_release(self, event):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(250, self.search_items)  # Reduced delay to 250 milliseconds

    def open_add_item_dialog(self):
        dialog = AddItemDialog(self)
        dialog.grab_set()

    def open_edit_item_dialog(self, event):
        selected_item = self.table.item(self.table.selection())['values'][0]
        dialog = ItemOptionsDialog(selected_item, self)
        dialog.grab_set()

    def open_manage_categories_dialog(self):
        dialog = ManageCategoriesDialog(self)
        dialog.grab_set()
        self.load_visible_categories()

    def open_cashier_module(self):
        app = QApplication([])
        cashier_window = CashierModule()
        cashier_window.show()
        app.exec_()

    def on_mouse_enter(self, event):
        row_id = self.table.identify_row(event.y)
        if row_id:
            self.table.tag_configure('highlight', background='lightblue')
            self.table.item(row_id, tags=('highlight',))
        # Reset the color of other rows
        for row in self.table.get_children():
            if row != row_id:
                self.table.item(row, tags=())

    def on_mouse_leave(self, event):
        for row_id in self.table.get_children():
            self.table.item(row_id, tags=())

    def show_items_in_category(self, category_name):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM items WHERE category = ?', (category_name,))
        items = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for item in items:
            self.table.insert("", "end", values=(item[0],))

    def create_customers_tab(self):
        widget = ctk.CTkFrame(self.tabs)
        layout = ctk.CTkFrame(widget)
        layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(layout)
        top_section.pack(fill="x", pady=10)

        self.customer_search_box = ctk.CTkEntry(top_section, placeholder_text="Search Customers...")
        self.customer_search_box.pack(side="left", padx=5, fill="x", expand=True)
        self.customer_search_box.bind("<KeyRelease>", self.on_customer_search_key_release)

        self.customer_table = ttk.Treeview(layout, columns=("Name"), show="headings")
        self.customer_table.heading("Name", text="Name")
        self.customer_table.pack(fill="both", expand=True, padx=10, pady=10)
        self.customer_table.bind("<Double-1>", self.open_edit_customer_dialog)

        return widget

    def on_customer_search_key_release(self, event):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(250, self.search_customers)  # Reduced delay to 250 milliseconds

    def search_customers(self):
        text = self.customer_search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM customers WHERE name LIKE ?', ('%' + text + '%',))
        customers = cursor.fetchall()
        conn.close()

        for i in self.customer_table.get_children():
            self.customer_table.delete(i)

        for customer in customers:
            self.customer_table.insert("", "end", values=(customer[0],))

    def open_edit_customer_dialog(self, event):
        selected_customer = self.customer_table.item(self.customer_table.selection())['values'][0]
        dialog = EditCustomerDialog(selected_customer, self)
        dialog.grab_set()

    def find_product_by_product_code(self, product_code):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, quantity, sale_price, barcode FROM items')
        items = cursor.fetchall()
        conn.close()
        for item in items:
            if item[3][:7] == product_code:  # Check first 7 digits of barcode
                return item[0], item[1], item[2], item[3] #product_name, quantity, price, product_barcode
        return None

class EditCustomerDialog(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title("Edit Customer")
        self.geometry("400x350")
        self.customer_name = customer_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.name_input = ctk.CTkEntry(form_layout, placeholder_text="Name")
        self.name_input.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Name:").grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.phone_input = ctk.CTkEntry(form_layout, placeholder_text="Phone")
        self.phone_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Phone:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.email_input = ctk.CTkEntry(form_layout, placeholder_text="Email")
        self.email_input.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Email:").grid(row=2, column=0, pady=5, padx=5, sticky="w")

        self.address_input = ctk.CTkEntry(form_layout, placeholder_text="Address")
        self.address_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Address:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.note_input = ctk.CTkEntry(form_layout, placeholder_text="Note")
        self.note_input.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Note:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        update_button = ctk.CTkButton(button_frame, text="Update Customer", command=self.update_customer)
        update_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

        self.load_customer_data()

    def load_customer_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, phone, email, address, note FROM customers WHERE name = ?', (self.customer_name,))
        customer = cursor.fetchone()
        conn.close()

        if customer:
            self.name_input.insert(0, customer[0])
            self.phone_input.insert(0, customer[1])
            self.email_input.insert(0, customer[2])
            self.address_input.insert(0, customer[3])
            self.note_input.insert(0, customer[4])

    def update_customer(self):
        name = self.name_input.get()
        phone = self.phone_input.get()
        email = self.email_input.get()
        address = self.address_input.get()
        note = self.note_input.get()

        if not name or not phone or not email or not address:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers
            SET name = ?, phone = ?, email = ?, address = ?, note = ?
            WHERE name = ?
        ''', (name, phone, email, address, note, self.customer_name))
        conn.commit()
        conn.close()

        print("Customer updated in the database")
        self.destroy()

class AddSupplierDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Add Supplier")
        self.geometry("400x400")
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.name_input = ctk.CTkEntry(form_layout, placeholder_text="Name")
        self.name_input.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Name:").grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.phone_input = ctk.CTkEntry(form_layout, placeholder_text="Phone")
        self.phone_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Phone:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.email_input = ctk.CTkEntry(form_layout, placeholder_text="Email")
        self.email_input.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Email:").grid(row=2, column=0, pady=5, padx=5, sticky="w")

        self.address_input = ctk.CTkEntry(form_layout, placeholder_text="Address")
        self.address_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Address:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.note_input = ctk.CTkEntry(form_layout, placeholder_text="Note")
        self.note_input.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Note:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.outstanding_balance_input = ctk.CTkEntry(form_layout, placeholder_text="Outstanding Balance")
        self.outstanding_balance_input.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Outstanding Balance:").grid(row=5, column=0, pady=5, padx=5, sticky="w")

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_supplier)
        save_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def save_supplier(self):
        name = self.name_input.get()
        phone = self.phone_input.get()
        email = self.email_input.get()
        address = self.address_input.get()
        note = self.note_input.get()
        outstanding_balance_text = self.outstanding_balance_input.get()

        if not name or not phone or not email or not address or not outstanding_balance_text:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            outstanding_balance = float(outstanding_balance_text)
        except ValueError:
            self.error_label.configure(text="Error: Outstanding Balance must be a valid number")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO suppliers (name, phone, email, address, note, outstanding_balance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, phone, email, address, note, outstanding_balance))
        conn.commit()
        conn.close()

        print("Supplier added to the database")
        self.destroy()

class ItemOptionsDialog(ctk.CTkToplevel):
    def __init__(self, item_name, parent=None):
        super().__init__(parent)
        self.title("Item Options")
        self.geometry("300x200")
        self.item_name = item_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        edit_item_button = ctk.CTkButton(layout, text="Edit Item", command=self.open_edit_item_dialog)
        edit_item_button.pack(pady=10)

        update_stock_button = ctk.CTkButton(layout, text="Update Stock", command=self.open_update_stock_dialog)
        update_stock_button.pack(pady=10)

        close_button = ctk.CTkButton(layout, text="Close", command=self.destroy)
        close_button.pack(pady=10)

    def open_edit_item_dialog(self):
        dialog = EditItemDialog(self.item_name, self)
        dialog.grab_set()

    def open_update_stock_dialog(self):
        dialog = UpdateStockDialog(self.item_name, self)
        dialog.grab_set()

class UpdateStockDialog(ctk.CTkToplevel):
    def __init__(self, item_name, parent=None):
        super().__init__(parent)
        self.title("Update Stock")
        self.geometry("300x200")
        self.item_name = item_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        self.quantity_input = ctk.CTkEntry(layout, placeholder_text="Quantity")
        self.quantity_input.pack(pady=10)

        update_button = ctk.CTkButton(layout, text="Update", command=self.update_stock)
        update_button.pack(pady=10)

        close_button = ctk.CTkButton(layout, text="Close", command=self.destroy)
        close_button.pack(pady=10)

    def update_stock(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM items WHERE name = ?', (self.item_name,))
        current_quantity = cursor.fetchone()[0]

        new_quantity_text = self.quantity_input.get()
        try:
            new_quantity = int(new_quantity_text)
        except ValueError:
            ctk.CTkMessageBox.show_warning("Input Error", "Quantity must be a valid number")
            return

        updated_quantity = current_quantity + new_quantity
        if updated_quantity < 0:
            updated_quantity = -abs(updated_quantity)

        cursor.execute('''
            UPDATE items
            SET quantity = ?
            WHERE name = ?
        ''', (updated_quantity, self.item_name))
        conn.commit()
        conn.close()

        print("Stock updated in the database")
        self.destroy()

if __name__ == '__main__':
    app = ERPApp()
    app.mainloop()