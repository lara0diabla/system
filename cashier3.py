import customtkinter as ctk
import sqlite3
from modules.barcode_reader import read_barcode  # Import the barcode reader

class Cashier3Module(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.primary_color = "#2E86C1"
        self.secondary_color = "#EAF2F8"
        self.button_color = "#2ECC71"
        self.text_color = "#2C3E50"
        self.error_color = "#E74C3C"
        self.search_timer = None #added to handle text search
        self.configure(fg_color=self.secondary_color)
        self.pack(fill="both", expand=True)

        self.total_amount = 0.0

        # Top frame for total amount
        self.top_frame = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
        self.top_frame.pack(side="top", fill="x")
        self.total_label = ctk.CTkLabel(self.top_frame, text=f"{self.total_amount:.2f}", font=("Arial", 30), text_color="white")
        self.total_label.pack(side="right", padx=20, pady=5)
        self.currency_label = ctk.CTkLabel(self.top_frame, text="ILS", font=("Arial", 20), text_color="white")
        self.currency_label.pack(side="right")

        # Left frame for products
        self.left_frame = ctk.CTkFrame(self, fg_color=self.secondary_color)
        self.left_frame.pack(side="left", fill="both", padx=10, pady=10, expand=True)
        self.left_frame.columnconfigure(0, weight=1)
        self.products_label = ctk.CTkLabel(self.left_frame, text="البحث حسب الاسم أو الباركود", font=("Arial", 12, "bold"), text_color=self.text_color)
        self.products_label.grid(row=0, column=0, sticky="ew", pady=10)
        self.search_bar = ctk.CTkEntry(self.left_frame, placeholder_text="بحث...", text_color=self.text_color)
        self.search_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.search_bar.bind("<KeyRelease>", self.on_search_key_release)
        self.search_bar.bind("<Return>", self.on_search_return)  # Bind Enter key for barcode search

        self.categories_frame = ctk.CTkFrame(self.left_frame, fg_color=self.secondary_color)
        self.categories_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.categories_frame.columnconfigure(0, weight=1)
        self.category_buttons = {}

        self.products_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color=self.secondary_color, scrollbar_button_color="#CCCCCC", scrollbar_button_hover_color="#A9A9A9")
        self.products_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.left_frame.rowconfigure(3, weight=1)

        self.product_buttons = []

        # Right frame for cart
        self.right_frame = ctk.CTkFrame(self, fg_color=self.secondary_color, width=300)  # Ensure reduced width
        self.right_frame.pack(side="right", fill="both", padx=10, pady=10, expand=True)
        self.right_frame.columnconfigure(0, weight=1)
        self.cart_labels_frame = ctk.CTkFrame(self.right_frame, fg_color="#CCCCCC", height=30)
        self.cart_labels_frame.grid(row=0, column=0, sticky="ew")
        self.cart_labels = ["#", "الاسم", "الكمية", "السعر", "الخصم", "المجموع"]
        for i, label in enumerate(self.cart_labels):
            label_widget = ctk.CTkLabel(self.cart_labels_frame, text=label, text_color=self.text_color, font=("Arial", 15))  # Increased font size
            label_widget.grid(row=0, column=i, padx=10, sticky="e")  # Adjusted column order
        self.cart_frame = ctk.CTkScrollableFrame(self.right_frame, fg_color="white", scrollbar_button_color="#CCCCCC", scrollbar_button_hover_color="#A9A9A9")
        self.cart_frame.grid(row=1, column=0, sticky="nsew")
        self.right_frame.rowconfigure(1, weight=1)
        self.cart_items = []

        # Bottom frame for buttons
        self.bottom_frame = ctk.CTkFrame(self.right_frame, fg_color=self.secondary_color)  # Moved inside right_frame
        self.bottom_frame.grid(row=2, column=0, pady=10, sticky="ew")  # Changed to grid layout
        self.bottom_buttons = ["دفع", "فتح الدرج", "فاتورة جديدة", "الفواتير المعلقة", "تعليق", "آخر فاتورة", "مرتجع جديد", "الصندوق", "الحاسبة"]
        for i, button in enumerate(self.bottom_buttons):
            btn = ctk.CTkButton(self.bottom_frame, text=button, fg_color="#E67E22", text_color="white", command=lambda b=button: self.handle_bottom_button(b))
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")  # Changed to grid layout
        self.bottom_frame.columnconfigure("all", weight=1)

        # Load categories and display default products
        self.load_categories()
        self.show_products("قهوة")

    def handle_bottom_button(self, button_name):
        print(f"تم الضغط على الزر: {button_name}")

    def load_categories(self):
      try:
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories WHERE visible = 1 LIMIT 7')
        categories = cursor.fetchall()
        conn.close()

        for category in categories:
            category_name = category[0]
            btn = ctk.CTkButton(self.categories_frame, text=category_name, command=lambda c=category_name: self.show_products(c), fg_color=self.primary_color, text_color="white")
            btn.grid(sticky="ew", pady=2)
            self.category_buttons[category_name] = btn
      except Exception as e:
        print(f"Error loading categories:{e}")

    def show_products(self, category):
        for button in self.product_buttons:
            button.destroy()
        self.product_buttons.clear()
        try:
            conn = sqlite3.connect('sqlite3.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, quantity, sale_price, contains_weight FROM items WHERE category = ?', (category,))
            products = cursor.fetchall()
            conn.close()

            for i, (product_name, quantity, price, contains_weight) in enumerate(products):
                button = ctk.CTkButton(self.products_frame, text=f"{product_name} - {quantity} متوفرة", command=lambda name=product_name, p=price, cw=contains_weight: self.add_to_cart(name, p, cw), fg_color=self.secondary_color, border_color="lightgray", border_width=1, text_color=self.text_color, hover_color="#F0F0F0")
                button.grid(row=i // 3, column=i % 3, sticky="ew", padx=5, pady=2)
                self.product_buttons.append(button)

            for col in range(3):
                self.products_frame.columnconfigure(col, weight=1)
        except Exception as e:
            print(f"Error showing products:{e}")

    def add_to_cart(self, product_name, price, contains_weight):
        if contains_weight:
            self.show_weight_amount_dialog(product_name, price)
        else:
            self.add_item_to_cart(product_name, 1, price, 0)

    def show_weight_amount_dialog(self, product_name, price):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enter Weight or Amount")
        dialog.geometry("300x200")

        layout = ctk.CTkFrame(dialog)
        layout.pack(fill="both", expand=True)

        input_type_frame = ctk.CTkFrame(layout)
        input_type_frame.pack(pady=10)

        weight_button = ctk.CTkButton(input_type_frame, text="Weight (kg)", command=lambda: self.set_input_type(dialog, "weight", product_name, price))
        weight_button.pack(side="left", padx=5)

        amount_button = ctk.CTkButton(input_type_frame, text="Amount ($)", command=lambda: self.set_input_type(dialog, "amount", product_name, price))
        amount_button.pack(side="left", padx=5)

        self.input_field = ctk.CTkEntry(layout, placeholder_text="Enter value")
        self.input_field.pack(pady=10)

        button_frame = ctk.CTkFrame(layout)
        button_frame.pack(pady=10)

        ok_button = ctk.CTkButton(button_frame, text="OK", command=lambda: self.process_weight_amount(dialog, product_name, price))
        ok_button.pack(side="left", padx=5)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side="left", padx=5)

    def set_input_type(self, dialog, input_type, product_name, price):
        self.input_type = input_type
        if input_type == "weight":
            self.input_field.configure(placeholder_text="Enter weight (kg)")
        elif input_type == "amount":
            self.input_field.configure(placeholder_text="Enter amount ($)")

    def process_weight_amount(self, dialog, product_name, price):
        input_value = self.input_field.get()
        try:
            if self.input_type == "weight":
                weight = float(input_value)
                final_price = price * weight
                self.add_item_to_cart(product_name, weight, final_price, 0)
            elif self.input_type == "amount":
                amount = float(input_value)
                weight = amount / price
                self.add_item_to_cart(product_name, weight, amount, 0)
            dialog.destroy()
        except ValueError:
            print("Invalid input")

    def add_item_to_cart(self, product_name, quantity, price, discount):
      print(f"add_item_to_cart called: {product_name}, quantity: {quantity}, price: {price}, discount: {discount}")
      item_exists = False
      for i, item in enumerate(self.cart_items):
          if item["name"] == product_name:
              self.cart_items[i]["quantity"] += quantity
              self.cart_items[i]["price"] += price
              self.cart_items[i]["discount"] += discount
              self.update_cart_display()
              item_exists = True
              break
      if not item_exists:
          self.cart_items.append({"name": product_name, "quantity": quantity, "price": price, "discount": discount})
          self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        for i, item in enumerate(self.cart_items):
            cart_row_frame = ctk.CTkFrame(self.cart_frame, fg_color="#A9CCE3", border_color="black", border_width=1, height=60)  # Reduced blue intensity and increased height
            cart_row_frame.grid(row=i, column=0, sticky="ew")
            cart_row_frame.columnconfigure(0, weight=1)

            number_label = ctk.CTkLabel(cart_row_frame, text=str(i + 1), text_color=self.text_color, font=("Arial", 14))  # Increased font size
            number_label.grid(row=0, column=0, padx=5, sticky="e")

            name_label = ctk.CTkLabel(cart_row_frame, text=item["name"], text_color=self.text_color, font=("Arial", 14))  # Increased font size
            name_label.grid(row=0, column=1, padx=5, sticky="e")

            quantity_entry = ctk.CTkEntry(cart_row_frame, width=50, text_color=self.text_color, fg_color="#A9CCE3", font=("Arial", 14))  # Added blue background and increased font size
            quantity_entry.insert(0, str(item["quantity"]))
            quantity_entry.grid(row=0, column=2, padx=5, sticky="e")
            quantity_entry.bind("<FocusOut>", lambda event, index=i: self.update_quantity(event, index, quantity_entry.get()))
            quantity_entry.bind("<Return>", lambda event, index=i: self.update_quantity(event, index, quantity_entry.get()))  # Update on Enter key press

            price_entry = ctk.CTkEntry(cart_row_frame, width=50, text_color=self.text_color, fg_color="#A9CCE3", font=("Arial", 14))  # Added blue background and increased font size
            price_entry.insert(0, f"{item['price']:.2f}")
            price_entry.grid(row=0, column=3, padx=5, sticky="e")
            price_entry.bind("<FocusOut>", lambda event, index=i: self.update_price(event, index, price_entry.get()))
            price_entry.bind("<Return>", lambda event, index=i: self.update_price(event, index, price_entry.get()))  # Update on Enter key press

            discount_entry = ctk.CTkEntry(cart_row_frame, width=50, text_color=self.text_color, fg_color="#A9CCE3", font=("Arial", 14))  # Added blue background and increased font size
            discount_entry.insert(0, f"{item['discount']:.2f}")
            discount_entry.grid(row=0, column=4, padx=5, sticky="e")
            discount_entry.bind("<FocusOut>", lambda event, index=i: self.update_discount(event, index, discount_entry.get()))
            discount_entry.bind("<Return>", lambda event, index=i: self.update_discount(event, index, discount_entry.get()))  # Update on Enter key press

            total_label = ctk.CTkLabel(cart_row_frame, text=f"{(item['quantity'] * item['price']) - item['discount']:.2f}", text_color=self.text_color, font=("Arial", 14))  # Increased font size
            total_label.grid(row=0, column=5, padx=5, sticky="e")

            delete_button = ctk.CTkButton(cart_row_frame, text="حذف", fg_color=self.error_color, text_color="white", width=50, command=lambda index=i: self.remove_from_cart(index))
            delete_button.grid(row=0, column=6, padx=5, sticky="e")
        self.calculate_total()

    def update_quantity(self, event, index, new_quantity):
        try:
            new_quantity = float(new_quantity)
            if new_quantity > 0:
                self.cart_items[index]["quantity"] = new_quantity
                self.update_cart_display()
            else:
                self.cart_items[index]["quantity"] = 1
                self.update_cart_display()
        except ValueError:
            self.update_cart_display()

    def update_price(self, event, index, new_price):
        try:
            new_price = float(new_price)
            if new_price >= 0:
                self.cart_items[index]["price"] = new_price
                self.update_cart_display()
        except ValueError:
            self.update_cart_display()

    def update_discount(self, event, index, new_discount):
        try:
            new_discount = float(new_discount)
            if new_discount >= 0:
                self.cart_items[index]["discount"] = new_discount
                self.update_cart_display()
        except ValueError:
            self.update_cart_display()

    def remove_from_cart(self, index):
        del self.cart_items[index]
        self.update_cart_display()

    def calculate_total(self):
        total = sum((item["quantity"] * item["price"]) - item["discount"] for item in self.cart_items)
        self.total_amount = total
        self.total_label.configure(text=f"{self.total_amount:.2f}")

    def on_search_key_release(self, event):
        if self.search_timer: # Check if self.search_timer is not None before cancel
            self.after_cancel(self.search_timer)
        if self.search_bar.get().isdigit():
          print(f"on_search_key_release: isdigit")
          self.search_timer = self.after(250, self.search_by_barcode)  # Delay for barcode search
        else:
          print(f"on_search_key_release: text search")
          self.search_items()  # Immediate search for item names

    def search_by_barcode(self):
      try:
        barcode = self.search_bar.get()
        print(f"search_by_barcode: barcode:{barcode}")
        conn = sqlite3.connect('sqlite3.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, sale_price, contains_weight FROM items WHERE barcode = ?', (barcode,))
        item = cursor.fetchone()
        conn.close()

        if item:
            product_name, price, contains_weight = item
            print(f"search_by_barcode: product found:{product_name}")
            self.add_to_cart(product_name, price, contains_weight)
            self.search_bar.delete(0, 'end')  # Clear the search bar after adding the item
        else:
           print("Item not found in search_by_barcode")
      except Exception as e:
          print(f"Error in search_by_barcode: {e}")
        
    def search_items(self):
        text = self.search_bar.get()
        try:
            conn = sqlite3.connect('sqlite3.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, quantity, sale_price, contains_weight FROM items WHERE name LIKE ?', ('%' + text + '%',))
            items = cursor.fetchall()
            conn.close()

            for button in self.product_buttons:
                button.destroy()
            self.product_buttons.clear()

            for i, (product_name, quantity, price, contains_weight) in enumerate(items):
                button = ctk.CTkButton(self.products_frame, text=f"{product_name} - {quantity} متوفرة", command=lambda name=product_name, p=price, cw=contains_weight: self.add_to_cart(name, p, cw), fg_color=self.secondary_color, border_color="lightgray", border_width=1, text_color=self.text_color, hover_color="#F0F0F0")
                button.grid(row=i // 3, column=i % 3, sticky="ew", padx=5, pady=2)
                self.product_buttons.append(button)

            for col in range(3):
                self.products_frame.columnconfigure(col, weight=1)
        except Exception as e:
            print(f"Error in search_items: {e}")
            

    def on_search_return(self, event):
      barcode_data = self.search_bar.get()
      print(f"Input barcode: {barcode_data}") # Added this print to follow the input
      result = read_barcode(barcode_data)
      if result:
          if len(result) == 2: # Handle 13 digits barcode
            product_code, weight = result
            print(f"Parsed product_code: {product_code} and weight: {weight}") # Added this print to follow result of parsing
            try:
                conn = sqlite3.connect('sqlite3.db')
                cursor = conn.cursor()
                cursor.execute('SELECT name, sale_price, contains_weight FROM items WHERE barcode = ?', (barcode_data,)) # using full barcode for search
                item = cursor.fetchone()
                conn.close()
                if item:
                    product_name, price, contains_weight = item
                    print(f"on_search_return: product found:{product_name} , contains_weight:{contains_weight}")
                    if contains_weight:
                       self.add_item_to_cart(product_name, weight, price, 0)
                    else:
                       self.add_item_to_cart(product_name, 1, price, 0)
                    self.search_bar.delete(0, 'end')
                else:
                   print("لم يتم العثور على منتج بهذا الباركود")
                   self.search_bar.delete(0, 'end')
            except Exception as e:
                print(f"Error searching database on barcode scan: {e}")
          elif len(result) == 1: # Handle 2-12 digit barcodes
              barcode = result[0]
              print(f"Parsed barcode with 2-12 digits: {barcode}") # Added this print to follow result of parsing
              try:
                    conn = sqlite3.connect('sqlite3.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, sale_price, contains_weight FROM items WHERE barcode = ?', (barcode,))
                    item = cursor.fetchone()
                    conn.close()
                    if item:
                        product_name, price, contains_weight = item
                        print(f"on_search_return: product found:{product_name} , contains_weight:{contains_weight}")
                        self.add_item_to_cart(product_name, 1, price, 0)
                        self.search_bar.delete(0, 'end')
                    else:
                       print("لم يتم العثور على منتج بهذا الباركود")
                       self.search_bar.delete(0, 'end')
              except Exception as e:
                    print(f"Error searching database on barcode scan: {e}")
          else:
                print("Invalid format from barcode")
                self.search_bar.delete(0, 'end')
      else:
          self.search_bar.delete(0, 'end')
          print("لم يتم التعرف على الباركود")