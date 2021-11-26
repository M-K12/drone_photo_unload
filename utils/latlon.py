import exifread
from PIL import Image
from io import BytesIO

def getLatLon(tags):
    try:
        lat_ = tags['GPS GPSLatitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        lon_ = tags['GPS GPSLongitude'].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
        # creattime = tags['Image DateTime'].printable.replace(":", "").replace(" ", "")
        # thumbnail = tags['JPEGThumbnail']
        # img = Image.open(BytesIO(thumbnail))
        # img.show('tt')
        # print(int(lat_[2]), int(lat_[3]))
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
        print("except error!")
        return None


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
