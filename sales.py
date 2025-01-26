import customtkinter as ctk
import sqlite3
from tkinter import ttk
from datetime import datetime, timedelta
from modules.cashier import CashierModule

class SalesModule:
    def __init__(self, master):
        self.widget = ctk.CTkFrame(master)
        self.layout = ctk.CTkFrame(self.widget)
        self.layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(self.layout)
        top_section.pack(fill="x", pady=10)

        self.search_box = ctk.CTkEntry(top_section, placeholder_text="Search Invoices...")
        self.search_box.pack(side="left", padx=5, fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.on_search_key_release)

        self.table = ttk.Treeview(self.layout, columns=("Invoice ID", "Date", "Total Amount"), show="headings")
        self.table.heading("Invoice ID", text="Invoice ID")
        self.table.heading("Date", text="Date")
        self.table.heading("Total Amount", text="Total Amount")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table.bind("<Double-1>", self.open_edit_invoice_dialog)

        self.create_sections()

    def create_sections(self):
        sections_frame = ctk.CTkFrame(self.layout)
        sections_frame.pack(side="right", fill="y", padx=10)

        daily_button = ctk.CTkButton(sections_frame, text="Daily Invoices", command=self.show_daily_invoices)
        daily_button.pack(pady=5)

        weekly_button = ctk.CTkButton(sections_frame, text="Weekly Invoices", command=self.show_weekly_invoices)
        weekly_button.pack(pady=5)

        monthly_button = ctk.CTkButton(sections_frame, text="Monthly Invoices", command=self.show_monthly_invoices)
        monthly_button.pack(pady=5)

        all_button = ctk.CTkButton(sections_frame, text="All Invoices", command=self.show_all_invoices)
        all_button.pack(pady=5)

        self.invoice_count_label = ctk.CTkLabel(self.layout, text="Total Invoices: 0")
        self.invoice_count_label.pack(side="bottom", pady=10)

    def on_search_key_release(self, event):
        if hasattr(self, 'search_timer'):
            self.widget.after_cancel(self.search_timer)
        self.search_timer = self.widget.after(500, self.search_invoices)

    def search_invoices(self):
        text = self.search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, total_amount FROM invoices WHERE id LIKE ?', ('%' + text + '%',))
        invoices = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for invoice in invoices:
            self.table.insert("", "end", values=(invoice[0], invoice[1], invoice[2]))

        self.update_invoice_count()

    def show_daily_invoices(self):
        today = datetime.now().date()
        self.load_invoices_by_date_range(today, today)

    def show_weekly_invoices(self):
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        self.load_invoices_by_date_range(start_of_week, today)

    def show_monthly_invoices(self):
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        self.load_invoices_by_date_range(start_of_month, today)

    def show_all_invoices(self):
        self.load_invoices_by_date_range(None, None)

    def load_invoices_by_date_range(self, start_date, end_date):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute('SELECT id, date, total_amount FROM invoices WHERE date BETWEEN ? AND ?', (start_date, end_date))
        else:
            cursor.execute('SELECT id, date, total_amount FROM invoices')
        invoices = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for invoice in invoices:
            self.table.insert("", "end", values=(invoice[0], invoice[1], invoice[2]))

        self.update_invoice_count()

    def update_invoice_count(self):
        total_invoices = len(self.table.get_children())
        self.invoice_count_label.configure(text=f"Total Invoices: {total_invoices}")

    def open_edit_invoice_dialog(self, event):
        selected_invoice_id = self.table.item(self.table.selection())['values'][0]
        dialog = EditInvoiceDialog(selected_invoice_id, self.widget)
        dialog.grab_set()

    def get_widget(self):
        return self.widget

class EditInvoiceDialog(ctk.CTkToplevel):
    def __init__(self, invoice_id, parent=None):
        super().__init__(parent)
        self.title("Edit Invoice")
        self.geometry("600x400")
        self.invoice_id = invoice_id
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.invoice_table = ttk.Treeview(layout, columns=("Item", "Quantity", "Price", "Total"), show="headings")
        self.invoice_table.heading("Item", text="Item")
        self.invoice_table.heading("Quantity", text="Quantity")
        self.invoice_table.heading("Price", text="Price")
        self.invoice_table.heading("Total", text="Total")
        self.invoice_table.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_invoice)
        save_button.pack(side="left", padx=5)

        delete_button = ctk.CTkButton(button_frame, text="Delete", command=self.delete_invoice)
        delete_button.pack(side="left", padx=5)

        print_button = ctk.CTkButton(button_frame, text="Print", command=self.print_invoice)
        print_button.pack(side="left", padx=5)

        edit_button = ctk.CTkButton(button_frame, text="Edit in Cashier", command=self.edit_in_cashier)
        edit_button.pack(side="left", padx=5)

        self.load_invoice_data()

    def load_invoice_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT item, quantity, price, total FROM invoice_items WHERE invoice_id = ?', (self.invoice_id,))
        items = cursor.fetchall()
        conn.close()

        for item in items:
            self.invoice_table.insert("", "end", values=(item[0], item[1], item[2], item[3]))

    def save_invoice(self):
        # Implement save functionality
        print("Invoice saved")
        self.destroy()

    def delete_invoice(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM invoices WHERE id = ?', (self.invoice_id,))
        cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (self.invoice_id,))
        conn.commit()
        conn.close()

        print("Invoice deleted")
        self.destroy()

    def print_invoice(self):
        # Implement print functionality
        print("Invoice printed")
        self.destroy()

    def edit_in_cashier(self):
        app = QApplication([])
        cashier_window = CashierModule(invoice_id=self.invoice_id)
        cashier_window.show()
        app.exec_()
        self.destroy()
