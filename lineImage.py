from geopy.distance import geodesic
from multiprocessing import Manager, Process, cpu_count
from io import BytesIO, BufferedReader
import PySimpleGUI as sg
import numpy as np
import json
import exifread
import hashlib
import time
from utils.latlon import getLatLon
from utils.ftpDL import ftp_upload
from utils.mysqlDL import mysql
from PIL import Image
import os

layout = [
    [sg.Text('航线日期', size=(15, 1), justification='right'), sg.InputText(time.strftime("%Y-%m-%d", time.localtime())),
     sg.CalendarButton('Date', format=('%Y-%m-%d'))],
    [sg.Text('照片路径', size=(15, 1), justification='right'), sg.Input(), sg.FolderBrowse('FolderBrowse')],
    [sg.Submit(), sg.Cancel()],
]

window = sg.Window('Test', layout, font=("宋体", "15"), default_element_size=(50, 5))


def md5value(key):
    md5key = hashlib.md5()
    md5key.update(key.encode("utf-8"))
    return md5key.hexdigest()


def lines(kjson):
    kpoints = {}
    pCount = 0
    rCount = 0

    for data in kjson:
        # print(data['id'], end=' ')
        points = json.loads(data[1])['points']
        for point in points:
            pCount += 1
            lat = float(point['lat'])
            lon = float(point['lon'])
            id = int(point['id'])
            match = point['match']
            if id in kpoints:
                # print("重复航点:", id)
                rCount += 1
            kpoints[id] = (lat, lon, match)
            # if len(match):
            #     print(match)

    return pCount, rCount, kpoints


def imgMatch(imgs, verfiedImgs, kPoints, pKeys, validImgs, repeatPoints, invalidImgs, matchedImgsPoints):
    ftp = ftp_upload(ip="192.168.2.18", user='gym', passwd='gym123qaz')

    for img in imgs:
        fb = open(img, 'rb')
        tags = exifread.process_file(fb)
        latlon = getLatLon(tags)

        if latlon is None:
            invalidImgs[img] = 'None'
            print(f"{img} 是无效照片, 经纬度提取失败!")
            verfiedImgs[img] = 'verified'
            continue

        pdata = np.zeros(len(pKeys), dtype=np.float16)

        for idx, lp in enumerate(pKeys):
            kp = kPoints[lp][:2]
            dis = geodesic(kp, latlon).m
            pdata[idx] = dis

        if pdata.min() <= 1:
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
                ftp_path = f"/home/gym/test/photo_crop/{img_name}.jpg"
                matchedImgsPoints[hid] = img_path
                ftp.upload(file_handler=img_buffer, remotepath=ftp_path)

            print(f"{img}  关联到航点 {hid}")
            # print(f"{img}  关联到航点 {hid} GOOD COUNT: {len(validImgs)}")

        else:
            invalidImgs[img] = 'None'
            print(f"{img} 是无效照片, 关联到的最近航点是 {pKeys[pdata.argmin()]},距离:{pdata.min()}")

        fb.close()
        verfiedImgs[img] = 'verified'


def photoCrop(imgbt, scale=1 / 8):
    imgbase = Image.open(imgbt)
    width, height = imgbase.size
    a = width * scale  # 图片距离左边的大小
    b = height * scale  # 图片距离上边的大小
    c = width * (1 - scale)  # 图片距离左边的大小 + 图片自身宽度
    d = height * (1 - scale)  # 图片距离上边的大小 + 图片自身高度
    # print('a= {},b= {},c= {}, d= {}'.format(a, b, c, d))
    imgcrop = imgbase.crop([a, b, c, d]).resize((800, 600))
    # imgcrop.thumbnail((800, 600), Image.BILINEAR)

    return imgcrop


def up_status(Tcount, vfImgCnt, validImgCnt, invalidImgCnt, repeatCnt):
    sg.one_line_progress_meter('上传进度',  # 窗口名称
                               vfImgCnt + 1,  # 当前进度
                               Tcount,  # 总进度
                               f"关联成功:{validImgCnt} 无效照片:{invalidImgCnt} 重复照片:{repeatCnt}",
                               orientation='h',  # 进度条方向h是横向，v是纵向
                               bar_color=('#AAFFAA', '#FFAAFF'),  # 进度条颜色
                               # size=(30, 30),
                               # keep_on_top=True,
                               no_titlebar=True,
                               no_button=True
                               )


