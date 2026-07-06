#!/usr/bin/env python3
import os
import json
import asyncio
import math
from pydub import AudioSegment
from groq import Groq
from google import genai
from google.genai import types
from gtts import gTTS # Thư viện dịch chữ thành giọng nói trực tiếp trên Robot

# TOÀN BỘ THƯ VIỆN ROS 2 JAZZY VÀ NAV2 SIMPLE COMMANDER
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
from nav2_simple_commander.robot_navigator import TaskResult as NavigationResult # Sửa lỗi chuyển đổi tên trên bản Jazzy

# ========================================================
# 1. CẤU HÌNH TOÀN BỘ API KEYS TẦNG TRÊN
# ========================================================
TELEGRAM_TOKEN = "api key"
GEMINI_API_KEY = "api key"
GROQ_API_KEY = "api key"

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========================================================
# 2. KHỞI TẠO CÁC PHÂN HỆ AI CLOUD & HÀNG ĐỢI
# ========================================================
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

robot_queue = asyncio.Queue()
is_robot_busy = False

# BẢNG TỌA ĐỘ MỐC THỰC TẾ (Quét map xong thì hai bạn điền đè số thật của Lab vào đây)
MAP_STATIONS = {
    "A": {"x": -0.245579, "y": 2.62362},
    "B": {"x": -0.56, "y": 2.3},
    "C": {"x": 5.0, "y": -5.0},
    "TRAM_SAC": {"x": 0.0, "y": 0.0}
}

MENU_CHINH = [['🔓 Mở Thùng Hàng', '🔒 Đóng Thùng Hàng'], ['📦 Đặt Lệnh Giao Hàng', '🏠 Về Trạm Sạc']]
MENU_CHON_KE = [['Kệ A', 'Kệ B', 'Kệ C'], ['⬅️ Quay Lại Menu Chính']]
MENU_CHON_NGAN = [['Ngăn 1', 'Ngăn 2', 'Ngăn 3'], ['⬅️ Quay Lại Chọn Kệ']]

user_states = {}

