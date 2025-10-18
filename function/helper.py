import cv2
import pytesseract
import easyocr
reader = easyocr.Reader(['vi', 'en'])
print("đã import hàm helper.py")
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Mapping ký tự OCR sai phổ biến
# Mapping ký tự OCR sai phổ biến
# Mapping ký tự OCR sai phổ biến
CORRECT_MAP = {'O':'U','6':'G', 'I':'1','L':'1','T':'1','Z':'2','S':'5','B':'8','A':'4'}
LETTER_TO_NUMBER = {'O':'0','G':'6','I':'1','L':'1','T':'1','S':'5','B':'8','Z':'2','A':'4'}
NUMBER_TO_LETTER = {'0':'U','6':'G','1':'I','2':'Z','5':'S','8':'B','4':'A'}




def ocr_image(img, whitelist="ABCDEFGHJKLMNPSTUVXYZ0123456789"):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = f"--psm 7 -c tessedit_char_whitelist={whitelist}"
    return pytesseract.image_to_string(thresh, config=config).strip().replace(" ", "")





def correct_plate_text_by_position(text, top_len):
    text = text.upper()
    text = "".join(ch for ch in text if ch.isalnum())
    top = list(text[:top_len])
    bottom = list(text[top_len:])

    # Xử lý ký tự thừa ở đầu hoặc cuối hàng trên
    if len(top) == 5:
        if top[0] not in '234567890':
            top = top[1:]
        elif top[-1] not in '234567890':
            top = top[:-1]
    elif len(top) == 6:
        top = top[1:-1]

    # Xử lý ký tự thừa ở đầu hoặc cuối hàng dưới
    if len(bottom) == 6:
        if bottom[0] not in '234567890':
            bottom = bottom[1:]
        elif bottom[-1] not in '234567890':
            bottom = bottom[:-1]
    elif len(bottom) == 7:
        bottom = bottom[1:-1]

    # Map ký tự đúng theo vị trí hàng trên
    for i, ch in enumerate(top):
        if i == 2 and ch.isdigit():  # ký tự thứ 3 -> chữ
            top[i] = NUMBER_TO_LETTER.get(ch, ch)
        elif i != 2 and ch.isalpha(): # các ký tự khác -> số
            top[i] = LETTER_TO_NUMBER.get(ch, '0')
     # Chèn dấu '-' sau ký tự thứ 2
    if len(top) > 4:
        top.insert(2, '-')


    # Xử lý bottom bằng vòng lặp for
    mapped_bottom = []
    for i, ch in enumerate(bottom):
        # Xóa ký tự đầu nếu là chữ
        if i == 0 and ch.isalpha():
            continue
        # Xóa ký tự cuối nếu là chữ
        if i == len(bottom)-1 and ch.isalpha():
            continue
        mapped_bottom.append(LETTER_TO_NUMBER.get(ch, ch))

    # Chèn dấu '.' sau 3 ký tự đầu nếu đủ 5 ký tự trở lên
    if len(mapped_bottom) >5:
        if len(mapped_bottom) >3:
            mapped_bottom.insert(3, '.')
            
    return "".join(top + mapped_bottom)


def process_horizontal_plate(text):
    """
    Xử lý biển số ngang 1 hàng (ví dụ: 23A12345)
    """
    text = text.upper()
    text = "".join(ch for ch in text if ch.isalnum())
    chars = list(text)

    # Xử lý ký tự thừa ở đầu/cuối
    if len(chars) == 9:
        if chars[0] not in '234567890':
            chars = chars[1:]
        elif chars[-1] not in '234567890':
            chars = chars[:-1]
    elif len(chars) == 10:
        chars = chars[1:-1]

    # Ký tự thứ 3 luôn là chữ
    if len(chars) >= 3 and chars[2].isdigit():
        chars[2] = NUMBER_TO_LETTER.get(chars[2], chars[2])

    # Ép các ký tự khác thành số nếu bị OCR nhầm
    for i, ch in enumerate(chars):
        if i != 2 and ch.isalpha():
            chars[i] = LETTER_TO_NUMBER.get(ch, '0')

    # Ghép lại và format kiểu 31A-304.23
    if len(chars) >= 8:
        formatted = f"{''.join(chars[:3])}-{''.join(chars[3:6])}.{''.join(chars[6:8])}"
    else:
        formatted = "".join(chars)

    return formatted


    # return "".join(chars)


def read_plate_from_crop(crop_img, is_two_lines=False, save_crops=False):
    if is_two_lines:
        h = crop_img.shape[0]

        # Cắt top 60% từ đầu
        top_h = int(h * 0.6)
        top_img = crop_img[:top_h, :]

        # Cắt bottom 50% từ cuối ảnh
        bottom_h = int(h * 0.5)
        bottom_img = crop_img[-bottom_h:, :]

        # OCR với EasyOCR trước
        res_top = reader.readtext(top_img, detail=1)  # detail=1 trả về (bbox, text, confidence)
        res_bottom = reader.readtext(bottom_img, detail=1)

        # Lấy text từ EasyOCR, nối lại và loại bỏ khoảng trắng
        top_text = "".join([r[1] for r in res_top]).replace(" ", "")
        bottom_text = "".join([r[1] for r in res_bottom]).replace(" ", "")

        # Nếu EasyOCR không đọc được -> fallback sang pytesseract
        if not top_text:
            top_text = ocr_image(top_img)
        if not bottom_text:
            bottom_text = ocr_image(bottom_img)

        # Sau đó dùng helper của bạn để xử lý ký tự
        return correct_plate_text_by_position(top_text + bottom_text, top_len=len(top_text))


    else:
        # text = ocr_image(crop_img)
        # if not text:
        #     res = reader.readtext(crop_img)
        #     text = "".join([r[1] for r in res]).replace(" ", "")

        res = reader.readtext(crop_img, detail=1)
        text = "".join([r[1] for r in res]).replace(" ", "")
        text = "".join(ch for ch in text if ch.isalnum())
        # --- Fallback pytesseract nếu EasyOCR không đọc được ---
        if len(text) < 8:
            text = ocr_image(crop_img)
        return process_horizontal_plate(text)