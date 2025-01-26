import customtkinter as ctk
import sqlite3
from tkinter import ttk

class CustomersModule:
    def __init__(self, master):
        self.widget = ctk.CTkFrame(master)
        self.layout = ctk.CTkFrame(self.widget)
        self.layout.pack(fill="both", expand=True)

        top_section = ctk.CTkFrame(self.layout)
        top_section.pack(fill="x", pady=10)

        self.search_box = ctk.CTkEntry(top_section, placeholder_text="Search Customers...")
        self.search_box.pack(side="left", padx=5, fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.on_search_key_release)

        add_customer_button = ctk.CTkButton(top_section, text="Add Customer", command=self.open_add_customer_dialog)
        add_customer_button.pack(side="left", padx=5)

        edit_customer_button = ctk.CTkButton(top_section, text="Edit Customer", command=self.open_edit_customer_dialog)
        edit_customer_button.pack(side="left", padx=5)

        payment_button = ctk.CTkButton(top_section, text="Payment", command=self.open_payment_window)
        payment_button.pack(side="left", padx=5)

        show_all_button = ctk.CTkButton(top_section, text="Show All Customers", command=self.show_all_customers)
        show_all_button.pack(side="left", padx=5)

        self.table = ttk.Treeview(self.layout, columns=("Name", "Outstanding Balance"), show="headings")
        self.table.heading("Name", text="Name")
        self.table.heading("Outstanding Balance", text="Outstanding Balance")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.table.bind("<Double-1>", self.open_customer_control_window)

        self.show_all_customers()

    def on_search_key_release(self, event):
        if hasattr(self, 'search_timer'):
            self.widget.after_cancel(self.search_timer)
        self.search_timer = self.widget.after(250, self.search_customers)  # Reduced delay to 250 milliseconds

    def search_customers(self):
        text = self.search_box.get()
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, outstanding_balance FROM customers WHERE name LIKE ?', ('%' + text + '%',))
        customers = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for customer in customers:
            self.table.insert("", "end", values=(customer[0], customer[1]))

    def show_all_customers(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, outstanding_balance FROM customers')
        customers = cursor.fetchall()
        conn.close()

        for i in self.table.get_children():
            self.table.delete(i)

        for customer in customers:
            self.table.insert("", "end", values=(customer[0], customer[1]))

    def open_add_customer_dialog(self):
        dialog = AddCustomerDialog(self.widget)
        dialog.grab_set()

    def open_edit_customer_dialog(self, event=None):
        if not self.table.selection():
            return
        selected_customer = self.table.item(self.table.selection())['values'][0]
        dialog = EditCustomerDialog(selected_customer, self.widget)
        dialog.grab_set()

    def open_payment_window(self):
        if not self.table.selection():
            return
        selected_customer = self.table.item(self.table.selection())['values'][0]
        dialog = PaymentWindow(selected_customer, self.widget)
        dialog.grab_set()

    def open_customer_control_window(self, event=None):
        if not self.table.selection():
            return
        selected_customer = self.table.item(self.table.selection())['values'][0]
        dialog = CustomerControlWindow(selected_customer, self.widget)
        dialog.grab_set()

    def get_widget(self):
        return self.widget

class AddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Add Customer")
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

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_customer)
        save_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def save_customer(self):
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
            INSERT INTO customers (name, phone, email, address, note, outstanding_balance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, phone, email, address, note, outstanding_balance))
        conn.commit()
        conn.close()

        print("Customer added to the database")
        self.destroy()

