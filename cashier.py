from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QTableView, QAbstractItemView, QHBoxLayout, QSizePolicy, QComboBox, QDialog, QRadioButton, QButtonGroup, QFormLayout, QMessageBox, QCheckBox, QPushButton, QCompleter, QGroupBox, QGridLayout, QListView, QInputDialog, QDialogButtonBox, QScrollArea
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QIcon, QDoubleValidator
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer
import sqlite3

class CashierModule(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.item_code_group = QGroupBox("Item Code")
        self.item_code_layout = QVBoxLayout()
        self.item_code_group.setLayout(self.item_code_layout)
        self.layout.addWidget(self.item_code_group)
        
        self.item_code_input = QLineEdit()
        self.item_code_input.setPlaceholderText("Enter item code")
        self.item_code_layout.addWidget(self.item_code_input)
        
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.add_item)
        
        self.item_code_input.textChanged.connect(self.restart_typing_timer)  # Restart timer when text changes
        
        # Sample item names for autocomplete
        self.item_names = ["Item1", "Item2", "Item3", "Item4", "Item5"]
        self.completer = QCompleter(self.item_names)
        self.item_code_input.setCompleter(self.completer)
        
        self.main_layout = QHBoxLayout()
        self.layout.addLayout(self.main_layout)
        
        self.left_group = QGroupBox("Invoice Items")
        self.left_layout = QVBoxLayout()
        self.left_group.setLayout(self.left_layout)
        self.left_group.setMaximumWidth(650)  # Reduce maximum width by 20%
        self.main_layout.addWidget(self.left_group)
        
        self.middle_group = QGroupBox("Categories")
        self.middle_layout = QVBoxLayout()
        self.middle_scroll_area = QScrollArea()
        self.middle_scroll_area.setWidgetResizable(True)
        self.middle_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide vertical scrollbar
        self.middle_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide horizontal scrollbar
        self.middle_widget = QWidget()
        self.middle_widget.setLayout(self.middle_layout)
        self.middle_scroll_area.setWidget(self.middle_widget)
        self.middle_scroll_area.setFixedWidth(125)  # Set fixed width for the scroll area to match the button width
        self.main_layout.addWidget(self.middle_scroll_area)
        
        self.right_group = QGroupBox("Inventory Items")
        self.right_layout = QVBoxLayout()
        self.right_group.setLayout(self.right_layout)
        self.main_layout.addWidget(self.right_group)
        
        self.items_model = QStandardItemModel(0, 3)  # Reduced column count
        self.items_model.setHorizontalHeaderLabels(["Item Name", "Quantity", "Price"])
        
        self.items_table = QTableView()
        self.items_table.setModel(self.items_model)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.items_table.setColumnWidth(0, 200)  # Reduce the width of the "Item Name" column to half
        self.left_layout.addWidget(self.items_table)
        
        self.total_group = QGroupBox("Total")
        self.total_layout = QVBoxLayout()
        self.total_group.setLayout(self.total_layout)
        self.layout.addWidget(self.total_group)
        
        self.total_label = QLabel("Total: $0.00")
        self.total_layout.addWidget(self.total_label)
        
        self.controls_group = QGroupBox("Controls")
        self.controls_layout = QHBoxLayout()
        self.controls_group.setLayout(self.controls_layout)
        self.layout.addWidget(self.controls_group)
        
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("Enter discount amount")
        self.discount_input.setFixedWidth(150)
        self.controls_layout.addWidget(self.discount_input)
        
        self.modify_quantity_button = QPushButton("Modify Quantity")
        self.modify_quantity_button.setFixedWidth(150)
        self.controls_layout.addWidget(self.modify_quantity_button)
        self.modify_quantity_button.clicked.connect(self.modify_quantity)
        
        self.suspend_invoice_button = QPushButton("Suspend Invoice")
        self.suspend_invoice_button.setFixedWidth(150)
        self.controls_layout.addWidget(self.suspend_invoice_button)
        
        self.suspended_invoices_combo = QComboBox()
        self.suspended_invoices_combo.setFixedWidth(150)
        self.controls_layout.addWidget(self.suspended_invoices_combo)
        
        self.new_invoice_button = QPushButton("New Invoice")
        self.new_invoice_button.setFixedWidth(150)
        self.controls_layout.addWidget(self.new_invoice_button)
        
        self.checkout_button = QPushButton("Checkout")
        self.layout.addWidget(self.checkout_button)
        
        self.checkout_button.clicked.connect(self.open_payment_window)
        self.suspend_invoice_button.clicked.connect(self.suspend_invoice)
        self.suspended_invoices_combo.currentIndexChanged.connect(self.load_suspended_invoice)
        self.new_invoice_button.clicked.connect(self.new_invoice)
        self.discount_input.textChanged.connect(self.update_total)  # Update total when discount changes
        
        self.items_table.doubleClicked.connect(self.on_row_click)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Prevent editing
        
        self.items_table.installEventFilter(self)  # Install event filter to capture delete key
        
        self.suspended_invoices = {}
        self.create_items_table()  # Ensure the items table exists
        self.load_inventory_items()
        self.load_categories()  # Load categories into the middle section
        self.create_invoices_table()  # Ensure the invoices table exists

    def restart_typing_timer(self):
        text = self.item_code_input.text()
        if text.isdigit():
            self.typing_timer.start(1000)  # Restart the timer with a 1-second delay for barcode search
        else:
            self.typing_timer.stop()  # Stop the timer for autocomplete search
            self.search_items(text)  # Call search_items for autocomplete

    def search_items(self, text):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, sale_price, contains_weight FROM items WHERE name LIKE ?', ('%' + text + '%',))
        items = cursor.fetchall()
        conn.close()

        self.item_model.clear()
        for item in items:
            item_name, price, contains_weight = item
            display_text = f"{item_name} - ${price:.2f}"

            # Create a standard item
            list_item = QStandardItem(display_text)
            list_item.setData(item_name, Qt.UserRole)  # Store the name
            list_item.setData(price, Qt.UserRole + 1)  # Store the price
            list_item.setData(contains_weight, Qt.UserRole + 2)  # Store contains_weight

            # Set formatting for the item
            list_item.setFont(QFont("Arial", 12))
            list_item.setTextAlignment(Qt.AlignCenter)
            list_item.setSizeHint(QSize(100, 60))  # Adjust size as needed
            list_item.setEditable(False)  # Prevent editing

            # Add the item to the model
            self.item_model.appendRow(list_item)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Delete:
            if source is self.items_table:
                selected_index = self.items_table.currentIndex()
                if selected_index.isValid():
                    self.items_model.removeRow(selected_index.row())
                    self.update_total()
        return super().eventFilter(source, event)

    def add_item(self):
        text = self.item_code_input.text()
        if text.isdigit():
            self.search_by_barcode(text)
        else:
            # Handle autocomplete search
            pass

    def search_by_barcode(self, barcode):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, sale_price FROM items WHERE barcode = ?', (barcode,))
        item = cursor.fetchone()
        conn.close()
        
        if item:
            item_name, price = item
            self.add_inventory_item_to_invoice(item_name, f"${price:.2f}")
        else:
            QMessageBox.warning(self, "Invalid Code", "Item not found in the inventory.")
        
        self.item_code_input.clear()  # Clear the input field after processing

    def add_inventory_item_to_invoice(self, item_name, price, contains_weight=False):
        if contains_weight:
            dialog = QDialog(self)
            dialog.setWindowTitle("Enter Weight or Amount")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout(dialog)
            
            input_type_group = QGroupBox("Input Type")
            input_type_layout = QHBoxLayout()
            input_type_group.setLayout(input_type_layout)
            layout.addWidget(input_type_group)
            
            weight_button = QPushButton("Weight (kg)")
            amount_button = QPushButton("Amount ($)")
            input_type_layout.addWidget(weight_button)
            input_type_layout.addWidget(amount_button)
            
            input_field = QLineEdit()
            input_field.setPlaceholderText("Enter value")
            layout.addWidget(input_field)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addWidget(button_box)
            
            def on_weight_button_clicked():
                weight_button.setStyleSheet("background-color: lightblue;")
                amount_button.setStyleSheet("")
                input_field.setPlaceholderText("Enter weight (kg)")
                input_field.setFocus()

            def on_amount_button_clicked():
                amount_button.setStyleSheet("background-color: lightblue;")
                weight_button.setStyleSheet("")
                input_field.setPlaceholderText("Enter amount ($)")
                input_field.setFocus()

            weight_button.clicked.connect(on_weight_button_clicked)
            amount_button.clicked.connect(on_amount_button_clicked)
            
            def on_ok():
                input_text = input_field.text()
                if weight_button.styleSheet() == "background-color: lightblue;":
                    weight = float(input_text)
                    final_price = float(price.replace("$", "")) * weight
                elif amount_button.styleSheet() == "background-color: lightblue;":
                    amount = float(input_text)
                    weight = amount / float(price.replace("$", ""))
                    final_price = amount
                else:
                    QMessageBox.warning(dialog, "Input Error", "Please select either weight or amount.")
                    return
                dialog.accept()
                self.add_item_to_invoice(item_name, weight, final_price)
            
            button_box.accepted.connect(on_ok)
            button_box.rejected.connect(dialog.reject)
            
            if not dialog.exec_():
                return

        else:
            self.add_item_to_invoice(item_name, 1, float(price.replace("$", "")))

    def add_item_to_invoice(self, item_name, quantity, price):
        # Check if the item already exists in the table
        for row in range(self.items_model.rowCount()):
            if self.items_model.item(row, 0).text() == item_name:
                # Update the quantity and price
                quantity_item = self.items_model.item(row, 1)
                quantity = float(quantity_item.text()) + quantity  # تعديل لتحويل الكمية إلى عدد عشري
                quantity_item.setText(str(quantity))
                
                price_item = self.items_model.item(row, 2)
                price_value = float(price_item.text().replace("$", "")) + price
                price_item.setText(f"${price_value:.2f}")
                
                self.update_total()
                return
        
        # If the item does not exist, add a new row
        row_position = self.items_model.rowCount()
        self.items_model.insertRow(row_position)
        self.items_model.setItem(row_position, 0, QStandardItem(item_name))
        self.items_model.setItem(row_position, 1, QStandardItem(str(quantity)))
        self.items_model.setItem(row_position, 2, QStandardItem(f"${price:.2f}"))
        self.update_total()

    def modify_quantity(self):
        selected_index = self.items_table.currentIndex()
        if not selected_index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select an item to modify its quantity.")
            return

        item_name = self.items_model.item(selected_index.row(), 0).text()
        quantity, ok = QInputDialog.getInt(self, "Modify Quantity", f"Enter new quantity for {item_name}:", min=1)
        
        if ok:
            self.items_model.setItem(selected_index.row(), 1, QStandardItem(str(quantity)))
            self.update_total()

    def update_total(self):
        total = 0.0
        for row in range(self.items_model.rowCount()):
            price_item = self.items_model.item(row, 2)
            quantity_item = self.items_model.item(row, 1)
            if price_item and quantity_item:
                price = float(price_item.text().replace("$", ""))
                quantity = float(quantity_item.text())  # تعديل لتحويل الكمية إلى عدد عشري
                total += price * quantity
        discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
        total -= discount
        self.total_label.setText(f"Total: ${total:.2f}")

    def checkout(self, payment_method, customer_name=None, paid_amount=None):
        total_amount = self.calculate_total_amount()
        if paid_amount is None:
            paid_amount = total_amount
        discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0

        # Save the invoice to the database
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (date, total_amount, discount, paid_amount, payment_method, customer_name)
            VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?)
        ''', (total_amount, discount, paid_amount, payment_method, customer_name))
        invoice_id = cursor.lastrowid

        for row in range(self.items_model.rowCount()):
            item_name = self.items_model.item(row, 0).text()
            quantity = float(self.items_model.item(row, 1).text())
            price = float(self.items_model.item(row, 2).text().replace("$", ""))
            cursor.execute('''
                INSERT INTO invoice_items (invoice_id, item_name, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (invoice_id, item_name, quantity, price))

        conn.commit()
        conn.close()

        print(f"Checkout complete with payment method: {payment_method}")
        if payment_method == "Credit" and customer_name:
            print(f"Customer: {customer_name}")
            conn = sqlite3.connect('sqlite3.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (customer, amount)
                VALUES (?, ?)
            ''', (customer_name, -total_amount))
            cursor.execute('''
                UPDATE customers
                SET outstanding_balance = outstanding_balance + ?
                WHERE name = ?
            ''', (total_amount - paid_amount, customer_name))
            conn.commit()
            conn.close()

        self.items_model.removeRows(0, self.items_model.rowCount())
        self.discount_input.clear()  # Clear the discount input
        self.update_total()

    def complete_sale(self):
        selected_customer = self.customer_combo.get()
        if not selected_customer:
            self.error_label.configure(text="Error: Please select a customer")
            return

        total_amount = self.calculate_total_amount()
        if total_amount <= 0:
            self.error_label.configure(text="Error: Total amount must be greater than zero")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (customer, amount)
            VALUES (?, ?)
        ''', (selected_customer, -total_amount))
        cursor.execute('''
            UPDATE customers
            SET outstanding_balance = outstanding_balance + ?
            WHERE name = ?
        ''', (-total_amount, selected_customer))
        conn.commit()
        conn.close()

        print(f"Sale completed for customer: {selected_customer} with amount: {total_amount}")
        self.destroy()

    def calculate_total_amount(self):
        total = 0.0
        for row in range(self.items_model.rowCount()):
            price_item = self.items_model.item(row, 2)
            quantity_item = self.items_model.item(row, 1)
            if price_item and quantity_item:
                price = float(price_item.text().replace("$", ""))
                quantity = float(quantity_item.text())
                total += price * quantity
        discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
        total -= discount
        return total

    def suspend_invoice(self):
        invoice_id = f"Invoice {len(self.suspended_invoices) + 1}"
        self.suspended_invoices[invoice_id] = []
        for row in range(self.items_model.rowCount()):
            item_name = self.items_model.item(row, 0).text()
            quantity = self.items_model.item(row, 1).text()
            price = self.items_model.item(row, 2).text()
            self.suspended_invoices[invoice_id].append((item_name, quantity, price))
        self.suspended_invoices_combo.addItem(invoice_id)
        self.items_model.removeRows(0, self.items_model.rowCount())
        self.discount_input.clear()  # Clear the discount input
        self.update_total()

    def load_suspended_invoice(self):
        invoice_id = self.suspended_invoices_combo.currentText()
        if invoice_id in self.suspended_invoices:
            self.items_model.removeRows(0, self.items_model.rowCount())
            for item in self.suspended_invoices[invoice_id]:
                row_position = self.items_model.rowCount()
                self.items_model.insertRow(row_position)
                self.items_model.setItem(row_position, 0, QStandardItem(item[0]))
                self.items_model.setItem(row_position, 1, QStandardItem(item[1]))
                self.items_model.setItem(row_position, 2, QStandardItem(item[2]))
            self.discount_input.clear()  # Clear the discount input
            self.update_total()

    def new_invoice(self):
        self.items_model.removeRows(0, self.items_model.rowCount())
        self.discount_input.clear()  # Clear the discount input
        self.update_total()

    def on_row_click(self, index):
        row = index.row()
        print(f"Row {row} clicked")

    def open_payment_window(self):
        if self.items_model.rowCount() == 0:
            QMessageBox.warning(self, "No Items", "Please add items to the invoice before proceeding to payment.")
            return
        self.payment_window = PaymentWindow(self, self.total_label.text(), self.discount_input.text())
        self.payment_window.exec_()

    def load_inventory_items(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, sale_price, contains_weight FROM items')
        inventory_items = cursor.fetchall()
        conn.close()

        self.item_view = QListView()
        self.item_model = QStandardItemModel(self.item_view)

        for item in inventory_items:
            item_name, price, contains_weight = item
            display_text = f"{item_name} - ${price:.2f}"

            # Create a standard item
            list_item = QStandardItem(display_text)
            list_item.setData(item_name, Qt.UserRole)  # Store the name
            list_item.setData(price, Qt.UserRole + 1)  # Store the price
            list_item.setData(contains_weight, Qt.UserRole + 2)  # Store contains_weight

            # Set formatting for the item
            list_item.setFont(QFont("Arial", 12))
            list_item.setTextAlignment(Qt.AlignCenter)
            list_item.setSizeHint(QSize(100, 60))  # Adjust size as needed
            list_item.setEditable(False)  # Prevent editing

            # Add the item to the model
            self.item_model.appendRow(list_item)

        # Set the model for the list view
        self.item_view.setModel(self.item_model)

        # Connect the item clicked event
        self.item_view.clicked.connect(self.on_item_clicked)

        # Add the list view to the right layout
        self.right_layout.addWidget(self.item_view)

    def on_item_clicked(self, index):
        # Retrieve data from the selected item
        item_name = index.data(Qt.UserRole)
        price = index.data(Qt.UserRole + 1)
        contains_weight = index.data(Qt.UserRole + 2)  # Assuming contains_weight is stored in Qt.UserRole + 2
        self.add_inventory_item_to_invoice(item_name, f"${price:.2f}", contains_weight)

    def create_items_table(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sale_price REAL NOT NULL,
                purchase_price REAL,
                barcode TEXT UNIQUE NOT NULL,
                note TEXT,
                contains_weight BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def clear_items_table(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items')
        conn.commit()
        conn.close()

    def load_categories(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories WHERE visible = 1')
        categories = cursor.fetchall()
        conn.close()

        for category in categories:
            category_name = category[0]
            category_button = QPushButton(category_name)
            category_button.setFixedSize(100, 100)
            category_button.setStyleSheet("border: 1px solid black; padding: 10px; background-color: lightgray;")
            category_button.clicked.connect(lambda _, name=category_name: self.show_items_in_category(name))
            self.middle_layout.addWidget(category_button)
            self.middle_layout.addSpacing(10)  # Add spacing between buttons

    def show_items_in_category(self, category_name):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, sale_price, contains_weight FROM items WHERE category = ?', (category_name,))
        items = cursor.fetchall()
        conn.close()

        self.item_model.clear()
        for item in items:
            item_name, price, contains_weight = item
            display_text = f"{item_name} - ${price:.2f}"

            # Create a standard item
            list_item = QStandardItem(display_text)
            list_item.setData(item_name, Qt.UserRole)  # Store the name
            list_item.setData(price, Qt.UserRole + 1)  # Store the price
            list_item.setData(contains_weight, Qt.UserRole + 2)  # Store contains_weight

            # Set formatting for the item
            list_item.setFont(QFont("Arial", 12))
            list_item.setTextAlignment(Qt.AlignCenter)
            list_item.setSizeHint(QSize(100, 60))  # Adjust size as needed
            list_item.setEditable(False)  # Prevent editing

            # Add the item to the model
            self.item_model.appendRow(list_item)

    def create_invoices_table(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                discount REAL,
                paid_amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                customer_name TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        conn.commit()
        conn.close()

class PaymentWindow(QDialog):
    def __init__(self, parent, total_amount, discount_amount):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Select Payment Method")
        self.setGeometry(100, 100, 300, 300)  # Increased height to accommodate remaining amount
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.payment_method_group = QButtonGroup(self)
        self.cash_radio = QRadioButton("Cash")
        self.credit_radio = QRadioButton("Credit")
        self.payment_method_group.addButton(self.cash_radio)
        self.payment_method_group.addButton(self.credit_radio)
        
        self.layout.addWidget(self.cash_radio)
        self.layout.addWidget(self.credit_radio)
        
        self.total_label = QLabel(f"Total: {total_amount}")
        self.layout.addWidget(self.total_label)
        
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("Enter discount amount")
        self.discount_input.setText(discount_amount)
        self.discount_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))  # Ensure only numeric values
        self.layout.addWidget(self.discount_input)
        
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText("Enter paid amount")
        self.paid_amount_input.setText(str(total_amount))  # Default to total amount
        self.paid_amount_input.setValidator(QDoubleValidator(0.0, 999999.99, 2))  # Ensure only numeric values
        self.paid_amount_input.installEventFilter(self)  # Install event filter to handle focus event
        self.layout.addWidget(self.paid_amount_input)
        
        self.remaining_amount_label = QLabel("Remaining: $0.00")
        self.layout.addWidget(self.remaining_amount_label)
        
        self.customer_combo = QComboBox(self)
        self.layout.addWidget(self.customer_combo)
        self.load_customers()
        self.customer_combo.setVisible(False)
        
        self.print_invoice_checkbox = QCheckBox("Print Invoice")
        self.layout.addWidget(self.print_invoice_checkbox)
        
        self.confirm_button = QPushButton("Confirm")
        self.layout.addWidget(self.confirm_button)
        
        self.cash_radio.setChecked(True)  # Set "Cash" as the default payment method
        
        self.credit_radio.toggled.connect(self.toggle_customer_input)
        self.confirm_button.clicked.connect(self.confirm_payment)
        self.discount_input.textChanged.connect(self.update_total_label)  # Update total when discount changes
        self.paid_amount_input.textChanged.connect(self.update_total_label)  # Update total when paid amount changes

    def eventFilter(self, source, event):
        if source is self.paid_amount_input and event.type() == QEvent.FocusIn:
            QTimer.singleShot(0, self.paid_amount_input.selectAll)
        return super().eventFilter(source, event)

    def toggle_customer_input(self):
        self.customer_combo.setVisible(self.credit_radio.isChecked())

    def confirm_payment(self):
        payment_method = "Cash" if self.cash_radio.isChecked() else "Credit"
        total_text = self.total_label.text().replace("Total: $", "")
        try:
            total = float(total_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Total", "Total amount is not a valid number.")
            return
        discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
        paid_amount = float(self.paid_amount_input.text()) if self.paid_amount_input.text() else total
        if discount > total:
            QMessageBox.warning(self, "Invalid Discount", "Discount amount cannot be greater than the total invoice amount.")
            return
        if paid_amount < total:
            payment_method = "Credit"
            self.credit_radio.setChecked(True)
        else:
            self.cash_radio.setChecked(True)
            paid_amount = total  # Ignore any excess amount paid
        if total < 0 and payment_method != "Credit":
            QMessageBox.warning(self, "Invalid Payment", "Total amount cannot be less than zero unless payment method is Credit.")
            return
        customer_name = self.customer_combo.currentText() if self.credit_radio.isChecked() else None
        self.parent.checkout(payment_method, customer_name, paid_amount)
        if self.print_invoice_checkbox.isChecked():
            self.print_invoice()
        self.close()

    def update_total_label(self):
        total_text = self.parent.total_label.text().replace("Total: $", "")
        try:
            total = float(total_text)
        except ValueError:
            total = 0.0
        discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
        paid_amount_text = self.paid_amount_input.text()
        try:
            paid_amount = float(paid_amount_text) if paid_amount_text else total
        except ValueError:
            paid_amount = total
        total -= discount
        remaining = total - paid_amount
        self.total_label.setText(f"Total: ${total:.2f}")
        self.remaining_amount_label.setText(f"Remaining: ${remaining:.2f}")
        if paid_amount < total:
            self.credit_radio.setChecked(True)
        else:
            self.cash_radio.setChecked(True)

    def print_invoice(self):
        # Code to print the invoice
        print("Invoice printed")

    def load_customers(self):
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM customers')
        customers = cursor.fetchall()
        conn.close()
        self.customer_combo.addItems([customer[0] for customer in customers])

class ReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Return Items")
        self.setGeometry(100, 100, 600, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Customer (Optional)")
        form_layout.addRow("Customer:", self.customer_input)

        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Item")
        form_layout.addRow("Item:", self.item_input)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        form_layout.addRow("Quantity:", self.quantity_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        form_layout.addRow("Price:", self.price_input)

        self.total_amount_label = QLabel("Total Amount: 0")
        form_layout.addRow("Total Amount:", self.total_amount_label)

        self.error_label = QLabel("")
        layout.addWidget(self.error_label)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_return)
        button_layout.addWidget(save_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        button_layout.addWidget(exit_button)

    def save_return(self):
        customer = self.customer_input.text()
        item = self.item_input.text()
        quantity_text = self.quantity_input.text()
        price_text = self.price_input.text()

        if not item or not quantity_text or not price_text:
            self.error_label.setText("Error: Item, Quantity, and Price must be filled")
            return

        try:
            quantity = int(quantity_text)
            price = float(price_text)
            total_amount = quantity * price
        except ValueError:
            self.error_label.setText("Error: Quantity and Price must be valid numbers")
            return

        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO returns (customer, item, quantity, price, total_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer, item, quantity, price, total_amount))
        cursor.execute('''
            UPDATE items
            SET quantity = quantity - ?
            WHERE name = ?
        ''', (quantity, item))
        conn.commit()
        conn.close()

        print("Return invoice saved to the database")
        self.close()
