from pyzbar.pyzbar import decode
from PIL import Image
import io

def read_barcode(barcode_data):
    """
    تقوم بقراءة الباركود وتحليل بيانات الوزن.
    
    Args:
        barcode_data (str): نص الباركود أو بيانات الباركود.
        
    Returns:
        tuple or None: (رمز المنتج, الوزن) أو None إذا لم يتم التعرف على الباركود.
    """
    try:
        # Simulate the barcode scanner
        # barcode_bytes = barcode_data.encode('utf-8') # If using real scanner.

        # You could replace this by reading it from the file if using a camera image.
        # pil_image = Image.open(io.BytesIO(barcode_bytes))
        # decoded_barcode_data = decode(pil_image)

        decoded_barcode_data = decode(barcode_data)  # If using a simple string instead.

        if decoded_barcode_data:
            barcode = decoded_barcode_data[0].data.decode('utf-8')  # If using real scanner, else use string directly
            # تحليل الباركود (مثال)
            # هذا الجزء يحتاج إلى التعديل بناءً على بنية الباركود الخاصة بميزانك
            # يفترض أن الباركود يتكون من 13 رقم، أول 7 أرقام هي رمز المنتج، وآخر 6 أرقام هي الوزن.
            if len(barcode) == 13:
                product_code = barcode[:7]
                weight_str = barcode[7:13]
                weight = int(weight_str) / 1000  # Convert to kilograms
                return product_code, weight
            elif 2 <= len(barcode) <= 12:
                return barcode, 0
            else:
                print("تنسيق الباركود غير صحيح.")
                return None

        else:
            print("لا يمكن قراءة الباركود")
            return None

    except Exception as e:
        print(f"حدث خطأ أثناء قراءة الباركود: {e}")
        return None

if __name__ == "__main__":
    # أمثلة للاختبار
    test_barcodes = [
        "1234567123456",
        "1234567012345",
        "9876543456789",
        "123456789012", #testing 12 digits barcode.
        "12", #testing 2 digits barcode
        "12345678901", #testing 11 digits barcode
        "invalid_barcode"  # Invalid barcode
    ]

    for barcode in test_barcodes:
        result = read_barcode(barcode)
        if result:
            product_code, weight = result
            print(f"رمز المنتج: {product_code}, الوزن: {weight:.3f}")