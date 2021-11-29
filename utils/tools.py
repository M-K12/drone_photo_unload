import exifread
import hashlib
import json
from PIL import Image


def getlines(kjson):
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
            fid = int(point['id'])
            match = point['match']
            if fid in kpoints:
                # print("重复航点:", id)
                rCount += 1
            kpoints[fid] = (lat, lon, match)
            # if len(match):
            #     print(match)

    return pCount, rCount, kpoints


def getLatLon(tags):
    try:
        lat_ = tags['GPS GPSLatitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        lon_ = tags['GPS GPSLongitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        # creattime = tags['Image DateTime'].printable.replace(":", "").replace(" ", "")
        # thumbnail = tags['JPEGThumbnail']
        if len(lat_) != 4 or len(lon_) != 4:
            return None
        lat = float(lat_[0]) + float(lat_[1]) / 60 + float(lat_[2]) / int(lat_[3]) / 3600
        lon = float(lon_[0]) + float(lon_[1]) / 60 + float(lon_[2]) / int(lon_[3]) / 3600
        if tags['GPS GPSLatitudeRef'].printable != "N":
            lat *= (-1)
        if tags['GPS GPSLongitudeRef'].printable != "E":
            lon *= (-1)
        LatLon = (lat, lon)
        return LatLon


    except:
        print("经纬度解析异常!")
        return None


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


def md5value(key):
    md5key = hashlib.md5()
    md5key.update(key.encode("utf-8"))
    return md5key.hexdigest()


if __name__ == '__main__':
    from glob import glob

    # imgs = glob(r"D:\uav\pictures\1114\2\*.JPG")
    imgs = ["../images/DJI_0002.JPG", "../images/1.jpg"]
    for img in imgs:
        # img = r'D:\uav\pictures\1114\2\DJI_0004.JPG'
        with open(img, 'rb') as fb:
            tags = exifread.process_file(fb)
        latlon = getLatLon(tags)
        print(latlon)
