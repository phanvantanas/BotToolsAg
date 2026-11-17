import asyncio
import json
import os
import re
import time
from pathlib import Path
from src.config import settings
from src.core.logger import logger


AVAILABLE_MODELS = {
    "gemini-3.8-flash-high": "Gemini 3.8 Flash (High)",
    "gemini-3.8-flash-medium": "Gemini 3.8 Flash (Medium)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 (Thinking)",
    "claude-opus-4-6-thinking": "Claude Opus 4.6 (Thinking)",
    "gpt-oss-120b-medium": "GPT-OSS 120B (Medium)",
}

# Probe prompt tối giản để kiểm tra quota (ít token nhất có thể)
_QUOTA_PROBE_PROMPT = "hi"


class AgyService:
    """Dịch vụ điều khiển và tương tác với Antigravity CLI (agy.exe)."""

    def __init__(self):
        self.current_model: str = settings.DEFAULT_MODEL
        # Mặc định là True (tiếp tục phiên hội thoại trước)
        self.continue_session: bool = True
        self.is_busy: bool = False
        # Thư mục làm việc hiện tại của Antigravity
        self.current_working_dir: Path = Path(os.getcwd()).resolve()
        # Bộ nhớ đệm lưu kết quả kiểm tra quota của các model
        self._quota_cache: dict[str, dict] = {}
        self._quota_cache_time: float = 0.0
        self._quota_cache_ttl: float = 300.0  # Lưu cache trong 5 phút

    def reset_session(self) -> None:
        """Đặt lại trạng thái phiên để câu lệnh tiếp theo bắt đầu một cuộc hội thoại mới."""
        self.continue_session = False
        logger.info("Đã đặt lại trạng thái phiên. Lệnh tiếp theo sẽ mở hội thoại mới.")

    def set_working_dir(self, dir_path: str) -> tuple[bool, str]:
        """Thay đổi thư mục làm việc hiện tại của Antigravity."""
        try:
            path_obj = Path(dir_path).expanduser().resolve()
            if not path_obj.exists():
                return False, f"❌ Thư mục không tồn tại: `{dir_path}`"
            if not path_obj.is_dir():
                return False, f"❌ Đường dẫn không phải là thư mục: `{dir_path}`"

            self.current_working_dir = path_obj
            # Tự động reset session để phiên mới áp dụng cho thư mục mới
            self.reset_session()
            logger.info(f"Đã chuyển thư mục làm việc sang: {self.current_working_dir}")
            return (
                True,
                f"📂 **Đã chuyển thư mục làm việc thành công!**\n"
                f"Đường dẫn: `{self.current_working_dir}`\n\n"
                f"*(Hệ thống đã tự động mở phiên mới cho thư mục này)*"
            )
        except Exception as e:
            logger.error(f"Lỗi khi đổi thư mục: {e}")
            return False, f"❌ Lỗi khi đổi thư mục: {str(e)}"

    def get_working_dir(self) -> str:
        """Lấy đường dẫn thư mục làm việc hiện tại."""
        return str(self.current_working_dir)

    def set_model(self, model_key: str) -> bool:
        """Thay đổi model AI sử dụng."""
        if model_key in AVAILABLE_MODELS:
            self.current_model = model_key
            logger.info(f"Đã chuyển model sang: {self.current_model}")
            return True
        return False

    def get_status_info(self) -> dict:
        """Lấy thông tin trạng thái hiện tại của service."""
        return {
            "model_key": self.current_model,
            "model_name": AVAILABLE_MODELS.get(self.current_model, self.current_model),
            "session_mode": "Tiếp tục ngữ cảnh (-c)" if self.continue_session else "Phiên mới (New)",
            "working_dir": str(self.current_working_dir),
            "is_busy": self.is_busy,
        }

    def _parse_reset_time(self, error_text: str) -> str | None:
        """
        Trích xuất thời gian reset từ thông báo lỗi quota của agy.exe.
        Ví dụ: 'Resets in 162h14m5s' → '162h 14m 5s'
        """
        match = re.search(
            r"[Rr]eset[s]?\s+in\s+([\d]+h)?\s*([\d]+m)?\s*([\d]+s)?",
            error_text
        )
        if not match:
            return None
        parts = [p for p in match.groups() if p]
        return " ".join(parts) if parts else None

    async def _probe_model_quota(self, model_key: str) -> dict:
        """
        Probe một model bằng cách gửi prompt tối giản.
        Trả về dict: {available: bool, resets_in: str|None, error: str|None}
        """
        agy_binary = settings.AGY_PATH
        if not os.path.isfile(agy_binary):
            return {"available": False, "resets_in": None, "error": "Không tìm thấy agy.exe"}

        cmd = [
            agy_binary,
            "--model", model_key,
            "-p", _QUOTA_PROBE_PROMPT,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.current_working_dir),
            )
            # Timeout 20s cho probe nhẹ
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=20
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return {"available": True, "resets_in": None, "error": "Timeout probe"}

            stderr_text = stderr_bytes.decode("utf-8", errors="replace")
            stdout_text = stdout_bytes.decode("utf-8", errors="replace")
            combined = stderr_text + stdout_text

            if process.returncode == 0:
                return {"available": True, "resets_in": None, "error": None}

            # Phân tích lỗi quota / rate limit
            combined_lower = combined.lower()
            if "quota" in combined_lower or "rate limit" in combined_lower or "resource_exhausted" in combined_lower:
                resets_in = self._parse_reset_time(combined)
                # Thử parse từ JSON AGY_ERROR
                json_match = re.search(r"AGY_ERROR:\s*(\{.*?\})", combined, re.DOTALL)
                if json_match:
                    try:
                        err_obj = json.loads(json_match.group(1))
                        short_err = err_obj.get("short_error", "")
                        resets_in = resets_in or self._parse_reset_time(short_err)
                    except json.JSONDecodeError:
                        pass
                return {
                    "available": False,
                    "resets_in": resets_in,
                    "error": "Hết quota",
                }

            # Lỗi khác (không phải quota)
            return {"available": True, "resets_in": None, "error": None}

        except Exception as e:
            logger.error(f"Lỗi probe model {model_key}: {e}")
            return {"available": False, "resets_in": None, "error": str(e)}

    async def check_all_models_quota(self, force_refresh: bool = False) -> dict[str, dict]:
        """
        Kiểm tra quota song song cho tất cả các model.
        Có cơ chế cache trong vòng 5 phút để tránh gọi lặp lại làm tốn tài nguyên và chậm phản hồi.
        Trả về dict: {model_key: {available, resets_in, error}}
        """
        now = time.time()
        if not force_refresh and self._quota_cache and (now - self._quota_cache_time < self._quota_cache_ttl):
            logger.info("Sử dụng dữ liệu quota từ bộ nhớ đệm (cache)")
            return dict(self._quota_cache)

        tasks = {
            key: self._probe_model_quota(key)
            for key in AVAILABLE_MODELS
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        quota_data = {
            key: (res if isinstance(res, dict) else {"available": False, "resets_in": None, "error": str(res)})
            for key, res in zip(tasks.keys(), results)
        }
        self._quota_cache = quota_data
        self._quota_cache_time = now
        return dict(self._quota_cache)

    async def execute_prompt(self, prompt: str) -> str:
        """
        Gửi prompt đến agy.exe và nhận kết quả trả về.
        """
        if self.is_busy:
            return "⏳ Antigravity đang xử lý một tác vụ khác. Vui lòng chờ trong giây lát rồi thử lại."

        agy_binary = settings.AGY_PATH
        if not os.path.isfile(agy_binary):
            return f"❌ Không tìm thấy file thực thi Antigravity tại: `{agy_binary}`"

        cmd = [agy_binary, "--model", self.current_model]

        # Nếu đang ở chế độ tiếp tục phiên
        if self.continue_session:
            cmd.append("-c")

        cmd.extend(["-p", prompt])

        self.is_busy = True
        logger.info(f"Thực thi Antigravity: {' '.join(cmd[:4])} -p \"{prompt[:60]}...\"")

        try:
            # Chạy subprocess bất đồng bộ
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.current_working_dir)
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=settings.AGY_TIMEOUT
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return f"⚠️ Hết thời gian chờ (Timeout {settings.AGY_TIMEOUT}s). Tác vụ đã bị dừng."

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

            # Sau khi thực hiện xong phiên mới đầu tiên, tự động bật lại continue_session
            # để các câu hỏi sau đó tiếp tục cuộc trò chuyện mới này.
            self.continue_session = True

            if process.returncode != 0:
                logger.error(f"agy.exe lỗi (code {process.returncode}): {stderr}")
                error_msg = stderr if stderr else stdout
                # Nhận diện nếu bị lỗi Quota / Rate limit
                error_lower = error_msg.lower()
                if "quota" in error_lower or "rate limit" in error_lower or "resource_exhausted" in error_lower:
                    resets_in = self._parse_reset_time(error_msg)
                    # Tự động cập nhật cache quota để menu /model biết ngay lập tức
                    self._quota_cache[self.current_model] = {
                        "available": False,
                        "resets_in": resets_in,
                        "error": "Hết quota",
                    }
                    self._quota_cache_time = time.time()

                    reset_info = f"\n⏰ **Lượt reset tiếp theo sau:** `{resets_in}`" if resets_in else ""
                    return (
                        f"⚠️ **Hạn mức (Quota) của model `{self.current_model}` đã hết!**{reset_info}\n\n"
                        f"👉 Bạn hãy bấm nút **⚙️ Đổi Model (+ Quota)** hoặc gõ `/model` để chuyển sang model khác khả dụng."
                    )
                return f"❌ Lỗi khi thực thi (Mã {process.returncode}):\n```\n{error_msg[:1000]}\n```"

            if not stdout:
                return "✅ Lệnh đã thực thi thành công nhưng không có dữ liệu trả về từ console."

            return stdout

        except Exception as e:
            logger.error(f"Ngoại lệ khi gọi agy.exe: {e}", exc_info=True)
            return f"❌ Đã xảy ra lỗi nội bộ: {str(e)}"
        finally:
            self.is_busy = False


agy_service = AgyService()
