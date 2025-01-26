import customtkinter as ctk
import sqlite3
from tkinter import ttk
import time

class PurchasesModule:
    def __init__(self, master):
        self.widget = ctk.CTkFrame(master)
        self.layout = ctk.CTkFrame(self.widget)
        self.layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(self.layout)
        top_section.pack(fill="x", pady=10)

        self.search_box = ctk.CTkEntry(top_section, placeholder_text="Search Purchase Invoices...")
        self.search_box.pack(side="left", padx=5, fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.on_search_key_release)

        add_purchase_button = ctk.CTkButton(top_section, text="Add Purchase Invoice", command=self.open_add_purchase_dialog)
        add_purchase_button.pack(side="left", padx=5)

        add_return_button = ctk.CTkButton(top_section, text="Add Return Invoice", command=self.open_add_return_dialog)
        add_return_button.pack(side="left", padx=5)

        self.table = ttk.Treeview(self.layout, columns=("Invoice ID", "Supplier", "Date", "Total Amount"), show="headings")
        self.table.heading("Invoice ID", text="Invoice ID")
        self.table.heading("Supplier", text="Supplier")
        self.table.heading("Date", text="Date")
        self.table.heading("Total Amount", text="Total Amount")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table.bind("<Double-1>", self.open_edit_purchase_dialog)

    def on_search_key_release(self, event):
        if hasattr(self, 'search_timer'):
            self.widget.after_cancel(self.search_timer)
        self.search_timer = self.widget.after(250, self.search_purchases)  # Reduced delay to 250 milliseconds

    def search_purchases(self):
        text = self.search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        if text:
            cursor.execute('SELECT id, supplier, date, total_amount FROM purchases WHERE id LIKE ?', ('%' + text + '%',))
        else:
            cursor.execute('SELECT id, supplier, date, total_amount FROM purchases')
        purchases = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for purchase in purchases:
            self.table.insert("", "end", values=(purchase[0], purchase[1], purchase[2], purchase[3]))

    def open_add_purchase_dialog(self):
        dialog = AddPurchaseDialog(self.widget, self)
        dialog.grab_set()

    def open_add_return_dialog(self):
        dialog = AddReturnDialog(self.widget)
        dialog.grab_set()

    def open_edit_purchase_dialog(self, event):
        selected_purchase_id = self.table.item(self.table.selection())['values'][0]
        dialog = PurchaseDetailsDialog(selected_purchase_id, self.widget)
        dialog.grab_set()

    def get_widget(self):
        return self.widget

    def add_purchase_to_table(self, invoice_id, supplier, date, total_amount):
        self.table.insert("", "end", values=(invoice_id, supplier, date, total_amount))

class AddPurchaseDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, purchases_module=None):
        super().__init__(parent)
        self.purchases_module = purchases_module
        self.title("Add Purchase Invoice")
        self.geometry("800x600")
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.supplier_combo = ttk.Combobox(form_layout)
        self.supplier_combo.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Supplier:").grid(row=0, column=0, pady=5, padx=5, sticky="w")
        self.load_suppliers()

        self.item_search_box = ctk.CTkEntry(form_layout, placeholder_text="Search Item...")
        self.item_search_box.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        self.item_search_box.bind("<KeyRelease>", self.search_items)
        ctk.CTkLabel(form_layout, text="Item:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.item_combo = ttk.Combobox(form_layout)
        self.item_combo.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        self.item_combo.bind("<<ComboboxSelected>>", self.load_item_prices)

        self.quantity_input = ctk.CTkEntry(form_layout, placeholder_text="Quantity")
        self.quantity_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Quantity:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.purchase_price_input = ctk.CTkEntry(form_layout, placeholder_text="Purchase Price")
        self.purchase_price_input.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Purchase Price:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.sale_price_input = ctk.CTkEntry(form_layout, placeholder_text="Sale Price")
        self.sale_price_input.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Sale Price:").grid(row=5, column=0, pady=5, padx=5, sticky="w")

        button_frame = ctk.CTkFrame(form_layout)
        button_frame.grid(row=6, column=1, pady=5, padx=5, sticky="ew")

        add_item_button = ctk.CTkButton(button_frame, text="Add Item", command=self.add_item_to_table)
        add_item_button.pack(side="left", padx=5)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_purchase)
        save_button.pack(side="left", padx=5)

        print_button = ctk.CTkButton(button_frame, text="Print", command=self.print_purchase)
        print_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

        self.table = ttk.Treeview(layout, columns=("Item", "Quantity", "Purchase Price", "Sale Price"), show="headings")
        self.table.heading("Item", text="Item")
        self.table.heading("Quantity", text="Quantity")
        self.table.heading("Purchase Price", text="Purchase Price")
        self.table.heading("Sale Price", text="Sale Price")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

    def load_suppliers(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM suppliers')
        suppliers = cursor.fetchall()
        conn.close()
        self.supplier_combo['values'] = [supplier[0] for supplier in suppliers]

    def search_items(self, event):
        text = self.item_search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM items WHERE name LIKE ?', ('%' + text + '%',))
        items = cursor.fetchall()
        conn.close()
        self.item_combo['values'] = [item[0] for item in items]

    def load_item_prices(self, event):
        item_name = self.item_combo.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT purchase_price, sale_price FROM items WHERE name = ?', (item_name,))
        item = cursor.fetchone()
        conn.close()
        if item:
            self.purchase_price_input.delete(0, 'end')
            self.purchase_price_input.insert(0, item[0])
            self.sale_price_input.delete(0, 'end')
            self.sale_price_input.insert(0, item[1])

    def add_item_to_table(self):
        item = self.item_combo.get()
        quantity_text = self.quantity_input.get()
        purchase_price_text = self.purchase_price_input.get()
        sale_price_text = self.sale_price_input.get()

        if not item or not quantity_text or not purchase_price_text or not sale_price_text:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            quantity = int(quantity_text)
            purchase_price = float(purchase_price_text)
            sale_price = float(sale_price_text)
        except ValueError:
            self.error_label.configure(text="Error: Quantity and Prices must be valid numbers")
            return

        self.table.insert("", "end", values=(item, quantity, purchase_price, sale_price))

    def save_purchase(self):
        supplier = self.supplier_combo.get()
        if not supplier:
            self.error_label.configure(text="Error: Supplier must be selected")
            return

        total_amount = 0
        for row in self.table.get_children():
            item, quantity, purchase_price, sale_price = self.table.item(row)['values']
            quantity = int(quantity)
            purchase_price = float(purchase_price)
            sale_price = float(sale_price)
            total_amount += quantity * purchase_price

        retries = 5
        while retries:
            try:
                conn = sqlite3.connect('sqlite3.db')
                cursor = conn.cursor()
                for row in self.table.get_children():
                    item, quantity, purchase_price, sale_price = self.table.item(row)['values']
                    quantity = int(quantity)
                    purchase_price = float(purchase_price)
                    sale_price = float(sale_price)
                    cursor.execute('''
                        INSERT INTO purchases (supplier, item, quantity, price, total_amount)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (supplier, item, quantity, purchase_price, quantity * purchase_price))
                    cursor.execute('''
                        UPDATE items
                        SET quantity = quantity + ?, purchase_price = ?, sale_price = ?
                        WHERE name = ?
                    ''', (quantity, purchase_price, sale_price, item))
                cursor.execute('''
                    UPDATE suppliers
                    SET outstanding_balance = outstanding_balance + ?
                    WHERE name = ?
                ''', (total_amount, supplier))
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    retries -= 1
                    time.sleep(1)
                else:
                    raise

        if self.purchases_module:
            self.purchases_module.add_purchase_to_table(cursor.lastrowid, supplier, "Today", total_amount)

        print("Purchase invoice saved to the database")
        self.destroy()

    def print_purchase(self):
        # Implement print functionality
        print("Purchase invoice printed")
        self.destroy()

class AddReturnDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Add Return Invoice")
        self.geometry("600x400")
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.supplier_input = ctk.CTkEntry(form_layout, placeholder_text="Supplier")
        self.supplier_input.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Supplier:").grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.item_input = ctk.CTkEntry(form_layout, placeholder_text="Item")
        self.item_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Item:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.quantity_input = ctk.CTkEntry(form_layout, placeholder_text="Quantity")
        self.quantity_input.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Quantity:").grid(row=2, column=0, pady=5, padx=5, sticky="w")

        self.price_input = ctk.CTkEntry(form_layout, placeholder_text="Price")
        self.price_input.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Price:").grid(row=3, column=0, pady=5, padx=5, sticky="w")

        self.total_amount_label = ctk.CTkLabel(form_layout, text="Total Amount: 0")
        self.total_amount_label.grid(row=4, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Total Amount:").grid(row=4, column=0, pady=5, padx=5, sticky="w")

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_return)
        save_button.pack(side="left", padx=5)

        print_button = ctk.CTkButton(button_frame, text="Print", command=self.print_return)
        print_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def save_return(self):
        supplier = self.supplier_input.get()
        item = self.item_input.get()
        quantity_text = self.quantity_input.get()
        price_text = self.price_input.get()

        if not supplier or not item or not quantity_text or not price_text:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            quantity = int(quantity_text)
            price = float(price_text)
            total_amount = quantity * price
        except ValueError:
            self.error_label.configure(text="Error: Quantity and Price must be valid numbers")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO returns (supplier, item, quantity, price, total_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (supplier, item, quantity, price, total_amount))
        cursor.execute('''
            UPDATE items
            SET quantity = quantity - ?
            WHERE name = ?
        ''', (quantity, item))
        cursor.execute('''
            UPDATE suppliers
            SET outstanding_balance = outstanding_balance - ?
            WHERE name = ?
        ''', (total_amount, supplier))
        conn.commit()
        conn.close()

        print("Return invoice saved to the database")
        self.destroy()

    def print_return(self):
        # Implement print functionality
        print("Return invoice printed")
        self.destroy()

class PurchaseDetailsDialog(ctk.CTkToplevel):
    def __init__(self, purchase_id, parent=None):
        super().__init__(parent)
        self.title("Purchase Invoice Details")
        self.geometry("800x600")
        self.purchase_id = purchase_id
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.purchase_table = ttk.Treeview(layout, columns=("Item", "Quantity", "Price", "Total"), show="headings")
        self.purchase_table.heading("Item", text="Item")
        self.purchase_table.heading("Quantity", text="Quantity")
        self.purchase_table.heading("Price", text="Price")
        self.purchase_table.heading("Total", text="Total")
        self.purchase_table.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy)
        close_button.pack(side="left", padx=5)

        self.load_purchase_data()

    def load_purchase_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT item, quantity, price, total FROM purchase_items WHERE purchase_id = ?', (self.purchase_id,))
        items = cursor.fetchall()
        conn.close()

        for item in items:
            self.purchase_table.insert("", "end", values=(item[0], item[1], item[2], item[3]))