if __name__ == '__main__':

    event, values = window.read()
    window.close()

    print('Date:', values['Date'])
    print('FolderBrowse:', values['FolderBrowse'])

    # if event is None or event == 'Cancel':
    #     exit()

    if event != 'Submit':
        exit()

    start = time.time()

    # imgfiles = glob.glob(r"D:\uav\pictures\1116\*\*.JPG")[:12]
    # flyDate = values['Date']
    flyDate = values[0]

    imgfiles = []
    for root, dirs, files in os.walk(values['FolderBrowse']):
        for file in files:
            if file.split('.')[-1] not in ['jpg', 'JPG', 'JPEG']:
                continue
            imgfiles.append(os.path.join(root, file))

    imgfiles = imgfiles
    kcodes = [
        f"SELECT id, source FROM t_uav_trajectory WHERE del_flag=0 AND file_id in (SELECT id FROM t_uav_file_info WHERE DATE_FORMAT( create_time, '%Y-%m-%d' ) = '{(flyDate)}' AND is_download = 1) ORDER BY file_id;"]
    mysql = mysql(h="192.168.2.18", u="root", passwd="123qaz")

    mysql.connect(db="ming")
    kmljson = mysql.my_select(kcodes)[0]
    mysql.close()
    # kfile = r'D:\uav\airlines\1116.json'
    # pcount, rcount, kPoints = linePoints(kfile)
    pcount, rcount, kPoints = lines(kmljson)
    kPointscnt = len(kPoints)
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
        p = Process(target=imgMatch,
                    args=(
                        imglist, verfiedImgs, kPoints, pKeys, validImgs, repeatPoints, invalidImgs, matchedImgsPoints))
        p.start()
        p_list.append(p)

    while len(verfiedImgs) < total_count:
        up_status(total_count, len(verfiedImgs), len(validImgs), len(invalidImgs), len(repeatPoints))

    for res in p_list:
        res.join()

    validImgCnt = len(validImgs)
    invalidImgCnt = len(invalidImgs)
    repeatCnt = len(repeatPoints)
    pointCnt = len(matchedImgsPoints)

    matchedHousesImgs = matchedImgsPoints.copy()
    for k in list(matchedHousesImgs):
        match = kPoints[k][-1]
        for mid in match:
            matchedHousesImgs[mid] = matchedHousesImgs[k]

    codes = ["show table status WHERE NAME = 'risk_house_pic_file'",
             f"SELECT fid, id FROM risk_house_pic_file WHERE file_path in {tuple(matchedHousesImgs.values())}"]
    # ttt = ('13435d4c-6554-4d0d-948c-3cd4d0ee1c50.JPG', '37f7bb6e961a1810421700b0ec7461f307ecd6de58a0fb8f_4.jpg')
    # codes = ["show table status WHERE NAME = 'risk_house_pic_file'",
    #          f"SELECT fid, id FROM risk_house_pic_file WHERE file_path in {ttt}"]

    mysql.connect(db="ming")
    results = mysql.my_select(codelist=codes, )

    auto_increment = int(results[0][0][10])  # 自增id
    existedHidImgs = dict(results[1])

    valuesList = []
    for fid in matchedHousesImgs:

        uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if fid in existedHidImgs:
            valuesList.append((existedHidImgs[fid], int(fid), 1, 1, str(matchedHousesImgs[fid]), uptime))
        else:
            valuesList.append((auto_increment, int(fid), 1, 1, str(matchedHousesImgs[fid]), uptime))
            auto_increment += 1

    insertCode = "replace into risk_house_pic_file(id, fid, damaged, zf, file_path, upload_time) values(%s,%s,%s,%s,%s,%s);"
    mysql.my_insert(sql=insertCode, val=valuesList)

    mysql.close()

    houseCnt = len(matchedHousesImgs)
    print(
        f"所有航线航点总数:{pcount} 重复航点:{rcount} 去重后航点数:{kPointscnt} "
        f"照片总数:{len(imgfiles)} 有效照片:{validImgCnt} 无效照片:{invalidImgCnt} "
        f"航点关联成功:{pointCnt} 重复照片:{repeatCnt}  "
        f"房屋关联成功:{houseCnt}")

    m, s = divmod(int(time.time() - start), 60)
    print(f"timecost:{m}分{s}秒")
    sg.popup("上传完成", f"关联成功:{validImgCnt} \n无效照片:{invalidImgCnt} \n重复照片:{repeatCnt} \ntimecost:{m}分{s}秒")
