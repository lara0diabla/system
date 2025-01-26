import customtkinter as ctk
import sqlite3
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import os

class ReportsModule:
    def __init__(self, master):
        self.widget = ctk.CTkFrame(master)
        self.layout = ctk.CTkFrame(self.widget)
        self.layout.pack(fill="both", expand=True)
        
        # واجهة التبويبات
        self.tabview = ctk.CTkTabview(self.layout)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # إضافة أقسام التقارير كـ تبويبات
        self.sales_tab = self.tabview.add("المبيعات")
        self.purchases_tab = self.tabview.add("المشتريات")
        self.customers_tab = self.tabview.add("الزبائن")
        self.suppliers_tab = self.tabview.add("الموردين")
        self.checks_tab = self.tabview.add("الشيكات")
        
        # تهيئة أقسام التقارير
        self.sales_frame = SalesReportsFrame(self.sales_tab, self.load_data_into_table, self.show_invoice, self.load_invoice_details_table)
        self.sales_frame.pack(fill="both", expand=True)
        self.purchases_frame = PurchasesReportsFrame(self.purchases_tab, self.load_data_into_table, self.show_invoice)
        self.purchases_frame.pack(fill="both", expand=True)
        self.customers_frame = CustomersReportsFrame(self.customers_tab, self.load_data_into_table)
        self.customers_frame.pack(fill="both", expand=True)
        self.suppliers_frame = SuppliersReportsFrame(self.suppliers_tab, self.load_data_into_table)
        self.suppliers_frame.pack(fill="both", expand=True)
        self.checks_frame = ChecksReportsFrame(self.checks_tab, self.load_data_into_table)
        self.checks_frame.pack(fill="both", expand=True)
    
    def load_data_into_table(self, headers, data, with_invoice=False, table_for_details=False, container=None):
        """تحديث جدول العرض مع البيانات الجديدة."""
        if container is None:
            container = self.tabview.tab(self.tabview.get())  # استخدم التبويب الحالي كحاوية افتراضية
        if table_for_details == False:
            # حذف البيانات القديمة من الجدول الرئيسي
            if hasattr(self, 'table'):
                for item in self.table.get_children():
                    self.table.delete(item)
            else:
                # إنشاء جدول رئيسي جديد إذا لم يكن موجود
                self.table = ttk.Treeview(container, show="headings")
           
            # إعادة تهيئة رؤوس الجدول الرئيسي
            self.table['columns'] = headers
            for header in headers:
                self.table.heading(header, text=header)

            # إضافة البيانات الجديدة
            for row in data:
               self.table.insert("", "end", values=row)
            
            # إضافة أوامر الطباعة والحفظ
            if hasattr(self, 'print_save_frame'):
                 self.print_save_frame.destroy()
            self.print_save_frame = ctk.CTkFrame(container)
            self.print_save_frame.pack(pady=5, fill="x")
            self.print_button = ctk.CTkButton(self.print_save_frame, text="طباعة", command=lambda: self.print_report(container), width=100)
            self.print_button.pack(side="left", padx=5)
            self.save_button = ctk.CTkButton(self.print_save_frame, text="حفظ", command=lambda: self.save_report(container), width=100)
            self.save_button.pack(side="left", padx=5)
            
            # إضافة حدث النقر على الصف إذا كان هناك فواتير
            if with_invoice:
                self.table.bind("<Double-1>", self.on_table_row_click)
            else:
               self.table.unbind("<Double-1>")

            # عرض الجدول في الواجهة
            self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def load_invoice_details_table(self, headers, data, container=None):
            # حذف البيانات القديمة من الجدول الثانوي
            if container is None:
                container = self.tabview.get_current_tab()
            if hasattr(self, 'details_table'):
                for item in self.details_table.get_children():
                     self.details_table.delete(item)
            else:
                # إنشاء جدول ثانوي جديد إذا لم يكن موجود
                 self.details_table = ttk.Treeview(container, show="headings")
            
             # إعادة تهيئة رؤوس الجدول الثانوي
            self.details_table['columns'] = headers
            for header in headers:
                self.details_table.heading(header, text=header)
             
             # إضافة البيانات الجديدة
            for row in data:
                self.details_table.insert("", "end", values=row)
            
            # عرض الجدول في الواجهة
            self.details_table.pack(fill="both", expand=True, padx=10, pady=10)
    
    def on_table_row_click(self, event):
        selected_item = self.table.selection()[0]
        invoice_id = self.table.item(selected_item)['values'][0] # نفترض أن الـ ID هو أول عمود
        current_tab = self.tabview.get_current_tab()
        if current_tab == "المبيعات":
             self.load_invoice_details_table_data(invoice_id)
        elif current_tab == "المشتريات":
             self.show_invoice(invoice_id, "purchases")
    
    def show_invoice(self, invoice_id, invoice_type):
         InvoiceWindow(self, invoice_id, invoice_type)
         
    def load_invoice_details_table_data(self, invoice_id):
        current_tab = self.tabview.get_current_tab()
        if current_tab == "المبيعات":
           invoice_details_data = get_sales_invoice_details_for_table(invoice_id)
           if invoice_details_data:
              headers = ("اسم العنصر", "الكمية", "السعر", "الإجمالي")
              self.load_invoice_details_table(headers, invoice_details_data, container=self.sales_tab)
           else:
              messagebox.showinfo("لا يوجد بيانات", "لا توجد تفاصيل لهذه الفاتورة.")

    def get_widget(self):
        return self.widget
        
    def print_report(self, container):
        """طباعة التقرير."""
        if hasattr(self, 'table') and self.table.get_children():
            try:
                import win32print
                printer_name = win32print.GetDefaultPrinter()
                
                # تجهيز التقرير للطباعة
                report_text = self.prepare_report_for_print()
                
                # طباعة التقرير
                with open("temp_report.txt", "w", encoding="utf-8") as temp_file:
                    temp_file.write(report_text)
                
                os.startfile("temp_report.txt", "print") # Windows
                os.remove("temp_report.txt")
            except Exception as e:
                messagebox.showerror("خطأ في الطباعة", f"حدث خطأ أثناء الطباعة: {e}")
        else:
           messagebox.showinfo("لا يوجد بيانات", "لا يوجد بيانات لطباعتها.")
    
    def prepare_report_for_print(self):
          """تجهيز التقرير كنص للطباعة أو الحفظ."""
          if hasattr(self, 'table'):
              report_text = ""
              headers = self.table['columns']
              report_text += "\t".join(headers) + "\n"
              for item in self.table.get_children():
                  row = self.table.item(item)['values']
                  report_text += "\t".join(map(str, row)) + "\n"
              return report_text
          else:
             return ""

    def save_report(self, container):
        """حفظ التقرير في ملف."""
        if hasattr(self, 'table') and self.table.get_children():
            report_text = self.prepare_report_for_print()
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(report_text)
                    messagebox.showinfo("تم الحفظ", "تم حفظ التقرير بنجاح.")
                except Exception as e:
                   messagebox.showerror("خطأ في الحفظ", f"حدث خطأ أثناء الحفظ: {e}")
        else:
             messagebox.showinfo("لا يوجد بيانات", "لا يوجد بيانات لحفظها.")
        
