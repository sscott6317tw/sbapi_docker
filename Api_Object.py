#In[]

from collections import defaultdict
import execjs
import hashlib
from PIL import Image
from numpy import False_
import pytesseract,os,time
from  Logger import create_logger 
import pathlib,re
from Common import Common
import csv
import urllib3
from urllib.parse import urlparse
urllib3.disable_warnings()

logger = create_logger(r"\AutoTest", 'test')

#In[]
class Login(Common):#取得驗證碼邏輯 
    def __init__(self,device="",sec_times='',stop_times='',url=''):
        super().__init__(sec_times,stop_times)
        #logger = create_logger(r"\AutoTest", 'test')
        if device == 'Pc driver':
            self.dr = self.get_driver()
        self.img_pic = pathlib.Path(__file__).parent.absolute().__str__() + "login_code.jpg"
        self.download_waiting_time = 3
        self.url = url
        self.cookies = ""# 預設空, 會從驗證碼時,拿取 ASP.NET_SessionId
    
    
    def login_api(self, device,user,password =  '1q2w3e4r',url='',client='',central_account='',central_password='',site=''):
        '''devive 為Pc 才會去叫 webdriver ,要取驗證碼'''
        if device in ['mobile','app']:
            mobile_api = Mobile_Api(device='app',  password=password, url=url ,client = client,
            sec_times=self.sec_times, stop_times=self.stop_times,site=site )

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


            desktop_api.desktop_login(central_account=central_account ,
            central_password=central_password)
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
        os.remove(self.img_pic)
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
            now = int(time.time()*1000)
            if 'xideqs' in self.url:# qasb 測試環境 url輸入後 取得當前 xideqseTWIN 的url
                
                self.dr.get(self.url)
                current_url = self.dr.current_url# 取得轉換後的測試url ex: http://qasb.athena000.com:42104/(S(xideqseTWIN-Avzh25wrew0zndzoe3tmqiamhf2X-MXwjdkH3qs47fawD1gZZ))/
                self.url = current_url.split('?')[0]#?scmt=tab01&ssmt=tab01 移除
                logger.info('轉換url : %s'%self.url )
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                self.dr.get(login_code_url)
            else:#Production athena000
                login_code_url = '%s/login_code.aspx?%s'%(self.url,now)
                logger.info('login_code_url: %s'%login_code_url)
                self.dr.get(login_code_url)
            
            self.dr.get_screenshot_as_file(self.img_pic)
            for i in range(self.download_waiting_time):
                if os.path.isfile(self.img_pic):
                    logger.info('圖片有找到')
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
                if 'qasb' in self.url:
                    break
                self.cookies = self.dr.get_cookies()
                logger.info('cookies: %s'%self.cookies )
                self.dr.close()
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
        r = self.session.post(self.url  + '/Default/RefreshPKey',headers=self.headers)
        try:
            PWKEY = r.json()['Data']['PWKEY']
            logger.info('PKey: %s'%PWKEY) 
            return PWKEY 
        except:
            logger.error('PKey: 取得失敗') 
            return False
    