# ========================================================
# 3. LỚP ĐIỀU KHIỂN TRUNG TÂM ROBOT (ROS 2 NODE CHẠY TRÊN MINI PC)
# ========================================================
class MiloRobotController(Node):
    def __init__(self):
        super().__init__('milo_robot_controller')
        # Khởi tạo bộ điều hướng cấp cao kết nối trực tiếp với Nav2 nội bộ
        self.navigator = BasicNavigator()
        self.get_logger().info("🤖 [HỆ THỐNG SẴN SÀNG] Bộ điều khiển Milo Robot đã khởi động!")

    def speak_at_lab(self, text_content: str):
        """Hàm ép trực tiếp phần cứng Mini PC phát tiếng Việt ra loa qua jack 3.5mm"""
        self.get_logger().info(f"🔊 [LOA ROBOT PHÁT]: {text_content}")
        try:
            # Gọi Google AI tạo file giọng nói ngầm trên bộ nhớ xe
            tts = gTTS(text=text_content, lang='vi')
            tts.save("milo_voice.mp3")
            # Ép phần cứng Ubuntu trên Mini PC phát âm thanh ra loa công cộng
            os.system("mpg123 -q milo_voice.mp3")
        except Exception as e:
            self.get_logger().error(f"Lỗi phần cứng phát loa: {e}")

    async def send_nav2_goal(self, target_shelf: str, target_tier: str, chat_id: int, tg_bot):
        # 1. Tra cứu tọa độ từ bảng mốc MAP_STATIONS
        x_target = MAP_STATIONS[target_shelf]["x"]
        y_target = MAP_STATIONS[target_shelf]["y"]

        # Sử dụng trực tiếp đối tượng tg_bot để gửi thông báo không cần thông qua CallbackContext
        status_msg = await tg_bot.send_message(
            chat_id=chat_id, 
            text=f"🚀 [XUẤT PHÁT] Xe bắt đầu tự hành đến Kệ {target_shelf} - Ngăn {target_tier}..."
        )

        # 🔊 LOA TRÊN ROBOT TỰ PHÁT TIẾNG NÓI PHẢN HỒI KHI XUẤT PHÁT
        if target_shelf == "TRAM_SAC":
            self.speak_at_lab("Milo nhận lệnh, đang tự động di chuyển quay về trạm sạc pin.")
        else:
            self.speak_at_lab(f"Milo bắt đầu di chuyển đến kệ {target_shelf} ngăn {target_tier}.")

        # 2. Khởi tạo gói tin mục tiêu theo chuẩn hình học ROS 2 Jazzy
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_pose.pose.position.x = x_target
        goal_pose.pose.position.y = y_target
        goal_pose.pose.orientation.w = 1.0 # Hướng quay mặc định

        # 3. Ra lệnh trực tiếp cho bộ điều hướng nội bộ trong bo mạch lăn bánh
        self.navigator.goToPose(goal_pose)

        # 4. Vòng lặp hướng feedback thời gian thực chống đơ luồng hệ thống
        last_reported_time = 0
        while not self.navigator.isTaskComplete():
            await asyncio.sleep(1.0) # Cứ 1 giây quét tiến độ phần cứng một lần
            
            feedback = self.navigator.getFeedback()
            if feedback:
                remaining_time = getattr(feedback, 'estimated_time_remaining', 0.0)
                
                # Cứ sau 4 giây thì chỉnh sửa tin nhắn Telegram một lần để tránh spam mạng
                current_time = int(self.get_clock().now().nanoseconds / 1e9)
                if current_time - last_reported_time >= 4:
                    try:
                        await status_msg.edit_text(
                            f"⏳ [ĐANG DI CHUYỂN] Robot Milo đang tự tìm đường đến Kệ {target_shelf}...\n"
                            f"⏱️ Thời gian dự kiến còn lại: {remaining_time:.1f} giây."
                        )
                        last_reported_time = current_time
                    except Exception:
                        pass

        # 5. Kiểm tra kết quả hành trình từ phần cứng trả về
        result = self.navigator.getResult()
        if result == NavigationResult.SUCCEEDED:
            if target_shelf == "TRAM_SAC":
                await status_msg.edit_text("🔌 [ĐÃ ĐẾN NƠI] Robot Milo đã cập bến dock sạc an toàn!")
                # 🔊 LOA ROBOT PHÁT TIẾNG KHI VỀ ĐẾN ĐOCK SẠC
                self.speak_at_lab("Milo đã về đến trạm sạc pin an toàn. Bắt đầu quá trình nạp năng lượng.")
            else:
                await status_msg.edit_text(f"✅ [ĐÃ ĐẾN NƠI] Robot Milo đã dừng chính xác trước Kệ {target_shelf} - Ngăn {target_tier}!")
                # 🔊 LOA ROBOT PHÁT TIẾNG KHI ĐẾN KỆ GIAO HÀNG THÀNH CÔNG
                self.speak_at_lab(f"Đã đến kệ {target_shelf} ngăn {target_tier}. Xin mời chủ nhân đến lấy hàng và đóng thùng xe.")
        else:
            await status_msg.edit_text(f"⚠️ [CẢNH BÁO] Hành trình tự hành thất bại hoặc bị hủy! Mã lỗi Nav2: {result}")
            # 🔊 LOA ROBOT BÁO CỨU HỘ KHI GẶP SỰ CỐ GIAO THÔNG
            self.speak_at_lab("Cảnh báo! Milo gặp vật cản lớn trên đường đi, cần cứu hộ gấp.")

# Khởi tạo đối tượng Node toàn cục để các hàm Telegram có thể gọi chung
ros_node = None

# ========================================================
# 4. HÀM AI GEMINI NLU (Phân Tích Ngữ Nghĩa Câu Lệnh)
# ========================================================
def nlu_robot_brain(user_command: str):
    system_instruction = (
        "Mày là bộ não phân tích ngôn ngữ (NLU) của một robot giao hàng tự hành trong kho.\n"
        "Nhiệm vụ của mày là đọc câu lệnh của con người và bóc tách nó thành một cấu trúc JSON duy nhất, không giải thích gì thêm.\n\n"
        "⚠️ QUY TẮC ÁNH XẠ VỊ TRÍ BẮT BUỘC:\n"
        "- Nếu câu lệnh có từ 'tầng 1' hoặc 'lầu 1' hoặc 'kệ A', mày phải trả về 'ke': 'A'\n"
        "- Nếu câu lệnh có từ 'tầng 2' hoặc 'lầu 2' hoặc 'kệ B', mày phải trả về 'ke': 'B'\n"
        "- Nếu câu lệnh có từ 'tầng 3' hoặc 'lầu 3' hoặc 'kệ C', mày phải trả về 'ke': 'C'\n"
        "- Nếu câu lệnh có từ 'trạm sạc', 'về sạc', 'sạc pin', mày phải trả về 'ke': 'TRAM_SAC' và 'ngan': '0'\n\n"
        "⚠️ QUY ĐỊNH CẤU TRÚC JSON ĐẦU RA:\n"
        "Mày CHỈ ĐƯỢC PHÉP trả về JSON theo đúng định dạng mẫu sau, nghiêm cấm thêm bớt trường:\n"
        "{\n"
        "  \"action\": \"giao_hang\" hoặc \"mo_thung\" hoặc \"dong_thung\" hoặc \"khong_hieu\",\n"
        "  \"ke\": \"A\" hoặc \"B\" hoặc \"C\" hoặc \"TRAM_SAC\" hoặc null,\n"
        "  \"ngan\": \"1\" hoặc \"2\" hoặc \"3\" hoặc \"0\" hoặc null\n"
        "}"
    )
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=user_command,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        data = json.loads(response.text)
        if data.get("ke") == "TRAM_SAC":
            data["action"] = "giao_hang"
            data["ngan"] = "0"
        return data
    except Exception:
        cmd = user_command.lower()
        if "sạc" in cmd or "về trạm" in cmd: return {"action": "giao_hang", "ke": "TRAM_SAC", "ngan": "0"}
        if "mở" in cmd: return {"action": "mo_thung", "ke": None, "ngan": None}
        if "đóng" in cmd or "khóa" in cmd: return {"action": "dong_thung", "ke": None, "ngan": None}
        return {"action": "khong_hieu", "ke": None, "ngan": None}

