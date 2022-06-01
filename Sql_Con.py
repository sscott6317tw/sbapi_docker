import re
import pymysql, time , datetime , json
from  Logger import create_logger 

class DataBaseInfo:
    def __init__(self ,env_index=0):
        self.log = create_logger(r"\AutoTest", 'test')
        self.host_list = ['localhost', '192.168.70.57', '192.168.74.194' ]#'192.168.74.194'
        self.host = self.host_list[env_index]
        
        self.user_list = ['root', 'kerr']
        self.user = self.user_list[env_index]
        self.password = 'LF64qad32gfecxPOJ603'

        self.dbname = 'siteapi'
        try:
            self.db_con = self.mysql_conn()
        except:
            pass

    def mysql_conn(self):
        self.log.info('DB 建立連線')
        self._conn = pymysql.connect(
            host=   self.host,
            user = self.user ,
            passwd = self.password,
            db= self.dbname)
        return self._conn
    

    '''
    Status 1 為成功, 0 代表此次有錯誤
    存放 all site 此次  回應時間平均 
    '''
    def site_response_insert(self   , Data ):# response_data 為 一個dict , 存放 到 DB
        try:
            db = self.db_con
            cursor = db.cursor()
        except Exception as e:
            self.log.error('DB 連線有誤 : %s '%e)
            return False


        #str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() ))
        try:
            date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_hour = datetime.datetime.now().strftime("%H")#執行時段

            sql = "INSERT INTO site_response_cal "  + "( Data ,Date_area , Create_date) VALUES( '{Data}', '{Date_area}', '{Create_date}'  )".format(ID = 1, 
             Data = json.dumps(Data)  ,  Create_date = date_time ,  Date_area = data_hour    )# json.dumps 將python 字典轉成  db 的 json型態
            self.log.info('insert sql: %s'%sql)
            
            cursor.execute(sql)
            db.commit()
            #db.close()
        except Exception as e:
            self.log.error(' site_response_insert 資料 insert有誤 : %s'%e)
            return False

    def site_data_insert(self   , Data, Device ,Site = 'AllSite' , Status= 1):# response_data 為 一個dict , 存放 到 DB
        try:
            db = self.db_con
            cursor = db.cursor()
        except Exception as e:
            self.log.error('DB 連線有誤 : %s '%e)
            return False


        #str_time= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() ))
        try:
            date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "INSERT INTO site_data "  + "(Site, Status,Create_date , Data , Device) VALUES( '{Site}', '{Status}', '{Create_date}', '{Data}', '{Device}'  )".format(ID = 1, 
            Site = Site , Status = Status ,  Create_date = date_time ,  Data = json.dumps(Data) ,Device = Device      )# json.dumps 將python 字典轉成  db 的 json型態
            self.log.info('insert sql: %s'%sql)
            
            cursor.execute(sql)
            db.commit()
            #db.close()
        except Exception as e:
            self.log.error(' site_data_insert 資料 insert有誤 : %s'%e)
            return False

    def site_data_select(self , site_name = 'AllSite'):# site_name 預設 待 all site, 之後也有可能用到 單一site查詢
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
            #db.close()
        
            return data_dict

        except Exception as e:
            self.log.error(' 資料 select : %s'%e)
            return False
    

    #query_num
    def site_response_select(self ):
        try:
            db = self.db_con
            cursor = db.cursor()
        except Exception as e:
            self.log.error('DB 連線有誤 : %s '%e)
            return False
        
        try:
            sql = "select * from site_response_cal order by ID desc limit 100"
            self.log.info('select sql: %s'%sql)
            cursor.execute(sql)

            query = cursor.fetchall()# 出來 的資料 為一個 tuple , 個順序 顯示 相對應欄位的內容
            column=[index[0] for index in cursor.description  ]# 先取出 欄位
            data_dict = [dict(zip(column, row)) for row in query]  #query 為一個 tuple. loop取出後, 和 欄位 zip , 再轉成字典

            self.log.info('data_dict : %s'%data_dict)

            db.commit()
            #db.close()
        
            return data_dict

        except Exception as e:
            self.log.error(' 資料 select : %s'%e)
            return False


#con = DataBaseInfo()

