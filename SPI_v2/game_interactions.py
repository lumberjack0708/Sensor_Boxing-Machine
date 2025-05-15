# RandomGenerate/SPI_v2/game_interactions.py
"""
處理遊戲核心互動邏輯，例如從感測器獲取情緒指數。
"""
import time # 可能在未來擴展時需要

# 這個模組本身不直接依賴硬體函式庫，而是接收已初始化的處理器物件。

def get_player_emotion_index(sensor_handler_instance, emotion_calculator_instance, 
                             sensor_is_ready, emotion_calc_is_ready, duration_sec=3):
    """
    從感測器獲取電壓，計算並回傳「負面情緒指數」。

    參數:
        sensor_handler_instance: 已初始化的 SensorHandler 物件。
        emotion_calculator_instance: 已初始化的 EmotionCalculator 物件。
        sensor_is_ready (bool): 感測器是否已準備好讀取。
        emotion_calc_is_ready (bool): 情緒計算器是否已準備好。
        duration_sec (int): 感測器讀取持續時間 (秒)。

    回傳:
        int: 計算得到的負面情緒指數。如果無法計算則回傳 0。
    """
    print("遊戲互動：開始偵測使用者力量以計算情緒指數...")
    
    overall_highest_voltage = 0.0
    if sensor_is_ready and sensor_handler_instance:
        # print("呼叫感測器讀取...") # 詳細日誌
        overall_highest_voltage = sensor_handler_instance.get_max_voltage_from_all_channels(duration_sec=duration_sec)
        # sensor_handler_instance.get_max_voltage_from_all_channels 內部已有print
    else:
        print("遊戲互動警告：感測器未就緒或未提供，將使用 0.0V 作為電壓輸入。")
    
    negative_emotion_index = 0
    if emotion_calc_is_ready and emotion_calculator_instance:
        negative_emotion_index = emotion_calculator_instance.calculate_negative_emotion_index(overall_highest_voltage)
        print(f"遊戲互動：計算出的【負面情緒指數】為: {negative_emotion_index}")
    else:
        print("遊戲互動警告：情緒計算器未就緒或未提供，無法計算情緒指數。將回傳 0。")
        # negative_emotion_index 保持為 0
        
    return negative_emotion_index

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    # 為了測試 get_player_emotion_index，我們需要模擬 SensorHandler 和 EmotionCalculator
    print("正在直接測試 game_interactions.py...")

    class MockSensorHandler:
        def __init__(self, is_ready_val=True, adc_channels_val=True):
            self.is_initialized = is_ready_val
            self.adc_channels = adc_channels_val # 模擬通道已設定
        def get_max_voltage_from_all_channels(self, duration_sec):
            print(f"  (模擬 SensorHandler) 正在讀取電壓 {duration_sec} 秒...")
            # 模擬一個隨機但合理的電壓值
            import random
            mock_voltage = random.uniform(0.05, 0.5) 
            print(f"  (模擬 SensorHandler) 所有通道中偵測到的最終最高電壓為：{mock_voltage:.3f} V")
            return mock_voltage

    class MockEmotionCalculator:
        def __init__(self, min_v=0.01, max_emo=1000):
            self.min_voltage_threshold = min_v
            self.max_emotion_value = max_emo
        def calculate_negative_emotion_index(self, voltage):
            if voltage < self.min_voltage_threshold:
                return 0
            raw_emotion_value = ((voltage * 5) ** 2) * 100
            calculated_emotion_index = min(raw_emotion_value, self.max_emotion_value)
            return int(calculated_emotion_index)

    print("\n測試案例 1: 所有模組正常")
    mock_sensor_ok = MockSensorHandler()
    mock_emotion_ok = MockEmotionCalculator()
    emotion_index1 = get_player_emotion_index(mock_sensor_ok, mock_emotion_ok, True, True, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index1}")

    print("\n測試案例 2: 感測器未就緒")
    mock_sensor_fail = MockSensorHandler(is_ready_val=False)
    emotion_index2 = get_player_emotion_index(mock_sensor_fail, mock_emotion_ok, False, True, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index2}")

    print("\n測試案例 3: 情緒計算器未就緒")
    emotion_index3 = get_player_emotion_index(mock_sensor_ok, None, True, False, duration_sec=1)
    print(f"  => 最終情緒指數: {emotion_index3}")
    
    print("\n測試案例 4: 感測器通道未設定 (SensorHandler 內部 is_initialized=True 但 adc_channels=False)")
    mock_sensor_no_channels = MockSensorHandler(is_ready_val=True, adc_channels_val=False) # 模擬通道未設定
    # 注意：目前的 get_player_emotion_index 依賴 sensor_is_ready 旗標，
    # 而 SensorHandler.get_max_voltage_from_all_channels 內部會檢查 self.adc_channels。
    # 為了更精確地測試這種情況，需要 SensorHandler 的真實行為或更細緻的模擬。
    # 假設 sensor_is_ready 包含了 adc_channels 的檢查。
    # 如果 SensorHandler 的 is_initialized 為 True 但 adc_channels 為空，其 get_max_voltage_from_all_channels 應回傳 0.0。
    # 此處的 sensor_is_ready 應反映這一點。
    
    # 假設 sensor_is_ready 的判斷是 (sensor and sensor.is_initialized and sensor.adc_channels)
    actual_sensor_ready_flag_for_case4 = mock_sensor_no_channels.is_initialized and mock_sensor_no_channels.adc_channels
    emotion_index4 = get_player_emotion_index(mock_sensor_no_channels, mock_emotion_ok, actual_sensor_ready_flag_for_case4, True, duration_sec=1)
    print(f"  => 最終情緒指數 (sensor_ready={actual_sensor_ready_flag_for_case4}): {emotion_index4}")


    print("\ngame_interactions.py 測試結束。")
