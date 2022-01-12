import re
import pymysql, time , datetime , json
from  Logger import create_logger 

class DataBaseInfo:
    def __init__(self ,env_index=1):
        self.log = create_logger(r"\AutoTest", 'test')
        self.host_list = ['localhost', '192.168.70.57']
        self.host = self.host_list[env_index]
        
        self.user_list = ['root', 'kerr']
        self.user = self.user_list[env_index]
        self.password = 'LF64qad32gfecxPOJ603'

        self.dbname = 'siteapi'
        self.db_con = self.mysql_conn()


    def mysql_conn(self):
        self._conn = pymysql.connect(
            host=   self.host,
            user = self.user ,
            passwd = self.password,
            db= self.dbname)
        return self._conn
    

    '''
    Status 1 為成功, 0 代表此次有錯誤
    '''
    def mysql_insert(self   , Data,  Site = 'AllSite' , Status= 1):# response_data 為 一個dict , 存放 到 DB
        try:
            db = self.db_con
            cursor = db.cursor()
        except Exception as e:
            self.log.error('DB 連線有誤 : %s '%e)
            return False


        #str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() ))
        try:
            date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "INSERT INTO site_data "  + "(Site, Status,Create_date , Data) VALUES( '{Site}', '{Status}', '{Create_date}', '{Data}'  )".format(ID = 1, 
            Site = Site , Status = Status ,  Create_date = date_time ,  Data = json.dumps(Data)     )# json.dumps 將python 字典轉成  db 的 json型態
            #self.log.info('insert sql: %s'%sql)
            
            cursor.execute(sql)
            db.commit()
            db.close()
        except Exception as e:
            self.log.error(' 資料 insert有誤 : %s'%e)
            return False

    def mysql_select(self , site_name = 'AllSite'):# site_name 預設 待 all site, 之後也有可能用到 單一site查詢
        try:
            db = self.db_con
            cursor = db.cursor()
        except Exception as e:
            self.log.error('DB 連線有誤 : %s '%e)
            return False
        
        try:
            sql = "select site, create_date, data  from site_data where site = '{site_name}'  order by ID desc limit 1;".format(site_name=site_name)
            self.log.info('select sql: %s'%sql)
            cursor.execute(sql)

            query = cursor.fetchall()# 出來 的資料 為一個 tuple , 個順序 顯示 相對應欄位的內容
            column=[index[0] for index in cursor.description  ]# 先取出 欄位
            data_dict = [dict(zip(column, row)) for row in query][0]  #query 為一個 tuple. loop取出後, 和 欄位 zip , 再轉成字典

            self.log.info('data_dict : %s'%data_dict)

            db.commit()
            db.close()
        
            return data_dict

        except Exception as e:
            self.log.error(' 資料 select : %s'%e)
            return False



con = DataBaseInfo()

