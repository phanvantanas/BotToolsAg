import io
import os
import subprocess
import tempfile
import mss
from PIL import Image, ImageDraw, ImageFont
from src.config import settings
from src.core.logger import logger


class ScreenService:
    """Dịch vụ chụp ảnh màn hình máy tính với cơ chế chịu lỗi cao."""

    @staticmethod
    def _create_fallback_image(reason: str = "Màn hình đang bị khóa hoặc chưa đăng nhập vào Desktop") -> io.BytesIO:
        """
        Tạo ảnh thông báo chẩn đoán khi hệ thống ở trạng thái khóa màn hình
        hoặc không có session đồ họa tương tác trực tiếp.
        """
        img = Image.new("RGB", (800, 400), color=(30, 30, 35))
        draw = ImageDraw.Draw(img)

        text_lines = [
            "⚠️ THÔNG BÁO GIÁM SÁT MÀN HÌNH",
            "────────────────────────────────────────",
            f"Trạng thái: {reason}",
            "",
            "Nguyên nhân thường gặp:",
            "• Màn hình Windows đang ở chế độ Lock (Khóa).",
            "• Màn hình đang ở chế độ Sleep/Tắt tín hiệu hiển thị.",
            "• Bot đang chạy ngầm trong session không có quyền truy cập GDI.",
            "",
            "👉 Máy tính và Antigravity vẫn đang hoạt động bình thường.",
        ]

        y = 40
        for line in text_lines:
            draw.text((40, y), line, fill=(220, 220, 220))
            y += 28

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf

    @classmethod
    def capture_screen(cls, monitor_index: int = 1) -> io.BytesIO:
        """
        Chụp màn hình máy tính và trả về Buffer BytesIO định dạng JPEG.
        Tự động fallback về ảnh thông báo nếu GDI BitBlt bị chặn (màn hình khóa/headless).
        """
        # Cách 1: Thử chụp bằng mss
        try:
            with mss.MSS() as sct:
                monitors = sct.monitors
                if monitor_index >= len(monitors):
                    monitor_index = 1 if len(monitors) > 1 else 0

                target_monitor = monitors[monitor_index]
                sct_img = sct.grab(target_monitor)

                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                if img.width > settings.SCREENSHOT_MAX_WIDTH:
                    ratio = settings.SCREENSHOT_MAX_WIDTH / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    img = img.resize((settings.SCREENSHOT_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85, optimize=True)
                buf.seek(0)
                return buf
        except Exception as e_mss:
            logger.warning(f"Chụp bằng mss thất bại ({e_mss}), thử phương án dự phòng PIL ImageGrab...")

        # Cách 2: Thử chụp bằng PIL ImageGrab
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            buf.seek(0)
            return buf
        except Exception as e_pil:
            logger.warning(f"PIL ImageGrab cũng không thể truy cập màn hình ({e_pil}).")

        # Cách 3: VBScript + Task Scheduler — ẩn hoàn toàn, chạy trong interactive session
        # WScript.Shell.Run với windowStyle=0 không flash bất kỳ cửa sổ nào lên màn hình
        try:
            import time
            tmp_path = os.path.join(tempfile.gettempdir(), "ag_screenshot_tmp.png")
            ps1_path = os.path.join(tempfile.gettempdir(), "ag_capture.ps1")
            vbs_path = os.path.join(tempfile.gettempdir(), "ag_capture.vbs")

            # Xóa file cũ nếu còn tồn tại
            for p in [tmp_path, ps1_path, vbs_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

            # Script PowerShell chụp màn hình
            safe_tmp = tmp_path.replace("\\", "/")
            ps_content = (
                "Add-Type -AssemblyName System.Windows.Forms\n"
                "Add-Type -AssemblyName System.Drawing\n"
                "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds\n"
                "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)\n"
                "$g = [System.Drawing.Graphics]::FromImage($bmp)\n"
                "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)\n"
                f"$bmp.Save('{safe_tmp}')\n"
                "$g.Dispose()\n"
                "$bmp.Dispose()\n"
            )
            with open(ps1_path, "w", encoding="utf-8") as f:
                f.write(ps_content)

            # VBScript: gọi PowerShell với windowStyle=0 (ẩn tuyệt đối, không flash terminal)
            vbs_content = (
                'Set sh = CreateObject("WScript.Shell")\n'
                f'sh.Run "powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ""{ps1_path}""", 0, True\n'
            )
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_content)

            task_name = "AGScreenCapture"
            tr_cmd = f'wscript.exe "{vbs_path}"'

            # Tạo và chạy task trong interactive session của người dùng
            subprocess.run(
                ["schtasks", "/Create", "/F", "/TN", task_name,
                 "/TR", tr_cmd, "/SC", "ONCE", "/ST", "00:00"],
                capture_output=True, timeout=10
            )
            subprocess.run(["schtasks", "/Run", "/TN", task_name],
                           capture_output=True, timeout=10)

            # Chờ file xuất hiện (tối đa 10 giây)
            for _ in range(20):
                time.sleep(0.5)
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
                    break

            # Dọn task và tất cả file tạm
            subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"],
                           capture_output=True, timeout=5)
            for p in [ps1_path, vbs_path]:
                try:
                    os.remove(p)
                except Exception:
                    pass

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
                img = Image.open(tmp_path).convert("RGB")
                if img.width > settings.SCREENSHOT_MAX_WIDTH:
                    ratio = settings.SCREENSHOT_MAX_WIDTH / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    img = img.resize((settings.SCREENSHOT_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85, optimize=True)
                buf.seek(0)
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                logger.info("Chụp màn hình thành công qua VBScript + Task Scheduler (ẩn hoàn toàn).")
                return buf
            else:
                logger.warning("VBScript + Task Scheduler thất bại: file không được tạo.")
        except Exception as e_ts:
            logger.warning(f"VBScript + Task Scheduler gặp lỗi ({e_ts}).")

        # Cách 4: Trả về ảnh thông báo chẩn đoán thân thiện
        logger.info("Tạo ảnh thông báo trạng thái màn hình khóa/headless.")
        return cls._create_fallback_image("Màn hình đang ở trạng thái Khóa (Locked) hoặc tắt tín hiệu hiển thị")


screen_service = ScreenService()
