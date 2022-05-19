#In[]

from ast import Try, excepthandler
from cmath import e
from collections import defaultdict
import execjs
import hashlib
from PIL import Image
import pytesseract,os,time
from  Logger import create_logger 
import pathlib
from Common import Common,betteam_trans
import csv,re
from Common import Common
import csv,re , requests
import urllib3 , json
import asyncio
from datetime import datetime
from aiowebsocket.converses import AioWebSocket
import json
from urllib.parse import urlparse
import threading
from bs4 import BeautifulSoup
urllib3.disable_warnings()

logger = create_logger(r"\AutoTest", 'test')

#In[]
class Login(Common):#取得驗證碼邏輯 
    def __init__(self,device="",sec_times='',stop_times='',url=''):
        super().__init__(sec_times,stop_times)
        #logger = create_logger(r"\AutoTest", 'test')
        #if device == 'Pc driver' or device == 'desktop':
            #self.dr = self.get_driver()
        import datetime;
        ts = datetime.datetime.now().timestamp()
        self.img_pic = pathlib.Path(__file__).parent.absolute().__str__() + "%s_login_code.jpg"%str(int(ts))
        self.download_waiting_time = 3
        self.url = url
        self.cookies = ""# 預設空, 會從驗證碼時,拿取 ASP.NET_SessionId
        #get_chrome_info = Common(sec_times='',stop_times='')
        #self.chrome_version = get_chrome_info.get_Chrome_version(split=False)
    
    def login_api(self, device,user,password =  '1q2w3e4r',url='',client='',central_account='',central_password='',
            site='', queue= ''):
        '''devive 為Pc 才會去叫 webdriver ,要取驗證碼'''
        if device in ['mobile','app']:
            mobile_api = Mobile_Api(device='app',  password=password, url=url ,client = client,
            sec_times=self.sec_times, stop_times=self.stop_times,site=site, queue= queue )

            login_rseult = mobile_api.mobile_login(user=user,central_account=central_account,
            central_password=central_password)# 初始 login為 None 一定先登入
            
            if login_rseult is False and site == '':
                return False
            

            '''
            All Site api 成功或 失敗 都是 回傳 mobile_api , 是用 erroe code msg 來給 AllSite 使用
            '''
            return  mobile_api
        else: #都是桌機
            desktop_api = Desktop_Api(device=device,user=user,url=url,client = client)


            login_rseult = desktop_api.desktop_login(central_account=central_account ,
            central_password=central_password)

            if login_rseult is False:
                return False
            elif 'Login Too Often' in str(login_rseult):
                return 'Login Too Often'

            return  desktop_api

    def validation(self):
    # 取得圖片
        #logger.info(self.img_pic)
        login_code = Image.open(self.img_pic)
        logger.info(login_code)
        # result.show()
        # 驗證碼圖片修正 轉為白底黑字
        identify_result = self.convert_img(login_code, 225)
        # result.show()
        pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR\\tesseract.exe'
        identify_result = pytesseract.image_to_string(identify_result).strip()
        # 刪除圖片
        try:
            os.remove(self.img_pic)
        except:
            pass
        logger.info('圖片刪除成功')
        return identify_result
    
    def convert_img(self,img, threshold):
        img = img.convert("L")
        # 處理灰度
        pixels = img.load()
        for x in range(img.width):
            for y in range(img.height):
                if pixels[x, y] < threshold:
                    pixels[x, y] = 255
                else:
                    pixels[x, y] = 0
        return img
    def assert_validation(self):# 驗證碼的流程, 寫成function, 如果有解析失敗,好retry
        
        while True:
            user_agent = self.dr.execute_script("return navigator.userAgent;")
            logger.info('user_agent: %s'%user_agent)
            self.headers['User-Agent'] = user_agent
            
            r = self.client_session.get(self.url  ,headers= self.headers,verify=False)# 需先拿 session url
            logger.info('url : %s'%r.url  )

            self.url = r.url
            now = int(time.time()*1000)
            login_code_url = '%s/login_code.aspx?%s'%(self.url , now)
            logger.info('login_code_url: %s'%login_code_url)
 
            self.dr.get(login_code_url)

            #self.img_pic = './login_code.jpg' 
            self.dr.get_screenshot_as_file(self.img_pic)
            for i in range(self.download_waiting_time):
                if os.path.isfile(self.img_pic):
                    logger.info('%s 圖片有找到'%self.img_pic)
                    break
                else: 
                    logger.info('圖片未找到')
                    time.sleep(1)
                    if i == self.download_waiting_time - 1:
                        raise IOError

            validate_result = self.validation()
            
            if validate_result.isdigit() is False:# 檢查取得的驗證碼是否都是數值,如果有字母 馬上retry
                logger.info('有英文字 %s,直接retry'%validate_result)
            elif len(validate_result) < 4:#長度小於4也要retry
                logger.info('長度小於4 %s,直接retry'%validate_result)
            else:
                logger.info('validate_result: %s'%validate_result)
               
                self.cookies = self.dr.get_cookies()
                #logger.info('cookies: %s'%self.cookies )
                #self.dr.close()
                break
        return validate_result

    def js_from_file(self,file_name):# 讀取js 加密邏輯  CFS
        """
        讀取js檔案
        :return:
        """
        with open(file_name, 'r', encoding='UTF-8') as file:
            result = file.read()

        return result



    def md(self,password,val):# md5 加密邏輯 ./DepositProcessLogin 登入加密 邏輯 使用 MD5(CFS(loginData.password) + loginData.validation)
        m = hashlib.md5()
        md5_str = str.encode(password) + str.encode(val)
        m.update(md5_str)
        sr = m.hexdigest()
        return sr

    def get_Pwekey(self):# 取得 pwekey 街口 ,mobile使用
        r = self.session.post(self.url  + '/Default/RefreshPKey',headers=self.headers,verify=False)
        try:
            PWKEY = r.json()['Data']['PWKEY']
            logger.info('PKey: %s'%PWKEY) 
            return PWKEY 
        except:
            logger.error('PKey: 取得失敗') 
            return False
    

