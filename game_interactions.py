# RandomGenerate/SPI_v2/game_interactions.py
"""
處理遊戲核心互動邏輯，例如從感測器獲取情緒指數。
"""
import time # 可能在未來擴展時需要
from led_controller import Color # 為了在測量時設定顏色

# 這個模組本身不直接依賴硬體函式庫，而是接收已初始化的處理器物件。

def get_player_emotion_index(sensor_handler, emotion_calculator, led_controller=None, duration_sec=3):
    """
    獲取玩家的情緒指數，並在測量期間提供 LED 視覺回饋。
    
    過程:
    1. 在指定的時間段內收集壓電薄膜感測器數據
    2. 使用情緒計算器計算負面情緒指數
    
    參數:
        sensor_handler: SensorHandler 實例
        emotion_calculator: EmotionCalculator 實例
        led_controller (LedController, optional): LED 控制器實例。
        duration_sec (int): 收集數據的持續時間（秒）
    
    返回:
        int: 計算出的負面情緒指數，如果過程中出現錯誤則返回 0
    """
    # 檢查參數是否有效
    if sensor_handler is None or emotion_calculator is None:
        print("錯誤: sensor_handler 或 emotion_calculator 未初始化")
        return 0
    
    if not hasattr(sensor_handler, 'get_max_voltage_from_all_channels'):
        print("錯誤: sensor_handler 缺少必要的方法")
        return 0
    
    # 開始測量
    print(f"開始測量，請在 {duration_sec} 秒內拍打壓電薄膜...")
    
    # --- 在測量期間的 LED 效果 ---
    # 我們將在 get_max_voltage_from_all_channels 內部（或此處的迴圈）處理 LED
    # 為了簡化，這裡暫時不在感測器讀取迴圈內頻繁操作 LED，而是在開始和結束時操作。
    # 更複雜的同步動畫需要執行緒或非阻塞的感測器讀取。
    # 作為替代，我們可以在 sensor_handler 的 _read_single_channel_max_voltage 內部加入燈效更新點。
    # 或者，在 main.py 呼叫此函式前後控制燈效。
    # 目前，我們讓 main.py 在此函數調用前就設定好燈效（例如閃爍），此函數專注於獲取數據。
    # 如果要在此函數內做持續的燈效，sensor_handler.get_max_voltage_from_all_channels 需要被重構為非阻塞，
    # 或者我們在這裡重新實現一個帶有燈效更新的讀取迴圈。

    # 這裡我們採用一個簡化的方式：修改 sensor_handler 讓它可以接收 led_controller
    # 或者，更簡單的是，讓此函數 *不* 控制測量期間的連續LED動畫，
    # 而是 main.py 在呼叫此函數前後設定一個燈效，例如呼吸燈開始，然後讀取，然後呼吸燈結束。

    # 此處暫不改變 LED。測量期間的 LED 由 main.py 在呼叫此函數之前設定的燈效控制。
    # 如果 LedController 的 breathing_light 是阻塞的，main.py 需要在另一個執行緒中運行它，
    # 或者 breathing_light 需要被設計為非阻塞的（例如，只更新一幀）。
    # 假設 main.py 會處理測量開始前的燈效。

    try:
        # 獲取最大電壓值
        max_voltage = sensor_handler.get_max_voltage_from_all_channels(duration_sec=duration_sec)
        
        if max_voltage <= 0:
            print(f"測量結果: 未檢測到有效的壓力 (最大電壓: {max_voltage:.3f}V)")
            return 0
        
        print(f"測量完成! 最大電壓: {max_voltage:.3f}V")
        
        # 計算情緒指數
        emotion_index = emotion_calculator.calculate_negative_emotion_index(max_voltage)
        print(f"計算的負面情緒指數: {emotion_index}")
        
        return emotion_index
    
    except Exception as e:
        print(f"測量過程中發生錯誤: {e}")
        return 0

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    # 為了測試 get_player_emotion_index，我們需要模擬 SensorHandler 和 EmotionCalculator
    print("正在直接測試 game_interactions.py...")

    class MockSensorHandler:
        def __init__(self, mock_voltage=0.5):
            self.mock_voltage = mock_voltage
        
        def get_max_voltage_from_all_channels(self, duration_sec=3):
            print(f"模擬測量 {duration_sec} 秒...")
            time.sleep(1)  # 模擬測量時間
            return self.mock_voltage

    class MockEmotionCalculator:
        def __init__(self, multiplier=100):
            self.multiplier = multiplier
        
        def calculate_negative_emotion_index(self, voltage):
            return int(voltage * self.multiplier)

    print("\n測試案例 1: 所有模組正常")
    mock_sensor = MockSensorHandler(mock_voltage=1.25)
    mock_emotion = MockEmotionCalculator(multiplier=100)
    emotion_index1 = get_player_emotion_index(mock_sensor, mock_emotion, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index1}")

    print("\n測試案例 2: 感測器未就緒")
    mock_sensor_fail = MockSensorHandler(mock_voltage=0.0)
    emotion_index2 = get_player_emotion_index(mock_sensor_fail, mock_emotion, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index2}")

    print("\n測試案例 3: 情緒計算器未就緒")
    emotion_index3 = get_player_emotion_index(mock_sensor, None, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index3}")
    
    print("\n測試案例 4: 感測器通道未設定 (SensorHandler 內部 is_initialized=True 但 adc_channels=False)")
    mock_sensor_no_channels = MockSensorHandler(mock_voltage=0.0) # 模擬通道未設定
    # 注意：目前的 get_player_emotion_index 依賴 sensor_is_ready 旗標，
    # 而 SensorHandler.get_max_voltage_from_all_channels 內部會檢查 self.adc_channels。
    # 為了更精確地測試這種情況，需要 SensorHandler 的真實行為或更細緻的模擬。
    # 假設 sensor_is_ready 包含了 adc_channels 的檢查。
    # 如果 SensorHandler 的 is_initialized 為 True 但 adc_channels 為空，其 get_max_voltage_from_all_channels 應回傳 0.0。
    # 此處的 sensor_is_ready 應反映這一點。
    
    # 假設 sensor_is_ready 的判斷是 (sensor and sensor.is_initialized and sensor.adc_channels)
    actual_sensor_ready_flag_for_case4 = mock_sensor_no_channels.is_initialized and mock_sensor_no_channels.adc_channels
    emotion_index4 = get_player_emotion_index(mock_sensor_no_channels, mock_emotion, duration_sec=1)
    print(f"  => 最終情緒指數 (sensor_ready={actual_sensor_ready_flag_for_case4}): {emotion_index4}")


    print("\ngame_interactions.py 測試結束。")
