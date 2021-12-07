import time
from ftplib import FTP
import io
import os
import traceback


# import socket
# socket.setdefaulttimeout(5)


class myftp:
    def __init__(self, ip="192.168.2.18", user='gym', passwd='gym123qaz', port=21):
        self.ftp = FTP()
        self.ftp.set_debuglevel(0)  # 打开调试级别2，显示详细信息;0为关闭调试信息
        self.ip = ip
        self.user = user
        self.passwd = passwd
        self.port = port

    def login(self):
        try:
            self.ftp.connect(self.ip, self.port)  # 连接
        except IOError:
            errmsg = traceback.format_exc().splitlines()[-1]
            # print(errmsg)
            return errmsg
        self.ftp.login(self.user, self.passwd)  # 登录，如果匿名登录则用空串代替即可
        print(self.ftp.getwelcome())  # 显示ftp服务器欢迎信息
        self.bufsize = 1024  # 设置缓冲块大小
        self.basepath = f"{self.ftp.pwd()}"

    def upload(self, file_handler, filepath, path="test/photo_crop"):
        fdir, fname = os.path.split(filepath)
        self.path = f"{self.basepath}/{path}/{fdir}"
        try:
            self.ftp.cwd(self.path)
            pass
        except:
            try:
                self.ftp.mkd(self.path)
                self.ftp.cwd(self.path)
            except:
                print("wrong")

        for i in range(5):
            try:
                self.ftp.storbinary("STOR " + fname, file_handler, self.bufsize)  # 上传文件
                break
            except:
                self.login()
                time.sleep(1)
            print(f"{filepath}上传失败")

        self.ftp.set_debuglevel(0)
        file_handler.close()

    def quit(self):
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
    from PIL import Image
    from glob import glob

    imgs = glob(r"D:\uav\pictures\1114\2\*.JPG")[:2]
    start = time.time()
    ftp = myftp(ip="192.168.2.18", user='gym', passwd='gym123qaz')
    lmsg = ftp.login()
    if lmsg is not None and lmsg.find('ERROR'):
        print(lmsg)
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

        ftp.upload(file_handler=imgB, filepath='tt.jpg')
        end = time.time()
        t = end - start
        # print("Runtime is ：", t)
    ftp.quit()
