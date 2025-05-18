from rich.live import Live
from rich.panel import Panel
from rich.console import Group # 新增匯入 Group
import time
from translate import Translate
from rich.align import Align

def mileage_decay(mileage: int, decay_rate: float) -> int:
    """Apply a decay to the mileage."""
    return int(mileage * (1 - (decay_rate)**0.76))

# 初始化當前里程數和衰減率
emo = 5963
current_mileage = Translate.translate_mileage(emo)  # 5963公里
decay_rate_value = 0.1

# 火車動畫參數
track_width = 40  # 火車軌道的寬度
train_char = "🚃🚃🚃"  # 代表火車的字符
train_position = 0  # 火車的初始位置
train_direction = 1  # 火車的初始移動方向 (1: 向右, -1: 向左)

# 函數：建立顯示里程數的 Panel
def make_mileage_panel(mileage: int) -> Panel:
    """建立顯示當前里程數的 Panel。"""
    # 如果您也想讓這個 Panel 的內容置中，可以做類似的修改：
    # content = Align.center(f"剩餘負面情緒值: {mileage}")
    # return Panel(content, title="負面情緒", border_style="blue")
    time.sleep(0.01) # 這裡可以調整顯示的速度
    return Panel(f"剩餘負面情緒值: {mileage}", title="負面情緒", border_style="blue")

# 函數：建立顯示火車軌道的 Panel
def make_train_track_panel(position: int, width: int, char: str) -> Panel:
    """建立顯示火車在軌道上位置的 Panel。"""
    # 建立軌道，使用 ' ' 字元代表軌道本身
    track = [' '] * width
    # 在指定位置放置火車字符
    if 0 <= position < width:
        track[position] = char
    
    # 將軌道字串包裝在 Align.center() 中，使其在 Panel 內容區域內置中
    centered_track_content = Align.center("".join(track))
    time.sleep(0.2)  # 這裡可以調整火車移動的速度   
    return Panel(
        centered_track_content, 
        title="我要離開這個令人傷心欲絕的城市", 
        border_style="green"
    )

# 建立 Live 物件的初始顯示內容
# 上半部：里程數衰減
initial_mileage_display = make_mileage_panel(current_mileage)
# 下半部：火車運行
initial_train_display = make_train_track_panel(train_position, track_width, train_char)

# 使用 Group 將上下兩部分組合起來
_initial_group_content = Group(
    initial_mileage_display,
    initial_train_display
)
# 這行會將整個動畫區塊（包含兩個 Panel）在螢幕上置中
initial_group = Align.center(_initial_group_content)

# 修改 animation 函式簽名以接收新的速度控制參數
def animation(
    current_mileage: int,  # 這個參數目前在動畫迴圈中未直接用於衰減，主要用於最終打印
    emo: int,
    train_position: int = 0,  # 火車的初始位置
    frame_interval: float = 0.05,  # 每幀之間的延遲，控制整體動畫快慢
    custom_emo_decay_rate: float = 0.1,  # 控制情緒值衰減的速率
    train_steps_per_frame: int = 1  # 火車每幀移動的步數
) -> None:
    total_emo = emo # 記錄初始情緒值

    local_initial_mileage_display = make_mileage_panel(emo)
    local_initial_train_display = make_train_track_panel(train_position, track_width, train_char)
    _live_initial_content = Group(
        local_initial_mileage_display,
        local_initial_train_display
    )
    live_initial_group_centered = Align.center(_live_initial_content)

    with Live(live_initial_group_centered, refresh_per_second=10, screen=True) as live:
        while emo > 0:
            # 1. 更新里程數 (負面情緒值)
            # 使用傳入的 custom_emo_decay_rate 控制衰減速度
            emo = mileage_decay(emo, custom_emo_decay_rate)
            if emo < 0:
                emo = 0
            
            mileage_display_update = make_mileage_panel(emo)

            # 2. 更新火車位置
            # 使用傳入的 train_steps_per_frame 控制火車移動速度
            # 假設 train_steps_per_frame 為正值，表示向右移動
            train_position += train_steps_per_frame
            
            if train_position >= track_width:
                train_position = 0  # 火車回到起點
                
            train_display_update = make_train_track_panel(train_position, track_width, train_char)

            _group_to_update_content = Group(
                mileage_display_update,
                train_display_update
            )
            group_to_update_centered = Align.center(_group_to_update_content)
            
            live.update(group_to_update_centered)
            
            # 使用 frame_interval 控制每幀的延遲
            time.sleep(frame_interval)

        final_mileage_display = make_mileage_panel(emo)
        final_train_display = make_train_track_panel(train_position, track_width, "🏁") 
        _final_group_content = Group(final_mileage_display, final_train_display)
        final_group_centered = Align.center(_final_group_content)
        live.update(final_group_centered)
        time.sleep(0.5)
    
    print(f"負面情緒值:{total_emo}")
    print(f"火車運行距離:{current_mileage}公里")

if __name__ == "__main__":
    # 現在可以分別調整：
    # frame_interval: 整體動畫快慢 (值越小越快)
    # custom_emo_decay_rate: 情緒值下降速度 (mileage_decay 內部計算基於此值，影響衰減幅度)
    # train_steps_per_frame: 火車移動速度 (值越大，火車每幀移動越遠，看起來越快)
    animation(
        current_mileage=350,  # 範例值
        emo=5963,
        frame_interval=0.05,  # 例如，讓整體動畫快一點
        custom_emo_decay_rate=0.1,  # 例如，讓情緒值衰減慢一點
        train_steps_per_frame=1  # 例如，讓火車移動快一點 (每幀移動2格)
    )