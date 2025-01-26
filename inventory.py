from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QDialog, QFormLayout, QLineEdit, QLabel, QHBoxLayout, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt
import sqlite3
import customtkinter as ctk

class InventoryModule:
    def __init__(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.textChanged.connect(self.search_items)
        self.layout.addWidget(self.search_input)
        
        self.add_item_button = QPushButton("Add Item")
        self.layout.addWidget(self.add_item_button)
        self.add_item_button.clicked.connect(self.open_add_item_window)
        
        self.items_layout = QGridLayout()
        self.items_layout.setAlignment(Qt.AlignRight)  # Align the grid layout to the right
        self.layout.addLayout(self.items_layout)
        
        self.create_table()
        self.load_items()

    def create_table(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                barcode TEXT,
                purchase_price REAL,
                sale_price REAL,
                note TEXT,
                contains_weight BOOLEAN,
                weight REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                number INTEGER UNIQUE,
                visible BOOLEAN NOT NULL DEFAULT 1
            )
        ''')
        # Ensure columns exist
        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'contains_weight' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN contains_weight BOOLEAN')
        if 'weight' not in columns:
            cursor.execute('ALTER TABLE items ADD COLUMN weight REAL')
        cursor.execute("PRAGMA table_info(categories)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'visible' not in columns:
            cursor.execute('ALTER TABLE categories ADD COLUMN visible BOOLEAN NOT NULL DEFAULT 1')
        conn.commit()
        conn.close()

    def open_add_item_window(self):
        self.add_item_window = AddItemWindow(self)
        self.add_item_window.exec_()

    def add_item(self, item_data):
        # Save item to database
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (name, barcode, purchase_price, sale_price, contains_weight, weight)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (item_data['name'], item_data['barcode'], item_data['purchase_price'], item_data['selling_price'], item_data['contains_weight'], item_data['weight']))
        conn.commit()
        conn.close()
        
        self.load_items()

    def load_items(self):
        # Load items from database
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, barcode, purchase_price, sale_price, note, contains_weight, weight FROM items')
        items = cursor.fetchall()
        conn.close()
        
        # Clear the current layout
        for i in reversed(range(self.items_layout.count())):
            widget = self.items_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        
        # Add items to the layout
        for i, item in enumerate(items):
            item_name, item_barcode, purchase_price, sale_price, note, contains_weight, weight = item
            item_group = QGroupBox()
            item_group.setFixedSize(150, 150)  # Set fixed size for the item group box
            item_layout = QVBoxLayout()
            item_group.setLayout(item_layout)
            item_label = QLabel(f"{item_name}\nWeight: {weight if weight else 'N/A'}")  # Display item name and weight
            item_label.setAlignment(Qt.AlignCenter)
            item_label.setStyleSheet("border: 1px solid black; padding: 10px; background-color: lightgray;")
            item_label.setFixedSize(140, 140)  # Set fixed size for the item label
            item_layout.addWidget(item_label)
            self.items_layout.addWidget(item_group, i // 3, i % 3)

    def search_items(self):
        search_text = self.search_input.text().lower()
        for i in range(self.items_layout.count()):
            item_group = self.items_layout.itemAt(i).widget()
            if item_group:
                item_label = item_group.layout().itemAt(0).widget()
                if search_text in item_label.text().lower():
                    item_group.show()
                else:
                    item_group.hide()

    def get_widget(self):
        return self.widget

class AddItemWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent.widget)
        self.parent = parent
        self.setWindowTitle("Add New Item")
        self.setGeometry(100, 100, 400, 300)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)
        
        self.name_input = QLineEdit()
        self.form_layout.addRow("Name:", self.name_input)
        
        self.barcode_input = QLineEdit()
        self.form_layout.addRow("Barcode:", self.barcode_input)
        
        self.purchase_price_input = QLineEdit()
        self.form_layout.addRow("Purchase Price:", self.purchase_price_input)
        
        self.selling_price_input = QLineEdit()
        self.form_layout.addRow("Selling Price:", self.selling_price_input)

        self.weight_input = QLineEdit()
        self.form_layout.addRow("Weight (if applicable):", self.weight_input)  # إضافة حقل الوزن
        
        self.buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_item)
        self.buttons_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.buttons_layout.addWidget(self.cancel_button)

    def save_item(self):
        item_data = {
            "name": self.name_input.text(),
            "barcode": self.barcode_input.text(),
            "purchase_price": float(self.purchase_price_input.text() or 0),
            "selling_price": float(self.selling_price_input.text() or 0),
            "contains_weight": bool(self.weight_input.text()),  # نصيحة تتعلق بالوزن
            "weight": float(self.weight_input.text() or 0) if self.weight_input.text() else None  # تحويل الوزن إلى معرف إذا لم يكن فارغًا
        }
        self.parent.add_item(item_data)
        self.close()

class POS:
    def __init__(self, root):
        self.root = root
        self.root.title("نقاط البيع (POS)")

        # إعداد الجدول
        self.columns = ('اسم العنصر', 'سعر البيع')
        self.tree = ctk.CTkTreeview(root, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack()

        # إدخال البيانات
        self.label_item = ctk.CTkLabel(root, text="اسم العنصر:")
        self.label_item.pack()
        self.entry_item = ctk.CTkEntry(root)
        self.entry_item.pack()

        self.label_price = ctk.CTkLabel(root, text="سعر البيع:")
        self.label_price.pack()
        self.entry_price = ctk.CTkEntry(root)
        self.entry_price.pack()

        self.button_add = ctk.CTkButton(root, text="إضافة", command=self.add_item)
        self.button_add.pack()

    def add_item(self):
        item_name = self.entry_item.get()
        item_price = self.entry_price.get()

        if item_name and item_price:
            # إضافة إلى الجدول
            self.tree.insert('', 'end', values=(item_name, item_price))
            # تفريغ المدخلات
            self.entry_item.delete(0, ctk.END)
            self.entry_price.delete(0, ctk.END)

if __name__ == "__main__":
    root = ctk.CTk()
    pos_app = POS(root)
    
    # هنا نقوم بدمج تطبيق PyQt5 مع customtkinter
    inventory_module = InventoryModule()
    
    # إعداد نافذة PyQt
    app = inventory_module.get_widget()
    app.setWindowTitle('ERP and Inventory Management')
    app.show()
    
    root.mainloop()