import pymysql
import time

import traceback


class mysql:
    def __init__(self, h="192.168.2.18", u="root", passwd="123qaz", p=3306):
        self.host = h
        self.user = u
        self.passwd = passwd
        self.port = p

    def connect(self, db):
        # 连接mysql数据库
        try:
            self.conn = pymysql.connect(host=self.host, user=self.user, passwd=self.passwd, database=db, port=self.port)
        except pymysql.err.OperationalError:
            errmsg = traceback.format_exc().splitlines()[-1]
            return errmsg
        # 得到一个游标
        self.cursor = self.conn.cursor()

    def my_select(self, codelist):
        results = []
        for code in codelist:
            # 只需要执行，不需要commit提交
            self.cursor.execute(code)
            # fetchone一次只能取出一条数据，相当于指针，取出一条数据后，指针指向后面那条数据
            r = self.cursor.fetchall()
            results.append(r)
        return results

    def my_insert(self, sql, val):
        self.cursor.executemany(sql, val)

        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def getlines_json(self, flydate):
        # 查询航线
        kcodes = [
            f"SELECT id, source FROM t_uav_trajectory WHERE del_flag=0 AND file_id in (SELECT id FROM t_uav_file_info "
            f"WHERE DATE_FORMAT( create_time, '%Y-%m-%d' ) = '{(flydate)}' AND is_download = 1) ORDER BY file_id;"]
        self.connect(db="ming")
        kmljson = self.my_select(kcodes)[0]
        self.close()
        return kmljson

    def get_existed_photos(self, existed_photos):
        codes = ["show table status WHERE NAME = 'risk_house_pic_file'",
                 f"SELECT fid, id FROM risk_house_pic_file WHERE file_path in {existed_photos}"]

        results = self.my_select(codelist=codes, )

        auto_increment = int(results[0][0][10])  # 自增id
        existedHidImgs = dict(results[1])

        return auto_increment, existedHidImgs

    def insert_data(self, existed_photos, matchedHousesImgs):

        self.connect(db="ming")
        auto_increment, existedHidImgs = self.get_existed_photos(existed_photos)
        valuesList = []
        for fid in matchedHousesImgs:

            uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            if fid in existedHidImgs:
                valuesList.append((existedHidImgs[fid], int(fid), 1, 1, str(matchedHousesImgs[fid]), uptime))
            else:
                valuesList.append((auto_increment, int(fid), 1, 1, str(matchedHousesImgs[fid]), uptime))
                auto_increment += 1

        insertCode = "replace into risk_house_pic_file(id, fid, damaged, zf, file_path, upload_time) values(%s,%s,%s,%s,%s,%s);"
        self.my_insert(sql=insertCode, val=valuesList)

        self.close()


if __name__ == '__main__':
    codes = ["show table status WHERE NAME = 'risk_house_pic_file'",
             "SELECT id, source FROM t_uav_trajectory WHERE del_flag=0 AND file_id in (SELECT id FROM t_uav_file_info "
             "WHERE DATE_FORMAT( create_time, '%Y-%m-%d' ) ='2021-11-18' AND is_download = 1) ORDER BY file_id"]
    sql = mysql()
    msg = sql.connect("ming")
    if isinstance(msg, str):
        print("=================")
    dbinfo, results = sql.my_select(codes)

    results = list(results)
    results.sort(key=lambda x: x[0])
    result_list = []
    for result in results[0]:
        result_list.append(result[1])
    print(result_list)
