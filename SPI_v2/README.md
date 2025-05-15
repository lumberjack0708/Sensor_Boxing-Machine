# 專案名稱：互動式解壓小遊戲

## 概述

本專案是一款結合硬體互動的 Pygame 小遊戲。玩家透過按鈕啟動，系統會偵測多個壓電薄膜感測器的壓力，將其轉換為「負面情緒指數」。此指數會作為遊戲的初始「生命值」或「里程」。玩家在 LCD 螢幕上操控角色躲避障礙物，目標是消耗完「負面情緒指數」或在指數歸零前生存下來。

LED 燈條提供視覺回饋：待機時顯示彩虹動畫，按鈕按下時有閃爍提示。

## 檔案結構樹狀圖 (SPI_v2 目錄下)

```
RandomGenerate/SPI_v2/
├── main.py                     # 主程式入口，協調各模組運作
├── system_configurator.py      # 硬體與模組初始化設定
├── led_controller.py           # LED 燈條控制模組
├── sensor_handler.py           # ADS1115 ADC 感測器處理模組
├── emotion_calculator.py       # 負面情緒指數計算模組
├── game_on_lcd.py              # LCD 顯示與遊戲邏輯控制模組
├── game_interactions.py        # 處理使用者互動觸發的遊戲核心邏輯 (如情緒指數獲取)
├── player.png                  # 玩家角色圖片
├── obstacle.png                # 障礙物圖片
├── (其他可能的 .py 檔案或 __pycache__)
└── README.md                   # 本說明檔案
```

## 模組功能說明

1.  **`main.py`**: 
    *   **功能**: 整個應用程式的最高層控制流程和主迴圈。
    *   **職責**:
        *   呼叫 `system_configurator.initialize_systems()` 來初始化所有硬體和軟體模組。
        *   管理主事件迴圈，監聽按鈕輸入和處理程式退出。
        *   根據系統狀態協調 `LedController` 的行為 (例如，待機動畫、按鈕提示)。
        *   在按鈕按下後，呼叫 `game_interactions.get_player_emotion_index()` 來獲取「負面情緒指數」。
        *   根據獲取的情緒指數，決定是否呼叫 `LcdGameController` 的 `play_game` 方法來啟動遊戲。
        *   處理遊戲結束後的流程，使系統返回待機狀態。
        *   在程式結束時執行最終的資源清理 (GPIO, Pygame)。

2.  **`system_configurator.py`**: 
    *   **功能**: 集中管理所有硬體腳位定義、模組參數設定，並負責初始化所有核心模組。
    *   **主要函式**: `initialize_systems()`
    *   **職責**:
        *   包含所有硬體相關的常數 (如 GPIO 腳位、LED 設定、LCD 設定、感測器參數)。
        *   匯入並實例化 `LedController`, `SensorHandler`, `EmotionCalculator`, `LcdGameController`。
        *   執行這些物件的初始設定 (例如 `led_controller.begin()`, `sensor_handler.initialize_ads1115()`, `lcd_game_controller` 的顯示器設定)。
        *   回傳所有初始化完成的物件實例給 `main.py`。

3.  **`led_controller.py`**: 
    *   **功能**: 封裝對 WS281x LED 燈條的控制邏輯。
    *   **主要類別**: `LedController`
    *   **方法**:
        *   `__init__`, `begin`: 初始化與啟動 LED 燈條。
        *   `update_rainbow_cycle_frame`: 更新彩虹循環動畫。
        *   `reset_rainbow_animation_state`: 重設彩虹動畫狀態。
        *   `clear`: 關閉所有 LED。
        *   `show_flash_pattern`: 顯示閃爍燈效。
        *   `set_brightness`: 設定 LED 亮度。

4.  **`sensor_handler.py`**: 
    *   **功能**: 處理 ADS1115 ADC 的初始化和資料讀取。
    *   **主要類別**: `SensorHandler`
    *   **方法**:
        *   `initialize_ads1115`, `setup_adc_channels`: 初始化 I2C、ADS1115 及 ADC 通道。
        *   `get_max_voltage_from_all_channels`: 從所有設定通道讀取並回傳最高電壓值。

