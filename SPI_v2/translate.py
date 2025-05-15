class Translate:
    def translate_emo(strength: float):
        """
        根據輸入的力量轉換為負面情緒值
        Args:
            strength (float): 力量值(kg)，由感測器輸入
        """
        if strength > 67:
            strength = 67
        emo = ((strength* 3.5) ** 2 + 10) * 100
        return emo

    def translate_mileage(emo: float):
        """
        根據輸入的負面情緒值轉換為里程數
        大約在力量輸入為67kg時，里程數接近350公里
        Args:
            emo (float): 負面情緒值
        """
        # 計算里程(公尺)
        mileage = ((emo * 3.5) ** 2 + 10) / 1250  
        # 將里程轉換為公里數
        mileage = round(mileage / 1000)
        return mileage
    
    def get_mileage(strength: float):
        """
        根據輸入的力量值計算里程數
        Args:
            strength (float): 力量值(kg)，由感測器輸入
        """
        emo = Translate.translate_emo(strength)
        mileage = Translate.translate_mileage(emo)
        return mileage
    