# ========================================================
# 5. TIẾN TRÌNH QUẢN LÝ HÀNG ĐỢI NGẦM (QUEUE WORKER ВОТ)
# ========================================================
async def queue_worker(tg_bot):
    """Tiến trình bốc lệnh tự động chạy độc lập, xử lý trực tiếp qua đối tượng bot"""
    global is_robot_busy, ros_node
    while True:
        job = await robot_queue.get()
        is_robot_busy = True
        chat_id = job["chat_id"]
        ke = job["ke"]
        ngan = job["ngan"]
        
        try:
            # Truyền trực tiếp tg_bot xuống để tiến hành gửi tin nhắn feedback hành trình
            await ros_node.send_nav2_goal(ke, ngan, chat_id, tg_bot)
        except Exception as e:
            print(f"Lỗi thực thi điều hướng: {e}")
            
        robot_queue.task_done()
        is_robot_busy = False
        await asyncio.sleep(1)

# ========================================================
# 6. CÁC HÀM XỬ LÝ SỰ KIỆN GIAO DIỆN TELEGRAM
# ========================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ros_node
    # 🔊 LOA PHÁT TIẾNG CHÀO KHỞI ĐỘNG TRỰC TIẾP TRÊN XE KHI ẤN /START (Nếu muốn nghe lại chào)
    if ros_node is not None:
        ros_node.speak_at_lab("Hệ thống tự hành Milo đã sẵn sàng nhận lệnh mới từ chủ nhân.")

    markup = ReplyKeyboardMarkup(MENU_CHINH, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 [AMR MILO - ĐỒ ÁN TỐT NGHIỆP]\n\nHệ thống điều khiển trung tâm chạy độc lập trên Mini PC ASUS đã sẵn sàng!", 
        reply_markup=markup
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    # --- XỬ LÝ HỆ THỐNG NÚT BẤM NHANH TĨNH ---
    if user_text == '🔓 Mở Thùng Hàng':
        await update.message.reply_text("🤖 [ROBOT ACTION] 🔓 MỞ THÙNG THÀNH CÔNG!")
        ros_node.speak_at_lab("Thùng chứa hàng đã được mở, xin mời cất hoặc lấy hàng hóa.")
        return
    elif user_text == '🔒 Đóng Thùng Hàng':
        await update.message.reply_text("🤖 [ROBOT ACTION] 🔒 KHÓA THÙNG THÀNH CÔNG!")
        ros_node.speak_at_lab("Thùng chứa hàng đã được khóa an toàn.")
        return
    elif user_text == '🏠 Về Trạm Sạc':
        await robot_queue.put({"chat_id": chat_id, "ke": "TRAM_SAC", "ngan": "0"})
        markup = ReplyKeyboardMarkup(MENU_CHINH, resize_keyboard=True)
        await update.message.reply_text("📥 Đã xếp lịch quay về Trạm Sạc vào hàng đợi hệ thống...", reply_markup=markup)
        return
    elif user_text == '📦 Đặt Lệnh Giao Hàng' or user_text == '⬅️ Quay Lại Chọn Kệ':
        markup = ReplyKeyboardMarkup(MENU_CHON_KE, resize_keyboard=True)
        await update.message.reply_text("📍 Bước 1: Vui lòng chọn KỆ HÀNG mục tiêu:", reply_markup=markup)
        return
    elif user_text in ['Kệ A', 'Kệ B', 'Kệ C']:
        user_states[chat_id] = {"ke": user_text.replace("Kệ ", "")}
        markup = ReplyKeyboardMarkup(MENU_CHON_NGAN, resize_keyboard=True)
        await update.message.reply_text(f"📥 Bước 2: Chọn [{user_text}], chọn tiếp NGĂN HÀNG:", reply_markup=markup)
        return
    elif user_text in ['Ngăn 1', 'Ngăn 2', 'Ngăn 3']:
        if chat_id in user_states and "ke" in user_states[chat_id]:
            ten_ke = user_states[chat_id]["ke"]
            so_ngan = user_text.replace("Ngăn ", "")
            
            await robot_queue.put({"chat_id": chat_id, "ke": ten_ke, "ngan": so_ngan})
            markup = ReplyKeyboardMarkup(MENU_CHINH, resize_keyboard=True)
            await update.message.reply_text("📥 Đã xếp lệnh nút bấm vào hàng đợi điều phối!", reply_markup=markup)
            del user_states[chat_id]
        return
    elif user_text == '⬅️ Quay Lại Menu Chính':
        markup = ReplyKeyboardMarkup(MENU_CHINH, resize_keyboard=True)
        await update.message.reply_text("Đã quay lại Menu chính.", reply_markup=markup)
        return

    # --- XỬ LÝ CHAT CHỮ TỰ DO (QUA BỘ NÃO AI GEMINI) ---
    ai_json = nlu_robot_brain(user_text)
    action = ai_json.get("action")
    ke = ai_json.get("ke")
    ngan = ai_json.get("ngan")

    if action == "giao_hang" and ke and ngan:
        await robot_queue.put({"chat_id": chat_id, "ke": ke, "ngan": ngan})
        await update.message.reply_text(f"📥 Bộ não AI đã nhận lệnh tự do. Đã đẩy mục tiêu Kệ {ke} vào hàng đợi điều phối...")
    else:
        await update.message.reply_text("❌ Lỗi: Cấu trúc câu lệnh nằm ngoài phạm vi xử lý của robot!")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    status_msg = await update.message.reply_text("🎙️ [GROQ AI] Đang dịch giọng nói...")
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        ogg_path = "voice.ogg"
        wav_path = "voice.wav"
        await voice_file.download_to_drive(ogg_path)
        
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        
        with open(wav_path, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                file=(wav_path, audio_file.read()), model="whisper-large-v3", language="vi"
            )
        text_output = transcript.text
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)
        await status_msg.delete()
        
        ai_json = nlu_robot_brain(text_output)
        if ai_json.get("action") == "giao_hang" and ai_json.get("ke") and ai_json.get("ngan"):
            await update.message.reply_text(f"🗣️ [Nghe thấy]: \"{text_output}\"")
            await robot_queue.put({"chat_id": chat_id, "ke": ai_json.get("ke"), "ngan": ai_json.get("ngan")})
        else:
            await update.message.reply_text(f"🗣️ [Nghe thấy]: \"{text_output}\"\n\n❌ Lỗi: Câu lệnh không hợp lệ!")
    except Exception as e:
        print(f"Lỗi voice: {e}")

