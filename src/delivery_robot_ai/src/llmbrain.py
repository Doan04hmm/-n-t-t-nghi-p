import json
from google import genai
from google.genai import types

# 1. ĐIỀN API KEY GEMINI CỦA BẠN VÀO ĐÂY
GEMINI_API_KEY = "api key"

# Khởi tạo client kết nối với Google AI
client = genai.Client(api_key=GEMINI_API_KEY)

def nlu_robot_brain(user_command: str):
    """
    Sử dụng Gemini để dịch câu nói tự nhiên thành dữ liệu JSON cấu trúc
    """
    
    # Thiết lập Prompt (Lệnh cấu hình chuyên gia cho AI)
    system_instruction = (
        "Mày là bộ não phân tích ngôn ngữ (NLU) của một robot giao hàng tự hành trong kho.\n"
        "Nhiệm vụ của mày là đọc câu lệnh của con người (bằng tiếng Việt hoặc tiếng Anh) "
        "và bóc tách nó thành một cấu trúc JSON duy nhất, không giải thích gì thêm.\n\n"
        "Cấu trúc JSON bắt buộc phải tuân theo quy định sau:\n"
        "{\n"
        "  'action': 'giao_hang' hoặc 'mo_thung' hoặc 'dong_thung' hoặc 'khong_hieu',\n"
        "  'ke': 'Tên kệ hàng tìm được (ví dụ: A, B1, C2), nếu không có thì để null',\n"
        "  'ngan': 'Số ngăn hàng tìm được (Kiểu số nguyên INT), nếu không có thì để null'\n"
        "}"
    )

    try:
        # Gọi mô hình gemini-2.5-flash (tốc độ siêu nhanh, miễn phí)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_command,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # Ép khuôn phản hồi trả về bắt buộc phải là định dạng JSON cấu trúc
                response_mime_type="application/json",
                temperature=0.1 # Đặt độ sáng tạo thấp để AI trả về kết quả chính xác, ổn định
            )
        )
        
        # Chuyển chuỗi JSON chữ thành đối tượng Dictionary trong Python
        data_json = json.loads(response.text)
        return data_json
        
    except Exception as e:
        print(f"Lỗi kết nối AI: {e}")
        return {"action": "khong_hieu", "ke": None, "ngan": None}

# --- CHƯƠNG TRÌNH CHẠY THỬ NGHIỆM ---
if __name__ == "__main__":
    print("🧠 Bộ não AI LLM đã sẵn sàng test thử nghiệm...")
    
    while True:
        text = input("\nNhập câu nói tự nhiên của bạn (hoặc gõ 'exit' để thoát): ")
        if text.lower() == 'exit':
            break
            
        print("🤖 Robot đang suy nghĩ và phân tích bằng Gemini...")
        ket_qua = nlu_robot_brain(text)
        
        print("\n--- KẾT QUẢ AI BÓC TÁCH ĐƯỢC ---")
        print(json.dumps(ket_qua, indent=4, ensure_ascii=False))
        print("--------------------------------")
        
        # Thử nghiệm logic điều khiển dựa trên JSON của AI
        if ket_qua['action'] == 'giao_hang':
            print(f"⏩ LỆNH ROS 2: Đang tìm tọa độ của KỆ [{ket_qua['ke']}] và NGÂN [{ket_qua['ngan']}] trên bản đồ để di chuyển...")
        elif ket_qua['action'] == 'mo_thung':
            print("⏩ LỆNH ROS 2: Đang gọi Service /toggle_cargo_hatch -> MỞ THÙNG HÀNG")
        elif ket_qua['action'] == 'dong_thung':
            print("⏩ LỆNH ROS 2: Đang gọi Service /toggle_cargo_hatch -> ĐÓNG THÙNG HÀNG")
        else:
            print("⏩ HÀNH VI: Robot phát âm thanh: 'Xin lỗi, tôi không hiểu hành động bạn yêu cầu!'")
