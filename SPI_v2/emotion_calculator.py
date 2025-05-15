# RandomGenerate/SPI_v2/emotion_calculator.py

class EmotionCalculator:
    """根據輸入電壓計算【負面情緒指數】的類別。"""

    def __init__(self, min_voltage_threshold=0.01, max_emotion_value=1000):
        """
        初始化情緒計算器。

        參數:
            min_voltage_threshold (float): 低於此電壓值時，情緒指數視為 0。
            max_emotion_value (int): 情緒指數的上限值。
        """
        self.min_voltage_threshold = min_voltage_threshold
        self.max_emotion_value = max_emotion_value

    def calculate_negative_emotion_index(self, voltage):
        """
        根據輸入電壓計算負面情緒指數。
        沿用 VoltageSensing_a3.py 中的原始公式，並套用閾值和上限。
        公式: emo = ((voltage * 5) ** 2) * 100

        參數:
            voltage (float): 從感測器讀取到的最高電壓值。

        回傳:
            int: 計算得到的負面情緒指數。
        """
        if voltage < self.min_voltage_threshold:
            # print(f"電壓 {voltage:.3f} V 低於閾值 {self.min_voltage_threshold:.3f} V，情緒指數為 0。")
            return 0
        
        # 原始公式計算
        raw_emotion_value = ((voltage * 5) ** 2) * 100
        
        # 套用上限
        calculated_emotion_index = min(raw_emotion_value, self.max_emotion_value)
        
        # print(f"輸入電壓: {voltage:.3f} V -> 原始計算情緒值: {raw_emotion_value:.0f} -> 校正後 (上限 {self.max_emotion_value}): {calculated_emotion_index:.0f}")
        return int(calculated_emotion_index)

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    calculator = EmotionCalculator(min_voltage_threshold=0.02, max_emotion_value=800)
    
    test_voltages = [0.005, 0.01, 0.02, 0.1, 0.195, 0.5, 1.0, 1.5, 2.0, 3.3]
    
    print(f"情緒計算器測試 (閾值={calculator.min_voltage_threshold}V, 上限={calculator.max_emotion_value}):")
    for v in test_voltages:
        emotion_index = calculator.calculate_negative_emotion_index(v)
        print(f"  電壓: {v:>5.3f} V  =>  負面情緒指數: {emotion_index:>5d}")

    # 測試 VoltageSensing_a3.py 中的一個例子
    # voltage_a3_example = 0.195 # 假設這是讀到的值
    # emo_a3_original_calc = ((voltage_a3_example * 5)**2) * 100
    # print(f"\n比較 VoltageSensing_a3.py 的例子 (電壓={voltage_a3_example}V):")
    # print(f"  原始計算 (無上限/閾值): {emo_a3_original_calc:.0f}")
    # print(f"  使用 EmotionCalculator: {calculator.calculate_negative_emotion_index(voltage_a3_example)}") 