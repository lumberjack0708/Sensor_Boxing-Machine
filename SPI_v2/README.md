# 專案名稱：互動式解壓小遊戲 (HDMI 版本)

## 概述

本專案是一款結合硬體互動的 Pygame 小遊戲，遊戲畫面運行在**外接 HDMI 顯示器**上。玩家透過按鈕啟動，系統會偵測多個壓電薄膜感測器的壓力，將其轉換為「負面情緒指數」。此指數會作為遊戲的初始「生命值」或「里程」。玩家在 HDMI 螢幕上操控角色躲避障礙物，可透過鍵盤或**拍擊壓電薄膜**來使角色跳躍，目標是消耗完「負面情緒指數」或在指數歸零前生存下來。

一個小型的 **SPI LCD 螢幕** 用於顯示遊戲的最終結果、情緒值以及系統狀態提示。
LED 燈條提供視覺回饋：待機時顯示彩虹動畫，按鈕按下時有閃爍提示。系統也會根據不同遊戲階段播放對應的背景音樂，增強遊戲體驗。

## 檔案結構樹狀圖 (SPI_v2 目錄下)

```
RandomGenerate/SPI_v2/
├── main.py                     # 主程式入口，協調各模組運作
├── system_configurator.py      # 硬體與模組初始化設定
├── led_controller.py           # LED 燈條控制模組
├── sensor_handler.py           # ADS1115 ADC 感測器處理模組
├── emotion_calculator.py       # 負面情緒指數計算模組
├── hdmi_game_engine.py         # HDMI 螢幕上的 Pygame 遊戲邏輯引擎
├── spi_lcd_display.py          # SPI LCD 顯示控制器 (用於顯示結果和狀態)
├── game_interactions.py        # 處理使用者互動觸發的遊戲核心邏輯 (如情緒指數獲取)
├── music_player.py             # 音樂播放器模組
├── player.png                  # 玩家角色圖片
├── obstacle.png                # 障礙物圖片
├── (其他可能的 .py 檔案或 __pycache__)
└── README.md                   # 本說明檔案
```

## 模組功能說明

1.  **`main.py`**: 
    *   **功能**: 整個應用程式的最高層控制流程和主迴圈。
    *   **職責**:
        *   呼叫 `system_configurator.initialize_systems()` 初始化所有模組。
        *   管理主事件迴圈，監聽按鈕輸入和處理程式退出。
        *   協調 `LedController` (待機動畫、提示) 和 `MusicPlayer` (各階段音樂)。
        *   按鈕按下後，呼叫 `game_interactions.get_player_emotion_index()` 獲取情緒指數。
        *   呼叫 `HdmiGameEngine.run_game()` 在 HDMI 螢幕上運行遊戲。
        *   遊戲結束後，從 `HdmiGameEngine` 獲取結果，並呼叫 `SpiLcdDisplay.display_game_results()` 在 LCD 上顯示。
        *   使用 `SpiLcdDisplay` 顯示系統狀態提示 (如 "測量中", "待機")。
        *   執行最終資源清理。

2.  **`system_configurator.py`**: 
    *   **功能**: 集中管理所有硬體腳位定義、模組參數設定，並負責初始化所有核心模組。
    *   **職責**:
        *   包含所有硬體相關的常數 (GPIO 腳位、LED、SPI LCD、感測器、HDMI 遊戲參數)。
        *   匯入並實例化 `LedController`, `SensorHandler`, `EmotionCalculator`, `HdmiGameEngine`, `SpiLcdDisplay`, `MusicPlayer`。
        *   執行這些物件的初始設定。
        *   回傳一個包含所有初始化模組的字典給 `main.py`。
        *   提供 `cleanup_systems()` 函數統一清理資源。

3.  **`led_controller.py`**: 
    *   **功能**: 封裝對 WS281x LED 燈條的控制邏輯。
    *   **主要類別**: `LedController`
    *   **方法**:
        *   `__init__`, `begin`: 初始化與啟動 LED 燈條。
        *   `update_rainbow_cycle_frame`: 更新彩虹循環動畫，支援外部控制動畫偏移。
        *   `reset_rainbow_animation_state`: 重設彩虹動畫狀態。
        *   `clear`: 關閉所有 LED。
        *   `show_flash_pattern`: 顯示閃爍燈效。
        *   `set_brightness`: 設定 LED 亮度。