# ========================================================
# 7. VÒNG LẶP ĐỒNG THỜI ROS 2 VÀ TELEGRAM (MAIN ENTRY)
# ========================================================
async def run_ros_and_tg(app):
    global ros_node
    # Khởi tạo cổng truyền thông ROS 2 nội bộ trong máy tính ASUS
    rclpy.init()
    ros_node = MiloRobotController()
    
    # 🔊 LOA PHÁT NGAY LẬP TỨC KHI VỪA BẬT FILE CODE TRÊN ROBOT
    ros_node.speak_at_lab("Hệ thống tự hành Milo đã kích hoạt thành công. Sẵn sàng nhận lệnh.")

    # KHỞI ĐỘNG TIẾN TRÌNH HÀNG ĐỢI NGẦM NGAY TỪ ĐẦU (Sửa lỗi: Truyền app.bot trực tiếp)
    asyncio.create_task(queue_worker(app.bot))
    
    # Khởi động ứng dụng mạng của Telegram Bot kết nối Internet
    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    
    print("🚀 [HỆ THỐNG ĐỘC LẬP] Đã kích hoạt Telegram Bot và ROS 2 nội bộ trên Mini PC!")
    
    try:
        while rclpy.ok():
            rclpy.spin_once(ros_node, timeout_sec=0.1)
            await asyncio.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        ros_node.navigator.lifecycleShutdown()
        ros_node.destroy_node()
        rclpy.shutdown()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    
    asyncio.run(run_ros_and_tg(app))

if __name__ == "__main__":
    main()