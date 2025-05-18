import adafruit_ads1x15

def main():
    try:
        print("adafruit_ads1x15 匯入成功！")
        # 嘗試列出模組內的內容
        print("模組內容：", dir(adafruit_ads1x15))
    except Exception as e:
        print("匯入失敗，錯誤訊息：", e)

if __name__ == "__main__":
    main()