#login_type 預設空字串, 是使用 athena 登入 
class Mobile_Api(Login):# Mobile 街口  ,繼承 Login
    def __init__(self,client,device="",url='',user='',password='',sec_times='',stop_times='',site=''):
        super().__init__(device,sec_times,stop_times) 
        self.login_session = {}# key 為 user ,value 放 NET_SessionId
        self.url = url
        self.default_url = url
        self.login_type = ''# api site 為 空字串
        if 'athena' in self.url or 'nova88' in self.url or 'spondemo' in self.url:
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
        


    '''
    共用 url 請求 的方式, 包含回傳 請求時間, 請求相關資訊放到 stress_dict, 避免每個新增街口, 都要寫一次
    '''
    def stress_request_post(self, request_data ,func_url  ): 
        self.count = self.count + 1
        self.stress_dict['request num'].append(self.count)
        self.stress_dict['request data'].append(request_data)
        start = time.perf_counter()
        #print(self.headers)
        r = self.client_session.post(self.url  + func_url , data = request_data,headers=self.headers)
        #self.url = r.url
        self.stress_dict['request url'].append(self.url  + func_url)

        request_time =  '{0:.4f} s'.format(time.perf_counter() - start) # 該次 請求的url 時間
        logger.info("Request completed in %s s"%request_time )
        self.stress_dict['request time'].append(request_time)

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
        r = self.client_session.get(self.url  + func_url ,headers=self.headers)
        #self.url = r.url
        self.stress_dict['request url'].append(self.url  + func_url)

        request_time =  '{0:.4f} s'.format(time.perf_counter() - start) # 該次 請求的url 時間
        logger.info("Request completed in %s s"%request_time )
        self.stress_dict['request time'].append(request_time)

        return r

        
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
    def mobile_login(self,user,central_account='',central_password=''):# Mobile Login街口邏輯
        
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
            
            r = self.client_session.post(self.url  + '/Login/index',data=login_data,headers=self.headers)
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
                            r = self.client_session.get(Data_url, headers=self.headers)
                        else:
                            self.nova_set_odds_type_url = self.url
                            r = self.client_session.get(self.url + Data_url, headers=self.headers)
                    else:
                        r = self.client_session.get(self.url  + Data_url, headers=self.headers)
                
                cookie_session = self.client_session.cookies.get_dict()
                NET_SessionId = cookie_session['ASP.NET_SessionId']
                logger.info('NET_SessionId: %s'%NET_SessionId )
                self.login_session[user] = NET_SessionId
                #logger.info('self.login_session: %s'%self.login_session)
                return True
            except Exception as e:
                logger.info('Login Api Fail: %s'%e)
                return False
        
        else: #api site登入

            '''
            這邊 api site 登入 , 如果登入 成功會回傳 True , 其餘失敗的 都會回傳 字串, 不會回傳 False, 因為 ALL Site 要接失敗訊息
            '''
            start = time.perf_counter()# 計算請求時間用
            try:
                r = self.client_session.get(self.url)
                session_url = r.url # api site 需先拿到 session url 在做登入
                logger.info('登入前 session url: %s'%session_url)
            except Exception as e:
                logger.error(' url 請求 有誤 : %s'%e)
                self.error_msg = 'login get error : %s'%e
                return self.error_msg
            
            
            self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
            
            
            #LicLogin , DepositLogin
            login_query = 'LicLogin/index?lang=en&txtUserName={user}&Password=1q2w3e4r&token=&skin=&CentralAccount={central_account}&CentralPassword={central_password}&menutype=&sportid=&leaguekey=&matchid=&isAPP=\
            &currencyName=&bdlogin=1&tsid=&SkinColor=&types=1%2C0%2Cl'.format(user=user,
            central_account=central_account,central_password=central_password)
            api_login_url = session_url.split('apilogin')[0] + login_query

            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9'
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            
            try:# 這邊 try login 如果遇到 503 或者別問題
                r =  self.client_session.get(api_login_url, headers=self.headers,verify=False)
            except Exception as e:
                self.error_msg = 'Login 接口: %s'%e
                return self.error_msg



            self.url = r.url.split('#Sports')[0]# 登入後 就是 拿這個 變數 去做後面 各個街口的使用
            logger.info('登入後 的 session url: %s'%self.url)# 登入後的轉導url
            

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
            return True

    def get_contirbutetor(self ):# /main/GetContributor
        
        data = 'isParlay=false&both=true&defaulteuro=false'
        r = self.stress_request_post(request_data= data, func_url = '/main/GetContributor' )
        try:
            repspone_json = r.json()
            ErrorCode = repspone_json['ErrorCode']
            self.stress_dict['response'].append('ErrorCode: %s'%ErrorCode)

            logger.info('ErrorCode: %s '%(ErrorCode ) )
            return True
        except:
            logger.error('response :%s'%r.text )
            self.stress_dict['response'].append(r.text) 
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
        r = self.client_session.post(self.url  + self.req_url  ,data=data,headers=self.headers)
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
        


    def balance(self):# /balance/GetAccountInfo
        
        data = 'localtime=8'
        #self.headers['Referer'] = self.url
    
        r = self.stress_request_post(request_data= data, func_url = '/balance/GetAccountInfo' )

        #r = self.client_session.post(self.url  + '/balance/GetAccountInfo', data=data,headers=self.headers)
       
        try:
            repspone_json = r.json()
            Bal = repspone_json['Data']['Bal']
            BCredit = repspone_json['Data']['BCredit']
            self.stress_dict['response'].append('Bal: %s , BCredit: %s '%(Bal ,BCredit ) )
            
            logger.info('Bal: %s , BCredit: %s '%(Bal ,BCredit ))
            return True
        except:
            logger.error('url :%s'%r.url )
            self.stress_dict['response'].append(r.text)
            logger.error('mobile balance Api Fail')
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
    def ShowAllOdds(self,type='',market=['e'],filter='',sport='Soccer',bet_type='OU'):# 取得 MatchId 傳給 GetMarket , 還有取得 TeamN 回傳給 DoplaceBet  的 home/away
        self.MatchId = {} #先清空
        
        # e為 早盤, t為 today
        #market = 't'# 預設 today
        self.sport = sport
        self.bet_type = bet_type
        if "nova88" in self.url:
            bet_type = "OU"
        else:
            bet_type = bet_type
        self.gameid = self.game_mapping(self.sport)# 後面 get market 和 betting 就不用在多傳 gameid 參數了, 統一在這宣告
        for market in market:
            data = 'GameId=%s&DateType=%s&BetTypeClass=%s&Gametype=0'%(self.gameid  ,market,bet_type)# 先寫死cricket, 之後優化
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            
            try:# athen 和部分api的 ,走 一個邏輯
                if self.login_type  == 'athena' or self.api_site =='web':# athena  
                    r = self.stress_request_post(request_data= data, func_url = '/Odds/ShowAllOdds' )

                    #r = self.client_session.post(self.url  + '/Odds/ShowAllOdds',data=data,headers=self.headers)
                    repspone_json = r.json()
                else:
                    if 'Authorization' not in list(self.headers.keys()):
                        logger.info('使用api site ,需先打 /Login/ExtendToken 拿出 Bearer')
                        r = self.client_session.post(self.url+ '/Login/ExtendToken',headers=self.headers)
                        Bearer_data = r.json()['Data']# 需傳到 showallodds
                        logger.info('Bearer_data: %s'%Bearer_data)
                        
                        self.headers['Authorization'] = 'Bearer  %s'%Bearer_data
                    
                    self.req_url = 'http://oplg1.fast4indo.com/' + '/Odds/ShowAllOddsApi?'+data
                    
                    start = time.perf_counter()# 計算請求時間用
                    r = self.client_session.get(self.req_url  ,headers=self.headers)
                    self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間


                    repspone_json = r.json()
                #logger.info('repspone_json: %s'%repspone_json)   
            except:
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
        
                    TeamId1 = dict_['TeamId1']
                    TeamId2 = dict_['TeamId2']
                    LeagueId = dict_['LeagueId']
                    League_name = LeagueN[str(LeagueId)]
                
                    if type == '':# 不能有test 的賽事 
                        if len(NewMatch) == 1 : #僅有 Test 的比賽，就不要移除 Test 的比賽，不寫再主判斷是為了到時候 Parlay 要修改
                            pass
                        else:
                            if any(test_parlay in League_name for test_parlay in  ['TESTING','test','Test','测试'] ):# 如果 不是要 針對test 然後 testing 又再 league ,不能串
                                continue
                    # type 帶 test 就 可以 忽略 testing 比賽 
                    team_name['Team1'] = TeamN[ str(TeamId1) ]
                    team_name['Team2'] = TeamN[str(TeamId2) ]
                    team_name['League'] = League_name
                    team_name['Market'] = market
                    
                    #logger.info('team_name: %s'%team_name)
                    MatchId = dict_['MatchId']# 取出Matchid ,並當作 Key
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

        len_matchid = len(self.MatchId)
        #logger.info('self.MatchId: %s'%self.MatchId)
        logger.info('len MatchId: %s'%len_matchid )
        self.stress_dict['response'].append('len MatchId: %s'%len_matchid )

        if len_matchid < 3:
            logger.info('長度小於3 無法串票')
            return 'False'
        else:
            return True


    '''
    parlay_len 預設 給3 是 找三個match 來串即可, 如果不是 3 就是 給其他長度
    BetType 預設為 parlay . parlaymore 為更多 bet

    取得   MarketId(oddsid), Price(odds) , BetTypeId
    '''
    def GetMarket(self,bettype_id=''):
        if 'parlay' in  self.bet_type:
            parlay_len = '3'
        else:
            parlay_len = '1'
        self.Match_dict = {}# key 當作 index, value 存放 該match id 裡所有 的bettype(self.MarketId)

        for index,match_id in enumerate(self.MatchId.keys()):
            #print(match_id)
            self.MarketId = {}
            market = self.MatchId[match_id]['Market']
            logger.info('match_id : %s, 資訊: %s'%(match_id, self.MatchId[match_id]))
            if self.gameid == 50 and "more" in self.bet_type: #當 Sports 為 Cricket，Gametype 為 1
                data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":1}
            else:
                data = {"GameId": self.gameid ,"DateType":market,"BetTypeClass":self.bet_type,"Matchid":match_id,"Gametype":0}
            try:

                self.req_url = '/Odds/GetMarket'
                start = time.perf_counter()# 計算請求時間用
                r = self.client_session.post(self.url  + self.req_url ,data=data,headers=self.headers)
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
                            NewOdds.append(SpMatch_market_odds)
                else:
                    NewOdds = repspone_json['Data']['NewOdds']
                if bettype_id != '': #判段於此 MatchID 是否有我要的 Bettype ID
                    if "'BetTypeId': %s"%bettype_id in str(NewOdds):
                        pass
                    else:
                        continue
                MatchId_value = self.MatchId[match_id]
                
                for dict_ in NewOdds:#list包字典# ,裡面 一個dict 會有 很多 marketid (Oddsid)要取得
                    #logger.info('dict: %s'%dict_)
                    new_dict = {}
                    if 'hdp2' in str(dict_) : #給 Match Handicap & Total 帶入的值
                        new_dict['hdp2'] = dict_['hdp2']
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
                if bettype_id == '':
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
        logger.info('self.Match_dict 0 : %s'%len(self.Match_dict[0] ))
        if int(parlay_len) ==3:
            logger.info('self.Match_dict 1 : %s'%len(self.Match_dict[1]))
            logger.info('self.Match_dict 2: %s'%len(self.Match_dict[2]))

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

                #self.fail_bettype.append(BetTypeId_list[0])
                return False
            
            elif response_code == '-91':# update odds
                logger.info('Message: %s'%Message)
                logger.info('休息 兩秒鐘 再做')
                time.sleep(2)
                return '重新'

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
                        odds_change_dict[Matchid] = odds_change    
                logger.info('odds_change_dict: %s'%odds_change_dict)

                for matchid in odds_change_dict.keys():# 把 變更後的odds 取出
                    og_odds = str(self.Odds_dict[matchid])# 把原本的 odds取出
                    odds_change = odds_change_dict[matchid]# 如果遇到 多個 相同的odds, 目前寫法可能有問題
                    data_str = data_str.replace( og_odds, odds_change)
                    self.Odds_dict[matchid] = odds_change # 從新變更dict
                if self.retry_count == 1: 
                    return 'retry 完'
                self.retry_count = self.retry_count + 1
                time.sleep(5)# 系統 有防止 快速 打 接口 ,回復 We are updating odds, please try again later
                
            elif response_code in ['0','1']:# 投注成功
                order_value = {}
                order_value['Message'] = Message

                TransId_Combo = Data['TransId_Combo']
                TransId_System = Data['TransId_System']

                TotalPerBet =  Data['TotalPerBet']
                order_value['TotalPerBet'] = TotalPerBet
                FinalBalance = Data['FinalBalance']
                order_value['FinalBalance'] = FinalBalance
                order_value['BetTypeId_list'] = self.BetTypeId_list
                
                Odds_list = list(self.Odds_dict.values() )
                Match_list = list(self.Odds_dict.keys() )
                if TransId_Combo in ['0','']:
                    order_value['注單ID'] = TransId_System

                else:
                    order_value['注單ID'] = TransId_Combo

                order_value['Match_list'] = Match_list
                order_value['Odds_list'] = Odds_list
                self.Order_dict[times] = order_value
                
                logger.info('order_value: %s'%order_value)
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
            if any(error_code in Itemdict['Message'] for error_code in  ['Odds has changed','min','updating odds',"has been changed","is closed","System Error","temporarily closed"] ):
                
                #logger.info('self.post_data: %s'%self.post_data)
                return Itemdict['Message']
            else:
                pass
            
            if self.site == '':
                try:
                    #order_value['DisplayOdds'] = Itemdict['DisplayOdds']
                    #BetRecommends = Itemdict['BetRecommends'][0]# 為一個 list ,裡面含 各個 bet type資訊，這個不是此注單的資訊，而且下方建議投注的資訊
                    match_key = Itemdict['Key'].split('_')[0]
                    self.order_value['oddsid'] = match_key
                    if self.betting_info['Pair/DecOdds'] == 0:
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
                            if str(BetTypeId) in str(row):
                                self.order_value['BettypeName'] = row[1]
                                break
                            else:
                                pass
                    self.order_value['BetChoice'] = self.betting_info['bet_team']
                    self.order_value['Odds'] = self.betting_info['odds']
                    
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
    def DoplaceBet(self,already_list=[],bet_team_index='0',parlay_type='1',times='',bettype_id='',not_bettype_id=''): #not_bettype_id 是為了不要重複下到同一個 Bettype
        import random
        '''
        SportName 和 gameid 之後 做動態傳入,目前寫死 
        '''
        self.BetTypeId_list = []
        self.Odds_dict = {}# key 為 match id ,value 為 odds
        Parlay_dict = {'1' : '1', '2': '4' }# value 是拿來 給 parlay data 的  BetCount 和 TotalStake

        len_Match_dic= len(self.Match_dict)
        logger.info('len_Match_dict : %s'%len_Match_dic)
       
        try:
            data_str = ""# 需loop 慢慢加起來
            for index_key in self.Match_dict.keys():#index_key 為 數值 ,一個 match 比賽 , 就是一個key
                #logger.info('index_key : %s'%index_key)
                Match = self.Match_dict[index_key]# key 為 Oddsid ,value為 字典,涵蓋 各種 資訊
                #logger.info('len : %s'%len(Match))

                Match_key_list = list(Match.keys())# list裡面放 bettype
                find_bet_type_id = False
                if self.bet_type != 'more': #more 要排除小於 3 的 Bettype ID
                    if bettype_id != '':
                        from random import shuffle #用來把 list 打亂可以不用一值下同一場比賽
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
                    elif not_bettype_id != '':
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != int(not_bettype_id):
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID"
                        pass
                else:
                    if not_bettype_id != '':
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] != int(not_bettype_id) and Match[Match_key]['BetTypeId'] >= 4:
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID"
                        pass
                    else:
                        for Match_key in Match_key_list:
                            if Match[Match_key]['BetTypeId'] >= 4:
                                Match_key_list = []
                                Match_key_list.append(Match_key)
                                find_bet_type_id = True
                                break
                            else:
                                pass
                        if find_bet_type_id == False:
                            return "No Other BetType ID"
                        pass
                retry_count = 0
                while True:
                    self.betting_info = {} #儲存我下注的值 

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
                    self.betting_info['odds'] = Match[Ran_Match_id]['odds_%s'%bet_team_index]
                except:
                    odds = Match[Ran_Match_id]['odds_0']
                
                try:# 有些 bettype 下 會有超過 2的長度, 如果 傳2 以上會爆錯, 就統一用 0來代替
                    bet_team = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                    self.betting_info['bet_team'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
                except:
                    bet_team = Match[Ran_Match_id]['bet_team_0']
                
                oddsid = Ran_Match_id
                BetTypeId = Match[Ran_Match_id]['BetTypeId']
                
                #Line = Match[Ran_Match_id]['Line']
                #if  Line == 0:
                    #Line = ''
            
                #if index > 2 and set_bet == 1:#串三個即可 . set_bet = 1代表
                    #break

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
                    if  self.gameid != 50:# cricket 的不用轉 
                        if BetTypeId not in [5, 15]:#  5: Ft 1x2 , 15: 1H 1x2 他們是 屬於Dec Odds
                            odds = self.Odds_Tran(odds,odds_type=self.odds_type)
                            logger.info('%s bettype: %s , 需轉乘 Dec odds: %s'%( self.sport,BetTypeId, odds) )
                logger.info('BetTypeId : %s'%BetTypeId)
                try:
                    data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                    ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                    ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                    ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                    ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                    ".format(index_key= index_key, BetTypeId=BetTypeId, oddsid=oddsid ,Matchid = Matchid ,
                    Team1 =Team1, Team2= Team2 ,odds=odds ,gameid = self.gameid,betteam = bet_team,  bet_type = "OU")
                except Exception as e:
                    logger.error('data_format: %s'%e)

                data_str = data_str + data_format + '&'
                '''
                parlay 串多少match 邏輯
                當 index 到了 總長度 的最後, 須把 combo_str 家回data裡
                '''
                if index_key == len_Match_dic -1 :
                    if 'parlay'  in self.bet_type :# parlay
                        if parlay_type == '2':# system parlay ,的total stake 要根據 長度 來做動態 計算
                            TotalStake = len_Match_dic - 3 +  3# 如果 總長度 為4 . 4- 3  +  4
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
                        
                        data_str = data_str + combo_str
                    else:# single

                        combo_str = "&ItemList[0][Minbet]=1"

                        data_str = data_str + combo_str
                        
                        self.req_url = '/BetV2/GetTickets'
                        
                        start = time.perf_counter()# 計算請求時間用
                        r = self.client_session.post(self.url  + self.req_url  , data = data_str.encode(),
                                headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
                        self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                        
                        try:
                            logger.info('GetTickets OK')
                            self.ticket_Data = r.json()['Data'][0]# Data 為一個list. 取出來為一個 dict
                            #logger.info('ticket: %s'%Data)

                            self.min_stake = self.ticket_Data['Minbet']
                            self.guid = self.ticket_Data['Guid']
                            self.Line = self.ticket_Data['Line']
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
                r = self.client_session.post(self.url  + '/BetParlay/DoplaceBet',data = self.post_data.encode(),
                headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
            else:# single bet
                # 這裡把 get_ticket拿到的 資訊 , 在加進  post_data
                self.post_data = data_format+ "&ItemList[0][stake]={bet_stake}&ItemList[0][Guid]={Guid}&\
                ItemList[0][Line]={Line}&ItemList[0][hdp1]={hdp1}&ItemList[0][hdp2]={hdp2}&ItemList[0][Hscore]={Hscore}&ItemList[0][Ascore]={Ascore}".format(bet_stake=self.min_stake
                ,Guid =self.guid,  Line =self.Line , hdp1 = self.Hdp1, hdp2 = self.Hdp2, Hscore = self.Hscore ,Ascore = self.Asocre)
                
                if self.site != '':
                    self.req_url = '/BetV2/ProcessBet'
                    start = time.perf_counter()# 計算請求時間用
                    r = self.client_session.post(self.url  + self.req_url ,data = self.post_data.encode(),
                    headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
                    
                    self.request_time =  '{0:.4f}'.format(time.perf_counter() - start) # 該次 請求的url 時間
                
                
                else:
                    retry = 0
                    while retry < 10 :
                        r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = self.post_data.encode(),headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
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
                        return str(self.order_value)

                    retry = 0
                    while retry < 6: 
                        betting_response = self.Betting_response(response=r, times=times)
                        if betting_response != True and betting_response != False:
                            if "is closed" in betting_response or "System Error" in betting_response or "is temporarily closed" in betting_response:
                                bettype_is_closed = True
                                retry = 6
                                break
                            elif retry >= 1: #如果 >1 代表以重做過一次還是錯，那就要用新的 Data 取代舊的
                                self.post_data = new_post_data
                                r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                            else:
                                r,new_post_data = self.retry_betting(betting_response,self.post_data,self.min_stake,retry) #現在只為了 Single betting 新增
                            retry += 1
                        else:
                            break
                    if retry == 6:
                        self.order_value['LeagueName'] = self.MarketId[int(Ran_Match_id)]['League']
                        self.order_value['Message'] = str(betting_response)
                        self.order_value['MatchID'] = Matchid
                        self.order_value['oddsid'] = Ran_Match_id
                        self.order_value['BetTypeId'] = Match[Ran_Match_id]['BetTypeId']
                        self.order_value['BetChoice'] = Match[Ran_Match_id]['bet_team_%s'%bet_team_index]
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
                                data_format = "ItemList%5B0%5D%5Btype%5D={bet_type}&ItemList%5B0%5D%5Bbettype%5D={BetTypeId}&ItemList%5B0%5D%5Boddsid%5D={oddsid}&ItemList%5B0%5D%5Bodds%5D={odds}&ItemList%\
                                    5B0%5D%5BLine%5D={Line}&ItemList%5B0%5D%5BHscore%5D=0&ItemList%5B0%5D%5BAscore%5D=32&ItemList%5B0%5D%5BMatchid%5D={Matchid}&ItemList%5B0%5D%5Bbetteam%5D={betteam}%2B&\
                                    ItemList%5B0%5D%5Bstake%5D={bet_stake}&ItemList%5B0%5D%5BQuickBet%5D=1%3A100%3A10%3A1&ItemList%5B0%5D%5BChoiceValue%5D=&ItemList%5B0%5D%5Bhome%5D={Team1}&\
                                    ItemList%5B0%5D%5Baway%5D={Team2}&ItemList%5B0%5D%5Bgameid%5D={gameid}&ItemList%5B0%5D%5BisMMR%5D=0&ItemList%5B0%5D%5BMRPercentage%5D=&ItemList%5B0%5D%5BGameName%5D=&\
                                    ItemList%5B0%5D%5BSportName%5D=Basketball&ItemList%5B0%5D%5BIsInPlay%5D=false&ItemList%5B0%5D%5BSrcOddsInfo%5D=&ItemList%5B0%5D%5Bpty%5D=1&\
                                    ItemList%5B0%5D%5BHdp1%5D={Line1}&ItemList%5B0%5D%5BHdp2%5D={Line2}&ItemList%5B0%5D%5BBonusID%5D=0&ItemList%5B0%5D%5BBonusType%5D=0&ItemList%5B0%5D%5Bsinfo%5D=F1B30X0000&\
                                    ItemList%5B0%5D%5BhasCashOut%5D=false".format(index_key= index_key, BetTypeId=self.betting_info['BetTypeId'], oddsid=self.betting_info['oddsid'] ,Matchid = self.betting_info['MatchId'] ,
                                    Team1 =self.betting_info['Team1'], Team2= self.betting_info['Team2'] ,odds=self.betting_info['odds'] ,gameid = self.gameid,betteam = new_betteam,
                                    Line = self.betting_info['Line'],Line1 = self.betting_info['Line1'],Line2 = self.betting_info['Line2'], bet_type = "OU", bet_stake = self.bet_stake )
                            else:
                                if ("H1" in self.betting_info['bet_team'] and "-" not in self.betting_info['bet_team']) or "O1" in self.betting_info['bet_team']:
                                    self.betting_info['bet_team'] = self.betting_info['bet_team'].replace("1","")
                                data_format = "ItemList[{index_key}][type]={bet_type}&ItemList[{index_key}][bettype]={BetTypeId}&ItemList[{index_key}][oddsid]={oddsid}&ItemList[{index_key}][odds]={odds}&\
                                ItemList[{index_key}][Line]={Line}&ItemList[{index_key}][Hscore]=0&ItemList[{index_key}][Ascore]=0&ItemList[{index_key}][Matchid]={Matchid}&ItemList[{index_key}][betteam]={betteam}&\
                                ItemList[{index_key}][stake]={bet_stake}&ItemList[{index_key}][QuickBet]=1:100:10:1&ItemList[{index_key}][ChoiceValue]=&ItemList[{index_key}][home]={Team1}&\
                                ItemList[{index_key}][away]={Team2}&ItemList[{index_key}][gameid]={gameid}&ItemList[{index_key}][isMMR]=0&ItemList[{index_key}][MRPercentage]=&ItemList[{index_key}][GameName]=&\
                                ItemList[{index_key}][SportName]=C&ItemList[{index_key}][IsInPlay]=false&ItemList[{index_key}][SrcOddsInfo]=&ItemList[{index_key}][pty]=1&ItemList[{index_key}][hdp1]={Line1}&\
                                ItemList[{index_key}][hdp2]={Line2}&ItemList[{index_key}][BonusID]=0&ItemList[{index_key}][BonusType]=0&ItemList[{index_key}][sinfo]=53FCX0000&ItemList[{index_key}][hasCashOut]=false\
                                ".format(index_key= index_key, BetTypeId=self.betting_info['BetTypeId'], oddsid=self.betting_info['oddsid'] ,Matchid = self.betting_info['MatchId'] ,
                                Team1 =self.betting_info['Team1'], Team2= self.betting_info['Team2'] ,odds=self.betting_info['odds'] ,gameid = self.gameid,betteam = self.betting_info['bet_team'],
                                Line = self.betting_info['Line'],Line1 = self.betting_info['Line1'],Line2 = self.betting_info['Line2'], bet_type = "OU", bet_stake = self.bet_stake )
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
                                    headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
                            try:
                                if any(_bet_team in self.betting_info['bet_team'] for _bet_team in  ['aos','AOS']) or any(_BetTypeId in str(self.betting_info['BetTypeId']) for _BetTypeId in ['468','469']): #如果是 aos 就要抓取 SrcOddsInfo，並放到 postdata 裡面
                                    repspone_json = r.json()
                                    SrcOddsInfo = repspone_json['Data'][0]['SrcOddsInfo']
                                    data_str = "ItemList[0][SrcOddsInfo]={SrcOddsInfo}&".format(SrcOddsInfo= SrcOddsInfo) + data_str
                                logger.info('GetTickets OK')
                            except Exception as e:
                                logger.error('Single Bet Get Ticket 有誤 : '+str(e))
                                return 'GetTickets False'

                        try:
                            import re
                            data_str = re.sub(r"\s+", "", data_str)# 移除空白,對 打接口沒影響 ,只是 data好看 

                            #self.headers['Cookie'] = 'ASP.NET_SessionId='+ self.login_session[user]
                            post_data =  data_str
                            retry = 0
                            while retry < 10 :
                                r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = post_data.encode(),headers=self.headers)# data_str.encode() 遇到中文編碼問題 姊法
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
                            logger.info('mobile DoplaceBet Api Fail: %s'%e)
                return already_list

        except Exception as e:
            logger.error('DoplaceBet: %s'%e)


    def retry_betting(self,error_code,post_data,bet_stake,retry):
        if "Odds has changed" in error_code:
            old_odds = re.findall('Odds has changed from (.+) to',error_code)[0] #去除尾數為 0 
            new_odds = re.findall('Odds has changed from .+ to (.+).',error_code)[0]
            if abs(float(old_odds)) < 100 and '.0' in old_odds: # 要把 .0 刪掉
                old_odds = old_odds.rstrip('0')
            if abs(float(new_odds)) < 100 and '.0' in old_odds:
                new_odds = new_odds.rstrip('0')
            post_data = re.sub("\[odds\]=(.*?)&I", "[odds]="+str(new_odds)+"&I",post_data)
            self.betting_info['odds'] = new_odds
        elif "updating odds" in error_code or "temporarily closed" in error_code:
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
        r = self.client_session.post(self.url  + '/BetV2/ProcessBet',data = post_data,headers=self.headers)
        return r,post_data


    def get_statement_info(self,transid): #用來抓取最後一個 TransID
        #先抓取 Get statement 所需資訊
        '''
        try:
            data_str = "RunningType=E" #固定帶入 E
            r = self.client_session.get(self.url  + '/Running/GetRunningOVR',data = data_str.encode(),headers=self.headers)
            responce_json = r.json() 
        except Exception as e:
            logger.error('mobile Get_Datatype Api Fail : %s'%str(e))
            return False
        data_str = 'datatype=%s'%responce_json['datatype']
        '''
        data_str = 'datatype=0'
        reget = 0
        while reget < 60:
            r = self.client_session.get(self.url  + '/Running/GetEarly_ch?%s'%data_str,headers=self.headers)
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

class Desktop_Api(Login):    
    def __init__(self,client="",device="",user='',url= ''):
        super().__init__(device)
        self.login = None
        self.user = user
        self.url = url
        self.login_type = ''# api site
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
        if 'athena' in self.url or 'spondemo' in self.url:
            self.login_type = 'athena' # 是 api site 登入 還是  athena site登入 , login方式不一樣
        if client == '':
            self.client_session = self.session
        else:
            self.client_session = client
    
    def desktop_login(self,central_account='',central_password=''):# PC端 login街口 邏輯
        '''加密邏輯 呼叫'''
        if self.login_type == 'athena':# athena 的登入 方式 , 會須使用 js 加密
            common_js = execjs.compile(self.js_from_file('./login_js/dsektop.js'))# 讀取 login js檔
            cfs_psswd = common_js.call("CFS", '1q2w3e4r')# password先做 前端 CFS 加密
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

        else:# api site
            if 'onelogin' not in self.url:# 多幫忙檢查 ,需要帶 onelogin
                self.url = self.url + '/onelogin.aspx'
            r = self.client_session.get(self.url  ,headers= self.headers)# 需先拿 session url
            
            self.url  = r.url.split('/onelogin.aspx')[0]# 回復的url 需再拿掉 onelogin.aspx . 再去打 despoist login
            logger.info('onelogin 需 先拿session url: %s'%self.url )
            # 然後 在用 這個 session url 去拿 驗證碼 ,但要移除  /onelogin.aspx

            login_data = "lang=en&WebSkinType=&matchid=&leaguekey=&market=T&menutype=0&act=sports&game=&gamename=&gameid=&Otype=&HomeUrl=&deposit=&extendSessionUrl=&Link=&Sport=&Date=&SkinColor=&centralAccount={central_account}&centralPassword={central_password}&txtUserName={user}&txtPasswd=1q2w3e4r&token=&TSID=&txtValidCode=&hidubmit=YES".format(central_account=central_account,central_password=central_password,user=self.user )

        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.headers['X-Requested-With'] =  'XMLHttpRequest'
        r = self.client_session.post(self.url  + '/DepositProcessLogin',data=login_data,headers=self.headers)
        
        try:
            #if self.login_type == 'athena':# athena 回復格式 有json 
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            if repspone_json['ShowErrorMsg'] == 'The validation code has expired.' or repspone_json['ErrorCode'] !='':
                logger.info('登入 Fail')
                return False

            reponse_url = r.json()['url']# 取得登入後 轉導url
            logger.info('reponse_url: %s'%reponse_url)
        
            if 'qasb' in self.url or 'xide' in self.url:# 有sesion 的判斷
                Val_url = '%s'%( reponse_url)
                logger.info('Val_url: %s'%Val_url)#/ValidateTicket?Guid=fa426c9c-739d-4b37-9589-db13ab0b1cdd
                r = self.client_session.get(Val_url,headers=self.headers )
                logger.info('r.url: %s'%r.url)
                u = urlparse(r.url)
                self.member_url = 'http://%s%s'%(u.netloc,u.path)
                self.member_url = self.member_url.split('/ValidateTicket')[0]
                logger.info('self.member_url: %s'%self.member_url)

                r = self.client_session.get(self.member_url +  '/NewIndex?lang=en&rt=0&webskintype=2',headers=self.headers )
                
            else:
                u = urlparse(reponse_url)# 擷取 動態 member_url 
                self.member_url = 'http://%s'%u.netloc
                logger.info('member_url: %s'% self.member_url)

                r = self.client_session.get(reponse_url,headers=self.headers )
            self.login = 'login ready'
            
            return True

        except:
            logger.info('登入 Fail')
            return False

    def balance(self):# /NewIndex/GetWalletBalance
        balance_info_data = 'TZone=8'
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url  + '/NewIndex/GetWalletBalance'
        logger.info('post_url: %s'%post_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.post( post_url,data=balance_info_data,headers=self.headers)
        try:
            repspone_json = r.json()
            logger.info('response: %s'%repspone_json)
            return True
        except:
            logger.info('desktop balance Api Fail')
            return False
    
    def hm_sport(self):# /NewIndex/GetWalletBalance
       
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        self.hm_url = self.member_url.replace('member','hm')
        
        logger.info('hm_url: %s'%self.hm_url)

        logger.info('header: %s'%self.headers)
        r = self.client_session.get( self.hm_url + '/NewIndex/GetWalletBalance',headers=self.headers)
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

        #用於抓取登入後的 hm session id
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        post_url = self.member_url + '/EntryIndex/OpenSports'
        logger.info('post_url: %s'%post_url)
        open_sports = self.session.get(post_url,headers = self.headers)
        cookie_session = self.session.cookies.get_dict()
        
        if self.login_type == 'athena':
            NET_SessionId = cookie_session['ASP.NET_SessionId']
        
            logger.info('NET_SessionId: %s'%NET_SessionId)
            self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
            self.headers['Cookie'] = "ASP.NET_SessionId=" + NET_SessionId
            self.hm_url = self.member_url.replace('member','hm')

            post_url = self.hm_url  + '/Sports/'
            logger.info('post_url: %s'%post_url)

            logger.info('header: %s'%self.headers)
            r = self.client_session.get( post_url,headers=self.headers)
            try:
                sucess_data = re.findall("<html.+>",r.text)[0]
                return r.text
            except Exception as e:
                logger.info('desktop balance Api Fail : %s'%str(e))
                return False
        else: #由於 api site opensports 打出後，會自動回傳 Sport API，不須像 Athena 再去打，所以直接判斷回傳是否正確
            try:
                sucess_data = re.findall("<html.+>",open_sports.text)[0]
                return sucess_data
            except Exception as e:
                return open_sports.text

    def check_whats_new_picture(self): #確認圖片是否會在網頁圖片 List 裡
        print(self.url)
        self.headers['Accept'] =  'application/json, text/javascript, */*; q=0.01'
        if "www" in self.url:
            self.url = self.url.replace("www","hm")
        else:
            pass
        r = self.client_session.post(self.url + '/Promotion/GetWhatIsNewData',headers=self.headers)
        print(r.text)


'''
#In[]


'''
