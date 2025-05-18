# RandomGenerate/SPI_v2/sensor_handler.py
import time
import board # For I2C bus SCL, SDA
import busio # For I2C
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class SensorHandler:
    """處理 ADS1115 ADC 感測器讀取的類別。"""

    def __init__(self):
        """初始化 SensorHandler。"""
        self.i2c_bus = None
        self.ads_sensor = None
        self.adc_channels = {}  # 儲存已設定的 AnalogIn 物件，以通道名稱為鍵
        self.is_initialized = False

    def initialize_ads1115(self):
        """
        初始化 I2C 匯流排和 ADS1115 感測器。
        回傳 True 表示成功，False 表示失敗。
        """
        if self.is_initialized:
            # print("ADS1115 已初始化。") # 減少重複訊息
            return True
        try:
            self.i2c_bus = busio.I2C(board.SCL, board.SDA)
            self.ads_sensor = ADS.ADS1115(self.i2c_bus)
            self.is_initialized = True
            print("SensorHandler: ADS1115 I2C 初始化成功。")
            return True
        except ValueError as ve:
            # 通常是 SCL/SDA 未正確設定或硬體未連接時引發
            print(f"SensorHandler: ADS1115 I2C 初始化失敗 (ValueError): {ve}")
            print("請檢查 SCL 和 SDA 是否已啟用，以及 ADS1115 是否正確連接。")
            self.ads_sensor = None
            self.i2c_bus = None
            self.is_initialized = False
            return False
        except Exception as e:
            print(f"SensorHandler: ADS1115 I2C 初始化時發生未預期錯誤: {e}")
            self.ads_sensor = None
            self.i2c_bus = None
            self.is_initialized = False
            return False

    def setup_adc_channels(self, channel_pins_config=None):
        """
        設定 ADS1115 的 ADC 輸入通道。

        參數:
            channel_pins_config (dict, optional):
                一個字典，鍵為通道名稱 (例如 'A0')，值為 ADS1115 的通道定義 (例如 ADS.P0)。
                預設為 {'A0': ADS.P0, 'A1': ADS.P1, 'A2': ADS.P2, 'A3': ADS.P3}。
        
        回傳 True 表示成功，False 表示失敗 (例如 ADS1115 未初始化)。
        """
        if not self.is_initialized or not self.ads_sensor:
            print("SensorHandler 錯誤: ADS1115 未初始化，無法設定 ADC 通道。")
            return False

        if channel_pins_config is None:
            channel_pins_config = {
                'A0': ADS.P0,
                'A1': ADS.P1,
                'A2': ADS.P2,
                'A3': ADS.P3
            }
        
        self.adc_channels = {} # 清除舊的通道設定
        try:
            for name, pin_definition in channel_pins_config.items():
                self.adc_channels[name] = AnalogIn(self.ads_sensor, pin_definition)
            print(f"SensorHandler: 成功設定 ADC 通道: {list(self.adc_channels.keys())}")
            return True
        except Exception as e:
            print(f"SensorHandler: 設定 ADC 通道時發生錯誤: {e}")
            self.adc_channels = {} # 設定失敗時清除
            return False

    def _read_single_channel_max_voltage(self, channel_name, duration_sec):
        """內部輔助函式，讀取指定單一通道在特定時間內的最高電壓。"""
        if channel_name not in self.adc_channels:
            # print(f"SensorHandler 錯誤: 通道 {channel_name} 未設定。") # 詳細日誌
            return 0.0

        chan_obj = self.adc_channels[channel_name]
        # print(f"開始偵測 {channel_name} 通道壓力（{duration_sec}秒內取最高電壓）...")
        start_time = time.time()
        max_voltage_on_channel = 0.0
        
        try:
            while time.time() - start_time < duration_sec:
                voltage = chan_obj.voltage
                if voltage > max_voltage_on_channel:
                    max_voltage_on_channel = voltage
                time.sleep(0.01)  # 快速取樣
        except Exception as e:
            # print(f"SensorHandler: 讀取 {channel_name} 電壓時發生錯誤: {e}") # 詳細日誌
            # 發生錯誤時，回傳目前為止偵測到的最大值，或者 0.0
            return max_voltage_on_channel 
        
        # print(f"{channel_name} 通道 {duration_sec} 秒內最高電壓：{max_voltage_on_channel:.3f} V")
        return max_voltage_on_channel

    def get_max_voltage_from_all_channels(self, duration_sec=3):
        """
        從所有已設定的 ADC 通道讀取電壓，每個通道獨立偵測指定時間內的最高電壓，
        然後回傳這些最高電壓中的最大值。

        參數:
            duration_sec (int): 每個通道的偵測持續時間 (秒)。

        回傳:
            float: 所有通道中偵測到的最高電壓值。如果沒有通道或未初始化，則回傳 0.0。
        """
        if not self.is_initialized or not self.adc_channels:
            print("SensorHandler 錯誤：ADS1115 未初始化或通道未設定，無法讀取峰值電壓。")
            return 0.0

        overall_max_voltage = 0.0
        channel_max_voltages = {}

        print(f"SensorHandler: 開始偵測 {duration_sec} 秒內各通道峰值電壓...")
        for channel_name in self.adc_channels.keys():
            voltage = self._read_single_channel_max_voltage(channel_name, duration_sec)
            channel_max_voltages[channel_name] = voltage
            if voltage > overall_max_voltage:
                overall_max_voltage = voltage
        
        # 為了簡化主控台輸出，可以選擇性地印出每個通道的詳細資訊
        for ch_name, ch_volt in channel_max_voltages.items():
            # print(f"  通道 {ch_name} 的最高電壓: {ch_volt:.3f} V") # 詳細日誌
            pass
        print(f"SensorHandler: 所有通道中偵測到的最終最高電壓為：{overall_max_voltage:.3f} V")
        return overall_max_voltage

    def check_any_piezo_trigger(self, threshold=0.1):
        """
        快速檢查是否有任何壓電薄膜被觸發 (電壓超過閾值)。
        這個方法設計為快速執行，適用於遊戲迴圈內的即時檢測。

        參數:
            threshold (float): 觸發跳躍的電壓閾值。

        回傳:
            bool: True 如果任何通道偵測到觸發，否則 False。
        """
        if not self.is_initialized or not self.adc_channels:
            # print("SensorHandler 警告: ADS1115 未就緒，無法檢查拍擊觸發。") # 可能過於頻繁
            return False
        
        for channel_name, chan_obj in self.adc_channels.items():
            try:
                # 為了速度，這裡只讀取一次電壓，不做延遲或迴圈
                voltage = chan_obj.voltage 
                if voltage > threshold:
                    # print(f"SensorHandler: 偵測到通道 {channel_name} 觸發，電壓 {voltage:.3f}V > {threshold}V") # 除錯用
                    return True
            except Exception as e:
                # print(f"SensorHandler: 檢查通道 {channel_name} 觸發時發生錯誤: {e}") # 可能過於頻繁
                # 發生錯誤時，假設此通道未觸發，繼續檢查其他通道
                continue 
        return False

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    print("SensorHandler 測試開始...")
    sensor_handler = SensorHandler()
    
    if sensor_handler.initialize_ads1115():
        # 使用預設通道設定 (A0-A3)
        if sensor_handler.setup_adc_channels():
            print("\n--- 測試 get_max_voltage_from_all_channels (3秒峰值) ---")
            input("請準備好觸發壓電感測器 (持續壓力)，然後按 Enter 鍵開始偵測...")
            max_v = sensor_handler.get_max_voltage_from_all_channels(duration_sec=3)
            print(f"  => 3秒內所有通道獲得的最高電壓是: {max_v:.3f} V")
            
            print("\n--- 測試 check_any_piezo_trigger (即時拍擊) ---")
            print(f"將在 5 秒內持續檢查是否有拍擊超過 0.1V (每 0.2 秒檢查一次)。請嘗試拍打感測器。")
            start_scan_time = time.time()
            triggered_count = 0
            while time.time() - start_scan_time < 5:
                if sensor_handler.check_any_piezo_trigger(threshold=0.1):
                    print(f"  偵測到拍擊! (第 {triggered_count + 1} 次)")
                    triggered_count += 1
                    # 可以在偵測到後短暫停止，避免同一拍擊被多次計數
                    time.sleep(0.3) # 簡易的去抖動/重複觸發延遲
                time.sleep(0.05) # 降低檢查頻率，避免過度佔用 I2C
            print(f"  5秒內共偵測到 {triggered_count} 次拍擊。")
        else:
            print("ADC 通道設定失敗。")
    else:
        print("ADS1115 初始化失敗。無法執行感測器讀取測試。")
    
    print("\n清理 GPIO (如果 system_configurator.py 的測試部分設定了)...")
    # 此處不直接呼叫 GPIO.cleanup()，因為 SensorHandler 不負責 GPIO 全域設定
    print("SensorHandler 測試結束。") 