4.  **`sensor_handler.py`**: 
    *   **功能**: 處理 ADS1115 ADC 的初始化和資料讀取。
    *   **主要類別**: `SensorHandler`
    *   **方法**:
        *   `initialize_ads1115`, `setup_adc_channels`: 初始化 I2C、ADS1115 及 ADC 通道。
        *   `get_max_voltage_from_all_channels`: 從所有設定通道讀取並回傳**峰值**電壓。
        *   **`check_any_piezo_trigger`**: 快速檢查是否有任何壓電薄膜通道的**即時電壓**超過指定閾值，用於遊戲中的拍擊跳躍偵測。

5.  **`emotion_calculator.py`**: 
    *   **功能**: 根據電壓值計算「負面情緒指數」。
    *   **主要類別**: `EmotionCalculator`
    *   **方法**:
        *   `__init__`: 設定計算參數 (電壓閾值、情緒上限)。
        *   `calculate_negative_emotion_index`: 執行情緒指數計算。

6.  **`hdmi_game_engine.py`**: 
    *   **功能**: 控制在 HDMI 外接螢幕上運行的 Pygame 小遊戲。
    *   **主要類別**: `HdmiGameEngine`
    *   **方法**:
        *   `__init__`: 初始化 Pygame 視窗 (HDMI 解析度)、載入遊戲資源 (圖片、字型)、設定遊戲參數。
        *   `run_game`: 啟動並運行一局完整的遊戲。處理遊戲邏輯 (玩家移動、跳躍、障礙物生成/移動、碰撞偵測、分數計算)、繪圖到 HDMI 螢幕、處理使用者輸入 (鍵盤、拍擊跳躍)。遊戲結束後返回結果字典。
        *   `_game_over_screen_on_hdmi`: 在 HDMI 上顯示遊戲結束畫面及重玩/離開選項。
        *   `cleanup`: 遊戲引擎相關的清理 (通常 pygame.quit 由 main 處理)。

7.  **`spi_lcd_display.py`**: 
    *   **功能**: 控制 ILI9341 SPI LCD 螢幕，專門用於顯示文字訊息。
    *   **主要類別**: `SpiLcdDisplay`
    *   **方法**:
        *   `__init__`: 初始化 SPI LCD 硬體、載入 PIL 字型。
        *   `display_message`: 在 LCD 上顯示多行文字。
        *   `display_game_results`: 格式化顯示遊戲的最終得分、情緒等。
        *   `show_standby_message`: 顯示待機或狀態提示訊息。
        *   `clear_display`: 清除 LCD 螢幕。
        *   `cleanup`: 關閉 LCD 背光等。

8.  **`game_interactions.py`**: 
    *   **功能**: 封裝由使用者互動觸發的、涉及多個模組協作的核心遊戲準備邏輯。
    *   **主要函式**: `get_player_emotion_index()`
    *   **職責**:
        *   接收 `SensorHandler` 和 `EmotionCalculator` 的實例。
        *   協調從感測器讀取最大電壓的過程。
        *   將獲取的電壓傳遞給情緒計算器以得到「負面情緒指數」。
        *   回傳計算出的情緒指數給呼叫者 (`main.py`)。

9.  **`music_player.py`**: 
    *   **功能**: 控制遊戲中的背景音樂播放。
    *   **主要類別**: `MusicPlayer`
    *   **方法**:
        *   `__init__`: 初始化音樂播放器、設定不同類別的音樂路徑。
        *   `play_random_music`: 從指定類別中隨機選擇一首音樂播放。
        *   `switch_to_category`: 切換到指定類別的音樂。
        *   `pause`, `unpause`, `stop`, `fade_out`: 控制音樂播放狀態。
        *   `set_volume`: 調整音樂音量。
        *   `cleanup`: 清理音樂資源。

## 硬體需求與接線 (概要)