#login_type 預設空字串, 是使用 athena 登入 
class Mobile_Api(Login):# Mobile 街口  ,繼承 Login
    def __init__(self,client,device="",url='',user='',password='',sec_times='',stop_times='',site='', queue= ''):
        super().__init__(device,sec_times,stop_times) 
        self.login_session = {}# key 為 user ,value 放 NET_SessionId
        self.url = url
        self.default_url = url
        self.login_type = ''# api site 為 空字串
        if 'athena' in self.url or 'nova88' in self.url or 'spondemo' in self.url or 'macaubet' in self.url:
            self.login_type = 'athena' # 是 api site 登入 還是  athena site登入 , login方式不一樣
        self.api_site = ''# 預設空
        self.password = password
        self.MatchId = {}# 存放 matchid value 放team
        self.MarketId = {}
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        self.count = 0 #用來跌加  請求個數
        self.stress_dict = defaultdict(list)# 用來 存放壓力測試 街口的 數據
        self.odds_type = 'Dec' #先預設為空，避免沒有執行 Odds type Change 就下注
        self.site = site
        self.error_msg = ''# 用來判斷 成功訊息 (AllSite.py)
        self.queue = queue

        #key 分別是 site , session_url , session ,value 分別放 list 
        self.stress_login_dict = defaultdict(list)#用來 存放 stress 壓測  login session 
        self.site_stress = {}# key 為 site , value 為 self.stress_login_dict

    '''
    共用 url 請求 的方式, 包含回傳 請求時間, 請求相關資訊放到 stress_dict, 避免每個新增街口, 都要寫一次
    '''
    def stress_request_post(self, request_data ,func_url  ): 
        self.count = self.count + 1
        self.stress_dict['request num'].append(self.count)
        self.stress_dict['request data'].append(request_data)
        start = time.perf_counter()
        #print(self.headers)
    
        r = self.client_session.post(self.url  + func_url, data = request_data,headers=self.headers,verify=False)
        #self.url = r.url
        self.stress_dict['request url'].append(self.req_url )

        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        logger.info("%s Request completed in %s s"%(func_url ,self.request_time ))
        self.stress_dict['request time'].append(self.request_time)

        return r

    '''
    共用 url 請求 的方式, 包含回傳 請求時間, 請求相關資訊放到 stress_dict, 避免每個新增街口, 都要寫一次
    '''
    def stress_request_get(self, func_url ,  request_data=''  ): 
        self.count = self.count + 1
        self.stress_dict['request num'].append(self.count)
        self.stress_dict['request data'].append(request_data)
        start = time.perf_counter()
        #print(self.headers)
        
        self.req_url = self.url  + func_url
        
        r = self.client_session.get(self.req_url ,headers=self.headers,verify=False)
        #self.url = r.url
        self.stress_dict['request url'].append(self.req_url)

        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        logger.info("%s Request completed in %s s"%(func_url, self.request_time ))
        self.stress_dict['request time'].append(self.request_time)

        return r

    def queue_object(self):# stress api 有用到的 街口  都要用 self.queue
        if self.queue == '':
            pass
        else:
            self.queue.put(self.stress_dict)
        return ''

        
    def Return_Bet_dict(self,assign_betype):
        return_dict = {}

        for bet_type in assign_betype:
            for index in self.Match_dict.keys():
                if bet_type in self.Match_dict[index].keys():
                    value_dict = {}
                    value_dict[bet_type] = self.Match_dict[index][bet_type]
                    return_dict[index] = value_dict
        index_list = list(self.Match_dict.keys())
        for index in index_list: #取出確認  return_dict 缺少哪個index ,隨機給
            if index in return_dict.keys():
                pass
            else:
                value_dict = {}
                bet_type = list(self.Match_dict[index].keys())[0]
                value_dict[bet_type] = self.Match_dict[index][bet_type]
                return_dict[index] = value_dict
        
        return return_dict


    '''
    athena 需叫 本地js , api site 直接 在 url 後面增加query 參數
    '''
    def mobile_login(self,user,central_account='',central_password='',site='',stress_url = ''):# Mobile Login街口邏輯
        
        self.user = user
        if self.login_type  == 'athena':# athena 登入
            common_js = execjs.compile(self.js_from_file('./login_js/mobile.js'))# 讀取 login js檔
            PKey = self.get_Pwekey()
            cfs_psswd = common_js.call("r", self.password ,PKey)#App 密碼加密,適用 密碼和 PKey 去做前端js處理
            logger.info('app cfs_psswd: %s'%cfs_psswd)
            if "nova88" in self.url:
                self.url = self.default_url
                login_data = 'Username={user}&Password={cfs_psswd}&Language=zh-CN&isGesture=false\
                &__tk=&detecas_analysis=%7B%22startTime%22%3A1630246986799%2C%22version\
                %22%3A%222.0.6%22%2C%22exceptions%22%3A%5B%5D%2C%22executions%22%3A%5B%5D%2C%22storages%22%3A%5B%5D%2C%22devices%22%3A%5B%5D%2C%22\
                enable%22%3Atrue%7D'.format(user=user, cfs_psswd=cfs_psswd)
            else:
                login_data = 'Username={user}&Password={cfs_psswd}&Language=zh-CN&isGesture=false\
                &skinMode=3%3D%3D&__tk=&detecas_analysis=%7B%22startTime%22%3A1630246986799%2C%22version\
                %22%3A%222.0.6%22%2C%22exceptions%22%3A%5B%5D%2C%22executions%22%3A%5B%5D%2C%22storages%22%3A%5B%5D%2C%22devices%22%3A%5B%5D%2C%22\
                enable%22%3Atrue%7D'.format(user=user, cfs_psswd=cfs_psswd)

            self.headers['X-Requested-With'] =  'XMLHttpRequest'
            self.headers['Content-Type'] =  'application/x-www-form-urlencoded; charset=UTF-8'
            #logger.info('headers: %s'%self.headers)
            start = time.perf_counter()# 計算請求時間用
            try:
                r = self.client_session.post(self.url  + '/Login/index',data=login_data,
                headers=self.headers,verify=False, timeout=10)
            except:
                logger.error('url 訪問 超過 10 s')
                self.error_msg = 'login get error : %s'%e
                return False
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            try:
                repspone_json = r.json()
                #logger.info('response: %s'%repspone_json)
                ErrorMsg = repspone_json['ErrorMsg']
                ErrorCode = repspone_json['ErrorCode']
                logger.info('ErrorMsg: %s'%ErrorMsg)
                logger.info('ErrorCode: %s'%ErrorCode)
                
                #if ErrorMsg != 'login_success':
                    #return ErrorMsg
                if ErrorMsg is None and str(repspone_json['ErrorCode']) == '0' :# 位存款帳號登入 會為 none
                    logger.info('未存款登入成功')
                else:
                    Data_url = repspone_json['Data']# 登入成功後, 需在get 一次 response 回傳的 url
                    if "nova88" in self.url :
                        if "nova88" in Data_url:
                            self.nova_set_odds_type_url = Data_url.split('/ValidateToken')[0]
                            r = self.client_session.get(Data_url, headers=self.headers,verify=False)
                        else:
                            self.nova_set_odds_type_url = self.url
                            r = self.client_session.get(self.url + Data_url, headers=self.headers,verify=False)
                    else:
                        r = self.client_session.get(self.url  + Data_url, headers=self.headers,verify=False)
                
                cookie_session = self.client_session.cookies.get_dict()
                NET_SessionId = cookie_session['ASP.NET_SessionId']
                logger.info('NET_SessionId: %s'%NET_SessionId )
                self.login_session[user] = NET_SessionId
                #logger.info('self.login_session: %s'%self.login_session)

                try:
                    r = self.client_session.get(self.url+ 'whoami.aspx',verify=False)
                    self.whoami_ip = self.return_IP(r= r)
                    logger.info('登入後 打whoami 取得 ip : %s'%self.whoami_ip)
                except:
                    logger.error('whoami 取得 ip有誤')
                    self.error_msg = 'whoami 取得 ip有誤'
                return True
            except Exception as e:
                logger.info('Login Api Fail: %s'%e)
                return False
        
        else: #api site登入

            '''
            這邊 api site 登入 , 如果登入 成功會回傳 True , 其餘失敗的 都會回傳 字串, 不會回傳 False, 因為 ALL Site 要接失敗訊息
            '''
            
            try:
                if 'stress_site' in site:
                    self.url = stress_url
                    #logger.info('stress url : %s'%self.url)
                    self.client_session = requests.Session()
                    strss_site_session = self.client_session

                r = self.client_session.get(self.url,verify=False,timeout=10)
                session_url = r.url # api site 需先拿到 session url 在做登入
                #logger.info('登入前 session url: %s'%session_url)
            except Exception as e:
                logger.error(' url 請求 有誤 : %s'%e)
                self.error_msg = 'login get error : %s'%e
                self.stress_login_dict['error'].append('false')#失敗 存放

                return self.error_msg
            
            
            
            
            
            #LicLogin , DepositLogin
            login_query = 'LicLogin/index?lang=en&txtUserName={user}&Password=1q2w3e4r&token=&skin=&CentralAccount={central_account}&CentralPassword={central_password}&menutype=&sportid=&leaguekey=&matchid=&isAPP=\
            &currencyName=&bdlogin=1&tsid=&SkinColor=&types=1%2C0%2Cl'.format(user=user,
            central_account=central_account,central_password=central_password)
            api_login_url = session_url.split('apilogin')[0] + login_query

            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9'
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            
            start = time.perf_counter()# 計算請求時間用
            try:# 這邊 try login 如果遇到 503 或者別問題
                r =  self.client_session.get(api_login_url, headers=self.headers,verify=False)
            
            except Exception as e:
                self.error_msg = 'Login 接口: %s'%e
                return self.error_msg
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            
            #logger.info('登入接口完 的 回復 url: %s'%r.url)# 登入後的轉導url
            if 'LicLogin/index' in r.url:
                logger.error('response : %s'%r.text)
                self.stress_login_dict['error'].append('false')#失敗 存放
                return False
            
            self.url = r.url.split('#Sports')[0]# 登入後 就是 拿這個 變數 去做後面 各個街口的使用
            #logger.info('登入後 的 session url: %s'%self.url)# 登入後的轉導url
            

            if 'Message' in self.url:
                self.error_msg = self.url.split('Message=')[1]
                return self.error_msg
            '''
            api site 不是每個 登入後的都會帶 session url ,ex: bbin
            這會再 showallodds 有不同的判斷
            '''
            if 's(' not in self.url:# 有session 的url 後面都會有 s(
                self.api_site = 'web'
            else:
               self.api_site = 'odds provider' 
            if site == 'stress_user' :# 壓測 才做這下面的 存放   壓測login user 方式
                new_dict = {} 
                new_dict['session'] =  self.client_session
                new_dict['url'] =  self.url
                self.site_stress[user] = new_dict
            elif 'stress_site' in site:#壓測 login site 方式
                site_name = site.split('stress_site_')[-1]
                self.stress_login_dict['site_name'].append(site_name)
                self.stress_login_dict['session'].append(strss_site_session)
                self.stress_login_dict['url'].append(self.url)

            else:
                pass
            
            try:
                r = self.client_session.get(self.url+ 'whoami.aspx',verify=False)
                self.whoami_ip = self.return_IP(r= r)
                logger.info('登入後 打whoami 取得 ip : %s'%self.whoami_ip)
            except:
                logger.error('whoami 取得 ip有誤')
                self.error_msg = 'whoami 取得 ip有誤'

            return True

    def GetReferenceData(self):#GetReferenceData/GetBettypeName?lang=en-US 

        r = self.stress_request_get( func_url = 'GetReferenceData/GetBettypeName?lang=en-US')
        try:
            repspone_json = r.json()
            len_response = len(repspone_json)
            msg = 'response len : %s'%len_response
            self.stress_dict['response'].append('msg: %s'%msg)

            logger.info('msg: %s '%(msg ) )
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('GetReferenceData Api Fail')
            return False


    def JSResourceApi(self): # /JSResourceApi/GetJSResource
        self.req_url = '/JSResourceApi/GetJSResource'
        r = self.stress_request_get( func_url = self.req_url )
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.error_msg =  ErrorCode
            self.stress_dict['response'].append('ErrorCode: %s'%self.error_msg )

            logger.info('ErrorCode: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('GetJSResource Api Fail')
            return False
        
    def GetStatusCount(self): #/MyBets/GetStatusCount
        data = 'currWC=0'
        self.req_url = '/MyBets/GetStatusCount'
        r = self.stress_request_post(request_data= data, func_url = '/MyBets/GetStatusCount' )
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)

            logger.info('ErrorCode: %s '%(ErrorCode ) )
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('MyBets/GetStatusCount Api Fail')
            return False

    def Statement_GetAllStatement(self):# /Statement/GetAllStatement_ch?datatype=0&bfday=1&_=
        now = int(time.time()*1000)
        self.req_url = '/Statement/GetAllStatement_ch?datatype=0&bfday=1&_=%s'%now
        r = self.stress_request_get( func_url = self.req_url)
        try:
            repspone_json = r.json()
            OpeningBalance = repspone_json['OpeningBalance'] 
            self.error_msg  = ' OpeningBalance : %s'%(OpeningBalance)
 
            self.stress_dict['response'].append('msg: %s'%self.error_msg )

            logger.info('msg: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg  = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('Statement_GetAllStatement Api Fail')
            return False

    def Statement_GetStatement(self):# '/Statement/GetStatementOVR?bfday=1&_='

        now = int(time.time()*1000)
        self.req_url = '/Statement/GetStatementOVR?bfday=1&_=%s'%now
        r = self.stress_request_get( func_url = self.req_url)
        try:
            repspone_json = r.json()
            ticketcount = repspone_json['ticketcount'] 
            self.error_msg  = ' ticket_count : %s'%(ticketcount)
 
            self.stress_dict['response'].append('msg: %s'%self.error_msg )

            logger.info('msg: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg  = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('Statement_GetStatement Api Fail')
            return False


    def Running_GetRunning(self):#/Running/GetRunningOVR
        now = int(time.time()*1000)
        self.req_url = '/Running/GetRunningOVR?RunningType=E&_=%s'%now
        r = self.stress_request_get( func_url = self.req_url)
        try:
            repspone_json = r.json()
            ticketcount = repspone_json['ticketcount'] 
            self.error_msg  = ' ticket_count : %s'%(ticketcount)
 
            self.stress_dict['response'].append('msg: %s'%self.error_msg )

            logger.info('msg: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg  = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('Running_GetRunning Api Fail')
            return False
    
    
    def Running_GetEarly(self): #Running/GetEarly

        now = int(time.time()*1000)
        self.req_url = '/Running/GetEarly_ch?datatype=0&_=%s'%now
        r = self.stress_request_get( func_url = self.req_url)
        try:
            repspone_json = r.json()
            stake_count = repspone_json['StakeCount']
            ticket_count = repspone_json['TicketCount'] 
            self.error_msg  = 'stake_count : %s , ticket_count : %s'%(stake_count, ticket_count)
 
            self.stress_dict['response'].append('msg: %s'%self.error_msg )

            logger.info('msg: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg  = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('Running_GetEarly Api Fail')
            return False

    
    def get_contirbutetor(self ):# /main/GetContributor
        
        self.req_url = '/main/GetContributor'
        data = 'isParlay=false&both=true&defaulteuro=false'
        r = self.stress_request_post(request_data= data, func_url = self.req_url )
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.error_msg =  ErrorCode
            self.stress_dict['response'].append('ErrorCode: %s'%self.error_msg)

            logger.info('ErrorCode: %s '%(self.error_msg ) )
            return True
        except:
            self.error_msg = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg) 
            logger.error('get_contirbutetor Api Fail')
            return False

    def statement_settle(self):
        r = self.stress_request_get( func_url = '/Statement/GetDBetList_ch?fdate=12%2F02%2F2021&datatype=8&isReport=false' )
        try:
            repspone_json = r.json()
            print(repspone_json)
            #ErrorCode = repspone_json['ErrorCode']
            #self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)

            logger.info('repspone_json: %s '%(repspone_json ) )
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('statement_settle Api Fali')
            return False


    def set_odds_type(self,odds_type='MY'):# /setting/SaveUserProfile
        self.odds_type = odds_type
        odds_type_dict = {'Dec' : '1','CN' : '2','Indo' : '3','MY' : '4','US' : '5'}
        data = 'DefaultLanguage=en-US&OddsType={odds_type}&BetStake=0&BetterOdds=false&oddssort=2&inpbetStake=0'.format(odds_type=odds_type_dict[odds_type])
        if "nova88" in self.url:
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9'
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.url = self.nova_set_odds_type_url
            #self.headers['Cookie'] = "ASP.NET_SessionId=" + self.client_session.cookies.get_dict()['ASP.NET_SessionId']
            #self.headers['Cookie'] = "ASP.NET_SessionId=zsas5pqboaj1eb30novyhuda" 
        
        #logger.info('NET_SessionId: %s'%self.client_session.cookies.get_dict()['ASP.NET_SessionId'])
        self.req_url = '/setting/SaveUserProfile'
        start = time.perf_counter()# 計算請求時間用
        r = self.client_session.post(self.url  + self.req_url  ,data=data,headers=self.headers,verify=False)
        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)
            logger.info('set_odds_type ErrorCode: %s '%(ErrorCode ) )
            return True
        except:

            self.error_msg = r.text
            logger.error('Setting Odds Type Api Fail response :%s'%self.error_msg )
            #self.stress_dict['response'].append(r.text) 
            return False

    def statement_running(self):
        r = self.stress_request_get( func_url = '/Running/GetRunningOVR?RunningType=E' )
        try:
            datatype = r.json()['datatype']
            ticketcount = r.json()['ticketcount']


            logger.info('datatype: %s , ticketcount: %s '%(datatype, ticketcount ) )
            #print(repspone_json)
            #ErrorCode = repspone_json['ErrorCode']
            #self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)

            
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('statement_running Api Fali')
            return False
        


    def balance(self):# /balance/GetAccountInfo # showallodds url
        
        data = 'localtime=8'
        #self.headers['Referer'] = self.url
 

        self.req_url = '/balance/GetAccountInfo'
        r = self.stress_request_post(request_data= data, func_url = self.req_url)

        #r = self.client_session.post(self.url  + '/balance/GetAccountInfo', data=data,headers=self.headers)
       
        try:
            repspone_json = r.json()
            Bal = repspone_json['Data']['Bal']
            BCredit = repspone_json['Data']['BCredit']
            self.error_msg = 'Bal: %s , BCredit: %s '%(Bal ,BCredit ) 
            self.stress_dict['response'].append(self.error_msg  )
            self.OddsServerUrl = repspone_json['Data']['OddsServerUrl']# 如果為none 代表是走web
            
            logger.info('self.OddsServerUrl: %s'%self.OddsServerUrl)
            return True
        except:
            self.error_msg = r.text
            logger.error('balance error :%s'%self.error_msg )

            self.stress_dict['response'].append(self.error_msg)

            return False

    def UpdateOdds (self):# /Odds/UpdateOdds
        
        data = '{"GameId":1,"DateType":"l","BetTypeClass":"OU","Gametype":0}'
        #self.headers['Referer'] = self.url
        self.headers['Content-Type'] = 'application/json;charset-UTF-8'#不用這個 會失敗
        r = self.stress_request_post(request_data= data, func_url = '/Odds/UpdateOdds' )

        #r = self.client_session.post(self.url  + '/balance/GetAccountInfo', data=data,headers=self.headers)
       
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            HKey = repspone_json['HKey']
            self.stress_dict['response'].append('ErrorCode: %s, HKey: %s'%(ErrorCode,HKey))

            logger.info('ErrorCode: %s, HKey: %s'%(ErrorCode,HKey) ) 
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
            logger.error('UpdateOdds Api Fali')

            return False


    '''
    type 帶 test 就 可以 忽略 testing 比賽  ,bet_type 可帶 其他(ex: parlay)
    '''
    def ShowAllOdds(self,type='',market=['e'],filter='',sport='Soccer',bet_type='OU',stress_type=''):# 取得 MatchId 傳給 GetMarket , 還有取得 TeamN 回傳給 DoplaceBet  的 home/away
        self.MatchId = {} #先清空
        
        # e為 早盤, t為 today
        #market = 't'# 預設 today
        self.sport = sport
        self.bet_type = bet_type
        if "nova88" in self.url or sport == "E-Sports":
            bet_type = "OU"
        else:
            bet_type = bet_type
        if 'o' in market: #outright game_id 為 999，game_type 為平常下注的 sports gameid
            self.gameid = 999
            self.gametype = self.game_mapping(self.sport)
            market = ['t']
        else:  
            self.gameid = self.game_mapping(self.sport)# 後面 get market 和 betting 就不用在多傳 gameid 參數了, 統一在這宣告
            self.gametype = 0
        for market in market:
            data = 'GameId=%s&DateType=%s&BetTypeClass=%s&Gametype=%s'%(self.gameid  ,market,bet_type,self.gametype)# 先寫死cricket, 之後優化
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            
            try:# athen 和部分api的 ,走 一個邏輯
                if self.login_type  == 'athena' or self.api_site =='web' or stress_type == 'stress':# athena   
                    self.req_url = '/Odds/ShowAllOdds'
                    r = self.stress_request_post(request_data= data, func_url = self.req_url )

                    #r = self.client_session.post(self.url  + '/Odds/ShowAllOdds',data=data,headers=self.headers)
                    repspone_json = r.json()
                    self.odds_provider = ''
                else:
                    if 'Authorization' not in list(self.headers.keys()):
                        logger.info('使用api site ,需先打 /Login/ExtendToken 拿出 Bearer')
                        r = self.client_session.post(self.url+ '/Login/ExtendToken',headers=self.headers,verify=False)
                        Bearer_data = r.json()['Data']# 需傳到 showallodds
                        logger.info('Bearer_data: %s'%Bearer_data)
                        
                        self.headers['Authorization'] = 'Bearer  %s'%Bearer_data
                    
                    try:
                        
                        self.req_url = 'https://%s/'%self.OddsServerUrl + '/Odds/ShowAllOddsApi?'+data
                    
                    except:
                        logger.info('需先打balance 拿取 server url')
                        self.balance()
                        self.req_url = 'https://%s/'%self.OddsServerUrl + '/Odds/ShowAllOddsApi?'+data
                    
                    self.odds_provider = 'true'

                    start = time.perf_counter()# 計算請求時間用
                    r = self.client_session.get(self.req_url  ,headers=self.headers,verify=False)
                    self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間


                    repspone_json = r.json()
                #logger.info('repspone_json: %s'%repspone_json)   
            except Exception as e:
                logger.error('error : %s'%e)
                self.error_msg = r.text
                logger.info('mobile ShowAllOdds Api Fail : %s'%self.error_msg)
                
                return False
            
            try:
                Data = repspone_json['Data']# 字典 裡面包兩個key, NewMatch 和 TeamN
                NewMatch = Data['NewMatch']# list
                TeamN = Data['TeamN']# dict
                LeagueN = Data['LeagueN']
                if len(NewMatch) == 0:
                    return "No Market"
                #logger.info('TeamN: %s'%TeamN)
                for index,dict_ in enumerate(NewMatch):
                    #logger.info('index: %s'%index)
                    team_name = {}
                    if self.gameid != 999:
                        TeamId1 = dict_['TeamId1']
                        TeamId2 = dict_['TeamId2']
                        LeagueId = dict_['LeagueId']
                        League_name = LeagueN[str(LeagueId)]
                    
                        if type == '':# 不能有test 的賽事 
                            if (len(NewMatch) == 1 and bet_type == 'OU') or (len(NewMatch) == 1 and bet_type == 'more'): #僅有 Test 的比賽，就不要移除 Test 的比賽，不寫再主判斷是為了到時候 Parlay 要修改，或是 LeaguID 只有一個的話
                                pass
                            else:
                                if any(test_parlay in League_name for test_parlay in  ['TESTING','test','Test','测试'] ) and 'Test Match' not in League_name:# 如果 不是要 針對test 然後 testing 又再 league ,不能串
                                    continue
                        # type 帶 test 就 可以 忽略 testing 比賽 
                        team_name['Team1'] = TeamN[ str(TeamId1) ]
                        team_name['Team2'] = TeamN[str(TeamId2) ]
                        team_name['League'] = League_name
                        team_name['Market'] = market
                        
                        #logger.info('team_name: %s'%team_name)
                        MatchId = dict_['MatchId']# 取出Matchid ,並當作 Key
                    else:
                        team_name['Market'] = market
                        MatchId = dict_['MatchId']
                        team_name['League'] = LeagueN[str(MatchId)]
                    self.MatchId[MatchId] = team_name# MatchId 當key ,value為 teamname
            except Exception as e:
                logger.error('ShowAllOdds: %s'%e)
                return False

        #logger.info('%s'%list(self.MatchId))
        if  filter != '' and len(filter) != 0 :# 只拿指定 的match id , 防呆 fiter如果帶空list
            for key in list(self.MatchId):
                if str(key) not in filter:
                    del self.MatchId[key]
            if len(self.MatchId) == 0: #寫在裡面判斷是因為，要確定 Match ID List不為 0，所以是 Filter 的問題
                return "No MatchID"
        elif "Number Game" in self.sport:
            for key in list(self.MatchId):
                if self.sport != str(self.MatchId[key]['League']):
                    del self.MatchId[key]
            if len(self.MatchId) == 0: #寫在裡面判斷是因為，要確定 Match ID List不為 0，所以是 Filter 的問題
                return "No Market"
        if self.gameid == 186 or self.gameid == 180: #如果是 Virtual Tennis & Soccer 抓第一個很容易錯，固定抓第二個
            new_MatchId_dict = {}
            new_MatchId_dict[list(self.MatchId)[2]] = self.MatchId[list(self.MatchId)[2]]
            self.MatchId = new_MatchId_dict
        len_matchid = len(self.MatchId)
        #logger.info('self.MatchId: %s'%self.MatchId)
        logger.info('len MatchId: %s'%len_matchid )
        self.stress_dict['response'].append('len MatchId: %s'%len_matchid )

        if len_matchid < 3:
            if len_matchid == 0:
                return "No Market"
            else:
                logger.info('長度小於3 無法串票')
                return 'False'
        else:
            return True



    '''
    這邊為 product 上 呼叫 get market 方式 , getmarkets/ getmarketsapi 
    data 為一個 list 裡包 多個  matichid , 並送出一個請求
    '''
    def New_GetMarkets(self):
        self.Match_dict = {}

        market_data_list = []#存放  字典的list
        for index,match_id in enumerate(self.MatchId.keys()):
            self.MarketId = {}
            market = self.MatchId[match_id]['Market']
            #logger.info('match_id : %s, 資訊: %s'%(match_id, self.MatchId[match_id]))
            if self.gameid == 999:
                data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":self.gametype}
            else:
                if self.gameid == 50 and "more" in self.bet_type: #當 Sports 為 Cricket，Gametype 為 1
                    data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":1}
                else:
                    data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":0}
            
            market_data_list.append(data)
            if index == 4:# 固定抓出 前面 5個 matchid
                break

        try:

            logger.info('market_data_list : %s'%market_data_list ) 
            start = time.perf_counter()# 計算請求時間用
            
            self.headers['Content-Type'] =  'application/json;charset-UTF-8'
            if self.odds_provider == '':# web
                self.req_url = self.url  + '/Odds/GetMarkets'
            else:# odds provider
                self.req_url = 'https://%s'%self.OddsServerUrl + '/Odds/GetMarketsApi'

            logger.info('get market url: %s'%self.req_url)

            r = self.client_session.post(self.req_url , data = json.dumps(market_data_list) ,headers= self.headers 
            ,verify=False  )
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間

            repspone_json = r.json()
            #logger.info('repspone_json: %s'%repspone_json) 
        except Exception as e:
            logger.error('mobile GetMarkets error: %s'%e)
            self.error_msg = r.text 
            logger.error('mobile GetMarkets Api Fail : %s'%self.error_msg)
            return False
        
        import random #亂數排列字典，讓程式不要重複下到原本的 Match ID
        match_id = list(self.MatchId.keys())
        random.shuffle(match_id)

        MatchId_value = self.MatchId[match_id[0]]
        #logger.info('MatchId_value: %s'%MatchId_value)

        match_key = list(repspone_json['Data'].keys())
        ran_index = random.randint(0, len(match_key)-1 )

        NewOdds = repspone_json['Data'][match_key[ran_index]]   ['NewOdds']
        
        for index, dict_ in enumerate(NewOdds):
            new_dict = {}
            MarketId = dict_['MarketId']
            new_dict['MatchId'] = dict_['MatchId']
            new_dict['BetTypeId'] = dict_['BetTypeId']
            new_dict['Line'] = dict_['Line']
            new_dict['Pty'] = dict_['Pty']
            Selecetion_key =  list(dict_['Selections'].keys())# 為一個betype 下面 所有的bet choice

            for bet_choice_index, bet_choice in enumerate(Selecetion_key): 
                odds = dict_['Selections'][bet_choice]['Price']
                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                new_dict['odds_%s'%bet_choice_index] = odds


            new_value = MatchId_value.copy()# 原本
            new_value.update(new_dict)# 新的放進來
            self.MarketId[MarketId] = new_value


        Market_value = self.MarketId
        self.Match_dict[0] = Market_value
        #logger.info('self.Match_dict[0] : %s'%self.Match_dict[0])



    '''
    parlay_len 預設 給3 是 找三個match 來串即可, 如果不是 3 就是 給其他長度
    BetType 預設為 parlay . parlaymore 為更多 bet

    取得   MarketId(oddsid), Price(odds) , BetTypeId
    '''
    def GetMarket(self,bettype_id='',not_bettype_id='',urgent_use=False): #not_bettype_id 是用來確認如果前面有下注過，就需要找 New_odds 有超過 2 的 League 來下注
        if 'parlay' in self.bet_type and urgent_use != True: #urgent_use 是用來讓 Parlay 不要抓三個 Match ID，我只要一個就好
            parlay_len = '3'
        else:
            parlay_len = '1'
        self.Match_dict = {}# key 當作 index, value 存放 該match id 裡所有 的bettype(self.MarketId)

        #if self.bet_type == 'more' or 'parlay' in self.bet_type: 
        import random #亂數排列字典，讓程式不要重複下到原本的 Match ID
        dict_key_is = list(self.MatchId.keys())
        random.shuffle(dict_key_is)
        new_dic = {}
        for key in dict_key_is:
            new_dic[key] = self.MatchId.get(key)
        self.MatchId = new_dic

        for index,match_id in enumerate(self.MatchId.keys()):
            #print(match_id)
            self.MarketId = {}
            market = self.MatchId[match_id]['Market']
            logger.info('match_id : %s, 資訊: %s'%(match_id, self.MatchId[match_id]))
            if self.gameid == 999:
                data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":self.gametype}
            else:
                if self.gameid == 50 and "more" in self.bet_type: #當 Sports 為 Cricket，Gametype 為 1
                    data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":1}
                else:
                    data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":0}
            try:

                self.req_url = '/Odds/GetMarket'
                start = time.perf_counter()# 計算請求時間用
                r = self.client_session.post(self.url  + self.req_url ,data=data,headers=self.headers,verify=False)
                self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間

                repspone_json = r.json()
                #logger.info('repspone_json: %s'%repspone_json) 
            except:
                self.error_msg = r.text 
                logger.error('mobile GetMarket Api Fail : %s'%self.error_msg)
                return False
            try:
                # 回傳的 資料結構不同
                if "more" in self.bet_type:
                    NewOdds = repspone_json['Data']['Markets']['NewOdds']# 一個list 裡面包一個長度的dict
                    SpMatch_odds_list = repspone_json['Data']['SpMatch']['NewMatch'] #會有 list 
                    for SpMatch in  SpMatch_odds_list:
                        for SpMatch_market_odds in SpMatch['Markets']:
                            try:
                                NewOdds.append(SpMatch_market_odds)
                            except:
                                NewOdds = []
                                NewOdds.append(SpMatch_market_odds)
                    try:
                        if urgent_use == True:
                            if self.gameid == 8 or self.gameid == 5: #Baseball 打 More，只會抓取到 More 的 Bettype 所以判斷 2 即可
                                if len(NewOdds) < 2:
                                    continue
                            else:
                                if len(NewOdds) < 8:
                                    continue
                        else:
                            pass
                    except: #有 League 是完全沒有 More 打了會回傳 None 值
                        continue
                else:
                    NewOdds = repspone_json['Data']['NewOdds']
                    if not_bettype_id != '': #Baseball 打 More，只會抓取到 More 的 Bettype 所以判斷 2 即可
                        if len(NewOdds) < 2:
                            continue
                    else:
                        pass
                if bettype_id != '' and self.gameid != 999: #判段於此 MatchID 是否有我要的 Bettype ID
                    if "'BetTypeId': %s"%bettype_id in str(NewOdds):
                        pass
                    else:
                        continue
                MatchId_value = self.MatchId[match_id]
                
                for dict_ in NewOdds:#list包字典# ,裡面 一個dict 會有 很多 marketid (Oddsid)要取得
                    #logger.info('dict: %s'%dict_)
                    new_dict = {}
                    if self.gameid != 999:
                        try:
                            if 'hdp2' in str(dict_) : #給 Match Handicap & Total 帶入的值
                                new_dict['hdp2'] = dict_['hdp2']
                        except:
                            pass
                        MarketId = dict_['MarketId']
                        new_dict['MatchId'] = dict_['MatchId']
                        new_dict['BetTypeId'] = dict_['BetTypeId']
                        
                        new_dict['Line'] = dict_['Line']
                        new_dict['Pty'] = dict_['Pty']
                        
                        Selecetion_key =  list(dict_['Selections'].keys())# 為一個betype 下面 所有的bet choice

                        for bet_choice_index, bet_choice in enumerate(Selecetion_key): 
                            odds = dict_['Selections'][bet_choice]['Price']
                            new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                            new_dict['odds_%s'%bet_choice_index] = odds
                    else:
                        MarketId = dict_['MarketId']
                        new_dict['MatchId'] = dict_['MatchId']
                        new_dict['TeamId'] = dict_['TeamId']
                        new_dict['odds_0'] = dict_['Price']

                    new_value = MatchId_value.copy()# 原本
                    new_value.update(new_dict)# 新的放進來
                    self.MarketId[MarketId] = new_value
                    
                Market_value = self.MarketId
                if bettype_id == '' and "more" not in self.bet_type and not_bettype_id == '':
                    self.Match_dict[index] = Market_value
                    if index == int(parlay_len) - 1:
                        logger.info('串%s場即可'%parlay_len)
                        #logger.info(self.MarketId)
                        break
                else:
                    self.Match_dict[0] = Market_value
                    if index >= int(parlay_len) - 1:
                        logger.info('串%s場即可'%parlay_len)
                        #logger.info(self.MarketId)
                        break


            except Exception as e:
                logger.error('GetMarket: %s'%e)
                return False
        if bettype_id != '' and len(self.Match_dict) == 0:
            return "No BetType ID"
        elif len(self.Match_dict) == 0 and 'more' in self.bet_type: #用來判斷 No More Bettype
            return "No More BetType"
        logger.info('self.Match_dict 0 : %s'%len(self.Match_dict[0] ))
        if int(parlay_len) ==3:
            logger.info('self.Match_dict 1 : %s'%len(self.Match_dict[1]))
            logger.info('self.Match_dict 2: %s'%len(self.Match_dict[2]))
        else:
            #logger.info('self.Match_dict[0] : %s'%self.Match_dict[0])
            return self.Match_dict[0]

    def Betting_response(self,response,times,BetTypeId=''):# 針對 投注 回復 做解析
        try:
            repspone_json = response.json()
        except:
            self.error_msg = response.text
            return False

        if 'parlay'  in self.bet_type:
            Data = repspone_json['Data']
            response_code = str(Data['Code'])
            Message = Data['Message']
            if response_code == '45':# HDP/OU has been changed
                logger.error('ErrorMsg: %s'%repspone_json['ErrorMsg'] ) 
                logger.info('Message: %s'%Message)
                
                print(self.BetTypeId_list)
                #self.fail_bettype.append(BetTypeId_list[0])
                return False
            
            elif response_code == '-91':# update odds
                logger.info('Message: %s'%Message)
                logger.info('休息 兩秒鐘 再做')
                return Message

            elif response_code == '15':# odds has changed
                logger.info('Message: %s'%Message)
                ItemList = Data['ItemList']
                logger.info('ItemList: %s'%ItemList)# 一個list 裡面包 多個dict ,確認 每個 單 是否都有 odds changed
                
                
                odds_change_dict = {}# 變更後的odds , key 為 matchid , value 為 odds
                for dict_ in ItemList:
                    if str(dict_['Code']) == '15':# odds changed
                        Matchid = dict_['Key']
                        odds_change = dict_['Message'].split('to')[-1].strip('.').replace(' ','')# 切割完, 在移除最後一個 . 移除空白
                        logger.info('odds_change: %s'%odds_change)
                        odds_change_dict[Matchid] = dict_['Message']    
                logger.info('odds_change_dict: %s'%odds_change_dict)
                return odds_change_dict
                
                
            elif response_code in ['0','1']:# 投注成功
                self.order_value = {}
                self.order_value['Message'] = Message
                
                TransId_Combo = Data['TransId_Combo']
                TransId_System = Data['TransId_System']
                TransId_Lucky = Data['TransId_Lucky']

                TotalPerBet =  Data['TotalPerBet']
                self.order_value['TotalPerBet'] = TotalPerBet
                FinalBalance = Data['FinalBalance']
                self.order_value['FinalBalance'] = FinalBalance
                
                if TransId_Combo in ['0','']:
                    if TransId_System in ['0','']:
                        self.order_value['TransId_Cash'] = TransId_Lucky
                        for idx,bet_info in enumerate(self.BetTypeId_list):
                            for _dict in Data['ItemList']:
                                self.BetTypeId_list[idx]['TransId'] = _dict['TransId']
                                break
                    else:
                        self.order_value['TransId_Cash'] = TransId_System

                else:
                    self.order_value['TransId_Cash'] = TransId_Combo

                self.order_value['BetTypeId_list'] = self.BetTypeId_list

                logger.info('order_value: %s'%self.order_value)
                return True
            
            else:#例外 沒抓到的 code
                logger.info('response_code : %s'%response_code)
                logger.info('Message: %s'%Message)
                return 'Bet Fail !'
        else:# single bet
            '''
            #  ItemList 為一個 list ,裡面 放各資訊 字典 
            '''
            self.order_value = {}
            Itemdict = repspone_json['Data']['ItemList'][0]# Itemdict 為一個字典
            logger.info('betting response Error Code: %s'%repspone_json['Data']['Common']['ErrorCode'])

            self.order_value['TransId_Cash'] = Itemdict['TransId_Cash']
            #self.order_value['Message'] = Itemdict['Message']
            logger.info('betting response message: %s'%Itemdict['Message'])
            #logger.info('self.post_data: %s'%self.post_data)
            if any(error_code in Itemdict['Message'] for error_code in  ['Odds has changed','maximum number of bets','min','updating odds',"has been changed","is closed","System Error","temporarily closed","IN-PLAY"] ):
                error_msg = Itemdict['Message']
                if 'maximum number of bets' in error_msg:
                    error_msg = 'maximum number of bets has been exceeded for this match.'
                self.error_msg = error_msg
                logger.error('response : %s'%Itemdict['Message'] )
                return Itemdict['Message']
            else:
                pass
            
            if self.site == '':
                try:
                    #order_value['DisplayOdds'] = Itemdict['DisplayOdds']
                    #BetRecommends = Itemdict['BetRecommends'][0]# 為一個 list ,裡面含 各個 bet type資訊，這個不是此注單的資訊，而且下方建議投注的資訊
                    match_key = Itemdict['Key'].split('_')[0]
                    self.order_value['oddsid'] = match_key
                    if self.gameid != 999:
                        if self.betting_info['Pair/DecOdds'] == 0 :
                            self.order_value['odds_type'] = self.odds_type
                        else:
                            self.order_value['odds_type'] = "Dec"
                        try: #給 DoplaceBet 使用的
                            self.order_value['Line'] = self.Line
                        except:
                            pass
                        self.order_value['LeagueName'] = self.MarketId[int(match_key)]['League'].replace(' ','').split('|')[0]
                        BetTypeId = self.MarketId[int(match_key)]['BetTypeId']
                        with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                        # 讀取 CSV 檔案內容
                            rows = csv.reader(csvfile)
                            # 以迴圈輸出每一列
                            for row in rows:
                                if str(BetTypeId) == str(row[0]):
                                    self.order_value['BettypeName'] = row[1]
                                    break
                                else:
                                    pass
                        self.order_value['BetChoice'] = self.betting_info['bet_team']
                        self.order_value['Odds'] = str(self.betting_info['odds'])
                    else:
                        self.order_value['odds_type'] = "Dec"
                        self.order_value['Line'] = self.Line
                        self.order_value['LeagueName'] = self.MarketId[int(match_key)]['League'].replace(' ','').split('|')[0]
                        self.order_value['BettypeName'] = 'Outright'
                        self.order_value['Odds'] = str(self.betting_info['odds'])

                    logger.info('order_value : %s'%self.order_value)
                    #方便查看資料的
                    pass_txt = open('Config/pass.txt', 'a+')
                    pass_txt.write(str(self.order_value)+'\n')
                    pass_txt.close()
                    return True
                except:
                    return False
            else:
                try:
                    self.order_value['DisplayOdds'] = Itemdict['DisplayOdds']
                    
                    #BetRecommends = Itemdict['BetRecommends'][0]# 為一個 list ,裡面含 各個 bet type資訊
                    #order_value['BettypeName'] = BetRecommends['BettypeName']
                    #order_value['LeagueName'] = BetRecommends['LeagueName']
                    self.order_value['site'] = self.site
    
                    logger.info('order_value  : %s'%self.order_value)
                    return self.order_value
                except:
                    return False
                   
    '''
    already_list 是有做過的bettype , 拿來 驗證 做過的bettype, 做 random bettype 5次 
    parlay_type 1 為 mix parlay , 2 為 Trixie (4 Bets) , 為空 為 Single bet
    bet_team_index 是拿來 要做 betttype 的 哪個bet choice , 一個bettype 下 正常會有 bet_team_1 , bet_team_2 ...甚至更多
    assign_list 是用來指定 bettype下注, 空字串就是不用,走random ,有值的話 , key 為 market value為
    '''
    def DoplaceBet(self,already_list=[],bet_team_index='0',parlay_type='1',times='',bettype_id='',not_bettype_id='',new_match_key_dict='',sport_list = ''): #not_bettype_id 是為了不要重複下到同一個 Bettype
        import random
        '''
        SportName 和 gameid 之後 做動態傳入,目前寫死 
        '''
        self.BetTypeId_list = []
        self.Odds_dict = {}# key 為 match id ,value 為 odds
        Parlay_dict = {'1' : '1', '2': '4', '3': '7' }# value 是拿來 給 parlay data 的  BetCount 和 TotalStake
        
        if new_match_key_dict != '':# cross market
            self.Match_dict = new_match_key_dict

        len_Match_dic= len(self.Match_dict)
        logger.info('len_Match_dict : %s'%len_Match_dic)

        try:
            data_str = ""# 需loop 慢慢加起來
            for index_key in self.Match_dict.keys():#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                if sport_list != '': #由於 Cross Sports Parlay 的運動會隨機，所以再傳入一個 List
                    self.sport = sport_list[index_key]
                    self.gameid = self.game_mapping(self.sport)
                #logger.info('index_key : %s'%index_key)
                Match = self.Match_dict[index_key]# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
                #logger.info('len : %s'%len(Match))

                Match_key_list = list(Match.keys())# list裡面放 bettype
                find_bet_type_id = False
                if self.bet_type != 'more': #more 要排除小於 3 的 Bettype ID
                    from random import shuffle #用來把 list 打亂可以不用一值下同一場比賽
                    if bettype_id != '' and self.gameid != 999:
                        shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] == bettype_id:
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No BetType ID"
                    elif not_bettype_id != '' and self.gameid != 999 :
                        shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != int(not_bettype_id):
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID %s"%not_bettype_id
                        pass
                    else:
                        shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            Match_key_list = []
                            Match_key_list.append(Match_key)
                            find_bet_type_id = True
                            break
                        if find_bet_type_id == False:
                            return "No BetType ID"
                else:
                    New_Match_key_list = []
                    if not_bettype_id != '':
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != int(not_bettype_id) and Match[Match_key]['BetTypeId'] >= 4:
                                New_Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID %s"%not_bettype_id
                        else:
                            Match_key_list = New_Match_key_list
                    else:
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] >= 4: 
                                New_Match_key_list.append(Match_key)
                                find_bet_type_id = True
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No More BetType"
                        else:
                            Match_key_list = New_Match_key_list
                        pass
                if self.gameid != 999:
                    retry_count = 0
                    while True:
                        self.betting_info = {} #儲存我下注的值 
                        print(len(Match_key_list)-1 )
                        ran_index = random.randint(0, len(Match_key_list) -1  )
                        Ran_Match_id =  Match_key_list[ran_index]# 隨機取出 odds id
                        logger.info('Ran_Match_id: %s'%Ran_Match_id)
                        
                        BetTypeId = Match[Ran_Match_id]['BetTypeId']
                        self.betting_info['Pair/DecOdds'] = Match[Ran_Match_id]['Pty'] #抓取 Pair or Dec Odds
                        logger.info('BetTypeId: %s'%BetTypeId)

                        if BetTypeId not in already_list:
                            logger.info('BetTypeId: %s 沒有投注過 ,成立'%BetTypeId)
                            break
                        logger.info('BetTypeId: %s 已經存在過注單裡 ,retry : %s'%(BetTypeId, retry_count ))
                        retry_count = retry_count + 1
                        if retry_count >= 10:   
                            break

                    Matchid = Match[Ran_Match_id]['MatchId']
                    Team1 = Match[Ran_Match_id]['Team1']
                    Team2 = Match[Ran_Match_id]['Team2']
                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        odds = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                    except:
                        odds = Match[Ran_Match_id]['odds_0']
                    self.betting_info['odds'] = odds

                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        bet_team = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                        self.betting_info['bet_team'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                    except:
                        bet_team = Match[Ran_Match_id]['bet_team_0']
                    
                    oddsid = Ran_Match_id
                    BetTypeId = Match[Ran_Match_id]['BetTypeId']

                    if 'parlay' in self.bet_type: #先把值存到這裡方便 Debug
                        self.betting_info['LeagueName'] = Match[Ran_Match_id]['League'].split('|')[0]
                        self.betting_info['BettypeName'] = BetTypeId
                        with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                        # 讀取 CSV 檔案內容
                            rows = csv.reader(csvfile)
                            # 以迴圈輸出每一列
                            for row in rows:
                                if str(BetTypeId) == str(row[0]):
                                    self.betting_info['BettypeName'] = row[1]
                                    break
                                else:
                                    pass
                        self.betting_info['MatchID'] = Match[Ran_Match_id]['MatchId']
                    #Line = Match[Ran_Match_id]['Line']
                    #if  Line == 0:
                        #Line = ''
                
                    #if index > 2 and set_bet == 1:#串三個即可 . set_bet = 1代表
                        #breake
                else:
                    self.betting_info = {} #儲存我下注的值

                    ran_index = random.randint(0, len(Match_key_list) -1  )
                    Ran_Match_id =  Match_key_list[ran_index]# 隨機取出 odds id
                    logger.info('Ran_Match_id: %s'%Ran_Match_id)

                    oddsid = Ran_Match_id
                    Matchid = Match[Ran_Match_id]['MatchId']
                    odds = Match[Ran_Match_id]['odds_0']
                    self.betting_info['odds'] = odds
                '''
                parlay
                其他sport 拿到的 odds 需轉成 Dec Odds , Cricket 原本就是 dec odds所以不做轉換 
                5: Ft 1x2 , 15: 1H 1x2(原本就是 dec odds, 不用轉) 
                '''
                if 'parlay' not in self.bet_type : # single odds 先不轉
                    logger.info('odds: %s'%odds)
                    odds = self.Odds_Tran(odds,odds_type=self.odds_type )
                    logger.info('odds type: %s , trands odds : %s'%(self.odds_type, odds))
                    pass
                    
                else:# parlay
                    if  self.gameid != 50 and self.gameid != 999:# cricket 的不用轉 
                        if BetTypeId not in [5, 15]:#  5: Ft 1x2 , 15: 1H 1x2 他們是 屬於Dec Odds
                            odds = self.Odds_Tran(odds,odds_type=self.odds_type)
                            self.betting_info['odds'] = odds
                            logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( self.sport,BetTypeId, odds) )
                if self.gameid != 999:
                    if 'parlay' in self.bet_type:
                        logger.info('BetTypeId : %s'%BetTypeId)
                        try:
                            data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                            ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                            ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                            ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                            ItemList[{index_key}][SportName]={sportName}&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                            ".format(index_key= index_key, BetTypeId=BetTypeId, oddsid=oddsid ,Matchid = Matchid ,
                            Team1 =Team1, Team2= Team2,odds=odds  ,gameid = self.gameid,betteam = bet_team,  bet_type = "parlay",sportName=self.sport)
                        except Exception as e:
                            logger.error('data_format: %s'%e)
                    else:
                        logger.info('BetTypeId : %s'%BetTypeId)
                        try:
                            data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                            ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                            ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                            ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                            ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                            ".format(index_key= index_key, BetTypeId=BetTypeId, oddsid=oddsid ,Matchid = Matchid ,
                            Team1 =Team1, Team2= Team2 ,odds=odds ,gameid = self.gameid,betteam = bet_team,  bet_type = "OU")
                            #logger.info('data_format : %s'%data_format)
                        
                        except Exception as e:
                            logger.error('data_format: %s'%e)
                else:
                    data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                        &ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&\
                        ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][GameName]=&\
                        ItemList[{index_key}][SportName]={sportName}&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][sinfo]=\
                        ".format(index_key= index_key,bet_type = "OT", oddsid=oddsid ,odds=odds, Matchid = Matchid ,
                            gameid = '999',sportName=self.sport  )

                data_str = data_str + data_format + '&'
                '''
                parlay 串多少match 邏輯
                當 index 到了 總長度 的最後, 須把 combo_str 家回data裡
                '''
                if 'parlay'  in self.bet_type:
                    self.betting_info['odds_type'] = "Dec"
                    self.BetTypeId_list.append(self.betting_info)
                if index_key == len_Match_dic -1 :
                    if 'parlay'  in self.bet_type :# parlay
                        if parlay_type == '2':# system parlay ,的total stake 要根據 長度 來做動態 計算
                            TotalStake = len_Match_dic # - 3 +  3 如果 總長度 為4 . 4- 3  +  4
                        elif parlay_type == '3': # Mix parlay 
                            TotalStake = int(Parlay_dict['3'])
                        else: # Mix parlay 
                            TotalStake = int(Parlay_dict['1'])
                        if len_Match_dic > 3:
                            if parlay_type == '1':
                                combo_type = 4
                            else:
                                combo_type = 1
                        else:
                            combo_type = parlay_type
                                     
                        combo_str = "ComboLists[0][Type]={combo_type}&ComboLists[0][BetCount]={parlay_value}&ComboLists[0][Stake]=1&Combi=false&IsAnyOdds=false&\
                        TotalStake={TotalStake}".format(combo_type=combo_type, parlay_value= Parlay_dict[parlay_type],TotalStake = TotalStake )
                        
                        data_str = data_str + combo_str + "&"

                        retry = 0
                        while retry < 10 :
                            r = self.client_session.post(self.url  + '/BetParlay/GetParlayTickets'  , data = data_str.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                            if "please try again" in r.text :
                                time.sleep(0.5)
                                retry += 1
                            elif "Your session has been terminated" in r.text:
                                self.mobile_login(user=self.user,central_account='web.desktop',central_password='1q2w3e4r')
                            else:
                                break
                        
                        try:
                            logger.info('GetTickets OK')
                            self.ticket_Data_list = r.json()['Data']['Tickets']# Data 為一個list. 取出來為一個 dict
                            parlay_data_str = ''
                            for index_key,ticket_Data in enumerate(self.ticket_Data_list):
                                #logger.info('ticket: %s'%Data)
                                self.min_stake = ticket_Data['Minbet']
                                self.guid = ticket_Data['Guid']
                                self.Line = ticket_Data['Line']
                                for idx,bet_info in enumerate(self.BetTypeId_list):
                                    if idx == index_key:
                                        self.BetTypeId_list[idx]['Line'] = self.Line
                                        break
                                self.Hdp1 = ticket_Data['Hdp1']
                                self.Hdp2 = ticket_Data['Hdp2']
                                if len(self.ticket_Data_list) < 3:
                                    for find_idx,match_info in enumerate(self.Match_dict):
                                        if ticket_Data['HomeName'] in str(self.Match_dict[match_info]):
                                            _index_key = find_idx
                                            break
                                        else:
                                            pass
                                else:
                                    _index_key = index_key
                                try:
                                    self.Hscore = ticket_Data['LiveHomeScore']
                                    self.Asocre = ticket_Data['LiveAwayScore']
                                except:
                                    self.Hscore = '0'
                                    self.Asocre = '0'
                                data_str = data_str.replace('ItemList[%s][Hscore]=0&'%index_key,'')
                                parlay_data_format = "ItemList[{index_key}][stake]={bet_stake}&ItemList[{index_key}][Guid]={Guid}&ItemList[{index_key}][Line]={Line}&ItemList[{index_key}][hdp1]={hdp1}&ItemList[{index_key}][hdp2]={hdp2}&ItemList[{index_key}][Hscore]={Hscore}\
                                &ItemList[{index_key}][Ascore]={Ascore}".format(bet_stake=self.min_stake,Guid =self.guid,  Line =self.Line , hdp1 = self.Hdp1, hdp2 = self.Hdp2, Hscore = self.Hscore ,Ascore = self.Asocre,index_key= _index_key )
                                parlay_data_str = parlay_data_str + parlay_data_format + '&'
                        except Exception as e:
                            self.error_msg = r.text
                            logger.error('Single Bet Get Ticket 有誤 : %s'%self.error_msg)
                            return 'GetTickets False'
                    
                        


                    else:# single

                        combo_str = "ItemList[0][Minbet]=1"

                        data_str = data_str + combo_str
                        
                        #logger.info('ticket data: %s'%data_str)
                        start = time.perf_counter()# 計算請求時間用
                        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                        r = self.client_session.post(self.url  + '/BetV2/GetTickets'  , data = data_str.encode(),
                                headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法

                        self.req_list = []# 存放 ticket 和 betting 的 列表
                        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                        self.req_list.append(self.request_time )


                        try:
                            
                            self.ticket_Data = r.json()['Data'][0]# Data 為一個list. 取出來為一個 dict
                            #logger.info('ticket: %s'%Data)
                            logger.info('GetTickets OK')
                            self.min_stake = self.ticket_Data['Minbet']
                            self.guid = self.ticket_Data['Guid']
                            self.Line = self.ticket_Data['Line']
                            self.betting_info['Line'] = self.Line
                            self.Hdp1 = self.ticket_Data['Hdp1']
                            self.Hdp2 = self.ticket_Data['Hdp2']
                            try:
                                self.Hscore = self.ticket_Data['LiveHomeScore']
                                self.Asocre = self.ticket_Data['LiveAwayScore']
                            except:
                                self.Hscore = '0'
                                self.Asocre = '0'
                        except:
                            self.error_msg = r.text
                            logger.error('Single Bet Get Ticket 有誤 : %s'%self.error_msg)
                            return 'GetTickets False'
                        if index_key == 0:
                            break 

                
                #self.Odds_dict[Matchid] = odds 
                #self.BetTypeId_list.append(BetTypeId)
            
            #logger.info('BetTypeId_list: %s'%self.BetTypeId_list)
            #logger.info('OddsId :%s'%self.Odds_dict)
        except Exception as e:
            logger.error('DoplaceBet: %s'%e)
        
        
        retry_count = 0

        try:
            import re
            data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 

            #self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]
            self.post_data =  data_str
            
            if 'parlay' in  self.bet_type:
                self.post_data = data_str + parlay_data_str
                retry = 0
                while retry < 10 :
                    r = self.client_session.post(self.url  + '/BetParlay/DoplaceBet',data = self.post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    if "please try again" in r.text :
                        time.sleep(0.5)
                        retry += 1
                    elif "Your session has been terminated" in r.text:
                        self.mobile_login(user=self.user,central_account='web.desktop',central_password='1q2w3e4r')
                    else:
                        break
                retry = 0
                while retry < 3: 
                    betting_response = self.Betting_response(response=r, times=times,)
                    if betting_response != True and betting_response != False:
                        if "is closed" in betting_response or "System Error" in betting_response or "is temporarily closed" in betting_response:
                            bettype_is_closed = True
                            retry = 3
                            break
                        elif "Bet Fail" in betting_response:
                            return False
                        elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                            self.post_data = new_post_data
                            r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                        else:
                            r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                        retry += 1
                    else:
                        break
                if retry == 3:
                    self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                    self.order_value['Message'] = str(betting_response)
                    self.order_value['MatchID'] = Matchid
                    self.order_value['oddsid'] = Ran_Match_id
                    self.order_value['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                    self.order_value['BetChoice'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                    return str(self.order_value)
                else:
                    return self.order_value
            else:# single bet
                # 這裡把 get_ticket拿到的 資訊 , 在加進  post_data
                self.post_data = data_format+ "&ItemList[0][stake]={bet_stake}&ItemList[0][Guid]={Guid}&\
                ItemList[0][Line]={Line}&ItemList[0][hdp1]={hdp1}&ItemList[0][hdp2]={hdp2}&ItemList[0][Hscore]={Hscore}&ItemList[0][Ascore]={Ascore}".format(bet_stake=self.min_stake
                ,Guid =self.guid,  Line =self.Line , hdp1 = self.Hdp1, hdp2 = self.Hdp2, Hscore = self.Hscore ,Ascore = self.Asocre)
                
                if self.site != '':
                    self.req_url = ['/BetV2/GetTickets','/BetV2/ProcessBet'] #會寫個list, 是因為 ticket 和 betting 在同個fucn裡
                    #self.req_url = '/BetV2/ProcessBet'
                    start = time.perf_counter()# 計算請求時間用
                    r = self.client_session.post(self.url  + '/BetV2/ProcessBet' ,data = self.post_data.encode(),
                    headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    
                    self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                    self.req_list.append(self.request_time )
                

                else:
                    retry = 0
                    while retry < 10 :
                        r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = self.post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                        if "please try again" in r.text :
                            time.sleep(0.5)
                            retry += 1
                        elif "Your session has been terminated" in r.text:
                            if "nova88" in self.url:
                                time.sleep(10)
                            self.mobile_login(user=self.user,central_account='web.desktop',central_password='1q2w3e4r')
                        else:
                            break
                    if retry == 10: #在最前面下注就失敗
                        self.order_value = {}
                        if self.gameid != 999:
                            self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                            try:
                                r.text['Message']
                            except:
                                repspone_json = r.json()
                                Data = repspone_json['Data']['ItemList'][0]
                                self.order_value['Message'] = Data['Message']
                            self.order_value['MatchID'] = Matchid
                            self.order_value['oddsid'] = Ran_Match_id
                            self.order_value['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                            self.order_value['BetChoice'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                        else:
                            self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                            try:
                                r.text['Message']
                            except:
                                repspone_json = r.json()
                                Data = repspone_json['Data']['ItemList'][0]
                                self.order_value['Message'] = Data['Message']
                            self.order_value['MatchID'] = Matchid
                            self.order_value['oddsid'] = Ran_Match_id
                            self.order_value['BetTypeId'] = 'Outright'
                        return str(self.order_value)

                    retry = 0
                    while retry < 3: 
                        betting_response = self.Betting_response(response=r, times=times)
                        if betting_response != True and betting_response != False:
                            if "is closed" in betting_response or "System Error" in betting_response or "is temporarily closed" in betting_response:
                                retry = 3
                                break
                            elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                                self.post_data = new_post_data
                                r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                            else:
                                r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                            retry += 1
                        else:
                            break
                    if retry == 3:
                        if self.gameid != 999:
                            self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                            self.order_value['Message'] = str(betting_response)
                            self.order_value['MatchID'] = Matchid
                            self.order_value['oddsid'] = Ran_Match_id
                            self.order_value['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                            self.order_value['BetChoice'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                        else:
                            self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                            self.order_value['Message'] = str(betting_response)
                            self.order_value['MatchID'] = Matchid
                            self.order_value['oddsid'] = Ran_Match_id
                            self.order_value['BetTypeId'] = 'Outright'
                        return str(self.order_value)
                    else:
                        return str(self.order_value)
                

                
                
                        
            
            return self.Betting_response(response = r, times=times)

            #return betting_response

            #logger.info('repspone_json: %s'%repspone_json)   

        except Exception as e:
            logger.info('mobile DoplaceBet Api Fail: %s'%e)
            return False


    def DoallbettypeBet(self,already_list=[],bet_team_index='0',times='',all_bet_choice= True):
        self.BetTypeId_list = []
        self.Odds_dict = {}# key 為 match id ,value 為 odds
        self.fail_betting = {}
        len_Match_dic= len(self.Match_dict)
        logger.info('len_Match_dict : %s'%len_Match_dic)
        try:
            for index_key in self.Match_dict.keys():#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                Match = self.Match_dict[index_key]# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊

                Match_key_list = list(Match.keys())# list裡面放 bettype
                
                for Ran_Match_id in Match_key_list:
                    bettype_is_closed = False #用來判斷 Bettype 是不是關閉了
                    self.betting_info = {} #儲存我下注的值
                    
                    logger.info('Ran_Match_id: %s'%Ran_Match_id)
                    BetTypeId = Match[Ran_Match_id]['BetTypeId']
                    '''
                    if BetTypeId != 9486:
                        continue
                    else:
                        pass
                    '''
                    self.betting_info['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                    self.betting_info['MatchId'] = Match[Ran_Match_id]['MatchId']
                    self.betting_info['Team1'] = Match[Ran_Match_id]['Team1']
                    self.betting_info['Team2'] = Match[Ran_Match_id]['Team2']
                    
                    if all_bet_choice == 'true':
                        do_all_bet_choice_count = str(Match[Ran_Match_id]).count('bet_team')
                    else:
                        do_all_bet_choice_count = 1
                    for bet_team_index in range(do_all_bet_choice_count): #str(Match[Ran_Match_id]).count('bet_team') 是用來計算有幾個 BetChoice
                        data_str = ""# 需loop 慢慢加起來
                        try:
                            self.betting_info['bet_team'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                            odds = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                            self.betting_info['odds'] = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                        except: #跳 except 代表沒有 choice 了
                            break 
                        if bettype_is_closed == False:
                            if self.bet_type == "OU": #讓 OU bettypeclass 的全下，到 more
                                logger.info('OddsId: %s 沒有投注過 ,成立'%Ran_Match_id)
                                pass
                            else:
                                if str(Ran_Match_id) in already_list :
                                    logger.info('OddsId: %s 有投注過，換下一個 Odds ID'%Ran_Match_id)
                                    continue
                                else:
                                    logger.info('OddsId: %s 沒有投注過 ,成立'%Ran_Match_id)
                                    pass
                        else:
                            logger.info('OddsId: %s 已經 Close ,不再下注'%Ran_Match_id)
                            break

                        self.betting_info['oddsid'] = Ran_Match_id
                        self.betting_info['Pair/DecOdds'] = Match[Ran_Match_id]['Pty']
                        self.betting_info['Line'] = Match[Ran_Match_id]['Line']
                        if self.betting_info['Line'] == 0:
                            self.betting_info['Line1'] = ''
                            self.betting_info['Line2'] = ''
                        elif self.betting_info['Line'] < 0:
                            if self.betting_info['bet_team'] == 'h':
                                self.betting_info['Line'] = abs(Match[Ran_Match_id]['Line'])
                                self.betting_info['Line1'] = 0
                                self.betting_info['Line2'] = abs(self.betting_info['Line'])
                            else:
                                self.betting_info['Line'] = Match[Ran_Match_id]['Line']
                                self.betting_info['Line1'] = 0
                                self.betting_info['Line2'] = abs(self.betting_info['Line'])
                        elif self.betting_info['Line'] > 0:
                            if self.betting_info['bet_team'] == 'h':
                                self.betting_info['Line'] = -Match[Ran_Match_id]['Line']
                                self.betting_info['Line1'] = abs(Match[Ran_Match_id]['Line'])
                                self.betting_info['Line2'] = 0
                            else:
                                self.betting_info['Line'] = Match[Ran_Match_id]['Line']
                                self.betting_info['Line1'] = Match[Ran_Match_id]['Line']
                                try:
                                    self.betting_info['Line2'] = Match[Ran_Match_id]['hdp2'] 
                                except:
                                    self.betting_info['Line2'] = 0
                        #if index > 2 and set_bet == 1:#串三個即可 . set_bet = 1代表
                            #break

                        '''
                        parlay
                        其他sport 拿到的 odds 需轉成 Dec Odds , Cricket 原本就是 dec odds所以不做轉換 
                        5: Ft 1x2 , 15: 1H 1x2(原本就是 dec odds, 不用轉) 
                        '''
                        self.bet_stake = 2 #大致上都是 2，先預設為 2

                        if self.betting_info['Pair/DecOdds'] == 0: #0 是 pair odds, 1 是 Dec odds
                            self.betting_info['odds'] = self.Odds_Tran(self.betting_info['odds'],odds_type=self.odds_type)
                            logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( self.sport,BetTypeId, odds) )
                        logger.info('BetTypeId : %s'%BetTypeId)
                        try:
                            if "+" in self.betting_info['bet_team'] : #當 betteam 包含 '+' 字串，會下注失敗，需要用 encode 格式去打
                                new_betteam = self.betting_info['bet_team'].replace("+","")
                                if new_betteam == 'G7/G7':
                                    new_betteam = 'G7%2B/G7'
                                data_format = "ItemList%5B0%5D%5Btype%5D={bet_type}&ItemList%5B0%5D%5Bbettype%5D={BetTypeId}&ItemList%5B0%5D%5Boddsid%5D={oddsid}&ItemList%5B0%5D%5Bodds%5D={odds}\
                                    &ItemList%5B0%5D%5BHscore%5D=0&ItemList%5B0%5D%5BAscore%5D=32&ItemList%5B0%5D%5BMatchid%5D={Matchid}&ItemList%5B0%5D%5Bbetteam%5D={betteam}%2B&\
                                    ItemList%5B0%5D%5BQuickBet%5D=1%3A100%3A10%3A1&ItemList%5B0%5D%5BChoiceValue%5D=&ItemList%5B0%5D%5Bhome%5D={Team1}&\
                                    ItemList%5B0%5D%5Baway%5D={Team2}&ItemList%5B0%5D%5Bgameid%5D={gameid}&ItemList%5B0%5D%5BisMMR%5D=0&ItemList%5B0%5D%5BMRPercentage%5D=&ItemList%5B0%5D%5BGameName%5D=&\
                                    ItemList%5B0%5D%5BSportName%5D=Basketball&ItemList%5B0%5D%5BIsInPlay%5D=false&ItemList%5B0%5D%5BSrcOddsInfo%5D=&ItemList%5B0%5D%5Bpty%5D=1&\
                                    ItemList%5B0%5D%5BBonusID%5D=0&ItemList%5B0%5D%5BBonusType%5D=0&ItemList%5B0%5D%5Bsinfo%5D=F1B30X0000&\
                                    ItemList%5B0%5D%5BhasCashOut%5D=false".format(index_key= index_key, BetTypeId=self.betting_info['BetTypeId'], oddsid=self.betting_info['oddsid'] ,Matchid = self.betting_info['MatchId'] ,
                                    Team1 =self.betting_info['Team1'], Team2= self.betting_info['Team2'] ,odds=self.betting_info['odds'] ,gameid = self.gameid,betteam = new_betteam, bet_type = "OU", bet_stake = self.bet_stake )
                            else:
                                if ("H1" in self.betting_info['bet_team'] and "-" not in self.betting_info['bet_team']) or "O1" in self.betting_info['bet_team']:
                                    self.betting_info['bet_team'] = self.betting_info['bet_team'].replace("1","")
                                elif '948' in str(self.betting_info['BetTypeId']):
                                    if '<' in self.betting_info['bet_team']:
                                        self.betting_info['bet_team'] = '0'
                                    elif '>' in self.betting_info['bet_team']:
                                        self.betting_info['bet_team'] = '7'
                                    else:
                                        self.betting_info['bet_team'] = str(int(self.betting_info['bet_team']) - 3)
                                data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                                ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Ascore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                                ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                                ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                                ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&\
                                &ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                                ".format(index_key= index_key, BetTypeId=self.betting_info['BetTypeId'], oddsid=self.betting_info['oddsid'] ,Matchid = self.betting_info['MatchId'] ,
                                Team1 =self.betting_info['Team1'], Team2= self.betting_info['Team2'] ,odds=self.betting_info['odds'] ,gameid = self.gameid,betteam = self.betting_info['bet_team'], bet_type = "OU" )
                        except Exception as e:
                            logger.error('data_format: %s'%e)

                        data_str = data_str + data_format + '&'
                        '''
                        parlay 串多少match 邏輯
                        當 index 到了 總長度 的最後, 須把 combo_str 家回data裡
                        '''
                        if index_key == len_Match_dic -1 :

                            combo_str = "&ItemList[0][Minbet]=1"

                            data_str = data_str + combo_str
                            
                            r = self.client_session.post(self.url  + '/BetV2/GetTickets',data = data_str.encode(),
                                    headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                            try:
                            
                                self.ticket_Data = r.json()['Data'][0]# Data 為一個list. 取出來為一個 dict
                                #logger.info('ticket: %s'%Data)
                                logger.info('GetTickets OK')
                                self.min_stake = self.ticket_Data['Minbet']
                                self.guid = self.ticket_Data['Guid']
                                self.Line = self.ticket_Data['Line']
                                self.betting_info['Line'] = self.Line
                                self.Hdp1 = self.ticket_Data['Hdp1']
                                self.Hdp2 = self.ticket_Data['Hdp2']
                                try:
                                    self.Hscore = self.ticket_Data['LiveHomeScore']
                                    self.Asocre = self.ticket_Data['LiveAwayScore']
                                except:
                                    self.Hscore = '0'
                                    self.Asocre = '0'
                                if any(_bet_team in self.betting_info['bet_team'] for _bet_team in  ['aos','AOS']) or any(_BetTypeId in str(self.betting_info['BetTypeId']) for _BetTypeId in ['468','469']): #如果是 aos 就要抓取 SrcOddsInfo，並放到 postdata 裡面
                                    SrcOddsInfo = repspone_json['Data'][0]['SrcOddsInfo']
                                    data_str = "ItemList[0][SrcOddsInfo]={SrcOddsInfo}&".format(SrcOddsInfo= SrcOddsInfo) + data_str

                                if "ItemList%5B" in data_str:
                                    data_str = "ItemList%5B0%5D%5Bstake%5D={bet_stake}&".format(bet_stake = self.min_stake) + data_str
                                else:                                
                                    data_str = "ItemList[0][stake]={bet_stake}&".format(bet_stake = self.min_stake) + data_str
                            except:
                                self.error_msg = r.text
                                logger.error('Single Bet Get Ticket 有誤 : %s'%self.error_msg)
                                return 'GetTickets False'

                        try:
                            import re
                            data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 
                            post_data = data_str+ "&ItemList[0][stake]={bet_stake}&ItemList[0][Guid]={Guid}&\
                                ItemList[0][Line]={Line}&ItemList[0][hdp1]={hdp1}&ItemList[0][hdp2]={hdp2}&ItemList[0][Hscore]={Hscore}&ItemList[0][Ascore]={Ascore}".format(bet_stake=self.min_stake
                                ,Guid =self.guid,  Line =self.Line , hdp1 = self.Hdp1, hdp2 = self.Hdp2, Hscore = self.Hscore ,Ascore = self.Asocre)
                            #self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]
                            #post_data =  data_str
                            retry = 0
                            while retry < 10 :
                                r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                                if "please try again" in r.text :
                                    time.sleep(0.5)
                                    retry += 1
                                elif "Your session has been terminated" in r.text:
                                    if "nova88" in self.url:
                                        time.sleep(10)
                                    self.mobile_login(user=self.user,central_account='web.desktop',central_password='1q2w3e4r')
                                else:
                                    break
                            if retry == 10: #在最前面下注就失敗
                                self.order_value = {}
                                try:
                                    r.text['Message']
                                except:
                                    repspone_json = r.json()
                                    Data = repspone_json['Data']['ItemList'][0]
                                    self.order_value['Message'] = Data['Message']
                                self.order_value['MatchID'] = self.betting_info['MatchId']
                                self.order_value['oddsid'] = self.betting_info['oddsid']
                                self.order_value['BetTypeId'] = self.betting_info['BetTypeId']
                                self.order_value['BetChoice'] = self.betting_info['bet_team']
                                fail_txt = open('Config/fail.txt', 'a+')
                                fail_txt.write(str(self.order_value)+'\n')
                                fail_txt.close()
                                continue

                            retry = 0
                            while retry < 6: 
                                betting_response = self.Betting_response(response=r, times=times)
                                if betting_response != True and betting_response != False:
                                    if "is closed" in betting_response or "System Error" in betting_response:
                                        bettype_is_closed = True
                                        retry = 6
                                        break
                                    elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                                        post_data = new_post_data
                                        r,new_post_data = self.retry_betting(betting_response,post_data,self.bet_stake,retry) #現在只為了 Single betting 新增
                                    else:
                                        r,new_post_data = self.retry_betting(betting_response,post_data,self.bet_stake,retry) #現在只為了 Single betting 新增
                                    retry += 1
                                else:
                                    if self.bet_type == "OU": #只要記錄 OU 的 Oddsid 避免 More 的重複下到
                                        already_list.append(self.order_value['oddsid'])
                                    break
                            if retry == 6:
                                self.order_value['Message'] = str(betting_response)
                                self.order_value['MatchID'] = self.betting_info['MatchId']
                                self.order_value['oddsid'] = self.betting_info['oddsid']
                                self.order_value['BetTypeId'] = self.betting_info['BetTypeId']
                                self.order_value['BetChoice'] = self.betting_info['bet_team']
                                fail_txt = open('Config/fail.txt', 'a+')
                                fail_txt.write(str(self.order_value)+'\n')
                                fail_txt.close()

                            #logger.info('repspone_json: %s'%repspone_json)   

                        except Exception as e:
                            logger.info('Desktop DoplaceBet Api Fail: %s'%e)
                return already_list

        except Exception as e:
            logger.error('DoplaceBet: %s'%e)


    def retry_betting(self,error_code,post_data,bet_stake,retry):
        if "Odds has changed" in str(error_code):
            if "parlay" in self.bet_type:
                error_code_dict = error_code
                for error_key in (error_code_dict.keys()):
                    error_code = error_code_dict[error_key]
                    old_odds = re.findall('Odds has changed from (.+) to',error_code)[0] #去除尾數為 0 
                    new_odds = re.findall('Odds has changed from .+ to (.+).',error_code)[0]
                    if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                        old_odds = old_odds.rstrip('0')
                    if abs(float(new_odds)) < 100 and '.0' in old_odds:
                        new_odds = new_odds.rstrip('0')
                    for idx,betslip in enumerate(self.BetTypeId_list):
                        if str(error_key) in str(betslip):
                            self.BetTypeId_list[idx]['odds'] = new_odds
                            post_data = re.sub("ItemList\["+str(idx)+"\]\[odds\]=(.*?)&I", "ItemList["+str(idx)+"][odds]="+str(new_odds)+"&I",post_data)
                            pass
                    '''   
                    for idx,betslip in enumerate(str(self.BetTypeId_list).split("}, {")): 
                        if str(error_key) in str(betslip):
                            bettype_list_new_odds = re.sub("'odds': '(.*?)'", "'odds': '"+str(new_odds)+"'",str(betslip))
                            self.BetTypeId_list = str(self.BetTypeId_list).replace(betslip,bettype_list_new_odds)
                            post_data = re.sub("ItemList\["+str(idx)+"\]\[odds\]=(.*?)&I", "ItemList["+str(idx)+"][odds]="+str(new_odds)+"&I",post_data)
                            break
                    '''      
                        
            else:
                old_odds = re.findall('Odds has changed from (.+) to',error_code)[0] #去除尾數為 0 
                new_odds = re.findall('Odds has changed from .+ to (.+).',error_code)[0]
                if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                    old_odds = old_odds.rstrip('0')
                if abs(float(new_odds)) < 100 and '.0' in old_odds:
                    new_odds = new_odds.rstrip('0')
                post_data = re.sub("\[odds\]=(.*?)&I", "[odds]="+str(new_odds)+"&I",post_data)
                self.betting_info['odds'] = new_odds
        elif "updating odds" in error_code or "temporarily closed" in error_code or "System Error" in error_code:
            time.sleep(5) # 系統 有防止 快速 打 接口 ,回復 We are updating odds, please try again later
        elif "score has been changed" in error_code :
            post_data = "ItemList[0][Ascore]={Ascore}&".format(Ascore= retry) + post_data
        elif "less than min stake or more than max stake" in error_code:
            if "nova88" in self.url :
                new_bet_stake = bet_stake + 10
            else:
                new_bet_stake = bet_stake + 4
            self.bet_stake = new_bet_stake
            post_data = post_data.replace('[stake]=%s'%bet_stake,'[stake]=%s'%new_bet_stake)
        elif "HDP/OU has been changed." in error_code:
            pass
        elif "IN-PLAY" in error_code:
            post_data = post_data.replace("ItemList[0][IsInPlay]=false","ItemList[0][IsInPlay]=true")
        if 'parlay' not in self.bet_type:
            r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = post_data,headers=self.headers,verify=False)
        else:
            r = self.client_session.post(self.url  + '/BetParlay/DoplaceBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
        return r,post_data


    def get_statement_info(self,transid,datatype='0'): #用來抓取最後一個 TransID
        data_str = 'datatype=%s'%datatype
        reget = 0
        while reget < 60:
            r = self.client_session.get(self.url  + '/Running/GetEarly_ch?%s'%data_str,headers=self.headers,verify=False)
            if transid in r.text:
                return r.text
                #bets_list = r.text.replace(' ','').split('bets_title')
                #del bets_list[0] #要先刪掉第 0 個，第 0 個不是注單資訊
                #for responce in bets_list:
                #    if transid in responce:
                #        return responce
            else:
                time.sleep(1)
                reget += 1

    def get_settled_info(self,bfday): 
        #先抓取有的下注分類
        try:
            r = self.client_session.get(self.url  + '/Statement/GetStatementOVR?bfday=%s'%bfday,headers=self.headers,verify=False)
            statementove_responce = r.json()
            filterList = {}
            #抓取有的 Settle 分類 & 分類 ID
            filterList = statementove_responce['filterList']
            if filterList == None:
                return "No Settle Betlist"
            else:
                settled_filterList = {}
                for filter in filterList:
                    settled_filterList[filter['filterID']] = {'displayName' : filter['displayName']}
        except Exception as e:
            logger.error('GetStatementOVR Fail : %s'%e)
            return "GetStatementOVR Fail"
        try:
            #開始抓取時間       
            for datatype in list(settled_filterList):
                r = self.client_session.get(self.url  + '/Statement/GetAllStatement_ch?datatype=%s&bfday=%s'%(datatype,bfday),headers=self.headers,verify=False)
                get_allstatement_responce = r.json()
                #抓取時間
                fdate = re.findall("(\d{4}\/\d{1,2}\/\d{1,2})",get_allstatement_responce['StatementViewModel_ch_detail'])[0]
                settled_filterList[datatype].update({'fdate' : fdate})
        except Exception as e:
            logger.error('GetAllStatement_ch Fail : %s'%e)
            return "GetAllStatement_ch Fail"
        #開始抓取 DB List
        try:
            settled_result_dict = {}
            for datatype in list(settled_filterList):
                try:
                    r = self.client_session.get(self.url  + '/Statement/GetDBetList_ch?fdate=%s&datatype=%s'%(settled_filterList[datatype]['fdate'],datatype),headers=self.headers,verify=False)
                    get_dbresponce = r.status_code
                    if get_dbresponce == 200:
                        settled_result_dict.update({settled_filterList[datatype]['displayName'] : r.text})
                    else:
                        settled_result_dict.update({settled_filterList[datatype]['displayName'] : "Responce Fail"})
                except Exception as e:
                    settled_result_dict.update({settled_filterList[datatype]['displayName'] : "Responce Fail"})
                    print(str(e))
            return settled_result_dict
        except Exception as e:
            logger.error('GetDBetList_ch Fail : %s'%e)
            return "GetDBetList_ch Fail"
    
    def get_result_info(self,filter_game,days=''): 
        #先抓取有的下注分類
        if filter_game == "Normal":
            try:
                data_str = "Selecteddate=%s"%days
                r = self.client_session.post(self.url  + '/Result/GetResultDropDownList',data = data_str.encode(),headers=self.headers,verify=False)
                result_dropdown_responce = r.json()
                filterList = result_dropdown_responce['Item1']
                #抓取有的 Settle 分類 & 分類 ID
                if filterList == None:
                    return "No Result"
                else:
                    sports_filterList = {}
                    for filter in filterList:
                        sports_filterList[filter['ID']] = {'displayName' : filter['Name']}
            except Exception as e:
                logger.error('GetResultDropDownList Fail : %s'%e)
                return "GetResultDropDownList Fail"
            try:
                result_dict = {}
                for selectedsport in list(sports_filterList):
                    try:
                        r = self.client_session.get(self.url  + '/Result/GetResult?Selecteddate=%s&Selectedsport=%s&SelectedGameType=0'%(days,selectedsport),headers=self.headers,verify=False)
                        get_result_responce = r.status_code
                        if get_result_responce == 200:
                            result_dict.update({sports_filterList[selectedsport]['displayName'] : r.text})
                        else:
                            result_dict.update({sports_filterList[selectedsport]['displayName'] : "Responce Fail"})
                    except Exception as e:
                        result_dict.update({sports_filterList[selectedsport]['displayName'] : "Responce Fail"})
                        print(str(e))
                return result_dict
            except Exception as e:
                logger.error('GetDBetList_ch Fail : %s'%e)
                return "GetDBetList_ch Fail"
        else:
            try:
                r = self.client_session.post(self.url  + '/Result/GetOutrightResultDropDownList',headers=self.headers,verify=False)
                result_dropdown_responce = r.json()
                filterList = result_dropdown_responce['Item2']
                #抓取有的 Settle 分類 & 分類 ID
                if filterList == None:
                    return "No Result"
                else:
                    sports_filterList = {}
                    for filter in filterList:
                        sports_filterList[filter['ID']] = {'displayName' : filter['Name']}
            except Exception as e:
                logger.error('GetOutrightResultDropDownList Fail : %s'%e)
                return "GetResultDropDownList Fail"
            try:
                result_dict = {}
                for selectedsport in list(sports_filterList):
                    try:
                        today = days.split(" to ")[0]
                        yesterday = days.split(" to ")[1]
                        r = self.client_session.get(self.url  + '/Result/GetOutrightResult?Selectedstartdate=%s&Selectedenddate=%s&Selectedsport=%s'%(yesterday,today,selectedsport),headers=self.headers,verify=False)
                        get_result_responce = r.status_code
                        if get_result_responce == 200:
                            result_dict.update({sports_filterList[selectedsport]['displayName'] : r.text})
                        else:
                            result_dict.update({sports_filterList[selectedsport]['displayName'] : "Responce Fail"})
                    except Exception as e:
                        result_dict.update({sports_filterList[selectedsport]['displayName'] : "Responce Fail"})
                        print(str(e))
                return result_dict
            except Exception as e:
                logger.error('GetDBetList_ch Fail : %s'%e)
                return "GetDBetList_ch Fail"
class Desktop_Api(Login):    
    def __init__(self,client="",device="",user='',url= ''):
        super().__init__(device)
        self.login = None
        self.user = user
        self.url = url
        self.login_type = ''# api site
        self.match_list_dict = {}
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        if 'athena' in self.url or 'spondemo' in self.url or 'macaubet' in self.url:
            self.login_type = 'athena' # 是 api site 登入 還是  athena site登入 , login方式不一樣
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        self.relogin = False

    def desktop_login(self,central_account='',central_password=''):# PC端 login街口 邏輯
        '''加密邏輯 呼叫'''
        if self.login_type == 'athena':# athena 的登入 方式 , 會須使用 js 加密
            common_js = execjs.compile(self.js_from_file('./login_js/dsektop.js'))# 讀取 login js檔
            cfs_psswd = common_js.call("CFS", '1q2w3e4r')# password先做 前端 CFS 加密
            self.dr = self.get_driver()
            val = self.assert_validation()# 取得驗證碼
            md5_psswd = self.md(password = cfs_psswd,val = val)# md5 將 Cfs加密 的密碼   跟 驗證碼 做md5
            login_data = "txtUserName={0}&txtPasswd={1}&txtValidCode={2}".format( self.user ,md5_psswd,val)
            if len(self.cookies) != 0:# aspx 的會為空 list
                asp_cookie = ''# 先初始 空字串, 後面 加起來
                for index,con_dict in enumerate(self.cookies): #self.cookies為 list 包 dict
                    cookie_name = con_dict['name']
                    cookie_value = con_dict['value']
                    asp_cookie = asp_cookie + '%s=%s'%(cookie_name,cookie_value)
                    #logger.info('asp_cookie: %s'%asp_cookie)
                    if index == 0: 
                        asp_cookie = asp_cookie + ';'# 因為會要串兩個 cookie 字串,需要用 ; 來傳進去
                logger.info('asp_cookie: %s'%asp_cookie)
                self.headers['Cookie'] = asp_cookie
            else:
                pass

        else:# api site
            if 'onelogin' not in self.url:# 多幫忙檢查 ,需要帶 onelogin
                self.url = self.url + '/onelogin.aspx'
            r = self.client_session.get(self.url  ,headers= self.headers,verify=False)# 需先拿 session url
            
            self.url  = r.url.split('/onelogin.aspx')[0]# 回復的url 需再拿掉 onelogin.aspx . 再去打 despoist login
            logger.info('onelogin 需 先拿session url: %s'%self.url )
            # 然後 在用 這個 session url 去拿 驗證碼 ,但要移除  /onelogin.aspx

            login_data = "lang=en&WebSkinType=&matchid=&leaguekey=&market=T&menutype=0&act=sports&game=&gamename=&gameid=&Otype=&HomeUrl=&deposit=&extendSessionUrl=&Link=&Sport=&Date=&SkinColor=&centralAccount={central_account}&centralPassword={central_password}&txtUserName={user}&txtPasswd=1q2w3e4r&token=&TSID=&txtValidCode=&hidubmit=YES".format(central_account=central_account,central_password=central_password,user=self.user )

        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.headers['X-Requested-With'] =  'XMLHttpRequest'
        start = time.perf_counter()# 計算請求時間用
        try:
            r = self.client_session.post(self.url  + '/DepositProcessLogin',data=login_data,headers=self.headers,verify=False)
        except : 
            self.error_msg = 'Login 接口: %s'%e
            return self.error_msg
        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        try:
            #if self.login_type == 'athena':# athena 回復格式 有json 
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            if repspone_json['ShowErrorMsg'] == 'The validation code has expired.' or repspone_json['ErrorCode'] !='':
                logger.info('登入 Fail')
                if 'Login Too Often' in str(repspone_json):
                    return 'Login Too Often'
                else:
                    return False

            reponse_url = r.json()['url']# 取得登入後 轉導url
            logger.info('reponse_url: %s'%reponse_url)
        
            if 'qasb' in self.url  or 'athena000' in self.url: #athena000 UAT 環境與 API Site 都有 Session，所以 UAT 環境用 athena000 判斷
                Val_url = '%s/%s'%(self.url ,  reponse_url)
                logger.info('Val_url: %s'%Val_url)#/ValidateTicket?Guid=fa426c9c-739d-4b37-9589-db13ab0b1cdd
                r = self.client_session.get(Val_url,headers=self.headers,verify=False)
                logger.info('r.url: %s'%r.url)
                u = urlparse(r.url)
                self.member_url = 'http://%s%s'%(u.netloc,u.path)
                self.member_url = self.member_url.split('/ValidateTicket')[0]
                logger.info('self.member_url: %s'%self.member_url)

                r = self.client_session.get(self.member_url +  '/NewIndex?lang=en&rt=0&webskintype=3',headers=self.headers,verify=False)

            elif 'xide' in self.url or self.login_type == 'athena': # 有sesion 的判斷
                Val_url = '%s'%(reponse_url)
                logger.info('Val_url: %s'%Val_url)#/ValidateTicket?Guid=fa426c9c-739d-4b37-9589-db13ab0b1cdd
                r = self.client_session.get(Val_url,headers=self.headers,verify=False)
                responce_dict = json.loads(r.text)
                logger.info('r.url: %s'%r.url)
                responce = responce_dict['url'].replace('~','')
                u = urlparse(r.url)
                self.member_url = 'http://%s%s'%(u.netloc,u.path)
                self.member_url = self.member_url.split('/ValidateTicket')[0]
                logger.info('self.member_url: %s'%self.member_url)

                r = self.client_session.get(self.member_url +  '/NewIndex?lang=en&rt=0&webskintype=3',headers=self.headers,verify=False)
                open_sports_data = responce.split('?')[1]

            else:
                u = urlparse(reponse_url)# 擷取 動態 member_url 
                if "https" in reponse_url:
                    self.member_url = 'https://%s'%u.netloc
                else:
                    self.member_url = 'http://%s'%u.netloc
                logger.info('member_url: %s'% self.member_url)

                r = self.client_session.get(reponse_url,headers=self.headers,verify=False)
                responce_dict = json.loads(r.text)
                logger.info('r.url: %s'%responce_dict['url'])
                responce = responce_dict['url'].replace('~','')

                r = self.client_session.get(self.member_url + responce,headers=self.headers,verify=False)
                open_sports_data = responce.split('?')[1]

            self.login = 'login ready'
            #需重新抓取 Net Session ID
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            try:
                post_url = '%s/EntryIndex/OpenSports?%s'%(self.member_url,open_sports_data)
            except:
                post_url = '%s/EntryIndex/OpenSports'%self.member_url
            logger.info('post_url: %s'%post_url)
            open_sports = self.session.get(post_url,headers = self.headers)
            cookie_session = self.session.cookies.get_dict()
            if 'ASP.NET_SessionId' in str(cookie_session):
                self.member_url = open_sports.url.split('/Sports/')[0]
                NET_SessionId = cookie_session['ASP.NET_SessionId']
                logger.info('NET_SessionId: %s'%NET_SessionId)

                self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
                self.headers['Cookie'] = "ASP.NET_SessionId=" + NET_SessionId 

            if '.ASPXAUTH' in str(cookie_session):
                if '/(S' in self.url: #如果有帶入 Session 的需要在這邊把打完 Open Sports 的新 Session 帶入 url
                    #self.url = self.url.split('/(S')[0] + '/('+re.findall("\((S.+)\)\)",open_sports.url)[0] + '))'
                    self.member_url = open_sports.url.split('/Sports/')[0]
                aspxauth = cookie_session['.ASPXAUTH']
                logger.info('aspxauth: %s'%aspxauth)
                try:
                    self.headers['Cookie'] = self.headers['Cookie'] + " ;.ASPXAUTH=" + aspxauth
                except:
                    self.headers['Cookie'] = ".ASPXAUTH=" + aspxauth

            try:
                r = self.client_session.get(self.url+ '/whoami.aspx',verify=False)
                self.whoami_ip = self.return_IP(r= r).replace(" ","")
                logger.info('登入後 打whoami 取得 ip : %s'%self.whoami_ip)
            except:
                logger.error('whoami 取得 ip有誤')
                self.error_msg = 'whoami 取得 ip有誤'

            return True

        except Exception as e:
            logger.info('登入 Fail : %s'%str(e))
            return False

    def balance(self):# /NewIndex/GetWalletBalance
        balance_info_data = 'TZone=8'
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url  + '/NewIndex/GetWalletBalance'
        logger.info('post_url: %s'%post_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.post( post_url,data=balance_info_data,headers=self.headers,verify=False)
        try:
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            return True
        except:
            logger.info('desktop balance Api Fail')
            return False
    
    def JSResourceApi(self): # /JSResourceApi/GetJSResource
        self.req_url = '/JSResourceApi/GetJSResource?lang=en'
        start = time.perf_counter()# 計算請求時間用
        r = self.client_session.post(self.member_url  + '/JSResourceApi/GetJSResource?lang=en',verify=False)
        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.error_msg =  ErrorCode
            #self.stress_dict['response'].append('ErrorCode: %s'%self.error_msg )

            logger.info('ErrorCode: %s '%(self.error_msg  ) )
            return True
        except:
            self.error_msg = r.text
            logger.error('response :%s'%self.error_msg )
            self.stress_dict['response'].append(self.error_msg ) 
            logger.error('GetJSResource Api Fail')
            return False

    def hm_sport(self):# /NewIndex/GetWalletBalance
       
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        self.hm_url = self.member_url.replace('member','hm')
        
        logger.info('hm_url: %s'%self.hm_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.get( self.hm_url + '/NewIndex/GetWalletBalance',headers=self.headers,verify=False)
        cookie_session = self.client_session.cookies.get_dict()
        logger.info('cookie_session: %s'%cookie_session)
        try:
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            return True
        except:
            logger.info('desktop balance Api Fail')
            return False

    def show_sports(self):# /Sports/
        '''
        #用於抓取登入後的 hm session id
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url + '/EntryIndex/OpenSports'
        logger.info('post_url: %s'%post_url)
        open_sports = self.session.get(post_url,headers = self.headers)
        cookie_session = self.session.cookies.get_dict()
        '''
        #if self.login_type == 'athena':
        '''
        NET_SessionId = cookie_session['ASP.NET_SessionId']
    
        logger.info('NET_SessionId: %s'%NET_SessionId)
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        self.headers['Cookie'] = "ASP.NET_SessionId=" + NET_SessionId
        '''
        retry = 0
        while retry < 10 :
            if 'qasb' in self.url :
                self.hm_url = self.member_url
            else:
                self.hm_url = self.member_url

            post_url = self.hm_url  + '/Sports/'
            logger.info('post_url: %s'%post_url)

            logger.info('header: %s'%self.headers)
            if 'qasb' in self.url or '/(S' in self.url:
                r = self.client_session.get( post_url,headers=self.headers,verify=False)
            else:
                r = self.client_session.get( post_url ,verify=False)
            if "Authentication has expired" in r.text :
                self.relogin = False
                if self.relogin == True:
                    retry += 1
                    continue
                logger.info('Your session has been terminated，等待 30 秒後重新登入')
                if '/(S' in self.url:
                    self.url = self.url.split('/(S')[0]
                desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                login_result = desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                if login_result == False:
                    logger.info("登入失敗，重新登入")
                    retry += 1
                    continue
                elif 'Login Too Often' in str(login_result):
                    logger.info("Login Too Often，等待 30 秒後再重新登入")
                    time.sleep(30)
                    retry += 1
                    continue
                else:
                    pass
                self.url = desktop_api.url
                self.member_url = desktop_api.member_url
                self.headers = desktop_api.headers
                retry += 1
                self.relogin = True
            else:
                break
        try:
            #sucess_data = re.findall("<html.+>",r.text)[0]
            return r.text
        except Exception as e:
            logger.info('desktop OpenSports Api Fail : %s'%str(e))
            return False

    def get_websocket_info(self,sport,market,bet_type='OU',first_get=True,parlay_type = ''):
        self.bet_type = bet_type
        sports_bettype_dict = {
            'Soccer' : '[1,3,5,7,8,15,301,302,303,304]',
            'Basketball' : '[401,402,403,404,1,2,3,7,8,12,20,21,609,610,611,612,615,616]',
            'Cricket' : '"fixed"',
            'E-Sports' : '[1,3,20,9001,9088]',
            'Volleyball' : '[1,2,3,20]',
            'Tennis' : '[1,2,3,20,153]'
        }
        get_sports_api_text = self.show_sports()
        #分析 Web Socket 需要的資料
        try:
            try:
                ms2_url = re.findall('MS2.url = {p: "(.+net)"};',get_sports_api_text)[0]
            except:
                try:
                    ms2_url = re.findall('MS2\.url = {p: "([0-9]+.[0-9]+.[0-9]+.[0-9]+:.[0-9]+)"',get_sports_api_text)[0]
                except:
                    try:
                        ms2_url = re.findall('MS2.url = {p: "(.+com)"};',get_sports_api_text)[0]
                    except:
                        ms2_url = 'agnj3.' + self.url.split('.')[1] + '.com'
            WS_token = re.findall('"pnv":{"tk":"(.+)","no"',get_sports_api_text)[0]
            WS_id = re.findall('MS2.id = "(.[0-9]+)";',get_sports_api_text)[0]
        except:
            return False
            
        async def startup(uri):
            try:
                async with AioWebSocket(uri) as aws:
                    converse = aws.manipulator
                    no_odds = False
                    betting_info = []
                    sport_parlay_odds = {}
                    league_id_dict = {}
                    market_id = ''
                    if self.bet_type != 'more':
                        retry = 0
                        parlay_reget = 0
                        if sport != 'Cross Sports':
                            parlay_reget_int = 2
                        else:
                            parlay_reget_int = 30
                        parlay_rec = ''
                        while retry < 60:
                            try:
                                mes = await converse.receive()
                                rec = mes.decode()
                                #print('{time}-Client receive: {rec}'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rec=rec))
                                if '0{"sid' in str(rec):
                                    await converse.send('2')
                                elif "40" == str(mes.decode()):
                                    await converse.send('42["init",{"gid":"123456","token":"{WS_token}","id":"{WS_id}","rid":"1","v":2}]')
                                elif 'empty' in str(rec) or ('reset' in str(rec) and 'leagueid' not in str(rec)): #代表沒有 Odds 
                                    no_odds = True
                                    raise Exception
                                elif '42["init' in str(mes):
                                    if "parlay" in self.bet_type:
                                        await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"n","condition":{"bettype":[1,12,15,153,2,20,21,3,301,302,303,304,401,402,403,404,5,501,609,610,611,612,615,616,7,701,704,705,706,707,708,709,710,712,713,8,9001,9088,9401,9404,9405,9406,9407,9408,9409,9410,9411,9412,9413,9414,9415,9428,9429,9430,9431,9432,9433,9490,9491,9496,9497,9498,9499,9502,9503,9504,9505,9506,9507,9514,9515,9516,9517,9538,9539,9540,9607,9608,9609,9610,9611,9612,9613,9614,4,30,413,414,405],"parlay":1}}]]]]')
                                    else:
                                        if market != "Outright":
                                            if sport == "Happy 5" or "Number Game" in sport: 
                                                await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":0,"condition":{"sporttype":%s,"marketid":"%s"}}]]]]'%(self.game_mapping(sport),str(market[0]).upper()))
                                            elif sport in ['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Basketball','Virtual Soccer','Virtual Tennis']:
                                                await converse.send('42["subscribe",[["odds",[{"id":"c5","rev":"","sorting":0,"condition":{"sporttype":%s}}]]]]'%(self.game_mapping(sport)))
                                            else:
                                                await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"t","condition":{"sporttype":%s,"marketid":"%s","bettype":%s}}]]]]'%(self.game_mapping(sport),str(market[0]).upper(),sports_bettype_dict[sport]))
                                        elif self.bet_type == 'more':
                                            if market != 'Live':
                                                await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"n","condition":{"marketid":"D","timestamp":0,"more":1,"matchid":%s}}]]]]'%matchid)
                                            else:
                                                await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"n","condition":{"marketid":"L","timestamp":0,"more":1,"matchid":%s}}]]]]'%matchid)
                                        else:
                                            await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"t","condition":{"sporttype":%s,"marketid":"E","bettype":%s}}]]]]'%(self.game_mapping(sport),[10]))
                                elif 'oddsid' in str(rec) :
                                    if "parlay" in self.bet_type :
                                        if parlay_reget < parlay_reget_int:
                                            parlay_reget += 1
                                            parlay_rec = parlay_rec + str(rec)
                                            await converse.send('2')
                                            continue
                                        else:
                                            parlay_rec = parlay_rec + str(rec)
                                            rec = parlay_rec
                                    if "Number Game" in sport:
                                        _rec = rec.split(",{")
                                        for _betting_info in _rec:
                                            num = [_betting_info for _betting_info in _rec if '"m"' in _betting_info ] #因為 Number Game 有三種，所以抓取 League ID 位子，就可以分出 Number Game 各個位子
                                            num_list = []
                                            for _num in num:
                                                num_list.append(_rec.index(_num))
                                        if "Turbo" not in sport:
                                            for count in range(num_list[0],num_list[1]):
                                                if 'oddsid' in _rec[count]:
                                                    betting_info.append(_rec[count])
                                        else:
                                            for count in range(num_list[1],num_list[2]):
                                                if 'oddsid' in _rec[count]:
                                                    betting_info.append(_rec[count])
                                        return betting_info
                                    else:
                                        _rec = rec.split(",{")
                                        if "parlay" in self.bet_type:         
                                            '''                     
                                            for _betting_info in _rec: #先把所有 Leagueid 抓出來判斷，為了讓下方判斷是否有 Test 的
                                                if 'type":"l","leagueid":' in _betting_info:
                                                    league_id_dict[re.findall('type":"l","leagueid":([0-9]+),',_betting_info)[0]] = re.findall('"leaguenameen":"(.+?)",',_betting_info)[0]
                                            '''
                                            if sport != 'Cross Sports' :
                                                test_game_id = self.game_mapping(sport)
                                            have_test_odds = True
                                            for _betting_info in _rec:
                                                if '"type":"m"' in _betting_info :
                                                    try:
                                                        if '"istest":1,' not in _betting_info:
                                                            #print(_betting_info)
                                                            #league_id = re.findall('"type":"m".+,"leagueid":([0-9]+),',_betting_info)[0] #抓出下面的 League 是否有 Test
                                                            game_id = re.findall('"type":"m".+,"sporttype":([0-9]+),',_betting_info)[0]
                                                            market_id = re.findall('"type":"m".+,"marketid":"([a-zA-Z]+)",',_betting_info)[0] #為了 Lucky Parlay 抓取 Market ID
                                                            have_test_odds = False
                                                        else:
                                                            have_test_odds = True
                                                    except: #有些"type":"m"會沒有 Sporttype
                                                        have_test_odds = False
                                                else:
                                                    pass

                                                if have_test_odds == False:
                                                    if sport != 'Cross Sports' : #此為 Single Sport 抓取 Odds id
                                                        if 'oddsid' in _betting_info and game_id == str(test_game_id):
                                                            betting_info.append(_betting_info)
                                                    else: #此為 Cross Sports 抓取 Odds id
                                                        if parlay_type != '3' or (market_id == 'E' and parlay_type == '3') :
                                                            if 'oddsid' in _betting_info :
                                                                if game_id not in sport_parlay_odds.keys(): #這裡分類出不同的 Sports 以及 Oddsid，因為 Desktop 是全部 Push 回來現階段沒辦法指定 Sports 
                                                                    betting_info = []
                                                                    betting_info.append(_betting_info)
                                                                    sport_parlay_odds[game_id] = betting_info
                                                                elif len(sport_parlay_odds[game_id]) <= 20: # 每個運動最高只抓 20 筆 Odds 資訊
                                                                    betting_info = sport_parlay_odds[game_id]
                                                                    betting_info.append(_betting_info)
                                                                    sport_parlay_odds[game_id] = betting_info
                                                                else:
                                                                    pass
                                                else:
                                                    pass
                                        else:
                                            for _betting_info in _rec:
                                                try:
                                                    if market != "Outright":
                                                        if '"type":"m"' in _betting_info :
                                                            if '"istest":1,' not in _betting_info:
                                                                more_count = re.findall('"mc":([0-9]+),',_betting_info)[0]
                                                                more_str = '"morecount":"%s",'%more_count
                                                                have_test_odds = False
                                                            else:
                                                                have_test_odds = True
                                                        if 'oddsid' in _betting_info and have_test_odds == False:
                                                            betting_info.append(more_str+_betting_info)
                                                    else:
                                                        if 'oddsid' in _betting_info:
                                                            betting_info.append(_betting_info)
                                                except:
                                                    pass
                                    if sport != 'Cross Sports':
                                        return betting_info
                                    else:
                                        if len(sport_parlay_odds.keys()) < 3:
                                            parlay_reget_int += 2
                                            retry += 1
                                        else:
                                            return sport_parlay_odds
                            except Exception as e:
                                if 'Baseball' in str(e):
                                    return False
                                elif '0 bytes read on' in str(e):
                                    return False
                                elif no_odds == True:
                                    return 'No Odds'
                                else:
                                    await converse.send('2')
                                    retry += 1
                        if retry == 60:
                            return False
                    else:
                        betting_info_dict = {}
                        did_match = ''
                        retry = 0
                        while retry < 60:
                            try:
                                mes = await converse.receive()
                                try:
                                    rec = mes.decode()
                                except:
                                    rec = None
                                #print('{time}-Client receive: {rec}'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rec=rec))
                                if '0{"sid' in str(rec):
                                    await converse.send('2')
                                elif "40" == str(rec):
                                    await converse.send('42["init",{"gid":"123456","token":"{WS_token}","id":"{WS_id}","rid":"1","v":2}]')
                                elif '42["init' in str(mes) or (did_match != '' and did_match != self.matchid) or rec == None: 
                                    if market != 'Live': 
                                        await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"n","condition":{"marketid":"D","timestamp":0,"more":1,"matchid":%s}}]]]]'%matchid)
                                    else:
                                        await converse.send('42["subscribe",[["odds",[{"id":"c1","rev":"","sorting":"n","condition":{"marketid":"L","timestamp":0,"more":1,"matchid":%s}}]]]]'%matchid)
                                elif 'empty' in str(rec) or ('reset' in str(rec) and 'leagueid' not in str(rec)): #代表沒有 Odds 
                                    no_odds = True
                                    raise Exception
                                elif 'oddsid' in str(rec):
                                    _rec = rec.split(",{")
                                    for _betting_info in _rec:
                                        if 'oddsid' in _betting_info:
                                            betting_info.append(_betting_info)
                                    betting_info_dict[self.matchid] = betting_info
                                    return betting_info_dict[self.matchid]
                            except Exception as e:
                                if no_odds == True:
                                    return 'No Odds'
                                print(str(e))
                                return None
                        if retry == 60:
                            return False
            except:
                return False
        
        Match_dict = {}
        if first_get == True:
            self.match_list_dict[sport] = {'Live' : '','Early' : '', 'Today' : ''}
        else:
            pass
        match_list = []
        if bet_type == 'OU' or 'parlay' in bet_type:
            if 'athena000' in self.url:
                remote = 'ws://{ms2_url}/socket.io/?gid=12345&token={WS_token}&id={WS_id}&rid=1&EIO=3&transport=websocket'.format(ms2_url=ms2_url,WS_token=WS_token,WS_id=WS_id)
            else:
                remote = 'wss://{ms2_url}/socket.io/?gid=12345&token={WS_token}&id={WS_id}&rid=1&EIO=3&transport=websocket'.format(ms2_url=ms2_url,WS_token=WS_token,WS_id=WS_id)
            get_Ws_info_result = False
            try:
                betting_info_list = asyncio.new_event_loop().run_until_complete(startup(remote))
                if betting_info_list != False and 'No Odds' not in betting_info_list and None not in betting_info_list:
                    if sport != 'Cross Sports':
                        for betting_info in betting_info_list:
                            if "Happy 5" == sport or "Number Game" in sport or sport in ['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Basketball','Virtual Soccer','Virtual Tennis']:
                                new_dict = {}
                                if "Happy 5" == sport:
                                    new_dict['MatchId'] = re.findall('"matchid":"H5_(.+?)",',betting_info)[0]
                                elif "Number Game" in sport:
                                    new_dict['MatchId'] = re.findall('"matchid":"NGL_(.+?)",',betting_info)[0]
                                elif sport in ['Virtual Soccer','Virtual Tennis']:
                                    new_dict['MatchId'] = re.findall('"matchid":(.+?),',betting_info)[0]
                                else:
                                    new_dict['MatchId'] = re.findall('"matchid":"BVS_(.+?)",',betting_info)[0]
                                new_dict['BetTypeId'] = re.findall('"bettype":(.+?),',betting_info)[0]
                                betteam_list = re.findall('"SelId":"(.+?)",',betting_info)
                                for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                    new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                    try:
                                        if re.findall('"SelId":"%s","Price":(.+?),'%str(bet_choice),betting_info)[0] == "0" : #這是 Live 的 Odds 為 0 就先抓 Deadball 來下就好
                                            continue
                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"SelId":"%s","Price":(.+?),'%str(bet_choice),betting_info)[0]
                                    except:
                                        pass
                                if "Happy 5" == sport:
                                    Match_dict[re.findall('"oddsid":"H5_(.+?)",',betting_info)[0]] = new_dict
                                elif sport in ['Virtual Soccer','Virtual Tennis']:
                                    Match_dict[re.findall('"oddsid":(.+?),',betting_info)[0]] = new_dict
                                elif "Number Game" in sport:
                                    Match_dict[re.findall('"oddsid":"NGL_(.+?)",',betting_info)[0]] = new_dict
                                else:
                                    Match_dict[re.findall('"oddsid":"BVS_(.+?)",',betting_info)[0]] = new_dict
                            else:
                                new_dict = {}
                                if "parlay" not in self.bet_type and '"bettype":10' not in betting_info: 
                                    if int(re.findall('"morecount":"([0-9]+)",',betting_info)[0]) > 2 :
                                        match_list.append(re.findall('"matchid":(.+?),',betting_info)[0]) #先幫 More 抓取所有 Match ID
                                if '"bettype":10' in betting_info: #Outright 的
                                    new_dict['MatchId'] = re.findall('"matchid":"o(.+?)",',betting_info)[0]
                                    new_dict['BetTypeId'] = re.findall('"bettype":(.+?),',betting_info)[0]
                                    new_dict['bet_team_0'] = "Outright"
                                    try:
                                        new_dict['odds_0'] = re.findall('"odds1a":(.+?),',betting_info)[0]
                                    except:
                                        new_dict['odds_0'] = re.findall('"odds1a":(.+?)}',betting_info)[0]
                                    Match_dict[re.findall('"oddsid":"o(.+?)",',betting_info)[0]] = new_dict
                                else:
                                    new_dict['BetTypeId'] = re.findall('"bettype":(.+?),',betting_info)[0]
                                    new_dict['MatchId'] = re.findall('"matchid":(.+?),',betting_info)[0]
                                    if int(new_dict['BetTypeId']) in betteam_trans.keys():
                                        for bet_choice_index,trans_key in enumerate(betteam_trans[int(new_dict['BetTypeId'])].keys()):
                                            new_dict['bet_team_%s'%bet_choice_index] = betteam_trans[int(new_dict['BetTypeId'])][trans_key]
                                            try:
                                                try:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?),'%trans_key,betting_info)[0]
                                                except:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?)}'%trans_key,betting_info)[0]
                                            except:
                                                pass
                                    else:
                                        if "com1" in betting_info:
                                            for bet_choice_index, bet_choice in enumerate(["1","x","2"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?),'%bet_choice,betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?)}'%bet_choice,betting_info)[0]
                                                except:
                                                    pass
                                        elif 'odds1a' in betting_info:
                                            for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                                except:
                                                    pass
                                        elif "cs" in betting_info:
                                            new_betting_info = betting_info.split("siteoddsgap3")[1]
                                            betteam_list = re.findall('cs([0-9]+)',new_betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?),'%str(bet_choice),new_betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?)}'%str(bet_choice),new_betting_info)[0]
                                                except:
                                                    pass
                                        elif "odds_flex" in betting_info and "AOS" in betting_info:
                                            betteam_list = re.findall('"([0-9]?\:[0-9]?\/.+?)":\[',betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(bet_choice).replace("/","\/"),betting_info)[0]
                                        elif "odds_flex" in betting_info and "G0" in betting_info:
                                            betteam_list = re.findall(':{"(.+?\/.+?)"|],"(.+?\/.+?)"',betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                new_dict['bet_team_%s'%bet_choice_index] = re.findall('.+\'(.+?\/.+?)\'',str(bet_choice))[0]
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(new_dict['bet_team_%s'%bet_choice_index]).replace("/","\/").replace("+","\+"),betting_info)[0]
                                        elif '44"A002' in betting_info :
                                            raise KeyboardInterrupt
                                        else:
                                            for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                                except:
                                                    pass
                                    odds_id = re.findall('"oddsid":(.+?),',betting_info)[0].replace('"','').replace('os_','').replace('es_','')
                                    Match_dict[odds_id] = new_dict
                        self.match_list_dict[sport][market] = list(set(match_list))
                    else:
                        for sport_filter in betting_info_list.keys():
                            cross_sports_parlay_Match_dict = {}
                            for betting_info in betting_info_list[sport_filter]:
                                try:
                                    new_dict = {}
                                    new_dict['BetTypeId'] = re.findall('"bettype":(.+?),',betting_info)[0]
                                    new_dict['MatchId'] = re.findall('"matchid":(.+?),',betting_info)[0]
                                    if int(new_dict['BetTypeId']) in betteam_trans.keys():
                                        for bet_choice_index,trans_key in enumerate(betteam_trans[int(new_dict['BetTypeId'])].keys()):
                                            new_dict['bet_team_%s'%bet_choice_index] = betteam_trans[int(new_dict['BetTypeId'])][trans_key]
                                            try:
                                                try:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?),'%trans_key,betting_info)[0]
                                                except:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?)}'%trans_key,betting_info)[0]
                                            except:
                                                pass
                                    else:
                                        if "com1" in betting_info:
                                            for bet_choice_index, bet_choice in enumerate(["1","x","2"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?),'%bet_choice,betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?)}'%bet_choice,betting_info)[0]
                                                except:
                                                    pass
                                        elif 'odds1a' in betting_info:
                                            for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                                except:
                                                    pass
                                        elif "cs" in betting_info:
                                            new_betting_info = betting_info.split("siteoddsgap3")[1]
                                            betteam_list = re.findall('cs([0-9]+)',new_betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?),'%str(bet_choice),new_betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?)}'%str(bet_choice),new_betting_info)[0]
                                                except:
                                                    pass
                                        elif "odds_flex" in betting_info and "AOS" in betting_info:
                                            betteam_list = re.findall('"([0-9]?\:[0-9]?\/.+?)":\[',betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                try:
                                                    new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(bet_choice).replace("/","\/"),betting_info)[0]
                                                except:
                                                    pass
                                        elif "odds_flex" in betting_info and "G0" in betting_info:
                                            betteam_list = re.findall(':{"(.+?\/.+?)"|],"(.+?\/.+?)"',betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                try:
                                                    new_dict['bet_team_%s'%bet_choice_index] = re.findall('.+\'(.+?\/.+?)\'',str(bet_choice))[0]
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(new_dict['bet_team_%s'%bet_choice_index]).replace("/","\/").replace("+","\+"),betting_info)[0]
                                                except:
                                                    pass
                                        else:
                                            for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    try:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                                    except:
                                                        new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                                except:
                                                    pass
                                    odds_id = re.findall('"oddsid":(.+?),',betting_info)[0].replace('"','').replace('os_','').replace('es_','')
                                    cross_sports_parlay_Match_dict[odds_id] = new_dict
                                except:
                                    pass
                            sport_filter = self.game_mapping(int(sport_filter)) #轉換為 Sport Name
                            Match_dict[sport_filter] = cross_sports_parlay_Match_dict
                    get_Ws_info_result = True
                    raise KeyboardInterrupt
                elif 'No Odds' in str(betting_info_list):
                    raise KeyboardInterrupt
                else:
                    raise KeyboardInterrupt #為了關閉 WS 的連線，需 Raise 至 KeyboardInterrupt 
            except KeyboardInterrupt as exc:
                print('Quit.')
                if get_Ws_info_result == True:
                    if sport != 'Cross Sports':
                        return Match_dict
                    else:
                        return Match_dict
                elif 'No Odds' in str(betting_info_list):
                    return 'No Odds'
                else:
                    return False
        elif bet_type == 'more':
            remote = 'ws://{ms2_url}/socket.io/?gid=12345&token={WS_token}&id={WS_id}&rid=1&EIO=3&transport=websocket'.format(ms2_url=ms2_url,WS_token=WS_token,WS_id=WS_id)
            get_Ws_info_result = False
            try:
                if self.match_list_dict[sport][market] == '' :
                    return "No Market"
                elif len(self.match_list_dict[sport][market]) == 0 :
                    return "No More Bettype"
                else:
                    match_list = self.match_list_dict[sport][market]
                    match_set = set(match_list)
                    match_list = list(match_set)
                for matchid in match_list:
                    logger.info('抓取 %s More Bettype'%matchid  )
                    self.matchid = matchid
                    self.bet_type = 'more'
                    betting_info_list = asyncio.new_event_loop().run_until_complete(startup(remote))
                    if betting_info_list != False and betting_info_list != None and '"oddsstatus":"closePrice"' not in betting_info_list and 'No Odds' not in betting_info_list:
                        for betting_info in betting_info_list:
                            new_dict = {}
                            if int(re.findall('"bettype":(.+?),',betting_info)[0]) < 10:
                                pass
                            else:
                                new_dict['MatchId'] = matchid
                                new_dict['BetTypeId'] = re.findall('"bettype":(.+?),',betting_info)[0]
                                if int(new_dict['BetTypeId']) in betteam_trans.keys():
                                    for bet_choice_index,trans_key in enumerate(betteam_trans[int(new_dict['BetTypeId'])].keys()):
                                        new_dict['bet_team_%s'%bet_choice_index] = betteam_trans[int(new_dict['BetTypeId'])][trans_key]
                                        try:
                                            try:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?),'%trans_key,betting_info)[0]
                                            except:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":(.+?)}'%trans_key,betting_info)[0]
                                        except:
                                            pass
                                else:
                                    if "com1" in betting_info:
                                        for bet_choice_index, bet_choice in enumerate(["1","x","2"]): 
                                            new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                            try:
                                                try:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?),'%bet_choice,betting_info)[0]
                                                except:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"com%s":(.+?)}'%bet_choice,betting_info)[0]
                                            except:
                                                pass
                                    elif 'odds1a' in betting_info:
                                        for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                            new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                            try:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                            except:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                    elif "cs" in betting_info:
                                        try:
                                            new_betting_info = betting_info.split("siteoddsgap3")[1]
                                            betteam_list = re.findall('cs([0-9]+)',new_betting_info)
                                            for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                                new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                                try:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?),'%str(bet_choice),new_betting_info)[0]
                                                except:
                                                    new_dict['odds_%s'%bet_choice_index] = re.findall('"cs%s":(.+?)}'%str(bet_choice),new_betting_info)[0]
                                        except:
                                            pass
                                    elif "odds_flex" in betting_info and "AOS" in betting_info:
                                        betteam_list = re.findall('"([0-9]?\:[0-9]?\/.+?)":\[',betting_info)
                                        for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                            new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                            new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(bet_choice).replace("/","\/"),betting_info)[0]
                                    elif "odds_flex" in betting_info and "G0" in betting_info:
                                        betteam_list = re.findall(':{"(.+?\/.+?)"|],"(.+?\/.+?)"',betting_info)
                                        for bet_choice_index, bet_choice in enumerate(betteam_list): 
                                            new_dict['bet_team_%s'%bet_choice_index] = re.findall('.+\'(.+?\/.+?)\'',str(bet_choice))[0]
                                            new_dict['odds_%s'%bet_choice_index] = re.findall('"%s":\[([0-9]+)'%str(new_dict['bet_team_%s'%bet_choice_index]).replace("/","\/").replace("+","\+"),betting_info)[0]
                                    else:
                                        for bet_choice_index, bet_choice in enumerate(["h","a"]): 
                                            new_dict['bet_team_%s'%bet_choice_index] = bet_choice
                                            try:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?),'%str(int(bet_choice_index)+1),betting_info)[0]
                                            except:
                                                new_dict['odds_%s'%bet_choice_index] = re.findall('"odds%sa":(.+?)}'%str(int(bet_choice_index)+1),betting_info)[0]
                                odds_id = re.findall('"oddsid":(.+?),',betting_info)[0]
                                if '"' in odds_id:
                                    odds_id = odds_id.replace('"','').replace('os_','').replace('es_','')
                                else:
                                    pass
                                Match_dict[odds_id] = new_dict
                        if len(Match_dict) < 2:
                            logger.info('Odds 數量小於二個，故抓取下一個 Match' )
                            Match_dict = {}
                            pass #再做一次，抓到都大於兩場為止
                        else:
                            get_Ws_info_result = True
                            raise KeyboardInterrupt
                    else:
                        pass
            except KeyboardInterrupt as exc:
                print('Quit.')
                if get_Ws_info_result == True:
                    return Match_dict
                else:
                    return False

    def set_odds_type(self,odds_type='MY'):# /setting/SaveUserProfile
        self.odds_type = odds_type
        odds_type_dict = {'Dec' : '1','CN' : '2','Indo' : '3','MY' : '4','US' : '5'}
        if "nova88" in self.url:
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9'
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.url = self.nova_set_odds_type_url
            #self.headers['Cookie'] = "ASP.NET_SessionId=" + self.client_session.cookies.get_dict()['ASP.NET_SessionId']
            #self.headers['Cookie'] = "ASP.NET_SessionId=zsas5pqboaj1eb30novyhuda" 
        
        #logger.info('NET_SessionId: %s'%self.client_session.cookies.get_dict()['ASP.NET_SessionId'])
        if 'qasb' in self.url or '/(S' in self.url :
            r = self.client_session.post(self.member_url  + '/Customer/OddsType?set={odds_type}'.format(odds_type=odds_type_dict[odds_type])  ,headers=self.headers,verify=False)
        else:
            r = self.client_session.post(self.member_url  + '/Customer/OddsType?set={odds_type}'.format(odds_type=odds_type_dict[odds_type]) ,verify=False)
        if r.ok == True:
            logger.info('/Customer/OddsType?set Api Success ' )
        else:
            self.error_msg = r.text
            logger.error('Setting Odds Type Api Fail response :%s'%self.error_msg )
            #self.stress_dict['response'].append(r.text) 
            return False
        self.req_url = '/EntryIndex/SetOddsType'
        data = 'OddsType={odds_type}'.format(odds_type=odds_type_dict[odds_type])
        start = time.perf_counter()# 計算請求時間用
        if 'qasb' in self.url or '/(S' in self.url :
            r = self.client_session.post(self.url  + '/EntryIndex/SetOddsType' ,data=data , headers=self.headers  ,verify=False)
        else:
            r = self.client_session.post(self.url  + '/EntryIndex/SetOddsType' ,data=data , verify=False)
        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
        if r.ok == True:
            logger.info('Set Odds type Success : %s'%odds_type )
        else:
            self.error_msg = r.text
            logger.error('Setting Odds Type Api Fail response :%s'%self.error_msg )
            #self.stress_dict['response'].append(r.text) 
            return False

    def DoplaceBet(self,sport,Match_dict,already_list=[],bet_team_index='0',parlay_type='1',times='',bettype_id='',not_bettype_id='',sport_list = '',bet_type=''): #not_bettype_id 是為了不要重複下到同一個 Bettype
        import random
        from random import shuffle
        if bet_type != '':
            self.bet_type = bet_type
        '''
        SportName 和 gameid 之後 做動態傳入,目前寫死 
        '''
        BetTypeId_list = []
        self.Odds_dict = {}# key 為 match id ,value 為 odds

        len_Match_dic= len(Match_dict)
        logger.info('len_Match_dict : %s'%len_Match_dic)

        if 'parlay' in self.bet_type :
            if sport_list == '':
                data_str_dict = {}
                #抓取兩個一般 Bettype 一個 More Bettype
                new_Match_dict = {} 
                old_Match_dict = Match_dict
                Match_key_list = list(Match_dict.keys())
                shuffle(Match_key_list)
                for match_key in Match_key_list:
                    if len(new_Match_dict.keys()) == 3: #已經抓出三個 Match ID
                        break
                    else:
                        if len(new_Match_dict.keys()) < 2 and int(Match_dict[match_key]['BetTypeId']) < 10:
                            new_Match_dict[match_key] = Match_dict[match_key]
                        elif len(new_Match_dict.keys()) == 2 and int(Match_dict[match_key]['BetTypeId']) > 10:
                            new_Match_dict[match_key] = Match_dict[match_key]
                Match_dict = new_Match_dict
            else:
                data_str_dict = {}
                #抓取兩個一般 Bettype 一個 More Bettype
                new_Match_dict = {} 
                old_Match_dict = Match_dict
                for sport in sport_list:
                    Match_key_list = list(Match_dict[sport].keys())
                    shuffle(Match_key_list)
                    for match_key in Match_key_list:
                        if sport == 'Soccer' :
                            if int(Match_dict[sport][match_key]['BetTypeId']) > 10 or Match_key_list.index(match_key) == len(Match_key_list)-1:
                                new_Match_dict[match_key] = Match_dict[sport][match_key]
                                break
                            else:
                                pass
                        else:
                            new_Match_dict[match_key] = Match_dict[sport][match_key]
                            break
                Match_dict = new_Match_dict

        try:
            data_str = ""# 需loop 慢慢加起來
            for index_key,Odds_id in enumerate(Match_dict.keys()):#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                if sport_list != '': #由於 Cross Sports Parlay 的運動會隨機，所以再傳入一個 List
                    sport = sport_list[index_key]
                    gameid = self.game_mapping(sport)
                if 'Outright' in str(Match_dict): #outright game_id 為 999，game_type 為平常下注的 sports gameid
                    gameid = 999
                else:
                    gameid = self.game_mapping(sport)
                #logger.info('index_key : %s'%index_key)
                Match = Match_dict# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
                #logger.info('len : %s'%len(Match))

                Match_key_list = list(Match_dict.keys())# list裡面放 bettype
                find_bet_type_id = False
                if self.bet_type != 'more': #more 要排除小於 3 的 Bettype ID
                    from random import shuffle #用來把 list 打亂可以不用一值下同一場比賽
                    if bettype_id != '' and gameid != 999:
                        shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] == str(bettype_id):
                                if 'bet_team' not in str(Match[Match_key]):
                                    continue
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No BetType ID"
                    elif not_bettype_id != '' and gameid != 999 :
                        shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != not_bettype_id:
                                if 'bet_team' not in str(Match[Match_key]):
                                    continue
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID %s"%not_bettype_id
                        pass
                    else:
                        if 'parlay' in self.bet_type:
                            Match_key_list = [Match_key_list[index_key]]
                        else:
                            shuffle(Match_key_list)
                        for Match_key in Match_key_list:
                            if 'bet_team' not in str(Match[Match_key]):
                                continue
                            Match_key_list = []
                            Match_key_list.append(Match_key)
                            find_bet_type_id = True
                            break
                        if find_bet_type_id == False:
                            return "No BetType ID"
                else:
                    from random import shuffle #用來把 list 打亂可以不用一值下同一場比賽
                    shuffle(Match_key_list)
                    New_Match_key_list = []
                    if not_bettype_id != '':
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != str(not_bettype_id) and int(Match[Match_key]['BetTypeId']) >= 4:
                                if 'bet_team' not in str(Match[Match_key]):
                                    continue
                                New_Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID %s"%not_bettype_id
                        else:
                            Match_key_list = New_Match_key_list
                    else:
                        for Match_key in Match_key_list:
                            if int(Match[Match_key]['BetTypeId']) >= 4: 
                                if 'bet_team' not in str(Match[Match_key]):
                                    continue
                                New_Match_key_list.append(Match_key)
                                find_bet_type_id = True
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No More BetType"
                        else:
                            Match_key_list = New_Match_key_list
                        pass
                if gameid != 999:
                    retry_count = 0
                    while True:
                        betting_info = {} #儲存我下注的值 
                        ran_index = random.randint(0, len(Match_key_list) -1  )
                        Ran_Match_id =  Match_key_list[ran_index]# 隨機取出 odds id
                        logger.info('Ran_Match_id: %s'%Ran_Match_id)
                        
                        BetTypeId = Match[Ran_Match_id]['BetTypeId']
                        logger.info('BetTypeId: %s'%BetTypeId)

                        if BetTypeId not in already_list:
                            logger.info('BetTypeId: %s 沒有投注過 ,成立'%BetTypeId)
                            break
                        logger.info('BetTypeId: %s 已經存在過注單裡 ,retry : %s'%(BetTypeId, retry_count ))
                        retry_count = retry_count + 1
                        if retry_count >= 10:   
                            break

                    Matchid = Match[Ran_Match_id]['MatchId']
                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        odds = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                    except:
                        odds = Match[Ran_Match_id]['odds_0']
                    betting_info['odds'] = odds

                    try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                        bet_team = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                        betting_info['bet_team'] = bet_team
                    except:
                        bet_team = Match[Ran_Match_id]['bet_team_0']
                    
                    oddsid = Ran_Match_id
                    BetTypeId = Match[Ran_Match_id]['BetTypeId']
                else:
                    betting_info = {} #儲存我下注的值

                    ran_index = random.randint(0, len(Match_key_list) -1  )
                    Ran_Match_id =  Match_key_list[ran_index]# 隨機取出 odds id
                    logger.info('Ran_Match_id: %s'%Ran_Match_id)

                    oddsid = Ran_Match_id
                    Matchid = Match[Ran_Match_id]['MatchId']
                    odds = Match[Ran_Match_id]['odds_0']
                    betting_info['odds'] = odds
                '''
                parlay
                其他sport 拿到的 odds 需轉成 Dec Odds , Cricket 原本就是 dec odds所以不做轉換 
                5: Ft 1x2 , 15: 1H 1x2(原本就是 dec odds, 不用轉) 
                '''
                if 'parlay' not in self.bet_type : # single odds 先不轉
                    logger.info('odds: %s'%odds)
                    pass
                    
                else:# parlay
                    if  gameid != 50 and gameid != 999:# cricket 的不用轉 
                        if BetTypeId not in [5, 15]:#  5: Ft 1x2 , 15: 1H 1x2 他們是 屬於Dec Odds
                            odds = self.Odds_Tran(odds,odds_type=self.odds_type)
                            betting_info['odds'] = odds
                            logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( sport,BetTypeId, odds) )
                if gameid != 999 and 'parlay' not in self.bet_type:
                    logger.info('BetTypeId : %s'%BetTypeId)
                    try:
                        data_format = "ItemList[{index_key}][Type]={bet_type}&ItemList[{index_key}][Bettype]={BetTypeId}&ItemList[{index_key}][Oddsid]={oddsid}&ItemList[{index_key}][Odds]={odds}&\
                            &ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][Gameid]={gameid}&ItemList[{index_key}][Betteam]={betteam}&ItemList[{index_key}][MMR]=&\
                            ItemList[{index_key}][SportName]={sportName}&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][pty]=1&ItemList[{index_key}][sinfo]=\
                            ".format(index_key= 0,bet_type = "OU",BetTypeId=BetTypeId, oddsid=oddsid ,odds=odds, Matchid = Matchid ,gameid = gameid,betteam = bet_team,sportName=sport  )
                    except Exception as e:
                        logger.error('data_format: %s'%e)
                    data_str = data_str + data_format + '&'
                elif 'parlay' in self.bet_type:
                    logger.info('BetTypeId : %s'%BetTypeId)
                    try:
                        data_format = "ItemList[{index_key}][Type]={bet_type}&ItemList[{index_key}][Bettype]={BetTypeId}&ItemList[{index_key}][Oddsid]={oddsid}&ItemList[{index_key}][Odds]={odds}&\
                            &ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][Gameid]={gameid}&ItemList[{index_key}][Betteam]={betteam}&ItemList[{index_key}][MMR]=&\
                            ItemList[{index_key}][SportName]={sportName}&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][sinfo]=\
                            ".format(index_key= 0,bet_type = "parlay",BetTypeId=BetTypeId, oddsid=oddsid ,odds=odds, Matchid = Matchid ,gameid = gameid,betteam = bet_team,sportName=sport  )
                    except Exception as e:
                        logger.error('data_format: %s'%e)
                    data_str_dict[index_key] = data_format + '&'
                else:
                    data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                        &ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][QuickBet]=1:100:10:1&\
                        ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][GameName]=&\
                        ItemList[{index_key}][SportName]={sportName}&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][sinfo]=\
                        ".format(index_key= index_key,bet_type = "OT", oddsid=oddsid ,odds=odds, Matchid = Matchid ,
                            gameid = '999',sportName=sport  )

                    data_str = data_str + data_format + '&'
                '''
                parlay 串多少match 邏輯
                當 index 到了 總長度 的最後, 須把 combo_str 家回data裡
                '''
                if 'parlay' in self.bet_type:
                    betting_info['odds_type'] = "Dec"
                    betting_info['Matchid'] = Matchid
                    BetTypeId_list.append(betting_info)
                    retry = 0
                    while retry < 10 :
                        if 'qasb' in self.url :
                            r = self.client_session.post(self.member_url  + '/BettingParlay/GetParlayTickets'  , data = data_str_dict[index_key].encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                        else:
                            r = self.client_session.post(self.url.replace("www","hm")  + '/BettingParlay/GetParlayTickets'  , data = data_str_dict[index_key].encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                        if "please try again" in r.text :
                            time.sleep(0.5)
                            retry += 1
                        elif "Authentication has expired" in r.text or "Logout" in r.text:
                            self.relogin = False
                            if self.relogin == True:
                                retry += 1
                                continue
                            print(sport)
                            logger.info('Your session has been terminated，等待 30 秒後重新登入')
                            if '/(S' in self.url:
                                self.url = self.url.split('/(S')[0]
                            desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                            login_result = desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                            if login_result == False:
                                logger.info("登入失敗，重新登入")
                                retry += 1
                                continue
                            elif 'Login Too Often' in str(login_result):
                                logger.info("Login Too Often，等待 30 秒後再重新登入")
                                time.sleep(30)
                                retry += 1
                                continue
                            else:
                                pass
                            self.url = desktop_api.url
                            self.member_url = desktop_api.member_url
                            self.headers = desktop_api.headers
                            retry += 1
                            self.relogin = True
                        else:
                            break
                    
                    try:
                        logger.info('GetTickets OK')
                        ticket_Data = r.json()['Data']['Tickets']# Data 為一個list. 取出來為一個 dict
                        #logger.info('ticket: %s'%Data)
                        min_stake = ticket_Data[0]['Minbet']
                        guid = ticket_Data[0]['Guid']
                        Line = ticket_Data[0]['Line']
                        betting_info['Line'] = Line
                        for idx,bet_info in enumerate(BetTypeId_list):
                            if idx == index_key:
                                BetTypeId_list[idx]['Line'] = Line
                                break
                        Hdp1 = ticket_Data[0]['Hdp1']
                        Hdp2 = ticket_Data[0]['Hdp2']
                        betting_info['LeagueName'] = ticket_Data[0]['LeagueName']
                        betting_info['BettypeId'] = ticket_Data[0]['Bettype']
                        betting_info['BettypeName'] = ticket_Data[0]['BettypeName']
                        betting_info['bet_team'] = ticket_Data[0]['ChoiceValue']
                        betting_info['oddsid'] = Ran_Match_id
                        try:
                            Hscore = ticket_Data[0]['LiveHomeScore']
                            Asocre = ticket_Data[0]['LiveAwayScore']
                        except:
                            Hscore = '0'
                            Asocre = '0'
                        parlay_data_format = "ItemList[{index_key}][Guid]={Guid}&ItemList[{index_key}][Line]={Line}&ItemList[{index_key}][hdp1]={hdp1}&ItemList[{index_key}][hdp2]={hdp2}&ItemList[{index_key}][Hscore]={Hscore}\
                        &ItemList[{index_key}][Ascore]={Ascore}".format(Guid =guid,  Line =Line , hdp1 = Hdp1, hdp2 = Hdp2, Hscore = Hscore ,Ascore = Asocre,index_key= index_key )
                        data_str_dict[index_key] = data_str_dict[index_key] + parlay_data_format + '&'
                    except Exception as e:
                        self.error_msg = r.text
                        logger.error('Parlay Bet Get Ticket 有誤 : %s'%self.error_msg)
                        return 'GetTickets False'
                
                    


                else:# single

                    combo_str = "ItemList[0][Minbet]=1"

                    data_str = data_str + combo_str
                    
                    #logger.info('ticket data: %s'%data_str)
                    start = time.perf_counter()# 計算請求時間用
                    self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                    retry = 0
                    while retry < 10 :
                        time.sleep(1)
                        self.req_list = []# 存放 ticket 和 betting 的 列表
                        start = time.perf_counter()# 計算請求時間用
                        if 'qasb' in self.url :
                            r = self.client_session.post(self.member_url + '/Betting/GetTickets/'  , data = data_str.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                        else:
                            no_NsessionID_header = self.headers.copy()
                            del no_NsessionID_header['Cookie']
                            r = self.client_session.post(self.member_url  + '/Betting/GetTickets/'  , data = data_str.encode(),headers=no_NsessionID_header,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                        if "please try again" in r.text :
                            time.sleep(3)
                            retry += 1
                        elif "Authentication has expired" in r.text or "Logout" in r.text:
                            self.relogin = False
                            if self.relogin == True:
                                retry += 1
                                continue
                            print(sport)
                            logger.info('Your session has been terminated，等待 30 秒後重新登入')
                            if '/(S' in self.url:
                                self.url = self.url.split('/(S')[0]
                            desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                            login_result = desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                            if login_result == False:
                                logger.info("登入失敗，重新登入")
                                retry += 1
                                continue
                            elif 'Login Too Often' in str(login_result):
                                logger.info("Login Too Often，等待 30 秒後再重新登入")
                                time.sleep(30)
                                retry += 1
                                continue
                            else:
                                pass
                            self.url = desktop_api.url
                            self.member_url = desktop_api.member_url
                            self.headers = desktop_api.headers
                            retry += 1
                            self.relogin = True
                            #Login().login_api(device='Pc driver', user=self.user, url=self.url,central_account='web.desktop',central_password='1q2w3e4r')
                        else:
                            break
                    self.req_list.append(self.request_time )
                    try:
                        order_value = {}
                        ticket_Data = r.json()['Data'][0]# Data 為一個list. 取出來為一個 dict
                        #logger.info('ticket: %s'%Data)
                        logger.info('GetTickets OK')
                        min_stake = ticket_Data['Minbet']
                        guid = ticket_Data['Guid']
                        Line = ticket_Data['Line']
                        if Line%1 == 0 : 
                            Line = int(Line)
                        betting_info['Line'] = Line
                        Hdp1 = ticket_Data['Hdp1']
                        if Hdp1%1 == 0 : 
                            Hdp1 = int(Hdp1)
                        Hdp2 = ticket_Data['Hdp2']
                        if Hdp2%1 == 0 : 
                            Hdp2 = int(Hdp2)
                        try:
                            Hscore = ticket_Data['LiveHomeScore']
                            Asocre = ticket_Data['LiveAwayScore']
                        except:
                            Hscore = '0'
                            Asocre = '0'           
                        try:
                            SrcOddsInfo = ticket_Data['SrcOddsInfo']
                        except:
                            SrcOddsInfo = ''
                        ChoiceValue = ticket_Data['ChoiceValue']
                        Home = ticket_Data['HomeName']
                        Away = ticket_Data['AwayName']
                        betting_info['LeagueName'] = ticket_Data['LeagueName']
                        betting_info['BettypeId'] = ticket_Data['Bettype']
                        betting_info['BettypeName'] = ticket_Data['BettypeName']
                        betting_info['bet_team'] = ticket_Data['ChoiceValue']
                        betting_info['oddsid'] = Ran_Match_id
                        try:
                            if 'Odds has changed from' in ticket_Data['Message']:
                                import re
                                old_odds = re.findall('Odds has changed from (.+) to',ticket_Data['Message'])[0]
                                new_odds = re.findall('Odds has changed from .+ to (.+).',ticket_Data['Message'])[0]
                                if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                                    old_odds = old_odds.rstrip('0')
                                if abs(float(new_odds)) < 100 and '.0' in old_odds:
                                    new_odds = new_odds.rstrip('0')
                                betting_info['odds'] = new_odds
                                data_str = re.sub("\[Odds\]=(.*?)&I", "[Odds]="+str(new_odds)+"&I",data_str)
                        except:
                            pass
                    except Exception as e:
                        import sys
                        import traceback
                        error_class = e.__class__.__name__ #取得錯誤類型
                        detail = e.args[0] #取得詳細內容
                        cl, exc, tb = sys.exc_info()
                        lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
                        fileName = lastCallStack[0] #取得發生的檔案名稱
                        lineNum = lastCallStack[1]
                        print(str(e))
                        error_msg = r.text
                        logger.error('Single Bet Get Ticket 有誤 : %s'%error_msg)
                        return 'GetTickets False'
                    if index_key == 0:
                        break 

        except Exception as e:
            logger.error('DoplaceBet: %s'%e)
        
        
        retry_count = 0

        try:
            import re
            data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 

            #self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]
            post_data =  data_str
            
            if 'parlay' in  self.bet_type:
                if parlay_type == '1' :
                    combo_str = "ComboLists[0][Type]=0&ComboLists[0][BetCount]=3&ComboLists[0][Stake]=0&ComboLists[1][Type]=1&ComboLists[1][BetCount]=1&ComboLists[1][Stake]=1\
                        &ComboLists[2][Type]=2&ComboLists[2][BetCount]=4&ComboLists[2][Stake]=0&ComboLists[3][Type]=3&ComboLists[3][BetCount]=7&ComboLists[3][Stake]=0"
                elif parlay_type == '2' :
                    combo_str = "ComboLists[0][Type]=0&ComboLists[0][BetCount]=3&ComboLists[0][Stake]=0&ComboLists[1][Type]=1&ComboLists[1][BetCount]=1&ComboLists[1][Stake]=0\
                        &ComboLists[2][Type]=2&ComboLists[2][BetCount]=4&ComboLists[2][Stake]=1&ComboLists[3][Type]=3&ComboLists[3][BetCount]=7&ComboLists[3][Stake]=0"
                elif parlay_type == '3' :
                    combo_str = "ComboLists[0][Type]=0&ComboLists[0][BetCount]=3&ComboLists[0][Stake]=0&ComboLists[1][Type]=1&ComboLists[1][BetCount]=1&ComboLists[1][Stake]=0\
                        &ComboLists[2][Type]=2&ComboLists[2][BetCount]=4&ComboLists[2][Stake]=0&ComboLists[3][Type]=3&ComboLists[3][BetCount]=7&ComboLists[3][Stake]=1"

                post_data = data_str_dict[0] + data_str_dict[1].replace('ItemList[0]','ItemList[1]') + data_str_dict[2].replace('ItemList[0]','ItemList[2]') + combo_str
                retry = 0
                while retry < 10 :
                    if 'qasb' in self.url :
                        r = self.client_session.post(self.member_url+ '/BettingParlay/DoplaceBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    else:
                        r = self.client_session.post(self.member_url + '/BettingParlay/DoplaceBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    if "please try again" in r.text :
                        time.sleep(0.5)
                        retry += 1
                    elif "Your session has been terminated" in r.text or "Logout" in r.text:
                        logger.info('Your session has been terminated，等待 30 秒後重新登入')
                        if '/(S' in self.url:
                            self.url = self.url.split('/(S')[0]
                        desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                        desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                        self.url = desktop_api.url
                        self.member_url = desktop_api.member_url
                        self.headers = desktop_api.headers
                    else:
                        break
                retry = 0
                while retry < 3: 
                    betting_response = self.Betting_response(response=r, times=times,betting_info=betting_info,gameid=gameid,BetTypeId_list=BetTypeId_list)
                    if betting_response != True and betting_response != False and 'TransId_Cash' not in betting_response:
                        if "is closed" in betting_response or "is temporarily closed" in betting_response:
                            retry = 3
                            break
                        elif "Bet Fail" in betting_response:
                            return False
                        elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                            post_data = new_post_data
                            r,new_post_data = self.retry_betting(betting_response,post_data,min_stake,retry,betting_info,BetTypeId_list=BetTypeId_list) #現在只為了 Single betting 新增
                        else:
                            r,new_post_data = self.retry_betting(betting_response,post_data,min_stake,retry,betting_info,BetTypeId_list=BetTypeId_list) #現在只為了 Single betting 新增
                        retry += 1
                    else:
                        break
                if retry == 3:
                    order_value['LeagueName'] = betting_info['LeagueName']
                    order_value['Message'] = str(betting_response)
                    order_value['MatchID'] = Matchid
                    order_value['oddsid'] = Ran_Match_id
                    order_value['BetTypeId'] = betting_info['BettypeName']
                    order_value['BetChoice'] = betting_info['bet_team'] 
                    return str(order_value)
                else:
                    return betting_response
            else:# single bet
                # 這裡把 get_ticket拿到的 資訊 , 在加進  post_data
                post_data = post_data+ "&ItemList[0][stake]={bet_stake}&ItemList[0][Guid]={Guid}&ItemList[0][ChoiceValue]={ChoiceValue}&ItemList[0][Home]={Home}&ItemList[0][Away]={Away}&\
                ItemList[0][Line]={Line}&ItemList[0][Hdp1]={hdp1}&ItemList[0][Hdp2]={hdp2}&ItemList[0][Hscore]={Hscore}&ItemList[0][Ascore]={Ascore}&ItemList[0][SrcOddsInfo]={SrcOddsInfo}".format(bet_stake=min_stake
                ,Guid =guid,ChoiceValue=ChoiceValue,Home=Home,Away=Away,  Line =Line , hdp1 = Hdp1, hdp2 = Hdp2, Hscore = Hscore ,Ascore = Asocre,SrcOddsInfo = SrcOddsInfo)
             
                retry = 0
                while retry < 5 :
                    start = time.perf_counter()# 計算請求時間用
                    if 'qasb' in self.url :
                        r = self.client_session.post(self.member_url + '/Betting/ProcessBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    else:
                        no_NsessionID_header = self.headers.copy()
                        del no_NsessionID_header['Cookie']
                        r = self.client_session.post(self.member_url  + '/Betting/ProcessBet',data = post_data.encode(),headers=no_NsessionID_header,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
                    self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                    if "please try again" in r.text :
                        time.sleep(2)
                        retry += 1
                    elif "Your session has been terminated" in r.text or "Logout" in r.text:
                        logger.info('Your session has been terminated，等待 30 秒後重新登入')
                        if '/(S' in self.url:
                            self.url = self.url.split('/(S')[0]
                        desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                        desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                        self.url = desktop_api.url
                        self.member_url = desktop_api.member_url
                        self.headers = desktop_api.headers
                    else:
                        break
                self.req_list.append(self.request_time )
                if retry == 5: #在最前面下注就失敗
                    order_value = {}
                    if gameid != 999:
                        order_value['LeagueName'] = betting_info['LeagueName']
                        try:
                            order_value['Message'] = re.findall('"Message":(.+?)","',r.text)[0]
                        except:
                            repspone_json = r.json()
                            order_value['Message'] = str(repspone_json['ErrorMsg'])
                        order_value['MatchID'] = Matchid
                        order_value['oddsid'] = Ran_Match_id
                        order_value['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                        order_value['BetChoice'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                        return str(order_value)
                    else:
                        order_value['LeagueName'] = betting_info['LeagueName']
                        try:
                            order_value['Message'] = r.text['Message']
                        except:
                            repspone_json = r.json()
                            Data = repspone_json['Data']['ItemList'][0]
                            order_value['Message'] = str(Data['Message'])
                        order_value['MatchID'] = Matchid
                        order_value['oddsid'] = Ran_Match_id
                        order_value['BetTypeId'] = betting_info['BettypeName']
                        order_value['BetChoice'] = betting_info['bet_team']
                        return str(order_value)

                retry = 0
                while retry < 5: 
                    betting_response = self.Betting_response(response=r, times=times,betting_info=betting_info,gameid=gameid)
                    if betting_response != True and betting_response != False and 'TransId_Cash' not in betting_response:
                        if "is closed" in betting_response or "System Error" in betting_response or "is temporarily closed" in betting_response:
                            retry = 5
                            break
                        elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                            post_data = new_post_data
                            r,new_post_data = self.retry_betting(betting_response,post_data,min_stake,retry,betting_info) #現在只為了 Single betting 新增
                        else:
                            r,new_post_data = self.retry_betting(betting_response,post_data,min_stake,retry,betting_info) #現在只為了 Single betting 新增
                        retry += 1
                    else:
                        break
                if retry == 5:
                    if gameid != 999:
                        order_value['LeagueName'] = betting_info['LeagueName']
                        order_value['Message'] = str(betting_response)
                        order_value['MatchID'] = Matchid
                        order_value['oddsid'] = Ran_Match_id
                        order_value['BetTypeId'] = betting_info['BettypeName']
                        order_value['BetChoice'] = betting_info['bet_team'] 
                    else:
                        order_value['LeagueName'] = betting_info['LeagueName']
                        order_value['Message'] = str(betting_response)
                        order_value['MatchID'] = Matchid
                        order_value['oddsid'] = Ran_Match_id
                        order_value['BetTypeId'] = 'Outright'
                    return str(order_value)
                else:
                    return str(betting_response)
                

        except Exception as e:
            import sys
            import traceback
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info()
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1]
            logger.info('Desktop DoplaceBet Api Fail: %s'%e)
            return False

    def Betting_response(self,response,times,BetTypeId_list='',betting_info='',gameid=''):# 針對 投注 回復 做解析
        try:
            repspone_json = response.json()
        except:
            error_msg = response.text
            return False

        if 'parlay'  in self.bet_type:
            Data = repspone_json['Data']
            response_code = str(Data['Code'])
            Message = Data['Message']
            if response_code == '45':# HDP/OU has been changed
                logger.error('ErrorMsg: %s'%repspone_json['ErrorMsg'] ) 
                logger.info('Message: %s'%Message)
                
                #self.fail_bettype.append(BetTypeId_list[0])
                return False
            
            elif response_code == '-91':# update odds
                logger.info('Message: %s'%Message)
                logger.info('休息 兩秒鐘 再做')
                return Message

            elif response_code == '15':# odds has changed
                logger.info('Message: %s'%Message)
                ItemList = Data['ItemList']
                logger.info('ItemList: %s'%ItemList)# 一個list 裡面包 多個dict ,確認 每個 單 是否都有 odds changed
                
                
                odds_change_dict = {}# 變更後的odds , key 為 matchid , value 為 odds
                for dict_ in ItemList:
                    if str(dict_['Code']) == '15':# odds changed
                        Matchid = dict_['Key']
                        odds_change = dict_['Message'].split('to')[-1].strip('.').replace(' ','')# 切割完, 在移除最後一個 . 移除空白
                        logger.info('odds_change: %s'%odds_change)
                        odds_change_dict[Matchid] = dict_['Message']    
                logger.info('odds_change_dict: %s'%odds_change_dict)
                return odds_change_dict
                
                
            elif response_code in ['0','1']:# 投注成功
                order_value = {}
                order_value['Message'] = Message
                
                TransId_Combo = Data['TransId_Combo']
                TransId_System = Data['TransId_System']
                TransId_Lucky = Data['TransId_Lucky']

                TotalPerBet =  Data['TotalPerBet']
                order_value['TotalPerBet'] = TotalPerBet
                FinalBalance = Data['FinalBalance']
                order_value['FinalBalance'] = FinalBalance
                
                if TransId_Combo in ['0','']:
                    if TransId_System in ['0','']:
                        order_value['TransId_Cash'] = TransId_Lucky
                        for idx,bet_info in enumerate(BetTypeId_list):
                            for _dict in Data['ItemList']:
                                BetTypeId_list[idx]['TransId'] = _dict['TransId']
                                break
                    else:
                        order_value['TransId_Cash'] = TransId_System

                else:
                    order_value['TransId_Cash'] = TransId_Combo

                order_value['BetTypeId_list'] = BetTypeId_list

                if 'None' in str(order_value) :
                    print(str(order_value))
                logger.info('order_value: %s'%order_value)
                return order_value
            
            else:#例外 沒抓到的 code
                logger.info('response_code : %s'%response_code)
                logger.info('Message: %s'%Message)
                return 'Bet Fail !'
        else:# single bet
            '''
            #  ItemList 為一個 list ,裡面 放各資訊 字典 
            '''
            order_value = {}
            try:
                Itemdict = repspone_json['Data']['ItemList'][0]# Itemdict 為一個字典
                logger.info('betting response Error Code: %s'%repspone_json['Data']['Common']['ErrorCode'])

                order_value['TransId_Cash'] = Itemdict['TransId_Cash']
                #self.order_value['Message'] = Itemdict['Message']
                logger.info('betting response message: %s'%Itemdict['Message'])
                error_message = Itemdict['Message']
            except:
                error_message = repspone_json['ErrorMsg']
            #logger.info('self.post_data: %s'%self.post_data)
            if any(error_code in error_message for error_code in  ['Odds has changed','min','updating odds',"has been changed","is closed","System Error","temporarily closed","IN-PLAY"] ):
                
                #logger.info('self.post_data: %s'%self.post_data)
                return error_message
            else:
                pass
            
            try:
                #order_value['DisplayOdds'] = Itemdict['DisplayOdds']
                #BetRecommends = Itemdict['BetRecommends'][0]# 為一個 list ,裡面含 各個 bet type資訊，這個不是此注單的資訊，而且下方建議投注的資訊
                order_value['oddsid'] = betting_info['oddsid']
                pair_odds = ['1', '2', '3', '7', '8', '12', '17', '18', '20', '21', '81', '82', '83', '84', '85', '86', '87', '88', '91', '183', '184', '194', '203', '123', '153', '154', '155', '156', '228', '229', '381', '382', '386', '387', '388', '389', '390', '393', '394', '400', '401', '402', '403', '404', '428', '470', '471', '472', '479', '481', '488', '489', '490', '491', '492', '603', '604', '605', '606', '607', '609', '610', '611', '612', '613', '615', '616', '617', '701', '702', '704', '705', '706', '707', '708', '709', '710', '712', '713', '714', '8101', '8102', '8104', '9001', '9002', '9003', '9004', '9005', '9006', '9007', '9008', '9009', '9010', '9011', '9012', '9013', '9014', '9015', '9016', '9017', '9018', '9019', '9020', '9021', '9022', '9023', '9024', '9025', '9026', '9027', '9028', '9029', '9030', '9031', '9032', '9033', '9034', '9035', '9036', '9037', '9038', '9039', '9040', '9041', '9042', '9043', '9044', '9045', '9046', '9047', '9048', '9049', '9050', '9051', '9052', '9053', '9054', '9055', '9056', '9057', '9058', '9059', '9060', '9061', '9062', '9063', '9064', '9065', '9066', '9067', '9077', '9068', '9069', '9070', '9071', '9072', '9073', '9074', '9075', '9076', '9078', '9079', '9080', '9081', '9082', '9083', '9084', '9085', '9086', '9087','9089','9090','9091','9092','9093','9094','9095','9096','9097','9098','9099','9100','9101','9102','9103','9104','9105','9106','9107','9108','9109','9110','9111','9112','9113','9114','9115','9116','9117','9118','9119','9120','9121','9122','9123','9124','9125','9126','9127','9128','9129','9130','9131','9132','9133','9134','9135','9136','9137','9138','9139','9140','9141','9142']
                if gameid != 999:
                    if betting_info['BettypeId'] in pair_odds :
                        order_value['odds_type'] = self.odds_type
                    else:
                        order_value['odds_type'] = "Dec"
                    try: #給 DoplaceBet 使用的
                        order_value['Line'] = betting_info['Line']
                    except:
                        pass
                    order_value['LeagueName'] = betting_info['LeagueName']
                    order_value['BettypeName'] = betting_info['BettypeName']
                    order_value['BetTypeId'] = betting_info['BettypeId']
                    if '<span' in betting_info['bet_team']:
                        betting_info['bet_team'] = re.findall('>([a-zA-Z]+)<',betting_info['bet_team'])[0]
                    order_value['BetChoice'] = betting_info['bet_team']
                    order_value['Odds'] = str(betting_info['odds'])
                else:
                    order_value['odds_type'] = "Dec"
                    order_value['Line'] = betting_info['Line']
                    order_value['LeagueName'] = betting_info['LeagueName']
                    order_value['BettypeName'] = 'Outright'
                    order_value['Odds'] = str(betting_info['odds'])

                logger.info('order_value : %s'%order_value)
                #方便查看資料的
                pass_txt = open('Config/pass.txt', 'a+')
                pass_txt.write(str(order_value)+'\n')
                pass_txt.close()
                return order_value
            except:
                return False

    def retry_betting(self,error_code,post_data,bet_stake,retry,betting_info,BetTypeId_list=''):
        if "Odds has changed" in str(error_code):
            if "parlay" in self.bet_type:
                error_code_dict = error_code
                for error_key in (error_code_dict.keys()):
                    error_code = error_code_dict[error_key]
                    old_odds = re.findall('Odds has changed from (.+) to',error_code)[0] #去除尾數為 0 
                    new_odds = re.findall('Odds has changed from .+ to (.+).',error_code)[0]
                    if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                        old_odds = old_odds.rstrip('0')
                    if abs(float(new_odds)) < 100 and '.0' in old_odds:
                        new_odds = new_odds.rstrip('0')
                    for idx,betslip in enumerate(BetTypeId_list):
                        if str(error_key) in str(betslip):
                            BetTypeId_list[idx]['odds'] = new_odds
                            post_data = re.sub("ItemList\["+str(idx)+"\]\[Odds\]=(.*?)&I", "ItemList["+str(idx)+"][Odds]="+str(new_odds)+"&I",post_data)
                            pass
                    '''   
                    for idx,betslip in enumerate(str(self.BetTypeId_list).split("}, {")): 
                        if str(error_key) in str(betslip):
                            bettype_list_new_odds = re.sub("'odds': '(.*?)'", "'odds': '"+str(new_odds)+"'",str(betslip))
                            self.BetTypeId_list = str(self.BetTypeId_list).replace(betslip,bettype_list_new_odds)
                            post_data = re.sub("ItemList\["+str(idx)+"\]\[odds\]=(.*?)&I", "ItemList["+str(idx)+"][odds]="+str(new_odds)+"&I",post_data)
                            break
                    '''              
            else:
                old_odds = re.findall('Odds has changed from (.+) to',error_code)[0] #去除尾數為 0 
                new_odds = re.findall('Odds has changed from .+ to (.+).',error_code)[0]
                if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                    old_odds = old_odds.rstrip('0')
                if abs(float(new_odds)) < 100 and '.0' in old_odds:
                    new_odds = new_odds.rstrip('0')
                post_data = re.sub("\[Odds\]=(.*?)&I", "[Odds]="+str(new_odds)+"&I",post_data)
                betting_info['odds'] = new_odds
        elif "updating odds" in error_code or "temporarily closed" in error_code:
            time.sleep(5) # 系統 有防止 快速 打 接口 ,回復 We are updating odds, please try again later
        elif "score has been changed" in error_code :
            post_data = "ItemList[0][Ascore]={Ascore}&".format(Ascore= retry) + post_data
        elif "less than min stake or more than max stake" in error_code:
            if "nova88" in self.url :
                new_bet_stake = bet_stake + 10
            else:
                new_bet_stake = bet_stake + 4
            bet_stake = new_bet_stake
            post_data = post_data.replace('[stake]=%s'%bet_stake,'[stake]=%s'%new_bet_stake)
        elif "HDP/OU has been changed." in error_code:
            pass
        elif "IN-PLAY" in error_code:
            post_data = post_data.replace("ItemList[0][IsInPlay]=false","ItemList[0][IsInPlay]=true")
        if 'qasb' in self.url :
            if 'parlay' not in self.bet_type:
                r = self.client_session.post(self.member_url+ '/Betting/ProcessBet',data = post_data,headers=self.headers,verify=False)
            else:
                r = self.client_session.post(self.member_url+ '/BettingParlay/DoplaceBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
        else:
            if 'parlay' not in self.bet_type:
                r = self.client_session.post(self.url.replace("www","hm") + '/Betting/ProcessBet',data = post_data,headers=self.headers,verify=False)
            else:
                r = self.client_session.post(self.url.replace("www","hm") + '/BettingParlay/DoplaceBet',data = post_data.encode(),headers=self.headers,verify=False)# data_str.encode() 遇到中文編碼問題 姊法
        return r,post_data

    def get_bet_list_mini(self,transid=''):
        reget = 0
        while reget < 30:
            self.req_url = '/Statement/BetListMini'
            start = time.perf_counter()# 計算請求時間用
            if 'qasb' in self.url or '/(S' in self.url:
                r = self.client_session.post(self.member_url + '/Statement/BetListMini',data='GMT=8',headers=self.headers,verify=False)
            else:
                r = self.client_session.post(self.member_url + '/Statement/BetListMini',data='GMT=8',verify=False)
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            if transid == '': #代表這是在做 AllSite Desktop 的下注測試，不需要抓到 transid
                try:
                    repspone_json = r.json()
                    ticketcount = len(repspone_json['Data']['Tickets'])
                    self.error_msg  = ' ticket_count : %s'%(ticketcount)
                    return True
                except:
                    logger.error('response :%s'%r.text )
                    #self.stress_dict['response'].append(r.text) 
                    logger.error('get_bet_list_mini Api Fali')
                    return False
            else:
                if transid in r.text:
                    return r.text
                    #bets_list = r.text.replace(' ','').split('bets_title')
                    #del bets_list[0] #要先刪掉第 0 個，第 0 個不是注單資訊
                    #for responce in bets_list:
                    #    if transid in responce:
                    #        return responce
                else:
                    time.sleep(1)
                    reget += 1

    def get_bet_list_full(self,transid=''):
        reget = 0
        while reget < 60:
            self.req_url = '/Statement/BetListApp?GMT=8'
            start = time.perf_counter()# 計算請self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間求時間用
            if 'qasb' in self.url or '/(S' in self.url:
                r = self.client_session.post(self.member_url + '/Statement/BetListApp?GMT=8',headers=self.headers,verify=False)
            else:
                r = self.client_session.post(self.member_url + '/Statement/BetListApp?GMT=8',verify=False)
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            if transid == '': #代表這是在做 AllSite Desktop 的下注測試，不需要抓到 transid
                try:
                    ticketcount = r.text.count("SerialNo")
                    self.error_msg  = ' ticket_count : %s'%(ticketcount)
                    return True
                except:
                    logger.error('response :%s'%r.text )
                    #self.stress_dict['response'].append(r.text) 
                    logger.error('get_bet_list_full Api Fali')
                    return False
            else:
                if transid in r.text:
                    return r.text
                    #bets_list = r.text.replace(' ','').split('bets_title')
                    #del bets_list[0] #要先刪掉第 0 個，第 0 個不是注單資訊
                    #for responce in bets_list:
                    #    if transid in responce:
                    #        return responce
                elif "Authentication has expired" in r.text :
                    self.relogin = False
                    if self.relogin == True:
                        retry += 1
                        continue
                    logger.info('Your session has been terminated，等待 30 秒後重新登入')
                    if '/(S' in self.url:
                        self.url = self.url.split('/(S')[0]
                    desktop_api = Desktop_Api(device='Pc driver',user=self.user,url=self.url,client = '')
                    login_result = desktop_api.desktop_login(central_account='web.desktop' ,central_password='1q2w3e4r')
                    if login_result == False:
                        logger.info("登入失敗，重新登入")
                        retry += 1
                        continue
                    elif 'Login Too Often' in str(login_result):
                        logger.info("Login Too Often，等待 30 秒後再重新登入")
                        time.sleep(30)
                        retry += 1
                        continue
                    else:
                        pass
                    self.url = desktop_api.url
                    self.member_url = desktop_api.member_url
                    self.headers = desktop_api.headers
                    retry += 1
                    self.relogin = True
                else:
                    time.sleep(1)
                    reget += 1

    def get_result_info(self,filter_game,days=''): 

        #先抓取有的下注分類
        if filter_game == "Normal":
            try:
                data_str = "selectDate=%s"%days
                if 'qasb' in self.url :
                    r = self.client_session.post(self.member_url + '/Result/tabletindex?gmt=8',data = data_str.encode(),headers=self.headers,verify=False)
                else:
                    r = self.client_session.get(self.url.replace("www","hm")  + '/Result/tabletindex?gmt=8',data = data_str.encode(),headers=self.headers,verify=False)
                result_dropdown_responce = r.json()
                try:
                    sports_filterList = result_dropdown_responce['SportIdDic']
                except:
                    sports_filterList = None
                #抓取有的 Settle 分類 & 分類 ID
                if sports_filterList == None:
                    return "No Result"
                else:
                    pass
            except Exception as e:
                logger.error('GetResultDropDownList Fail : %s'%e)
                return "GetResultDropDownList Fail"
            try:
                result_dict = {}
                for selectedsport in list(sports_filterList):
                    try:
                        if 'qasb' in self.url :
                            r = self.client_session.post(self.member_url + '/Result/tabletindex?selectDate=%s&selectSid=%s&gmt=8'%(days,selectedsport),headers=self.headers,verify=False)
                        else:
                            r = self.client_session.get(self.url.replace("www","hm")  + '/Result/tabletindex?selectDate=%s&selectSid=%s&gmt=8'%(days,selectedsport),headers=self.headers,verify=False)
                        get_result_responce = r.status_code
                        if get_result_responce == 200:
                            result_dict.update({sports_filterList[selectedsport] : r.text})
                        else:
                            result_dict.update({sports_filterList[selectedsport] : "Responce Fail"})
                    except Exception as e:
                        result_dict.update({sports_filterList[selectedsport] : "Responce Fail"})
                        print(str(e))
                return result_dict
            except Exception as e:
                logger.error('GetDBetList_ch Fail : %s'%e)
                return "GetDBetList_ch Fail"
        else:
            try:
                today = days.split(" to ")[0]
                yesterday = days.split(" to ")[1]
                if 'qasb' in self.url :
                    r = self.client_session.post(self.member_url + '/Result/TabletOutright?sDate=%s&eDate=%s&gmt=8'%(yesterday,today),headers=self.headers,verify=False)
                else:
                    r = self.client_session.get(self.url.replace("www","hm")  + '/Result/TabletOutright?sDate=%s&eDate=%s&gmt=8'%(yesterday,today),headers=self.headers,verify=False)
                result_dropdown_responce = r.json()
                try:
                    sports_filterList = result_dropdown_responce['SportIdDic']
                except:
                    sports_filterList = None
                #抓取有的 Settle 分類 & 分類 ID
                if sports_filterList == None:
                    return "No Result"
                else:
                    pass
            except Exception as e:
                logger.error('GetOutrightResultDropDownList Fail : %s'%e)
                return "GetResultDropDownList Fail"
            try:
                result_dict = {}
                for selectedsport in list(sports_filterList):
                    try:
                        if 'qasb' in self.url :
                            r = self.client_session.post(self.member_url + '/Result/TabletOutright?sDate=%s&eDate=%s&gmt=8&selectSid=%s'%(yesterday,today,selectedsport),headers=self.headers,verify=False)
                        else:
                            r = self.client_session.get(self.url.replace("www","hm")  + '/Result/TabletOutright?sDate=%s&eDate=%s&gmt=8&selectSid=%s'%(yesterday,today,selectedsport),headers=self.headers,verify=False)
                        get_result_responce = r.status_code
                        if get_result_responce == 200:
                            result_dict.update({sports_filterList[selectedsport] : r.text})
                        else:
                            result_dict.update({sports_filterList[selectedsport] : "Responce Fail"})
                    except Exception as e:
                        result_dict.update({sports_filterList[selectedsport] : "Responce Fail"})
                        print(str(e))
                return result_dict
            except Exception as e:
                logger.error('GetDBetList_ch Fail : %s'%e)
                return "GetDBetList_ch Fail"

    def get_statement_info(self,statement_remark=''): 
        statement_remark_dict = {1 : "Betting Statement" ,3 : "Outstanding Bet", 2 : "Cancelled Bet"}
        try:
            self.req_url = '/Statement/AllStatement'
            start = time.perf_counter()# 計算請self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間求時間用
            if 'qasb' in self.url or '/(S' in self.url :
                r = self.client_session.get(self.member_url + '/Statement/AllStatement',headers=self.headers,verify=False)
            else:
                r = self.client_session.get(self.member_url  + '/Statement/AllStatement',verify=False)
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            if statement_remark == '':
                respone = r.text
                html = BeautifulSoup(respone,'html.parser')
                title = html.find_all(class_=re.compile("^balance"))[3]
                self.error_msg  = ' OpenBalance : %s'%(title.next)
                return True
            else:
                all_statement_text = r.text
                all_statement_list = r.text.split('date-smaller')
                if all_statement_text != None and statement_remark_dict[statement_remark] in all_statement_text:
                    all_statement_text = [statement_split for statement_split in all_statement_list if statement_remark_dict[statement_remark] in statement_split ]
                    date_list = re.findall('([0-9]+\/[0-9]+\/[0-9]+)[\d\D]*?%s'%statement_remark_dict[statement_remark],str(all_statement_text))
                else:
                    return "No Statement Result"
        except Exception as e:
            logger.error('Get AllStatement Fail : %s'%e)
            return "Get AllStatement Fail"
        try:
            statement_dict = {}
            for date in date_list:
                try:
                    if 'qasb' in self.url :
                        r = self.client_session.get(self.member_url + '/Statement/BettingStatement?date=%s&datatype=%s'%(str(time.strftime("%d-%m-%Y", time.strptime(str(date), "%m/%d/%Y"))),statement_remark),headers=self.headers,verify=False)
                    else:
                        r = self.client_session.get(self.url.replace("www","hm")  + '/Statement/BettingStatement?date=%s&datatype=%s'%(str(time.strftime("%d-%m-%Y", time.strptime(str(date), "%m/%d/%Y"))),statement_remark),headers=self.headers,verify=False)
                    get_result_responce = r.status_code
                    if get_result_responce == 200:
                        sport_filter_list = re.findall('sporttype=([A-Za-z0-9]+)',r.text) #抓出 Sports filter 的名稱，用於打 API
                    else:
                        pass
                except Exception as e:
                    logger.error('Get Sport Filter Fail : %s'%e)
                    return "Get Sport Filter Fail"
                sport_filter_result_dict = {}
                for sport_filter in sport_filter_list:
                    try:
                        if 'qasb' in self.url :
                            r = self.client_session.get(self.member_url + '/Statement/DBetList?date=%s&datatype=%s&sporttype=%s&GMT=8 '%(str(time.strftime("%d-%m-%Y", time.strptime(str(date), "%m/%d/%Y"))),statement_remark,sport_filter),headers=self.headers,verify=False)
                        else:
                            r = self.client_session.get(self.url.replace("www","hm")  + '/Statement/DBetList?date=%s&datatype=%s&sporttype=%s&GMT=8 '%(str(time.strftime("%d-%m-%Y", time.strptime(str(date), "%m/%d/%Y"))),statement_remark,sport_filter),headers=self.headers,verify=False)
                        get_result_responce = r.status_code
                        if get_result_responce == 200:
                            sport_filter_result_dict.update({sport_filter : r.text})
                        else:
                            pass
                    except Exception as e:
                        logger.error('Get Sport Filter Fail : %s'%e)
                        return "Get Sport Filter Fail"
                statement_dict[date] = sport_filter_result_dict
            return statement_dict
        except Exception as e:
            logger.error('GetDBetList_ch Fail : %s'%e)
            return "GetDBetList_ch Fail"

    def get_statement_history_info(self): 
        history_dict = {"Betting Statement" : []}
        #抓取當月 Statement
        import datetime
        selectyear = datetime.datetime.now().year
        selectmonth = datetime.datetime.now().month
        data = 'selectYear=%s&selectMonth=%s'%(selectyear,selectmonth)
        no_NsessionID_header = self.headers.copy()
        del no_NsessionID_header['Cookie']
        try:
            self.req_url = '/Statement/History_AllStatement'
            start = time.perf_counter()# 計算請self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間求時間用
            if 'qasb' in self.url or '/(S' in self.url :
                r = self.client_session.post(self.member_url + '/Statement/History_AllStatement',data = data,headers=self.headers,verify=False)
            else:
                r = self.client_session.post(self.member_url  + '/Statement/History_AllStatement',data = data,headers=no_NsessionID_header,verify=False)
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            respone = r.text
            html = BeautifulSoup(respone,'html.parser')
            title = html.find_all('div')
            for idx,div in enumerate(html.find_all('div')):
                if div.text == "Betting Statement":
                    history_dict["Betting Statement"].append(html.find_all('div')[idx+1].text)
            self.error_msg  = '%s'%history_dict
            return True
        except Exception as e:
            logger.error('Get AllStatement Fail : %s'%e)
            return "Get AllStatement Fail"

    def check_whats_new_picture(self): #確認圖片是否會在網頁圖片 List 裡
        print(self.url)
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        if "www" in self.url:
            self.url = self.url.replace("www","hm")
        else:
            pass
        r = self.client_session.post(self.url + '/Promotion/GetWhatIsNewData',headers=self.headers,verify=False)
        print(r.text)



# %%
