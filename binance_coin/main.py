# my_app_project/my_app/main.py

import logging
from my_app.config import config
from my_app.api.client import get_bearer_token, subscribe_application

# Cấu hình logging cho ứng dụng chính
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_application():
    """Chức năng chính của ứng dụng để lấy token và subscribe."""
    server_manager = config.get('server_manager')
    org_id = config.get('org_id')
    client_id = config.get('client_id')
    client_secret = config.get('client_secret')
    username = config.get('username')
    password = config.get('password')

    application_id = config.get('application_id')
    plan_id = config.get('plan_id')

    # Kiểm tra các thông tin cần thiết đã được tải từ cấu hình
    if not all([server_manager, org_id, client_id, client_secret, username, password, application_id, plan_id]):
        logger.critical("Lỗi: Thiếu một hoặc nhiều thông tin cấu hình cần thiết để chạy ứng dụng. Vui lòng kiểm tra config.yaml và dataRun.yaml.")
        return

    logger.info(f"Đang bắt đầu quá trình đăng ký ứng dụng '{application_id}' với Plan ID '{plan_id}' trên {server_manager}...")

    # Bước 1: Lấy Bearer Token
    access_token = get_bearer_token()

    if access_token:
        logger.info("Đã có Access Token. Tiến hành đăng ký ứng dụng...")
        # Bước 2: Đăng ký ứng dụng
        subscribe_application(access_token)
    else:
        logger.error("Không thể lấy Access Token. Quá trình đăng ký bị dừng lại.")

if __name__ == "__main__":
    logger.info("Ứng dụng đăng ký API Manager đang khởi chạy...")
    run_application()
    logger.info("Ứng dụng đã kết thúc.")