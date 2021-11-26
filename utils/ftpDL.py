import time
from ftplib import FTP
import io


class ftp_upload:
    def __init__(self, ip="192.168.2.18", user='gym', passwd='gym123qaz'):
        self.ftp = FTP()
        self.ftp.set_debuglevel(2)  # 打开调试级别2，显示详细信息;0为关闭调试信息
        self.ftp.connect(ip, 21)  # 连接
        self.ftp.login(user, passwd)  # 登录，如果匿名登录则用空串代替即可
        # print(self.ftp.getwelcome())  # 显示ftp服务器欢迎信息
        self.bufsize = 1024  # 设置缓冲块大小

    def upload(self, file_handler, remotepath):
        # localpath = '/xxx/xxx/xxx/tifFile_final/VFB_000' + str(id) + '.tif'  # 在本地的文件
        # remotepath = '/xxx/xxx/tifFile_final/VFB_000' + str(id) + '.tif'  # 在ftp端的文件
        # file_handler = open(localpath, 'rb')  # 以读模式在本地打开文件
        self.ftp.storbinary('STOR ' + remotepath, file_handler, self.bufsize)  # 上传文件
        self.ftp.set_debuglevel(0)
        # print("ftp upload VFB_000 " + str(id) + " OK")
        file_handler.close()

    def ftp_quit(self):
        self.ftp.quit()

def photoCrop(imgbt, scale=1 / 8):
    imgbase = Image.open(imgbt)
    width, height = imgbase.size
    imgbase.thumbnail((width, height), Image.BILINEAR)
    a = width * scale  # 图片距离左边的大小
    b = height * scale  # 图片距离上边的大小
    c = width * (1 - scale)  # 图片距离左边的大小 + 图片自身宽度
    d = height * (1 - scale)  # 图片距离上边的大小 + 图片自身高度
    # print('a= {},b= {},c= {}, d= {}'.format(a, b, c, d))
    imgcrop = imgbase.crop([a, b, c, d])
    return imgcrop

if __name__ == "__main__":
    from os.path import basename
    from PIL import Image
    from glob import glob

    imgs = glob(r"D:\uav\pictures\1114\2\*.JPG")[:2]
    start = time.time()
    ftp = ftp_upload(ip="192.168.2.18", user='gym', passwd='gym123qaz')
    # localpath = r"D:\uav\pictures\1114\2\DJI_0002.JPG"
    for localpath in imgs:
        file_handler = open(localpath, 'rb')  # 以读模式在本地打开文件
        crop_img = photoCrop(file_handler)
        img = Image.open(str(localpath))
        img_byte = io.BytesIO()
        # img.name = "t.jpg"
        img.save(img_byte, format='JPEG')
        imgg = img_byte.getvalue()
        im = io.BytesIO(imgg)
        imgB = io.BufferedReader(im)

        print(imgB)

        ftp.upload(remotepath=f"/home/gym/test/photo_crop/{basename(localpath)}", file_handler=imgB)
        end = time.time()
        t = end - start
        # print("Runtime is ：", t)
