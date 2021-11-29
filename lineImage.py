from geopy.distance import geodesic
from multiprocessing import Manager, Process, cpu_count
from io import BytesIO, BufferedReader
import PySimpleGUI as sg
import numpy as np
import exifread
import time
from utils.tools import getLatLon, md5value, photoCrop, getlines
from utils.ftpDL import myftp
from utils.mysqlDL import mysql
from utils.sgwindow import input_messages, up_status
import os

ftp = myftp()
ftp_msg = ftp.login()
if ftp_msg is not None and ftp_msg.find('ERROR'):
    sg.popup(ftp_msg + "\nERROR:FTP网络连接异常！", title="FTP Error", keep_on_top=True)
    exit()

mysql = mysql()
sql_msg = mysql.connect('ming')
if sql_msg is not None and sql_msg.find('ERROR'):
    sg.popup(sql_msg + "\nERROR:数据库网络连接异常！", title="Mysql Error", keep_on_top=True)
    exit()
mysql.close()


def photo_match(imgs, verfiedImgs, kPoints, pKeys, validImgs, repeatPoints, invalidImgs, matchedImgsPoints):
    for img in imgs:
        verfiedImgs[img] = 'verified'

        fb = open(img, 'rb')
        tags = exifread.process_file(fb)
        latlon = getLatLon(tags)

        if latlon is None:
            invalidImgs[img] = 'None'
            print(f"{img} 是无效照片, 经纬度提取失败!")
            continue

        pdata = np.zeros(len(pKeys), dtype=np.float16)

        for idx, lp in enumerate(pKeys):
            kp = kPoints[lp][:2]
            dis = geodesic(kp, latlon).m
            pdata[idx] = dis

        if pdata.min() <= 2:
            hid = pKeys[pdata.argmin()]
            validImgs[img] = hid
            if hid in matchedImgsPoints:
                print("重复照片", hid, matchedImgsPoints[hid], img, pdata.min())
                repeatPoints[img] = hid
            else:

                croped_img = photoCrop(fb)
                img_byte = BytesIO()
                # img_byte.name = f"{hid}.jpg"
                croped_img.save(img_byte, format='JPEG')
                imgg = img_byte.getvalue()
                im = BytesIO(imgg)
                img_buffer = BufferedReader(im)

                img_name = md5value(f"{hid}_drone.jpg")
                img_path = f"{str(hid)[:12]}/{img_name}.jpg"
                # ftp_path = f"/home/gym/test/photo_crop/{img_name}"
                matchedImgsPoints[hid] = img_path
                ftp.upload(file_handler=img_buffer, filepath=img_path)

            print(f"{img}  关联到航点 {hid}")
            # print(f"{img}  关联到航点 {hid} GOOD COUNT: {len(validImgs)}")

        else:
            invalidImgs[img] = 'None'
            print(f"{img} 是无效照片, 关联到的最近航点是 {pKeys[pdata.argmin()]},距离:{pdata.min()}")

        fb.close()
    ftp.quit()


if __name__ == '__main__':

    flyDate, photoFolder = input_messages()

    start = time.time()

    imgfiles = []
    for root, dirs, files in os.walk(photoFolder):
        for file in files:
            if file.split('.')[-1] not in ['jpg', 'JPG', 'JPEG']:
                continue
            imgfiles.append(os.path.join(root, file))

    kmljson = mysql.getlines_json(flyDate)
    # imgfiles = imgfiles[:5]
    # kfile = r'D:\uav\airlines\1116.json'
    # pcount, rcount, kPoints = linePoints(kfile)
    pcount, rcount, kPoints = getlines(kmljson)
    kPointscnt = len(kPoints)
    if not kPointscnt:
        sg.popup(f"{flyDate} 未查询到航线", title='Error')
        exit()
    elif not len(imgfiles):
        sg.popup(f"{photoFolder} 下无照片", title='Error')
        exit()
    pKeys = sorted(list(kPoints.keys()))
    # 测试单个照片航点关联
    # imgfiles = [r'D:\uav\pictures\1116\31\DJI_0811.JPG']
    # pKeys = ['3304211052070807']

    cpuCount = cpu_count() if len(imgfiles) > 100 else 1

    manager = Manager()
    total_count = len(imgfiles)
    verfiedImgs = manager.dict()  # 验证过的照片
    kPoints = manager.dict(kPoints)
    pKeys = manager.list(pKeys)
    validImgs = manager.dict()  # 照片关联到航点
    repeatPoints = manager.dict()  # {重复的照片:房屋id}
    invalidImgs = manager.dict()  # 无效照片
    matchedImgsPoints = manager.dict()  # {房屋id:照片}

    p_list = []
    stride = len(imgfiles) // max(1, cpuCount - 1)
    for i in range(cpuCount):
        imglist = imgfiles[i * stride:min(len(imgfiles), (1 + i) * stride)]
        p = Process(target=photo_match,
                    args=(
                        imglist, verfiedImgs, kPoints, pKeys, validImgs, repeatPoints, invalidImgs, matchedImgsPoints))
        p.start()
        p_list.append(p)

    ss = True
    while len(verfiedImgs) <= total_count and ss:
        up_status(total_count, len(verfiedImgs), len(validImgs), len(invalidImgs), len(repeatPoints))
        ss = True if len(verfiedImgs) < total_count else False

    for res in p_list:
        res.join()

    validImgCnt = len(validImgs)
    invalidImgCnt = len(invalidImgs)
    repeatCnt = len(repeatPoints)
    pointOkCnt = len(matchedImgsPoints)

    matchedHousesImgs = matchedImgsPoints.copy()
    for k in list(matchedHousesImgs):
        match = kPoints[k][-1]
        for mid in match:
            matchedHousesImgs[mid] = matchedHousesImgs[k]

    existed_photos = tuple(matchedHousesImgs.values())
    mysql.insert_data(existed_photos, matchedHousesImgs)

    houseCnt = len(matchedHousesImgs)
    print(
        f"所有航线航点总数:{pcount} 重复航点:{rcount} 去重后航点数:{kPointscnt} "
        f"照片总数:{len(imgfiles)} 有效照片:{validImgCnt} 无效照片:{invalidImgCnt} "
        f"航点关联成功:{pointOkCnt} 重复照片:{repeatCnt}  "
        f"房屋关联成功:{houseCnt}")

    m, s = divmod(int(time.time() - start), 60)
    print(f"timecost:{m}分{s}秒")
    sg.popup("上传完成", f"关联成功:{pointOkCnt} \n无效照片:{invalidImgCnt} \n重复照片:{repeatCnt} \ntimecost:{m}分{s}秒")
