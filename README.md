# 專案名稱：互動式解壓小遊戲 (HDMI 版本)

## 概述

本專案是一款結合硬體互動的 Pygame 小遊戲，遊戲畫面運行在**外接 HDMI 顯示器**上。玩家透過按鈕啟動，系統會偵測多個壓電薄膜感測器的壓力，將其轉換為「負面情緒指數」。此指數會作為遊戲的初始「生命值」或「里程」。玩家在 HDMI 螢幕上操控角色躲避障礙物，可透過鍵盤或**拍擊壓電薄膜**來使角色跳躍，目標是消耗完「負面情緒指數」或在指數歸零前生存下來。

一個小型的 **SPI LCD 螢幕** 用於顯示遊戲的最終結果、情緒值以及系統狀態提示。
LED 燈條提供視覺回饋：待機時顯示彩虹動畫，按鈕按下時有閃爍提示。系統也會根據不同遊戲階段播放對應的背景音樂，增強遊戲體驗。

## 檔案結構樹狀圖

```
RandomGenerate/
├── main.py                     # 主程式入口，協調各模組運作
├── system_configurator.py      # 硬體與模組初始化設定檔
├── led_controller.py           # LED 燈條控制模組
├── sensor_handler.py           # ADS1115 ADC 感測器處理模組
├── emotion_calculator.py       # 負面情緒指數計算模組
├── hdmi_game_engine.py         # HDMI 螢幕上的 Pygame 遊戲邏輯引擎
├── spi_lcd_display.py          # SPI LCD 顯示控制器 (用於顯示結果和狀態)
├── game_interactions.py        # 處理使用者互動觸發的遊戲核心邏輯 (如情緒指數獲取)
├── music_player.py             # 音樂播放器模組
├── player.png                  # 玩家角色圖片
├── obstacle.png                # 障礙物圖片
├── requirements.txt            # Python 函式庫依賴列表
├── README.md                   # 本說明檔案
├── Start_Order.md              # 範例啟動指令說明
├── animation.py                # (工具) Rich Console 動畫展示 (通常不直接參與主遊戲流程)
└── ... (其他設定檔、測試檔或快取檔)
```
## 專案總覽
| 語言       | 檔案數 | 空白行 | 註解行 | 程式碼行數 |
|------------|--------|--------|--------|-------------|
| Python     | 22     | 433    | 551    | 2051        |
| Markdown   | 2      | 24     | 0      | 177         |
| JSON       | 3      | 0      | 0      | 101         |
| Text       | 1      | 0      | 0      | 30          |
| **總計**   | 28     | 457    | 551    | **2359**    |

## 模組功能說明

