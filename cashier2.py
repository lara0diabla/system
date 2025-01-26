import customtkinter as ctk
import sqlite3

class Cashier2Module(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.primary_color = "#2E86C1"  # Blue
        self.secondary_color = "#EAF2F8"  # Light gray
        self.button_color = "#2ECC71"  # Green
        self.text_color = "#2C3E50"  # Dark gray
        self.error_color = "#E74C3C"  # Red

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
        self.left_frame.pack(side="left", fill="both", padx=10, pady=10)
        self.products_label = ctk.CTkLabel(self.left_frame, text="البحث حسب الاسم أو الباركود", font=("Arial", 12, "bold"), text_color=self.text_color)
        self.products_label.pack(pady=10)
        self.search_bar = ctk.CTkEntry(self.left_frame, placeholder_text="بحث...", text_color=self.text_color)
        self.search_bar.pack(fill="x", padx=10, pady=5)

        self.categories_frame = ctk.CTkFrame(self.left_frame, fg_color=self.secondary_color)
        self.categories_frame.pack(side="top", fill="x", expand=True, padx=10, pady=5)
        self.categories = ["قهوة", "مكسرات", "زينه", "زيوت", "بقوليات", "توابل", "بذور"]
        self.category_buttons = {}
        for category in self.categories:
            btn = ctk.CTkButton(self.categories_frame, text=category, command=lambda c=category: self.show_products(c), fg_color=self.primary_color, text_color="white")
            btn.pack(side="top", fill="x", pady=2)
            self.category_buttons[category] = btn

        self.products_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color=self.secondary_color, scrollbar_button_color="#CCCCCC", scrollbar_button_hover_color="#A9A9A9")
        self.products_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        self.products = {
            "قهوة": [
                ("شموط سريع تحضير", 76, 5.00),
                ("قهوة الشام 250 غم", 9, 13.00),
                ("قهوة الشام اصابع", 93, 1.00),
                ("قهوة خضراء", 13.749, 30.00),
                ("قهوة دله الشام", 33, 5.00),
                ("قهوة سادة", 20.486112, 52.00),
            ],
            "مكسرات": [("فستق", 100, 25.00), ("لوز", 150, 20.00)],
            "زينه": [("بالونات", 50, 3.00), ("ورود", 20, 10.00)],
            "زيوت": [("زيت زيتون", 25, 50.00)],
            "بقوليات": [("حمص", 100, 10.00), ("فول", 150, 8.00)],
            "توابل": [("كمون", 500, 5.00), ("فلفل اسود", 250, 7.00)],
            "بذور": [("بذور دوار الشمس", 100, 4.00), ("بذور اليقطين", 75, 6.00)],
        }
        self.product_buttons = []

        # Right frame for cart
        self.right_frame = ctk.CTkFrame(self, fg_color=self.secondary_color)
        self.right_frame.pack(side="right", fill="both", padx=10, pady=10, expand=True)
        self.cart_labels_frame = ctk.CTkFrame(self.right_frame, fg_color="#CCCCCC", height=30)
        self.cart_labels_frame.pack(side="top", fill="x")
        self.cart_labels = ["#", "الاسم", "الكمية", "السعر", "الخصم", "المجموع"]
        for i, label in enumerate(self.cart_labels):
            label_widget = ctk.CTkLabel(self.cart_labels_frame, text=label, text_color=self.text_color)
            label_widget.pack(side="right", padx=10)
        self.cart_frame = ctk.CTkScrollableFrame(self.right_frame, fg_color="white", scrollbar_button_color="#CCCCCC", scrollbar_button_hover_color="#A9A9A9")
        self.cart_frame.pack(side="top", fill="both", expand=True)

        self.cart_items = []

        # Bottom frame for buttons
        self.bottom_frame = ctk.CTkFrame(self, fg_color=self.secondary_color)
        self.bottom_frame.pack(side="bottom", fill="x", pady=10)
        self.bottom_buttons = ["دفع", "فتح الدرج", "فاتورة جديدة", "الفواتير المعلقة", "تعليق", "آخر فاتورة", "مرتجع جديد", "الصندوق", "الحاسبة"]
        for button in self.bottom_buttons:
            btn = ctk.CTkButton(self.bottom_frame, text=button, fg_color="#E67E22", text_color="white", command=lambda b=button: self.handle_bottom_button(b))
            btn.pack(side="left", padx=5, pady=5, expand=True)

        # Display default products
        self.show_products("قهوة")

    def handle_bottom_button(self, button_name):
        print(f"تم الضغط على الزر: {button_name}")

    def show_products(self, category):
        for button in self.product_buttons:
            button.destroy()
        self.product_buttons.clear()

        if category in self.products:
            for product_name, quantity, price in self.products[category]:
                button = ctk.CTkButton(self.products_frame, text=f"{product_name} - {quantity} متوفرة", command=lambda name=product_name, p=price: self.add_to_cart(name, p), fg_color=self.secondary_color, border_color="lightgray", border_width=1, text_color=self.text_color, hover_color="#F0F0F0")
                button.pack(side="top", fill="x", pady=2)
                self.product_buttons.append(button)

    def add_to_cart(self, product_name, price):
        item_exists = False
        for i, item in enumerate(self.cart_items):
            if item["name"] == product_name:
                self.cart_items[i]["quantity"] += 1
                self.update_cart_display()
                item_exists = True
                break
        if not item_exists:
            self.cart_items.append({"name": product_name, "quantity": 1, "price": price})
            self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        for i, item in enumerate(self.cart_items):
            cart_row_frame = ctk.CTkFrame(self.cart_frame, fg_color="white")
            cart_row_frame.pack(side="top", fill="x")
            number_label = ctk.CTkLabel(cart_row_frame, text=str(i + 1), text_color=self.text_color)
            number_label.pack(side="right", padx=10)
            name_label = ctk.CTkLabel(cart_row_frame, text=item["name"], text_color=self.text_color)
            name_label.pack(side="right", padx=10)
            quantity_label = ctk.CTkLabel(cart_row_frame, text=str(item["quantity"]), text_color=self.text_color)
            quantity_label.pack(side="right", padx=10)
            price_label = ctk.CTkLabel(cart_row_frame, text=f"{item['price']:.2f}", text_color=self.text_color)
            price_label.pack(side="right", padx=10)
            discount_label = ctk.CTkLabel(cart_row_frame, text="0.00", text_color=self.text_color)  # Discount can be added functionality later
            discount_label.pack(side="right", padx=10)
            total_label = ctk.CTkLabel(cart_row_frame, text=f"{item['quantity'] * item['price']:.2f}", text_color=self.text_color)
            total_label.pack(side="right", padx=10)
        self.calculate_total()

    def calculate_total(self):
        total = sum(item["quantity"] * item["price"] for item in self.cart_items)
        self.total_amount = total
        self.total_label.configure(text=f"{self.total_amount:.2f}")