class EditCustomerDialog(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title("Edit Customer")
        self.geometry("400x400")
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

        self.outstanding_balance_input = ctk.CTkEntry(form_layout, placeholder_text="Outstanding Balance")
        self.outstanding_balance_input.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        ctk.CTkLabel(form_layout, text="Outstanding Balance:").grid(row=5, column=0, pady=5, padx=5, sticky="w")

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
        cursor.execute('SELECT name, phone, email, address, note, outstanding_balance FROM customers WHERE name = ?', (self.customer_name,))
        customer = cursor.fetchone()
        conn.close()

        if customer:
            self.name_input.insert(0, customer[0])
            self.phone_input.insert(0, customer[1])
            self.email_input.insert(0, customer[2])
            self.address_input.insert(0, customer[3])
            self.note_input.insert(0, customer[4])
            self.outstanding_balance_input.insert(0, customer[5])

    def update_customer(self):
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
            UPDATE customers
            SET name = ?, phone = ?, email = ?, address = ?, note = ?, outstanding_balance = ?
            WHERE name = ?
        ''', (name, phone, email, address, note, outstanding_balance, self.customer_name))
        conn.commit()
        conn.close()

        print("Customer updated in the database")
        self.destroy()

class PaymentWindow(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title("Customer Payment")
        self.geometry("400x300")
        self.customer_name = customer_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        form_layout = ctk.CTkFrame(layout)
        form_layout.pack(pady=10, padx=10, fill="both", expand=True)

        self.customer_label = ctk.CTkLabel(form_layout, text=f"Customer: {self.customer_name}")
        self.customer_label.grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.payment_input = ctk.CTkEntry(form_layout, placeholder_text="Enter payment amount")
        self.payment_input.grid(row=1, column=0, pady=5, padx=5, sticky="ew")

        self.error_label = ctk.CTkLabel(layout, text="")
        self.error_label.pack(pady=5)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_payment)
        save_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.destroy)
        exit_button.pack(side="left", padx=5)

    def save_payment(self):
        payment_text = self.payment_input.get()
        if not payment_text:
            self.error_label.configure(text="Error: Payment amount must be filled")
            return

        try:
            payment_amount = float(payment_text)
        except ValueError:
            self.error_label.configure(text="Error: Payment amount must be a valid number")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT outstanding_balance FROM customers WHERE name = ?', (self.customer_name,))
        customer = cursor.fetchone()
        if customer:
            outstanding_balance = customer[0]
            new_balance = outstanding_balance - payment_amount
            cursor.execute('''
                UPDATE customers
                SET outstanding_balance = ?
                WHERE name = ?
            ''', (new_balance, self.customer_name))
            conn.commit()
        conn.close()

        print(f"Payment of {payment_amount} saved for customer {self.customer_name}")
        self.destroy()

class CustomerControlWindow(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title("Customer Control")
        self.geometry("400x600")
        self.customer_name = customer_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.customer_label = ctk.CTkLabel(layout, text=f"Customer: {self.customer_name}")
        self.customer_label.pack(pady=10)

        payment_button = ctk.CTkButton(layout, text="دفع", command=self.open_payment_screen, fg_color="green")
        payment_button.pack(pady=10)

        add_debt_button = ctk.CTkButton(layout, text="إضافة رصيد مدين", command=self.add_debt_balance, fg_color="#D4AC0D")
        add_debt_button.pack(pady=10)

        view_payments_button = ctk.CTkButton(layout, text="عرض المدفوعات", command=self.view_payments, fg_color="blue")
        view_payments_button.pack(pady=10)

        edit_customer_button = ctk.CTkButton(layout, text="تعديل الزبون", command=self.edit_customer, fg_color="blue")
        edit_customer_button.pack(pady=10)

        close_button = ctk.CTkButton(layout, text="إغلاق", command=self.destroy, fg_color="firebrick")
        close_button.pack(pady=10)

    def open_payment_screen(self):
        dialog = PaymentWindow(self.customer_name, self)
        dialog.grab_set()

    def add_debt_balance(self):
        print("تم فتح شاشة إضافة رصيد مدين")
        # Implement the add debt balance logic here

    def view_payments(self):
        dialog = ViewPaymentsWindow(self.customer_name, self)
        dialog.grab_set()

    def edit_customer(self):
        print("تم فتح شاشة تعديل الزبون")
        dialog = EditCustomerDialog(self.customer_name, self)
        dialog.grab_set()

class ViewPaymentsWindow(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title("Customer Payments")
        self.geometry("600x400")
        self.customer_name = customer_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True)

        self.table = ttk.Treeview(layout, columns=("Date", "Amount"), show="headings")
        self.table.heading("Date", text="Date")
        self.table.heading("Amount", text="Amount")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        close_button = ctk.CTkButton(layout, text="Close", command=self.destroy)
        close_button.pack(pady=10)

        self.load_payments()

    def load_payments(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT date, amount FROM transactions WHERE customer = ?', (self.customer_name,))
        payments = cursor.fetchall()
        conn.close()

        for payment in payments:
            self.table.insert("", "end", values=(payment[0], payment[1]))

class CustomerWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("إضافة/تعديل زبون")
        self.geometry("400x300")
        
        # عناصر الواجهة
        self.label_name = ctk.CTkLabel(self, text="الاسم:")
        self.label_name.pack(pady=10)
        
        self.entry_name = ctk.CTkEntry(self)
        self.entry_name.pack(pady=10)

        self.label_phone = ctk.CTkLabel(self, text="رقم الهاتف:")
        self.label_phone.pack(pady=10)
        
        self.entry_phone = ctk.CTkEntry(self)
        self.entry_phone.pack(pady=10)

        self.label_address = ctk.CTkLabel(self, text="العنوان:")
        self.label_address.pack(pady=10)
        
        self.entry_address = ctk.CTkEntry(self)
        self.entry_address.pack(pady=10)

        self.button_save = ctk.CTkButton(self, text="حفظ", command=self.save_customer)
        self.button_save.pack(pady=20)

    def save_customer(self):
        name = self.entry_name.get()
        phone = self.entry_phone.get()
        address = self.entry_address.get()
        
        # هنا يمكنك إضافة كود لحفظ البيانات، مثل قاعدة بيانات
        print(f"تم حفظ الزبون: {name}, {phone}, {address}")
        
        # مسح الحقول بعد الحفظ
        self.entry_name.delete(0, ctk.END)
        self.entry_phone.delete(0, ctk.END)
        self.entry_address.delete(0, ctk.END)

def main():
    # إعداد نافذة التطبيق الرئيسية
    root = ctk.CTk()
    root.title("برنامج المبيعات")
    root.geometry("300x200")

    button_add_customer = ctk.CTkButton(root, text="إضافة زبون", command=lambda: CustomerWindow(master=root))
    button_add_customer.pack(pady=40)

    root.mainloop()

if __name__ == "__main__":
    main()