*   **Raspberry Pi**: 作為主控制器。
*   **HDMI 顯示器**: 用於顯示主遊戲畫面。
*   **ILI9341 SPI LCD 顯示器**: 用於顯示遊戲結果和狀態提示。
*   **WS281x LED 燈條**: 用於視覺回饋。
*   **按鈕**: 一個實體按鈕，用於觸發遊戲開始。
*   **壓電薄膜感測器 (x4)**: 用於偵測壓力。
*   **ADS1115 ADC 模組**: 將類比訊號轉換為數位訊號。
*   **揚聲器或耳機**: 用於播放背景音樂。

*具體腳位定義及拍擊跳躍閾值請參考 `system_configurator.py` 頂部的常數設定。*

## 操作流程

1.  **連接硬體**: 確保所有硬體元件 (包括 HDMI 顯示器和 SPI LCD) 已正確連接。
2.  **環境設定**: 
    *   確保已安裝必要的 Python 函式庫：`pygame`, `RPi.GPIO`, `adafruit-circuitpython-ads1x15`, `rpi_ws281x`, `Pillow`, `adafruit-circuitpython-rgb-display`。
    *   啟用 Raspberry Pi 上的 I2C 和 SPI 介面。
    *   確認音樂檔案路徑及遊戲圖片路徑在 `system_configurator.py` 中設定正確。
3.  **執行程式**: 
    *   導航到 `RandomGenerate/SPI_v2/` 目錄。
    *   執行主程式：`python3 main.py`
4.  **程式啟動**: 
    *   主控台會顯示各模組的初始化訊息。
    *   LED 燈條進入彩虹待機動畫。
    *   SPI LCD 顯示待機訊息 (如 "按鈕啟動")。
    *   播放預設背景音樂。
5.  **開始測量情緒**: 
    *   按下按鈕。
    *   LED 燈條閃爍提示，音樂淡出。
    *   SPI LCD 顯示 "測量情緒中..."。
    *   系統開始偵測壓電薄膜壓力以計算「負面情緒指數」。
6.  **遊戲開始準備**: 
    *   情緒指數測量完成後，SPI LCD 會短暫顯示獲取的情緒值。
    *   若情緒指數達標，切換到遊戲音樂。
7.  **進行遊戲 (HDMI 螢幕)**: 
    *   遊戲主畫面在 HDMI 顯示器上啟動。
    *   玩家使用鍵盤或拍擊壓電薄膜控制角色跳躍。
    *   遊戲目標是消耗「負面情緒里程」。
8.  **遊戲結束 (HDMI 螢幕)**: 
    *   遊戲結束條件達成後 (撞到障礙物或情緒里程歸零)，HDMI 螢幕顯示遊戲結束畫面，並提供**重玩 (R)** 或 **離開 (Q)** 選項。
    *   切換到遊戲結束音樂。
9.  **顯示結果 (SPI LCD)**: 
    *   無論玩家在 HDMI 上選擇重玩還是離開，SPI LCD 都會顯示本局的最終結果 (得分、剩餘情緒、結束原因)。
    *   等待數秒讓玩家查看。
10. **返回待機 / 重玩**: 
    *   如果玩家在 HDMI 上選擇離開遊戲會話，或遊戲結束後流程自然結束，系統返回待機狀態：
        *   LED 恢復彩虹動畫。
        *   SPI LCD 顯示待機訊息。
        *   切換回預設背景音樂。
    *   如果玩家選擇重玩，則直接在 HDMI 上開始新的一局 (使用相同的初始情緒值)。SPI LCD 可能不會更新，直到該局遊戲也結束。
11. **結束程式**: 
    *   在主控台按 `Ctrl+C` 中斷程式。

## 注意事項

*   確保 `player.png` 和 `obstacle.png` 圖片檔案位於 `RandomGenerate/SPI_v2/` 目錄下。
*   仔細檢查 `system_configurator.py` 中的所有硬體腳位和參數設定。
*   拍擊跳躍的靈敏度 (電壓閾值) 可在 `system_configurator.py` 中調整。
*   音樂檔案路徑設定位於 `system_configurator.py` 中的 `MUSIC_DIRECTORIES` 常數，可根據需要調整。
*   如需添加新的音樂類別(如遊戲開始時、勝利時等)，可以在 `MUSIC_DIRECTORIES` 中增加對應的類別和音樂檔案路徑。 