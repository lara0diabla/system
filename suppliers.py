import customtkinter as ctk
import sqlite3
from tkinter import ttk

class SuppliersModule:
    def __init__(self, master):
        self.widget = ctk.CTkFrame(master)
        self.layout = ctk.CTkFrame(self.widget)
        self.layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(self.layout)
        top_section.pack(fill="x", pady=10)

        self.search_box = ctk.CTkEntry(top_section, placeholder_text="Search Suppliers...")
        self.search_box.pack(side="left", padx=5, fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.on_search_key_release)

        add_supplier_button = ctk.CTkButton(top_section, text="Add Supplier", command=self.open_add_supplier_dialog)
        add_supplier_button.pack(side="left", padx=5)

        edit_supplier_button = ctk.CTkButton(top_section, text="Edit Supplier", command=self.open_edit_supplier_dialog)
        edit_supplier_button.pack(side="left", padx=5)

        payments_button = ctk.CTkButton(top_section, text="Payments", command=self.open_payments_dialog)
        payments_button.pack(side="left", padx=5)

        self.table = ttk.Treeview(self.layout, columns=("Name", "Outstanding Balance"), show="headings")
        self.table.heading("Name", text="Name")
        self.table.heading("Outstanding Balance", text="Outstanding Balance")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table.bind("<Double-1>", self.open_edit_supplier_dialog)

        self.load_suppliers()

    def on_search_key_release(self, event):
        if hasattr(self, 'search_timer'):
            self.widget.after_cancel(self.search_timer)
        self.search_timer = self.widget.after(500, self.search_suppliers)

    def search_suppliers(self):
        text = self.search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, outstanding_balance FROM suppliers WHERE name LIKE ?', ('%' + text + '%',))
        suppliers = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for supplier in suppliers:
            self.table.insert("", "end", values=(supplier[0], supplier[1]))

    def open_add_supplier_dialog(self):
        dialog = AddSupplierDialog(self.widget, self)
        dialog.grab_set()

    def open_edit_supplier_dialog(self, event=None):
        selected_supplier = self.table.item(self.table.selection())['values'][0]
        dialog = EditSupplierDialog(selected_supplier, self.widget)
        dialog.grab_set()

    def open_payments_dialog(self):
        dialog = PaymentsDialog(self.widget)
        dialog.grab_set()

    def get_widget(self):
        return self.widget

    def add_supplier_to_table(self, name, outstanding_balance):
        self.table.insert("", "end", values=(name, outstanding_balance))

    def load_suppliers(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, outstanding_balance FROM suppliers')
        suppliers = cursor.fetchall()
        conn.close()

        for supplier in suppliers:
            self.table.insert("", "end", values=(supplier[0], supplier[1]))

class AddSupplierDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, suppliers_module=None):
        super().__init__(parent)
        self.suppliers_module = suppliers_module
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
        if self.suppliers_module:
            self.suppliers_module.add_supplier_to_table(name, outstanding_balance)
        self.destroy()

class EditSupplierDialog(ctk.CTkToplevel):
    def __init__(self, supplier_name, parent=None):
        super().__init__(parent)
        self.title("Edit Supplier")
        self.geometry("400x400")
        self.supplier_name = supplier_name
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

        update_button = ctk.CTkButton(button_frame, text="Update Supplier", command=self.update_supplier)
        update_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

        self.load_supplier_data()

    def load_supplier_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, phone, email, address, note, outstanding_balance FROM suppliers WHERE name = ?', (self.supplier_name,))
        supplier = cursor.fetchone()
        conn.close()

        if supplier:
            self.name_input.insert(0, supplier[0])
            self.phone_input.insert(0, supplier[1])
            self.email_input.insert(0, supplier[2])
            self.address_input.insert(0, supplier[3])
            self.note_input.insert(0, supplier[4])
            self.outstanding_balance_input.insert(0, supplier[5])

    def update_supplier(self):
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
            UPDATE suppliers
            SET name = ?, phone = ?, email = ?, address = ?, note = ?, outstanding_balance = ?
            WHERE name = ?
        ''', (name, phone, email, address, note, outstanding_balance, self.supplier_name))
        conn.commit()
        conn.close()

        print("Supplier updated in the database")
        self.destroy()

class PaymentsDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Add Payment")
        self.geometry("400x300")
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

        self.amount_input = ctk.CTkEntry(form_layout, placeholder_text="Amount")
        self.amount_input.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Amount:").grid(row=1, column=0, pady=5, padx=5, sticky="w")

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_payment)
        save_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def load_suppliers(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM suppliers')
        suppliers = cursor.fetchall()
        conn.close()
        self.supplier_combo['values'] = [supplier[0] for supplier in suppliers]

    def save_payment(self):
        supplier = self.supplier_combo.get()
        amount_text = self.amount_input.get()

        if not supplier or not amount_text:
            self.error_label.configure(text="Error: All fields must be filled")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            self.error_label.configure(text="Error: Amount must be a valid number")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE suppliers
            SET outstanding_balance = outstanding_balance - ?
            WHERE name = ?
        ''', (amount, supplier))
        conn.commit()
        conn.close()

        print("Payment recorded in the database")
        self.destroy()
