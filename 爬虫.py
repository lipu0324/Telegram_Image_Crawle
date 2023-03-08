#! /usr/bin/python3
# from bs4 import BeautifulSoup

import datetime
import json
import requests
import os
from telethon import TelegramClient, sync
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
import time
import wget
import pickle


api_id = "你的TelegramAPI_id"
api_hash = "你的telegramhash"
phone_number = "你的手机号码"
client_name = "给你的爬虫起一个名字"



client = TelegramClient(client_name, api_id, api_hash)
client.connect()
if not client.is_user_authorized():
    try:
        client.send_code_request(phone_number)
        client.sign_in(phone_number, input("Enter the code sent to your phone: "))
    except PhoneNumberInvalidError:
        print("Invalid phone number.")
channel_name = "@你需要爬取的频道名称"
channel = client.get_entity(channel_name)
file_forder_name = "存图片的文件夹"
if not os.path.exists(file_forder_name):
    os.mkdir(file_forder_name)
if os.path.exists(file_forder_name):
    print("File folder is ok now.")

flag = input("1.获取所有历史信息\n2.仅获取昨日信息\n")
flag= "1"

if flag == "2":
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    print(str(yesterday))
    messages = client(
        GetHistoryRequest(
            peer=channel,
            offset_date=yesterday,
            offset_id=0,
            add_offset=0,
            limit=400,
            max_id=0,
            min_id=0,
            hash=0,
        )
    )


def download_images_from_telegraph(url, ):
    # 检查已下载完成的文件夹列表
    completed_folders = set()
    completed_folders_file="completed_folders_file.txt"
    if os.path.exists(completed_folders_file):
        with open(completed_folders_file, "r") as f:
            for line in f:
                completed_folders.add(line.strip())

    retry_count = 0
    while retry_count < 10:
        try:
            response = requests.get(url)
            response.raise_for_status()  # 抛出异常，处理失败的情况
            data = json.loads(response.text)["result"]
            print(data["path"])
            title = data["path"]

            # 检查文件夹是否已下载完成
            if title.replace(" ", "_") in completed_folders:
                print(f"Folder {title} has been downloaded, skipping...")
                return

            # 创建以标题为名的文件夹，用于存放图片
            folder_name = file_forder_name + "/" + title.replace(" ", "_")
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)

            # 查找所有图片链接，并下载图片
            image_urls = [
                node["children"][0]["attrs"]["src"]
                for node in data["content"]
                if node["tag"] == "figure"
            ]
            print(len(image_urls))
            real_count = 0
            for i, image_url in enumerate(image_urls):
                if os.path.exists(folder_name+f"/image_{i}.jpg"):
                    print("File already exists, skipping...")
                    continue
                image_real_url = "https://telegra.ph/file/" + image_url.split("/")[-1]
                print(image_real_url)
                retry_count = 0
                while retry_count < 10:
                    try:
                        wget.download(image_real_url,f"{folder_name}/image_{i}.jpg")
                        break
                    except Exception as e:
                        print(f"下载失败，正在尝试重试，错误信息：{str(e)}")
                        time.sleep(1)  # 等待1秒钟后再次尝试下载
                        retry_count += 1
                else:
                    print(f"文件下载失败，已经尝试了{retry_count}次")
                    continue
                real_count+=1
                print(" ")
            
            # 下载完成后将文件夹名称追加到已下载完成的文件中
            with open(completed_folders_file, "a") as f:
                f.write(title.replace(" ", "_") + "\n")
            
            print(f"{real_count} images downloaded to {folder_name} folder")
            return
        
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            # 捕获请求异常和JSON解码错误，进行重试
            print("Error occurred. Retrying...")
            retry_count += 1
            time.sleep(1)  # 休眠1秒后重试
            
    print("Failed to download the images after 10 retries.")

############################################################################################################################

# download_images_from_telegraph(
#     "https://api.telegra.ph/getPage/Sample-Page-12-15?return_content=true")


if flag == "1":
    try:
         with open('downloaded_dates.pkl', 'rb') as f:
             downloaded_dates = pickle.load(f)
    except FileNotFoundError:
         downloaded_dates = []
    tempDate = OriginDate
    # 循环减一天，直到一年以前
    while tempDate > datetime.datetime.today()-datetime.timedelta(days=365):
        # 如果日期已经下载过，则跳过
        if tempDate.strftime("%Y-%m-%d") in downloaded_dates:
            print(f"{tempDate.strftime('%Y-%m-%d')} 已经下载过了，正在跳过...")
            downloaded_dates.append(tempDate.strftime("%Y-%m-%d"))
            downloaded_dates= list(set(downloaded_dates))
            tempDate = tempDate - datetime.timedelta(days=1)
            with open('downloaded_dates.pkl', 'wb') as f:
                pickle.dump(downloaded_dates, f)
            continue
        messages = client(
            GetHistoryRequest(
                peer=channel,
                offset_date=tempDate,
                offset_id=0,
                add_offset=0,
                limit=4000,
                max_id=0,
                min_id=0,
                hash=0,
            )
        )
        print(len(str(messages)))
        print(f"正在下载 {tempDate.strftime('%Y-%m-%d')}")
        for subs in str(messages).split(","):
            if "url='telegra.ph" in subs:
                urlfrt = subs.split("'")[1].split("/")[0]
                urlbhd = subs.split("'")[1].split("/")[1]
                urltmp = "https://api." + urlfrt + "/getPage/" + urlbhd + "?return_content=true"
                download_images_from_telegraph(urltmp)
        # 添加已下载的日期到列表中
        downloaded_dates.append(tempDate.strftime("%Y-%m-%d"))
        downloaded_dates= list(set(downloaded_dates))
        print(f"{tempDate.strftime('%Y-%m-%d')} 下载完成...")
        tempDate = tempDate - datetime.timedelta(days=1)
        # 将更新后的列表保存回文件中
        with open('downloaded_dates.pkl', 'wb') as f:
            pickle.dump(downloaded_dates, f)

elif flag == "2":
    print(len(str(messages)))
    for subs in str(messages).split(","):
        if "url='telegra.ph" in subs:
            urlfrt = subs.split("'")[1].split("/")[0]
            urlbhd = subs.split("'")[1].split("/")[1]
            urltmp = "https://api." + urlfrt + "/getPage/" + urlbhd + "?return_content=true"
            print(urltmp)
            download_images_from_telegraph(urltmp)
            # break
