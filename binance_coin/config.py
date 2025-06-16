# my_app_project/my_app/config.py

import os
import yaml
import logging

# Thiết lập logging cơ bản để hiển thị thông báo lỗi/thông tin
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Đường dẫn đến thư mục gốc của project
# os.path.dirname(__file__) là thư mục của file config.py (my_app/)
# os.path.abspath(...) để lấy đường dẫn tuyệt đối
# os.path.join(...) để nối đường dẫn an toàn
# os.pardir là '..' để đi lên một cấp thư mục (từ my_app/ đến my_app_project/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

APP_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.yaml')
DATA_RUN_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'dataRun.yaml')

class AppConfig:
    """
    Class để quản lý và truy cập các cài đặt cấu hình.
    Sử dụng Singleton pattern để đảm bảo chỉ có một thể hiện của cấu hình được tải.
    """
    _instance = None
    _config_data: dict = {} # Sẽ chứa dữ liệu cấu hình đã tải

    def __new__(cls) -> 'AppConfig':
        """Đảm bảo chỉ có một thể hiện (instance) của AppConfig."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_configs() # Tải cấu hình khi instance được tạo lần đầu
        return cls._instance

    def _load_configs(self):
        """
        Tải cấu hình từ config.yaml và dataRun.yaml.
        Ưu tiên các giá trị trong dataRun.yaml nếu có trùng lặp.
        """
        app_config = {}
        data_run_config = {}

        # Tải config.yaml
        if os.path.exists(APP_CONFIG_PATH):
            try:
                with open(APP_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    app_config = yaml.safe_load(f) or {} # Đảm bảo là dict rỗng nếu file trống
                logging.info(f"Đã tải cấu hình chung từ: {APP_CONFIG_PATH}")
            except yaml.YAMLError as e:
                logging.error(f"Lỗi khi đọc file cấu hình chung '{APP_CONFIG_PATH}': {e}")
            except IOError as e:
                logging.error(f"Không thể mở file cấu hình chung '{APP_CONFIG_PATH}': {e}")
        else:
            logging.warning(f"Không tìm thấy file cấu hình chung: '{APP_CONFIG_PATH}'. Tiếp tục mà không có.")

        # Tải dataRun.yaml
        if os.path.exists(DATA_RUN_CONFIG_PATH):
            try:
                with open(DATA_RUN_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data_run_config = yaml.safe_load(f) or {} # Đảm bảo là dict rỗng nếu file trống
                logging.info(f"Đã tải cấu hình chạy từ: {DATA_RUN_CONFIG_PATH}")
            except yaml.YAMLError as e:
                logging.error(f"Lỗi khi đọc file cấu hình chạy '{DATA_RUN_CONFIG_PATH}': {e}")
            except IOError as e:
                logging.error(f"Không thể mở file cấu hình chạy '{DATA_RUN_CONFIG_PATH}': {e}")
        else:
            logging.warning(f"Không tìm thấy file cấu hình chạy: '{DATA_RUN_CONFIG_PATH}'. Tiếp tục mà không có.")


        # Hợp nhất các cấu hình: dataRun.yaml sẽ ghi đè appConfig.yaml nếu có key trùng
        # Sử dụng copy() và update() để tránh sửa đổi trực tiếp các dict gốc
        combined_config = app_config.copy()
        combined_config.update(data_run_config)

        self._config_data = combined_config

    def get(self, key: str, default=None):
        """
        Lấy giá trị cấu hình theo key.
        :param key: Tên của cấu hình (ví dụ: 'server_manager', 'client_id').
        :param default: Giá trị mặc định nếu key không tồn tại.
        :return: Giá trị cấu hình hoặc giá trị mặc định.
        """
        return self._config_data.get(key, default)

    def get_all(self) -> dict:
        """Trả về toàn bộ dữ liệu cấu hình đã tải."""
        return self._config_data.copy() # Trả về bản sao để tránh thay đổi từ bên ngoài

# Khởi tạo instance của cấu hình ngay lập tức khi module này được import
# Điều này đảm bảo cấu hình được tải một lần duy nhất
config = AppConfig()

# Ví dụ về cách kiểm tra cấu hình khi module này được chạy trực tiếp
if __name__ == '__main__':
    logging.info("Đang kiểm tra module config.py...")
    logging.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
    logging.info(f"APP_CONFIG_PATH: {APP_CONFIG_PATH}")
    logging.info(f"DATA_RUN_CONFIG_PATH: {DATA_RUN_CONFIG_PATH}")

    # Truy cập cấu hình thông qua instance 'config'
    logging.info(f"\nServer Manager: {config.get('server_manager')}")
    logging.info(f"Org ID: {config.get('org_id')}")
    logging.info(f"Application ID: {config.get('application_id')}")
    logging.info(f"Plan ID: {config.get('plan_id')}")
    logging.info(f"Client Secret: {config.get('client_secret')}") # Cẩn thận khi in thông tin nhạy cảm
    logging.info(f"Giá trị không tồn tại (mặc định): {config.get('non_existent_key', 'DEFAULT_VALUE')}")

    logging.info("\nToàn bộ cấu hình đã tải:")
    import pprint
    pprint.pprint(config.get_all())