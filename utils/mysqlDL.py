import pymysql


class mysql:
    def __init__(self, h, u, passwd, p=3306):
        self.host = h
        self.user = u
        self.passwd = passwd
        self.port = p

    def connect(self, db):
        # 连接mysql数据库
        self.conn = pymysql.connect(host=self.host, user=self.user, passwd=self.passwd, database=db, port=self.port)
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


if __name__ == '__main__':
    codes = ["show table status WHERE NAME = 'risk_house_pic_file'",
             "SELECT id, source FROM t_uav_trajectory WHERE del_flag=0 AND file_id in (SELECT id FROM t_uav_file_info "
             "WHERE DATE_FORMAT( create_time, '%Y-%m-%d' ) ='2021-11-18' AND is_download = 1) ORDER BY file_id"]
    insert_code = ""
    print(codes[0][:6])
    results = mysql(h="192.168.2.18", u="root", passwd="123qaz", db="ming")

    results = list(results)
    results.sort(key=lambda x: x[0])
    result_list = []
    for result in results[0]:
        result_list.append(result[1])
    print(result_list)