1.  **[`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py)**:
    *   **功能**: 整個應用程式的最高層控制流程和主迴圈。
    *   **職責**:
        *   呼叫 [`system_configurator.initialize_systems()`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 初始化所有模組。
        *   管理主事件迴圈，監聽按鈕 ([`BUTTON_PIN`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)) 輸入和處理程式退出 (Ctrl+C)。
        *   協調 [`LedController`](g:\CodeBase\Sensor_Boxing-Machine\led_controller.py) (待機動畫、提示) 和 [`MusicPlayer`](g:\CodeBase\Sensor_Boxing-Machine\music_player.py) (各階段音樂)。
        *   按鈕按下後，呼叫 [`game_interactions.get_player_emotion_index()`](g:\CodeBase\Sensor_Boxing-Machine\game_interactions.py) 獲取情緒指數。
        *   呼叫 [`HdmiGameEngine.run_game()`](g:\CodeBase\Sensor_Boxing-Machine\hdmi_game_engine.py) 在 HDMI 螢幕上運行遊戲。
        *   遊戲結束後，從 `HdmiGameEngine` 獲取結果，並呼叫 [`SpiLcdDisplay.display_game_results()`](g:\CodeBase\Sensor_Boxing-Machine\spi_lcd_display.py) 在 LCD 上顯示。
        *   使用 `SpiLcdDisplay` 顯示系統狀態提示 (如 "測量中", "待機")。
        *   執行最終資源清理，呼叫 [`system_configurator.cleanup_systems()`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、`GPIO.cleanup()` 和 `pygame.quit()`。

2.  **[`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)**:
    *   **功能**: 集中管理所有硬體腳位定義、模組參數設定，並負責初始化所有核心模組。
    *   **職責**:
        *   包含所有硬體相關的常數 (GPIO 腳位如 [`BUTTON_PIN`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、LED 設定如 [`LED_PIN`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py), [`LED_COUNT`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、SPI LCD 腳位如 [`LCD_CS_PIN`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、感測器設定如 [`PIEZO_CHANNELS`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py), [`PIEZO_JUMP_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、HDMI 遊戲參數如 [`HDMI_SCREEN_WIDTH`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、音樂路徑 [`MUSIC_DIRECTORIES`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 等)。
        *   匯入並實例化 [`LedController`](g:\CodeBase\Sensor_Boxing-Machine\led_controller.py), [`SensorHandler`](g:\CodeBase\Sensor_Boxing-Machine\sensor_handler.py), [`EmotionCalculator`](g:\CodeBase\Sensor_Boxing-Machine\emotion_calculator.py), [`HdmiGameEngine`](g:\CodeBase\Sensor_Boxing-Machine\hdmi_game_engine.py), [`SpiLcdDisplay`](g:\CodeBase\Sensor_Boxing-Machine\spi_lcd_display.py), [`MusicPlayer`](g:\CodeBase\Sensor_Boxing-Machine\music_player.py)。
        *   執行這些物件的初始設定於 [`initialize_systems()`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 函式中。
        *   回傳一個包含所有初始化模組的字典給 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py)。
        *   提供 [`cleanup_systems()`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 函數統一清理各模組資源。

3.  **[`led_controller.py`](g:\CodeBase\Sensor_Boxing-Machine\led_controller.py)**:
    *   **功能**: 封裝對 WS281x LED 燈條的控制邏輯。
    *   **主要類別**: `LedController`
    *   **方法**:
        *   `__init__`, `begin`: 初始化與啟動 LED 燈條。
        *   `update_rainbow_cycle_frame`: 更新彩虹循環動畫，支援外部控制動畫偏移。
        *   `reset_rainbow_animation_state`: 重設彩虹動畫狀態。
        *   `clear`: 關閉所有 LED。
        *   `show_flash_pattern`: 顯示閃爍燈效。
        *   `static_color`, `color_wipe`, `theater_chase_rainbow`, `breathing_light`: 提供多種燈光效果。
        *   `set_brightness`: 設定 LED 亮度。

4.  **[`sensor_handler.py`](g:\CodeBase\Sensor_Boxing-Machine\sensor_handler.py)**:
    *   **功能**: 處理 ADS1115 ADC 的初始化和資料讀取。
    *   **主要類別**: `SensorHandler`
    *   **方法**:
        *   `initialize_ads1115`, `setup_adc_channels`: 初始化 I2C、ADS1115 及 ADC 通道 (通道定義於 [`PIEZO_CHANNELS`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))。
        *   `get_max_voltage_from_all_channels`: 在指定時間內，從所有設定通道讀取並回傳**峰值**電壓。
        *   `check_any_piezo_trigger`: 快速檢查是否有任何壓電薄膜通道的**即時電壓**超過指定閾值 ([`PIEZO_JUMP_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))，用於遊戲中的拍擊跳躍偵測。

5.  **[`emotion_calculator.py`](g:\CodeBase\Sensor_Boxing-Machine\emotion_calculator.py)**:
    *   **功能**: 根據電壓值計算「負面情緒指數」。
    *   **主要類別**: `EmotionCalculator`
    *   **方法**:
        *   `__init__`: 設定計算參數 (電壓閾值 [`EMOTION_VOLTAGE_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)、情緒上限 [`MAX_EMOTION_INDEX`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))。
        *   `calculate_negative_emotion_index`: 根據輸入的電壓執行情緒指數計算。

6.  **[`hdmi_game_engine.py`](g:\CodeBase\Sensor_Boxing-Machine\hdmi_game_engine.py)**:
    *   **功能**: 控制在 HDMI 外接螢幕上運行的 Pygame 小遊戲。
    *   **主要類別**: `HdmiGameEngine`
    *   **方法**:
        *   `__init__`: 初始化 Pygame 視窗 (HDMI 解析度定義於 [`HDMI_SCREEN_WIDTH`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py), [`HDMI_SCREEN_HEIGHT`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))、載入遊戲資源 (圖片路徑如 [`PLAYER_IMAGE_PATH`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))、設定遊戲參數。
        *   `run_game`: 啟動並運行一局完整的遊戲。處理遊戲邏輯 (玩家移動、跳躍、障礙物生成/移動、碰撞偵測、分數計算)、繪圖到 HDMI 螢幕、處理使用者輸入 (鍵盤、透過 [`SensorHandler.check_any_piezo_trigger()`](g:\CodeBase\Sensor_Boxing-Machine\sensor_handler.py) 實現的拍擊跳躍)。遊戲結束後返回結果字典。
        *   `show_hdmi_standby_screen`, `show_measuring_emotion_screen`: 在 HDMI 上顯示特定狀態畫面。
        *   `_game_over_screen_on_hdmi`: 在 HDMI 上顯示遊戲結束畫面及重玩/離開選項。
        *   `cleanup`: 遊戲引擎相關的清理 (Pygame 本身的 quit 由 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 處理)。

7.  **[`spi_lcd_display.py`](g:\CodeBase\Sensor_Boxing-Machine\spi_lcd_display.py)**:
    *   **功能**: 控制 ILI9341 SPI LCD 螢幕，專門用於顯示文字訊息。
    *   **主要類別**: `SpiLcdDisplay`
    *   **方法**:
        *   `__init__`: 初始化 SPI LCD 硬體 (腳位定義於 [`LCD_CS_PIN`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 等)、載入 PIL 字型。
        *   `display_message`: 在 LCD 上顯示多行文字。
        *   `display_game_results`: 格式化顯示遊戲的最終得分、情緒等。
        *   `show_standby_message`: 顯示待機或狀態提示訊息。
        *   `clear_display`: 清除 LCD 螢幕。
        *   `cleanup`: 關閉 LCD 背光等。

8.  **[`game_interactions.py`](g:\CodeBase\Sensor_Boxing-Machine\game_interactions.py)**:
    *   **功能**: 封裝由使用者互動觸發的、涉及多個模組協作的核心遊戲準備邏輯。
    *   **主要函式**: `get_player_emotion_index()`
    *   **職責**:
        *   接收 [`SensorHandler`](g:\CodeBase\Sensor_Boxing-Machine\sensor_handler.py) 和 [`EmotionCalculator`](g:\CodeBase\Sensor_Boxing-Machine\emotion_calculator.py) 的實例。
        *   協調從感測器讀取最大電壓的過程 (呼叫 [`SensorHandler.get_max_voltage_from_all_channels()`](g:\CodeBase\Sensor_Boxing-Machine\sensor_handler.py))。
        *   將獲取的電壓傳遞給情緒計算器以得到「負面情緒指數」 (呼叫 [`EmotionCalculator.calculate_negative_emotion_index()`](g:\CodeBase\Sensor_Boxing-Machine\emotion_calculator.py))。
        *   回傳計算出的情緒指數給呼叫者 ([`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py))。

9.  **[`music_player.py`](g:\CodeBase\Sensor_Boxing-Machine\music_player.py)**:
    *   **功能**: 控制遊戲中的背景音樂播放。
    *   **主要類別**: `MusicPlayer`
    *   **方法**:
        *   `__init__`: 初始化音樂播放器、設定不同類別的音樂路徑 (定義於 [`MUSIC_DIRECTORIES`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))。
        *   `play_random_music`: 從指定類別中隨機選擇一首音樂播放。
        *   `switch_to_category`: 切換到指定類別的音樂。
        *   `pause`, `unpause`, `stop`, `fade_out`: 控制音樂播放狀態。
        *   `set_volume`: 調整音樂音量 (預設音量 [`MUSIC_DEFAULT_VOLUME`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py), 遊戲音量 [`MUSIC_GAME_VOLUME`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py))。
        *   `is_music_playing`: 檢查是否有音樂正在播放。
        *   `cleanup`: 清理音樂資源 (停止播放)。

10. **[`requirements.txt`](g:\CodeBase\Sensor_Boxing-Machine\requirements.txt)**:
    *   列出專案所需的 Python 函式庫，方便環境設定。可使用 `pip install -r requirements.txt` 指令安裝。

## 硬體需求與接線 (概要)

*   **Raspberry Pi**: 作為主控制器 (建議 Raspberry Pi 3B+ 或更高版本)。
*   **HDMI 顯示器**: 用於顯示主遊戲畫面。
*   **ILI9341 SPI LCD 顯示器**: 用於顯示遊戲結果和狀態提示。
*   **WS281x LED 燈條**: 用於視覺回饋 (例如 Neopixel)。
*   **按鈕**: 一個實體按鈕，用於觸發遊戲開始。
*   **壓電薄膜感測器 (x4)**: 用於偵測壓力。
*   **ADS1115 ADC 模組**: 將壓電薄膜的類比訊號轉換為數位訊號。
*   **揚聲器或耳機**: 透過 Raspberry Pi 的 3.5mm 音訊孔或 HDMI 播放背景音樂。

*具體腳位定義 (如 GPIO、SPI、I2C) 及拍擊跳躍閾值等參數，請參考 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 頂部的常數設定。*

![電路圖](Circuit_diagram.png)

## 操作流程

1.  **連接硬體**: 確保所有硬體元件 (包括 HDMI 顯示器、SPI LCD、LED 燈條、按鈕、感測器、ADC 模組及音訊輸出) 已根據 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中的腳位設定正確連接到 Raspberry Pi。
2.  **環境設定**:
    *   確保已安裝必要的 Python 函式庫，可參考 [`requirements.txt`](g:\CodeBase\Sensor_Boxing-Machine\requirements.txt) 並使用 `pip install -r requirements.txt` 安裝。
    *   啟用 Raspberry Pi 上的 I2C 和 SPI 介面 (可透過 `sudo raspi-config` 設定)。
    *   確認音樂檔案路徑 (於 [`MUSIC_DIRECTORIES`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中設定) 及遊戲圖片 ([`player.png`](g:\CodeBase\Sensor_Boxing-Machine\player.png), [`obstacle.png`](g:\CodeBase\Sensor_Boxing-Machine\obstacle.png)) 存在且路徑正確。
3.  **執行程式**:
    *   導航到專案目錄 (例如 `cd Sensor_Boxing-Machine`)。
    *   執行主程式：`python3 main.py`。詳細的啟動指令（可能包含環境變數設定）可參考 [`Start_Order.md`](g:\CodeBase\Sensor_Boxing-Machine\Start_Order.md)。
4.  **程式啟動**:
    *   主控台會顯示各模組的初始化訊息。
    *   LED 燈條進入彩虹待機動畫。
    *   SPI LCD 顯示待機訊息 (如 "按鈕啟動")。
    *   播放預設背景音樂。
    *   HDMI 螢幕顯示待機畫面。
5.  **開始測量情緒**:
    *   按下已連接的實體按鈕。
    *   LED 燈條閃爍提示，背景音樂淡出。
    *   SPI LCD 顯示 "測量情緒中..."。
    *   HDMI 螢幕顯示 "測量情緒中..."。
    *   系統開始在接下來的幾秒內偵測壓電薄膜壓力，以計算「負面情緒指數」。
6.  **遊戲開始準備**:
    *   情緒指數測量完成後，SPI LCD 會短暫顯示獲取的情緒值。
    *   若情緒指數達到 [`GAME_START_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\main.py) (定義於 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 中，預設由 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 間接提供)，則切換到遊戲音樂。
    *   否則，提示情緒不足，並返回待機狀態。
7.  **進行遊戲 (HDMI 螢幕)**:
    *   遊戲主畫面在 HDMI 顯示器上啟動。
    *   玩家使用鍵盤方向鍵或拍擊壓電薄膜 (觸發閾值為 [`PIEZO_JUMP_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py)) 控制角色跳躍。
    *   遊戲目標是透過成功躲避障礙物來消耗「負面情緒里程」(初始值等於測量得到的情緒指數)。
8.  **遊戲結束 (HDMI 螢幕)**:
    *   遊戲結束條件達成後 (例如角色撞到障礙物，或情緒里程成功歸零)，HDMI 螢幕顯示遊戲結束畫面，並提供**重玩 (R)** 或 **離開 (Q)** 選項。
    *   系統切換到遊戲結束音樂。
9.  **顯示結果 (SPI LCD)**:
    *   無論玩家在 HDMI 上選擇重玩還是離開，SPI LCD 都會顯示本局的最終結果 (得分、剩餘情緒里程、遊戲結束原因)。
    *   等待數秒讓玩家查看。
10. **返回待機 / 重玩**:
    *   如果玩家在 HDMI 上選擇**離開 (Q)** 遊戲會話，或遊戲結束後流程自然結束 (例如情緒里程歸零後未選擇重玩)，系統返回待機狀態：
        *   LED 恢復彩虹動畫。
        *   SPI LCD 顯示待機訊息。
        *   HDMI 螢幕顯示待機畫面。
        *   切換回預設背景音樂。
    *   如果玩家在 HDMI 上選擇**重玩 (R)**，則直接在 HDMI 上開始新的一局 (通常使用相同的初始情緒值，除非遊戲邏輯有特殊設計)。SPI LCD 可能不會更新，直到該局重玩的遊戲也結束。
11. **結束程式**:
    *   在執行 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 的主控台按 `Ctrl+C` 中斷程式。程式會嘗試優雅地清理所有已初始化的資源。

## 注意事項

*   確保 [`player.png`](g:\CodeBase\Sensor_Boxing-Machine\player.png) 和 [`obstacle.png`](g:\CodeBase\Sensor_Boxing-Machine\obstacle.png) 圖片檔案與 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 等腳本位於同一目錄下，或依照 [`PLAYER_IMAGE_PATH`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 和 [`OBSTACLE_IMAGE_PATH`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 在 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中的定義放置。
*   仔細檢查 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中的所有硬體腳位 (GPIO, SPI, I2C) 和模組參數設定，確保它們與您的硬體接線和期望行為一致。
*   拍擊跳躍的靈敏度 (電壓閾值) 可在 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中調整 [`PIEZO_JUMP_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 常數。
*   音樂檔案路徑設定位於 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中的 [`MUSIC_DIRECTORIES`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 常數。請確保路徑正確且音樂檔案存在。
*   如需添加新的音樂類別 (例如遊戲勝利時的特殊音樂)，可以在 [`MUSIC_DIRECTORIES`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 字典中增加新的鍵 (類別名稱) 和對應的音樂檔案路徑列表。然後在 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 或其他相關模組中呼叫 [`MusicPlayer.switch_to_category()`](g:\CodeBase\Sensor_Boxing-Machine\music_player.py) 來使用新的音樂類別。
*   LED 燈條的亮度 [`LED_BRIGHTNESS`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 和數量 [`LED_COUNT`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 可以在 [`system_configurator.py`](g:\CodeBase\Sensor_Boxing-Machine\system_configurator.py) 中調整。
*   遊戲啟動的情緒指數閾值 [`GAME_START_THRESHOLD`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 定義在 [`main.py`](g:\CodeBase\Sensor_Boxing-Machine\main.py) 中，可以根據需要調整。