class InvoiceWindow(ctk.CTkToplevel):
    def __init__(self, master, invoice_id, invoice_type, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"تفاصيل الفاتورة رقم: {invoice_id}")
        self.geometry("600x400")
        
        self.invoice_id = invoice_id
        self.invoice_type = invoice_type
        
        self.load_invoice_details()
    
    def load_invoice_details(self):
        if self.invoice_type == "sales":
            invoice_data = get_sales_invoice_details(self.invoice_id)
            if invoice_data:
                self.create_sales_invoice_layout(invoice_data)
        elif self.invoice_type == "purchases":
            invoice_data = get_purchases_invoice_details(self.invoice_id)
            if invoice_data:
                self.create_purchases_invoice_layout(invoice_data)
    
    def create_sales_invoice_layout(self, invoice_data):
         # عرض البيانات في مربعات نصوص
         ctk.CTkLabel(self, text=f"رقم الفاتورة: {invoice_data[0]}", font=("Arial", 14, "bold")).pack(pady=5)
         ctk.CTkLabel(self, text=f"تاريخ الفاتورة: {invoice_data[1]}", font=("Arial", 12)).pack(pady=3)
         ctk.CTkLabel(self, text=f"اسم العميل: {invoice_data[2]}", font=("Arial", 12)).pack(pady=3)
         ctk.CTkLabel(self, text=f"اسم المنتج: {invoice_data[3]}", font=("Arial", 12)).pack(pady=3)
         ctk.CTkLabel(self, text=f"الكمية: {invoice_data[4]}", font=("Arial", 12)).pack(pady=3)
         ctk.CTkLabel(self, text=f"سعر الوحدة: {invoice_data[5]}", font=("Arial", 12)).pack(pady=3)
         ctk.CTkLabel(self, text=f"المجموع الكلي: {invoice_data[6]}", font=("Arial", 12)).pack(pady=3)
        
    def create_purchases_invoice_layout(self, invoice_data):
        ctk.CTkLabel(self, text=f"رقم الفاتورة: {invoice_data[0]}", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(self, text=f"تاريخ الفاتورة: {invoice_data[1]}", font=("Arial", 12)).pack(pady=3)
        ctk.CTkLabel(self, text=f"اسم المورد: {invoice_data[2]}", font=("Arial", 12)).pack(pady=3)
        ctk.CTkLabel(self, text=f"اسم المنتج: {invoice_data[3]}", font=("Arial", 12)).pack(pady=3)
        ctk.CTkLabel(self, text=f"الكمية: {invoice_data[4]}", font=("Arial", 12)).pack(pady=3)
        ctk.CTkLabel(self, text=f"سعر الوحدة: {invoice_data[5]}", font=("Arial", 12)).pack(pady=3)
        ctk.CTkLabel(self, text=f"المجموع الكلي: {invoice_data[6]}", font=("Arial", 12)).pack(pady=3)

# --- أقسام التقارير ---

class ReportFrameBase(ctk.CTkFrame):
    def __init__(self, master, load_data_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.load_data_callback = load_data_callback
    
class SalesReportsFrame(ReportFrameBase):
    def __init__(self, master, load_data_callback, show_invoice_callback, load_invoice_details_table, **kwargs):
        super().__init__(master, load_data_callback, **kwargs)
        self.show_invoice_callback = show_invoice_callback
        self.load_invoice_details_table = load_invoice_details_table
        
        # عناوين الأزرار
        sales_report_label = ctk.CTkLabel(self, text="تقارير المبيعات", font=ctk.CTkFont(size=18, weight="bold"))
        sales_report_label.pack(pady=10)

        # زر مبيعات اليوم
        self.daily_sales_button = ctk.CTkButton(self, text="مبيعات اليوم", command=self.show_daily_sales_report)
        self.daily_sales_button.pack(pady=5)

        # زر مبيعات الشهر
        self.monthly_sales_button = ctk.CTkButton(self, text="مبيعات الشهر", command=self.show_monthly_sales_report)
        self.monthly_sales_button.pack(pady=5)

        # زر مبيعات عنصر محدد
        self.item_sales_button = ctk.CTkButton(self, text="مبيعات عنصر محدد", command=self.show_item_sales_report)
        self.item_sales_button.pack(pady=5)
        
        # زر مبيعات خلال مدة
        self.date_range_sales_button = ctk.CTkButton(self, text="مبيعات خلال مدة", command=self.show_date_range_sales_report)
        self.date_range_sales_button.pack(pady=5)
    
    def show_daily_sales_report(self):
        today = datetime.now().strftime("%Y-%m-%d")
        sales_data = get_daily_sales_invoices(today)
        headers = ("رقم الفاتورة", "تاريخ الفاتورة", "اسم العميل", "المبلغ الإجمالي")
        self.load_data_callback(headers, sales_data, with_invoice=True)

    def show_monthly_sales_report(self):
        today = datetime.now()
        first_day_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        last_day_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        last_day_of_month = last_day_of_month.strftime("%Y-%m-%d")
        sales_data = get_sales_in_range(first_day_of_month, last_day_of_month)
        headers = ("المنتج", "المبلغ")
        self.load_data_callback(headers, sales_data)

    def show_item_sales_report(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم المنتج:", title="بحث عن مبيعات منتج")
        item_name = dialog.get_input()
        if item_name:
            sales_data = get_sales_for_item(item_name)
            headers = ("التاريخ", "المبلغ")
            self.load_data_callback(headers, sales_data)

    def show_date_range_sales_report(self):
        dialog = DateRangeDialog(self, title="تحديد نطاق زمني")
        if dialog.result:
            start_date, end_date = dialog.result
            sales_data = get_sales_in_range(start_date, end_date)
            headers = ("المنتج", "المبلغ", "التاريخ")
            self.load_data_callback(headers, sales_data)

class PurchasesReportsFrame(ReportFrameBase):
    def __init__(self, master, load_data_callback, show_invoice_callback, **kwargs):
        super().__init__(master, load_data_callback, **kwargs)
        self.show_invoice_callback = show_invoice_callback
        
        purchases_report_label = ctk.CTkLabel(self, text="تقارير المشتريات", font=ctk.CTkFont(size=18, weight="bold"))
        purchases_report_label.pack(pady=10)
        
        # زر مشتريات من الموردين
        self.supplier_purchases_button = ctk.CTkButton(self, text="مشتريات من الموردين", command=self.show_all_suppliers_purchases_report)
        self.supplier_purchases_button.pack(pady=5)
        
        # زر عرض مشتريات مورد معين
        self.single_supplier_purchases_button = ctk.CTkButton(self, text="مشتريات مورد معين", command=self.show_single_supplier_purchases_report)
        self.single_supplier_purchases_button.pack(pady=5)
        
        # زر عرض جميع مبالغ الفواتير
        self.all_invoices_amounts_button = ctk.CTkButton(self, text="جميع مبالغ الفواتير", command=self.show_all_invoices_amounts_report)
        self.all_invoices_amounts_button.pack(pady=5)
        
        # زر عرض جميع فواتير الشراء لمورد محدد
        self.all_invoices_supplier_button = ctk.CTkButton(self, text="فواتير شراء مورد معين", command=self.show_all_invoices_for_supplier_report)
        self.all_invoices_supplier_button.pack(pady=5)
    
    def show_all_suppliers_purchases_report(self):
        purchases_data = get_all_suppliers_purchases()
        headers = ("المورد", "المبلغ")
        self.load_data_callback(headers, purchases_data)
        
    def show_single_supplier_purchases_report(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم المورد:", title="بحث عن مشتريات مورد")
        supplier_name = dialog.get_input()
        if supplier_name:
            purchases_data = get_purchases_for_supplier(supplier_name)
            headers = ("رقم الفاتورة", "التاريخ", "المبلغ")
            self.load_data_callback(headers, purchases_data, with_invoice=True) # هنا مع الفواتير
            
    def show_all_invoices_amounts_report(self):
        amounts_data = get_all_invoices_amounts()
        headers = ("المبلغ",)
        self.load_data_callback(headers, amounts_data)
    
    def show_all_invoices_for_supplier_report(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم المورد:", title="فواتير شراء مورد محدد")
        supplier_name = dialog.get_input()
        if supplier_name:
            invoices_data = get_invoices_for_supplier(supplier_name)
            headers = ("رقم الفاتورة", "التاريخ", "المبلغ")
            self.load_data_callback(headers, invoices_data, with_invoice=True)

class CustomersReportsFrame(ReportFrameBase):
    def __init__(self, master, load_data_callback, **kwargs):
        super().__init__(master, load_data_callback, **kwargs)

        customers_report_label = ctk.CTkLabel(self, text="تقارير الزبائن", font=ctk.CTkFont(size=18, weight="bold"))
        customers_report_label.pack(pady=10)

        # زر تقارير مبيعات زبون معين
        self.customer_sales_button = ctk.CTkButton(self, text="مبيعات زبون معين", command=self.show_customer_sales_report)
        self.customer_sales_button.pack(pady=5)

        # زر تقارير جميع المبالغ المستحقة
        self.all_customers_dues_button = ctk.CTkButton(self, text="جميع المبالغ المستحقة", command=self.show_all_customers_dues_report)
        self.all_customers_dues_button.pack(pady=5)
            
    def show_customer_sales_report(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم الزبون:", title="بحث عن مبيعات زبون")
        customer_name = dialog.get_input()
        if customer_name:
            sales_data = get_customer_sales(customer_name)
            headers = ("المشتريات", "المدفوع")
            self.load_data_callback(headers, sales_data)

    def show_all_customers_dues_report(self):
        dues_data = get_all_customers_dues()
        headers = ("الزبون", "المبلغ المستحق", "المبلغ المدفوع")
        self.load_data_callback(headers, dues_data)
        dialog = CustomerDuesDialog(dues_data, self)
        dialog.grab_set()

class CustomerDuesDialog(ctk.CTkToplevel):
    def __init__(self, dues_data, parent=None):
        super().__init__(parent)
        self.title("جميع المبالغ المستحقة على الزبائن")
        self.geometry("400x300")
        self.dues_data = dues_data
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        self.table = ttk.Treeview(layout, columns=("الزبون", "المبلغ المستحق", "المبلغ المدفوع"), show="headings")
        self.table.heading("الزبون", text="الزبون")
        self.table.heading("المبلغ المستحق", text="المبلغ المستحق")
        self.table.heading("المبلغ المدفوع", text="المبلغ المدفوع")
        self.table.pack(fill="both", expand=True)

        self.load_dues_data()
        self.table.bind("<Double-1>", self.on_customer_double_click)

    def load_dues_data(self):
        for due in self.dues_data:
            self.table.insert("", "end", values=due)

    def on_customer_double_click(self, event):
        selected_item = self.table.selection()
        if selected_item:
            customer_name = self.table.item(selected_item)['values'][0]
            dialog = CustomerInvoicesDialog(customer_name, self)
            dialog.grab_set()

class CustomerInvoicesDialog(ctk.CTkToplevel):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        self.title(f"Invoices for {customer_name}")
        self.geometry("600x400")
        self.customer_name = customer_name
        self.initUI()

    def initUI(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        self.table = ttk.Treeview(layout, columns=("رقم الفاتورة", "التاريخ", "السعر"), show="headings")
        self.table.heading("رقم الفاتورة", text="رقم الفاتورة")
        self.table.heading("التاريخ", text="التاريخ")
        self.table.heading("السعر", text="السعر")
        self.table.pack(fill="both", expand=True)

        self.load_invoices_data()

    def load_invoices_data(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, total_amount FROM sales WHERE customer_name = ?', (self.customer_name,))
        invoices = cursor.fetchall()

        # Fetch credit invoices for customer "Ahmed"
        cursor.execute('SELECT id, date, total_amount FROM sales WHERE customer_name = "Ahmed"')
        credit_invoices = cursor.fetchall()
        conn.close()

        for invoice in invoices + credit_invoices:
            self.table.insert("", "end", values=invoice)

class SuppliersReportsFrame(ReportFrameBase):
    def __init__(self, master, load_data_callback, **kwargs):
        super().__init__(master, load_data_callback, **kwargs)

        suppliers_report_label = ctk.CTkLabel(self, text="تقارير الموردين", font=ctk.CTkFont(size=18, weight="bold"))
        suppliers_report_label.pack(pady=10)

        # زر عرض مشتريات كل مورد مع المستحقات
        self.supplier_purchases_dues_button = ctk.CTkButton(self, text="مشتريات ومستحقات المورد", command=self.show_supplier_purchases_dues)
        self.supplier_purchases_dues_button.pack(pady=5)

    def show_supplier_purchases_dues(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم المورد:", title="بحث عن مشتريات ومستحقات مورد")
        supplier_name = dialog.get_input()
        if supplier_name:
            supplier_data = get_supplier_purchases_dues(supplier_name)
            headers = ("المشتريات", "المدفوع")
            self.load_data_callback(headers, supplier_data)

class ChecksReportsFrame(ReportFrameBase):
    def __init__(self, master, load_data_callback, **kwargs):
        super().__init__(master, load_data_callback, **kwargs)

        checks_report_label = ctk.CTkLabel(self, text="تقارير الشيكات", font=ctk.CTkFont(size=18, weight="bold"))
        checks_report_label.pack(pady=10)
        
        # زر عرض جميع الشيكات الصادرة
        self.outgoing_checks_button = ctk.CTkButton(self, text="الشيكات الصادرة", command=self.show_outgoing_checks)
        self.outgoing_checks_button.pack(pady=5)
        
        # زر عرض جميع الشيكات الواردة
        self.incoming_checks_button = ctk.CTkButton(self, text="الشيكات الواردة", command=self.show_incoming_checks)
        self.incoming_checks_button.pack(pady=5)

    def show_outgoing_checks(self):
       checks_data = get_outgoing_checks()
       headers = ("رقم الشيك", "التاريخ", "المبلغ", "المستفيد")
       self.load_data_callback(headers, checks_data)
       
    def show_incoming_checks(self):
        checks_data = get_incoming_checks()
        headers = ("رقم الشيك", "التاريخ", "المبلغ", "المصدر")
        self.load_data_callback(headers, checks_data)
        
class DateRangeDialog(ctk.CTkToplevel):
    def __init__(self, master, title="تحديد نطاق زمني", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("300x200")
        self.result = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.start_date_label = ctk.CTkLabel(self, text="تاريخ البداية:")
        self.start_date_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.start_date_entry = ctk.CTkEntry(self)
        self.start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.start_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        self.end_date_label = ctk.CTkLabel(self, text="تاريخ النهاية:")
        self.end_date_label.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.end_date_entry = ctk.CTkEntry(self)
        self.end_date_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.end_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        self.ok_button = ctk.CTkButton(self, text="موافق", command=self.on_ok)
        self.ok_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.cancel_button = ctk.CTkButton(self, text="إلغاء", command=self.on_cancel)
        self.cancel_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.grab_set() #تفعيل النافذة فوق النوافذ الاخرى
        self.focus_force()
        self.wait_window(self)
    
    def on_ok(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            self.result = (start_date, end_date)
            self.destroy()
        except ValueError:
            messagebox.showerror("خطأ", "صيغة التاريخ غير صحيحة يجب ان تكون YYYY-MM-DD")
    
    def on_cancel(self):
        self.destroy()

# --- وظائف قاعدة البيانات (SQLite) ---
def get_daily_sales(date):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_name, total_amount FROM sales WHERE date = ?', (date,))
    sales = cursor.fetchall()
    conn.close()
    return sales
    
def get_sales_in_range(start_date, end_date):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_name, total_amount, date FROM sales WHERE date BETWEEN ? AND ?', (start_date, end_date))
    sales = cursor.fetchall()
    conn.close()
    return sales

def get_sales_for_item(item_name):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, total_amount FROM sales WHERE item_name = ?', (item_name,))
    sales = cursor.fetchall()
    conn.close()
    return sales

def get_all_suppliers_purchases():
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT supplier_name, total_amount FROM purchases')
    purchases = cursor.fetchall()
    conn.close()
    return purchases

def get_purchases_for_supplier(supplier_name):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, total_amount FROM purchases WHERE supplier_name = ?', (supplier_name,)) #جلب رقم الفاتورة
    purchases = cursor.fetchall()
    conn.close()
    return purchases
    
def get_all_invoices_amounts():
     conn = sqlite3.connect('sqlite3.db')
     cursor = conn.cursor()
     cursor.execute('SELECT total_amount FROM purchases')
     amounts = cursor.fetchall()
     conn.close()
     return amounts
    
def get_invoices_for_supplier(supplier_name):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, total_amount FROM purchases WHERE supplier_name = ?', (supplier_name,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_customer_sales(customer_name):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount_bought, amount_paid FROM customer_transactions WHERE customer_name = ?', (customer_name,))
    sales = cursor.fetchall()
    conn.close()
    return sales
    
def get_all_customers_dues():
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.name, c.outstanding_balance, 
               IFNULL(SUM(t.amount_paid), 0) AS amount_paid
        FROM customers c
        LEFT JOIN customer_transactions t ON c.name = t.customer_name
        GROUP BY c.name, c.outstanding_balance
    ''')
    dues = cursor.fetchall()
    conn.close()
    return dues
    
def get_supplier_purchases_dues(supplier_name):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount_purchased, amount_paid FROM supplier_transactions WHERE supplier_name = ?', (supplier_name,))
    supplier_data = cursor.fetchall()
    conn.close()
    return supplier_data

def get_outgoing_checks():
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, amount, beneficiary FROM outgoing_checks')
    checks = cursor.fetchall()
    conn.close()
    return checks
    
def get_incoming_checks():
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, amount, source FROM incoming_checks')
    checks = cursor.fetchall()
    conn.close()
    return checks
    
def get_sales_invoice_details(invoice_id):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, customer_name, item_name, quantity, unit_price, total_amount FROM sales WHERE id = ?', (invoice_id,))
    invoice = cursor.fetchone()
    conn.close()
    return invoice
    
def get_daily_sales_invoices(date):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, customer_name, total_amount FROM sales WHERE date = ?', (date,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices
    
def get_sales_invoice_details_for_table(invoice_id):
    conn = sqlite3.connect('sqlite3.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_name, quantity, unit_price, total_amount FROM sales_items WHERE sales_id = ?', (invoice_id,))
    details = cursor.fetchall()
    conn.close()
    return details

def get_purchases_invoice_details(invoice_id):
     conn = sqlite3.connect('sqlite3.db')
     cursor = conn.cursor()
     cursor.execute('SELECT id, date, supplier_name, item_name, quantity, unit_price, total_amount FROM purchases WHERE id = ?', (invoice_id,))
     invoice = cursor.fetchone()
     conn.close()
     return invoice

if __name__ == '__main__':
    root = ctk.CTk()
    root.geometry("1200x700")
    reports_module = ReportsModule(root)
    reports_module.get_widget().pack(fill="both", expand=True)
    root.mainloop()