5.  **`emotion_calculator.py`**: 
    *   **功能**: 根據電壓值計算「負面情緒指數」。
    *   **主要類別**: `EmotionCalculator`
    *   **方法**:
        *   `__init__`: 設定計算參數 (電壓閾值、情緒上限)。
        *   `calculate_negative_emotion_index`: 執行情緒指數計算。

6.  **`game_on_lcd.py`**: 
    *   **功能**: 控制 ILI9341 SPI LCD 顯示，並在其上運行遊戲。
    *   **主要類別**: `LcdGameController`
    *   **方法**:
        *   `__init__`: 初始化 LCD、載入遊戲資源 (圖片、字型)、初始化 Pygame。
        *   `play_game`: 啟動並運行一局完整的遊戲，處理遊戲邏輯、繪圖和使用者輸入。
        *   `_game_over_screen`: 顯示遊戲結束畫面及訊息。
        *   `cleanup`: 關閉 LCD 背光等。

7.  **`game_interactions.py`**: 
    *   **功能**: 封裝由使用者互動觸發的、涉及多個模組協作的核心遊戲準備邏輯。
    *   **主要函式**: `get_player_emotion_index()`
    *   **職責**:
        *   接收 `SensorHandler` 和 `EmotionCalculator` 的實例。
        *   協調從感測器讀取最大電壓的過程。
        *   將獲取的電壓傳遞給情緒計算器以得到「負面情緒指數」。
        *   回傳計算出的情緒指數給呼叫者 (`main.py`)。

## 硬體需求與接線 (概要)

*   **Raspberry Pi**: 作為主控制器。
*   **WS281x LED 燈條**: 用於視覺回饋。
*   **按鈕**: 一個實體按鈕，用於觸發遊戲開始。
*   **壓電薄膜感測器 (x4)**: 用於偵測壓力。
*   **ADS1115 ADC 模組**: 將類比訊號轉換為數位訊號，透過 I2C 與 Raspberry Pi 通訊。
*   **ILI9341 SPI LCD 顯示器**: 用於顯示遊戲畫面。

*具體腳位定義請參考 `system_configurator.py` 頂部的常數設定。*

## 操作流程

1.  **連接硬體**: 確保所有硬體元件已按照 `system_configurator.py` 中的腳位設定正確連接到 Raspberry Pi。
2.  **環境設定**: 
    *   確保已安裝必要的 Python 函式庫：`pygame`, `RPi.GPIO`, `adafruit-circuitpython-ads1x15`, `rpi_ws281x`, `Pillow`, `adafruit-circuitpython-rgb-display`。
    *   (可能需要) 啟用 Raspberry Pi 上的 I2C 和 SPI 介面 (`sudo raspi-config`)。
3.  **執行程式**: 
    *   導航到 `RandomGenerate/SPI_v2/` 目錄。
    *   執行主程式：`python3 main.py`
4.  **程式啟動**: 
    *   主控台會顯示各模組的初始化訊息。
    *   LED 燈條會進入彩虹動畫的待機模式。
5.  **開始遊戲**: 
    *   按下按鈕。
    *   LED 燈條會閃爍提示。
    *   系統開始偵測壓電薄膜在 3 秒內的最高壓力，並轉換為「負面情緒指數」。
6.  **進行遊戲**: 
    *   若情緒指數達標，LCD 螢幕上啟動遊戲。
    *   使用鍵盤**空格鍵**或**向上箭頭**跳躍。
7.  **遊戲結束**: 
    *   **撞到障礙物**: LCD 顯示「你很菜」。
    *   **情緒里程歸零**: LCD 顯示「恭喜脫離苦海」。
    *   可按 **R 鍵**重玩或 **Q 鍵**退出 LCD 遊戲會話。
8.  **返回待機**: 
    *   結束 LCD 遊戲會話後，程式返回待機模式。
9.  **結束程式**: 
    *   在主控台按 `Ctrl+C` 中斷程式。

## 注意事項

*   確保 `player.png` 和 `obstacle.png` 圖片檔案位於 `RandomGenerate/SPI_v2/` 目錄下，或根據 `system_configurator.py` 中的路徑設定調整。
*   仔細檢查 `system_configurator.py` 中的硬體腳位設定。


</rewritten_file> 