import os
import json
from datetime import datetime
from .handle import NotificationHandle
from CEACStatusBot.request import query_status
from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle

class NotificationManager():
    def __init__(self, location: str, number: str, passport_number: str, surname: str, captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx")) -> None:
        self.__handleList = []
        self.__location = location
        self.__number = number
        self.__captchaHandle = captchaHandle
        self.__passport_number = passport_number
        self.__surname = surname
        self.__status_file = 'status_record.json'

    def addHandle(self, notificationHandle: NotificationHandle) -> None:
        self.__handleList.append(notificationHandle)

    def send(self) -> None:
        res = query_status(self.__location, self.__number, self.__passport_number, self.__surname, self.__captchaHandle)
        current_status = res['status']
    
        # 加载之前的状态记录
        statuses = self.__load_statuses()
    
        # 始终保存当前状态并发送通知
        self.__save_current_status(current_status)
        self.__send_notifications(res)

    def __load_statuses(self) -> list:
        if os.path.exists(self.__status_file):
            with open(self.__status_file, 'r') as file:
                return json.load(file).get('statuses', [])
        return []

    def __save_current_status(self, status: str) -> None:
        statuses = self.__load_statuses()
        statuses.append({'status': status, 'date': datetime.now().isoformat()})

        with open(self.__status_file, 'w') as file:
            json.dump({'statuses': statuses}, file)

    def __send_notifications(self, res: dict) -> None:
        if res['status'] == "Refused":
            import pytz, datetime
            try:
                TIMEZONE = os.environ["TIMEZONE"]
                localTimeZone = pytz.timezone(TIMEZONE)
                localTime = datetime.datetime.now(localTimeZone)
            except pytz.exceptions.UnknownTimeZoneError:
                print("UNKNOWN TIMEZONE Error, use default")
                localTime = datetime.datetime.now()
            except KeyError:
                print("TIMEZONE Error")
                localTime = datetime.datetime.now()

            if localTime.hour < 8 or localTime.hour > 22:
                print("In Manager, no disturbing time")
                return
            if localTime.minute > 30:
                print("In Manager, no disturbing time")
                return

        for notificationHandle in self.__handleList:
            notificationHandle.send(res)
