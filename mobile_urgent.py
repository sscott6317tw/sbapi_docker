from codecs import BufferedIncrementalDecoder
import time,coloredlogs
import Api_Object
from  Logger import create_logger 
import pytest,allure
from Common import Env,NoTestException
import re
import json,csv
import datetime,time
import sys

AlreadyLogin = ""

virtual_sports_bettype_list_dict = {
    'Virtual Soccer' : [1201],
    'Virtual Tennis': [1220],
    'Virtual Basketball': [2805 , 2806],
}

from Logger import create_logger
log = create_logger(r"\AutoTest", 'common')



url = sys.argv[1]
id=sys.argv[2]
pw=sys.argv[3]
'''
url = 'http://qasb3.athena000.com:50005/'
id='autoqa01'
pw='1q2w3e4r'
'''
def odds_check(odds,check_odds_type='MY'):
    if odds == "" or odds is None:
        return False
    with allure.step("%s Odds Type 確認 : %s"%(odds,check_odds_type)):
        odds = float(odds)
        if check_odds_type == "CN":
            if 0 <= odds <= 100:
                return True
        elif check_odds_type == "Indo":
            if 1 <= odds <= 100 or -100 <= odds <= -1:
                return True
        elif check_odds_type == "US":
            if 100 <= odds <= 10000 or -10000 <= odds <= -100:
                return True
        elif check_odds_type == "Dec":
            if 1 < odds:
                return True
        elif check_odds_type == "MY":
            if -1 <= odds <= 1:
                return True
        else:
            return False

def CompareDict(sport,Dict1Key,all_str2Key,is_parlay=False):
    try:
        bets_list = all_str2Key.replace(' ','').split('betsbets')

        str2Key = ''
        try:
            Dict1Key = json.loads(Dict1Key.replace("'",'"')) #由於字串格式為 ' ' 無法轉
        except:
            pass
        for bets_info in bets_list:
            if Dict1Key['TransId_Cash'] in bets_info:
                str2Key = bets_info
                break
        if str2Key == '':
            return False
        if is_parlay == True:
            comparekey = ['TransId_Cash','Line','LeagueName','BettypeName','odds']
            result_info_list = Dict1Key['BetTypeId_list']
            sport_list = ''
            if "、" in sport:
                sport_list = sport.split(" ")[0].split("、")
            for result_info in result_info_list:
                if sport_list != '':
                    sport = sport_list[result_info_list.index(result_info)]
                else:
                    sport = 'Soccer'
                AssertDict = {}
                same_list = []
                Dict1Key = result_info
                with allure.step("比較 %s %s Quick Bet / Statement Info"%(sport,Dict1Key['BettypeName'])):
                    for key in comparekey:
                        if key == 'TransId_Cash': #如果 Line 是 0.0 就不用比了
                            same_list.append(key)
                            continue
                        data1 = Dict1Key[key]
                        data2 = str2Key #此為字串
                        if key == "BettypeName":
                            for bettypeName_split in data1.split(' '):
                                if str(bettypeName_split) in str(data2):# 兩個相等
                                    same_list.append(key)
                                    break
                            if "BettypeName" not in str(same_list):
                                AssertDict[key] = 'Not same'
                            else:
                                pass
                        elif key == 'Line' and data1 == 0.0: #如果 Line 是 0.0 就不用比了
                            same_list.append(key)
                        else:
                            if key == 'Line' :
                                if str(int(data1)) in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                    same_list.append(key)
                                else:
                                    AssertDict[key] = 'Not same'
                            elif key == 'odds':
                                if str(str(data1).split(".")[0]) in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                    same_list.append(key)
                                else:
                                    AssertDict[key] = 'Not same'
                            else:
                                if str(data1).replace(" ","") in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                    same_list.append(key)
                                else:
                                    AssertDict[key] = 'Not same'
                    if len(AssertDict) == 0:# AssertDict 為空 代表比對ok
                        allure.attach(str(same_list),"%s %s 比較資訊皆正確"%(Dict1Key['LeagueName'],Dict1Key['BettypeName']))
                        assert True
                    else:
                        allure.attach(str(AssertDict),"%s %s 比較資訊有誤"%(Dict1Key['LeagueName'],Dict1Key['BettypeName']))
                        assert False
        else:
            AssertDict = {}
            same_list = []
            comparekey = ['TransId_Cash', 'odds_type','Line','LeagueName','BettypeName','Odds'] #比較的資訊
            with allure.step("比較 %s %s Quick Bet / Statement Info"%(sport,Dict1Key['BettypeName'])):
                for key in comparekey:
                    data1 = Dict1Key[key]
                    data2 = str2Key #此為字串
                    if key == "BettypeName":
                        for bettypeName_split in data1.split(' '):
                            if str(bettypeName_split) in str(data2):# 兩個相等
                                same_list.append(key)
                                break
                        if "BettypeName" not in str(same_list):
                            AssertDict[key] = 'Not same'
                        else:
                            pass
                    elif key == 'Line' : #如果 Line 是 0.0 就不用比了
                        if data1 != 0.0 :
                            if str(int(data1)) in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                same_list.append(key)
                            else:
                                AssertDict[key] = 'Not same'
                        else:
                            pass
                    else:
                        if "saba" not in str(data1).lower() and "Virtual" in str(data1): #針對字串有 Virtual 做修正，Virtual 為自己加的
                            if "(Virtual)" in str(data1):
                                data1 = str(data1).replace("(Virtual)",'')
                            else:
                                data1 = str(data1).replace("Virtual",'')
                        if str(data1) in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                            same_list.append(key)
                        else:
                            AssertDict[key] = 'Not same'
                if len(AssertDict) == 0:# AssertDict 為空 代表比對ok
                    allure.attach(str(same_list),"比較資訊皆正確")
                    assert True
                else:
                    log.info(all_str2Key + " 比較資訊有誤")
                    allure.attach(str(AssertDict),"比較資訊有誤")
                    assert False
    except Exception as e:
        print(str(e))
        
class mobile_urgent_controller:
    def __init__(self,url,id,pw,central_account,central_password,sport):
        super().__init__()
        self.url = url #測試用
        self.id = id
        self.pw = pw
        self.sport = sport
        self.central_account = central_account
        self.central_password = central_password
        self.log = create_logger(r"\AutoTest", 'mobile_api_betting')
        self.result = 'PASS' #用來判斷是不是有 No Test 的測試項目
        if AlreadyLogin == "":# , 所以執行單一case ,一定會先叫 登入 方式
            self.login()
        else: #給第二個 Case 用
            self.mobile_api = global_mobile_api

    def login(self):
        global AlreadyLogin,global_mobile_api
        retry = 0 
        while retry < 3:
            self.mobile_api = Api_Object.Login().login_api(device='app', user=self.id,password=self.pw, url=self.url,central_account=self.central_account,central_password=self.central_password)
            if "nova88" in self.url and self.mobile_api == False:
                time.sleep(60)
                retry += 1
            else:
                AlreadyLogin = 'success'
                global_mobile_api = self.mobile_api
                break

    def test_betting(self,market,bettype_class='OU',bettype_id='',no_bettype=''): #no_bettype 用來判斷是否有不要重複下注的 Bettype ID
        self.mobile_api.set_odds_type(odds_type='MY')
        self.log.info("開始下注 %s %s 下注"%(self.sport,market))
        showallodds_result = self.mobile_api.ShowAllOdds(type='',market=[str(market[0]).lower()],sport=self.sport,bet_type=bettype_class)
        if showallodds_result == True or showallodds_result == 'False':
            pass
        else:
            if showallodds_result == "No Market":
                self.log.info("%s 無 %s Market"%(self.sport,market))
                return "No Market"
            else:
                self.log.info("打 Show All Odds API 發生錯誤")
                return "Show All Odds API Fail"
        get_market_result = self.mobile_api.GetMarket(bettype_id,not_bettype_id=no_bettype,urgent_use=True)
        if "No " in str(get_market_result) and type(get_market_result) == str:
            return get_market_result
        elif get_market_result == False :
            self.log.info("打 GetMarket API Fail 發生錯誤")
            return "GetMarket API Fail"
            
        betting_result = self.mobile_api.DoplaceBet(already_list=[],bettype_id=bettype_id,not_bettype_id=no_bettype) #not_bettype_id 用來排除不要下到的注單
        return betting_result

    def get_statement_info(self,transid):
        if self.sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']:
            datatype = '8'
        elif "Number Game" in self.sport:
            datatype = '7'
        elif "Happy 5" in self.sport:
            datatype = '36'
        else:
            datatype = '5' 
        try:
            statement_info = self.mobile_api.get_statement_info(transid,datatype=datatype)
            return statement_info
        except:
            self.log.info('抓取 Total Statement Info Fail')
        
    def report_generate(self,result_info):
        if self.parlay == True:
            #result_info = json.loads(result_info.replace("'",'"'))
            with allure.step("下注 %s %s " %(self.sport,"Cross Market")):
                with allure.step("Parlay 注單資訊 TransId_Cash : %s，Message : %s"%(result_info['TransId_Cash'],result_info['Message'])):
                    result_info_list = result_info['BetTypeId_list']
                    for result_info in result_info_list:
                        BetTypeId = result_info['BettypeName']
                        market = "Cross Market"
                        check_odds_type = result_info['odds_type']
                        odds = result_info['odds']
                        with allure.step("串票 %s %s " %(result_info['LeagueName'],BetTypeId)):
                            allure.attach(str(result_info),"串票資訊")
                            if odds_check(odds,check_odds_type=check_odds_type) == True:
                                allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認正確為 %s Odds Type"%check_odds_type)
                                assert True
                            else:
                                allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認錯誤不為 %s Odds Type"%check_odds_type)
                                assert False
        else:
            if " No " in result_info and " No Bet " not in result_info:
                if "No BetType ID" in result_info:
                    BetTypeId = result_info.split(' No BetType ID')[1]
                    with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                    # 讀取 CSV 檔案內容
                        rows = csv.reader(csvfile)
                        # 以迴圈輸出每一列
                        for row in rows:
                            if str(BetTypeId) in str(row):
                                BetTypeId = row[1]
                                break
                            else:
                                pass
                    market = result_info.split(' No BetType ID')[0]
                    with allure.step("%s %s 無 %s " %(self.sport,market,BetTypeId)):
                        self.result = 'Except'
                        raise NoTestException
                elif "No Other BetType ID" in result_info:
                    BetTypeId = result_info.split(' No Other BetType ID ')[1]
                    market = result_info.split(' No Other BetType ID')[0]
                    with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                    # 讀取 CSV 檔案內容
                        rows = csv.reader(csvfile)
                        # 以迴圈輸出每一列
                        for row in rows:
                            if str(BetTypeId) in str(row):
                                BetTypeId = row[1]
                                break
                            else:
                                pass
                    with allure.step("%s %s 無 %s 之外的 Bettype" %(self.sport,market,BetTypeId)):
                        self.result = 'Except'
                        raise NoTestException
                elif "No More BetType" in result_info:
                    market = result_info.split(' No More BetType')[0]
                    with allure.step("%s %s 無 More Bettype" %(self.sport,market)):
                        self.result = 'Except'
                        raise NoTestException
                else:
                    with allure.step("%s 無 %s Market" %(self.sport,result_info.split(' No ')[1])):
                        self.result = 'Except'
                        raise NoTestException
            elif "api fail" in result_info.lower():
                with allure.step("%s %s %s" %(self.sport,result_info.split(' API Fail')[1],result_info)):
                    assert False
            elif self.sport not in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports'] and ("TransId_Cash': '0'" in result_info or "'TransId_Cash': None" in result_info or "TransId" not in result_info):
                try:
                    BetTypeId = str(re.findall(r"'BetTypeId': (.+), 'BetChoice",result_info)[0])
                    with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                        # 讀取 CSV 檔案內容
                            rows = csv.reader(csvfile)
                            # 以迴圈輸出每一列
                            for row in rows:
                                if str(BetTypeId) in str(row):
                                    BetTypeId = row[1]
                                    break
                                else:
                                    pass
                except:
                    BetTypeId = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",result_info)[0])
                market = str(re.findall(r"'market' : '(.+)'.+",result_info)[0])
                with allure.step("下注 %s %s %s " %(self.sport,market,BetTypeId)):
                    allure.attach(result_info,"下注失敗注單")
                    self.result = 'Except'
                    raise NoTestException    
            elif "TransId_Cash': '0'" in result_info or "'TransId_Cash': None" in result_info or "TransId" not in result_info:
                try:
                    BetTypeId = str(re.findall(r"'BetTypeId': (.+), 'BetChoice",result_info)[0])
                    with open('bettype_id.csv', newline='') as csvfile: #抓取 Site 於什麼 Server Group
                        # 讀取 CSV 檔案內容
                            rows = csv.reader(csvfile)
                            # 以迴圈輸出每一列
                            for row in rows:
                                if str(BetTypeId) in str(row):
                                    BetTypeId = row[1]
                                    break
                                else:
                                    pass
                except:
                    try:
                        BetTypeId = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",result_info)[0])
                    except:
                        BetTypeId = str(re.findall(r"'BetTypeId': '(.+)'",result_info)[0])
                market = str(re.findall(r"'market' : '(.+)'.+",result_info)[0])
                with allure.step("下注 %s %s %s " %(self.sport,market,BetTypeId)):
                    allure.attach(result_info,"下注失敗注單")
                    self.result = 'Fail'
                    assert False
            else:
                if "Outright" not in str(result_info) :
                    BetTypeId = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",result_info)[0])
                    market = str(re.findall(r"'market' : '(.+)'.+",result_info)[0])
                else:
                    BetTypeId = "Outright"
                    market = "Today"
                check_odds_type = str(re.findall(r"'odds_type': '(.+)', 'Line",result_info)[0])
                odds = str(re.findall(r"'Odds': '(.+)' ,'market",result_info)[0])
                with allure.step("下注 %s %s %s " %(self.sport,market,BetTypeId)):
                    allure.attach(result_info,"下注成功注單")
                    if odds_check(odds,check_odds_type=check_odds_type) == True:
                        allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認正確為 %s Odds Type"%check_odds_type)
                        assert True
                    else:
                        allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認錯誤不為 %s Odds Type"%check_odds_type)
                        assert False
                
    def process_betting(self,bettype_class='OU',bettype_id_list='',single_sport_parlay=''):
        bets_dict = {}
        self.parlay = False #給 Genreport 參數
        betting_result = True
        if single_sport_parlay == '':
            if self.sport == "Virtual Sports":
                #['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Soccer','Virtual Basketball','Virtual Tennis']
                betradar_vs_sports = ['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Basketball']
                sports_list = []
                import random
                random.shuffle(betradar_vs_sports) 
                for i in range(2):#隨機取兩個 betradar Sports
                    sports_list.append(betradar_vs_sports[i])    
                sports_list.append('Virtual Soccer')
                sports_list.append('Virtual Tennis')
            elif self.sport == "Number Game": #['Turbo Number Game','Number Game']
                sports_list = ['Turbo Number Game','Number Game']
            else:
                sports_list = []
                sports_list.append(self.sport)
            for sport in sports_list:
                self.sport = sport
                bets_dict[self.sport] = []
                if self.sport not in ['Soccer','Basketball','Tennis','Cricket','E-Sports'] :
                    bettype_class_list =  ['OU']
                else:
                    bettype_class_list =  ['OU','more'] #['OU','more']
                for bettype_class in bettype_class_list:
                    if self.sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']:
                        if bettype_class == 'OU':
                            market_list = ['Live','Today','Early','Outright']
                        else:
                            market_list = ['Live','Today','Early']
                    elif "Number Game" in self.sport or "Happy 5" in self.sport:
                        market_list = ['Live']
                    else:
                        market_list = ['Today']
                    #['Live','Today','Early']['Outright']
                    for market in market_list:
                        if market != 'Outright' :
                            if bettype_id_list == '' or bettype_class == 'more':
                                bettype_id_list = ['','']
                            elif "Virtual" in self.sport :
                                bettype_id_list = virtual_sports_bettype_list_dict[self.sport]
                            elif "Happy 5" in self.sport :
                                bettype_id_list = [8101,8102]
                        else:
                            bettype_id_list = ['']
                        no_bettype = ''
                        for bettype_id in bettype_id_list:
                            retry = 0
                            while retry <= 5: #為了讓下注時發生 Odds 變更的可以 Retry 下注
                                retry_betting = False
                                try:
                                    bet_result = self.test_betting(market,bettype_class=bettype_class,bettype_id=bettype_id,no_bettype=no_bettype)
                                    if bet_result == "No Market":
                                        bets_dict[self.sport].append('%s No %s'%(self.sport,market))
                                        break
                                    elif bet_result == "No BetType ID":
                                        bets_dict[self.sport].append('%s No BetType ID%s'%(market,bettype_id))
                                        break
                                    elif bet_result == "No More BetType":
                                        bets_dict[self.sport].append('%s No More BetType%s'%(market,bettype_id))
                                        break
                                    elif "No Other BetType ID" in bet_result:
                                        bets_dict[self.sport].append('%s %s'%(market,bet_result))
                                        break
                                    elif "API Fail" in bet_result:
                                        bets_dict[self.sport].append('%s %s'%(bet_result,market))
                                        break
                                    else:
                                        if any(fail_info in str(bet_result) for fail_info in  ['closed','HDP/OU','updating odds','Odds has changed','Live score'] ) and retry < 5 and self.sport not in ['Turbo Number Game','Number Game','Baseball']:
                                            if retry == 5:
                                                if market == 'Outright':
                                                    no_bettype = str(re.findall(r"'BetTypeId': '(.+)'",bet_result)[0])
                                                else:
                                                    no_bettype = str(re.findall(r"'BetTypeId': (.+), 'BetChoice",bet_result)[0])
                                            self.log.error('Odds Closed Retry Betting')
                                            retry_betting = True
                                        else:
                                            bet_result = bet_result.replace("}"," ,'market' : '%s'}"%market)
                                            if market != "Outright" :
                                                try:
                                                    bettype_name = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",bet_result)[0])
                                                    with open('bettype_id.csv', newline='') as csvfile: 
                                                    # 讀取 CSV 檔案內容
                                                        rows = csv.reader(csvfile)
                                                        # 以迴圈輸出每一列
                                                        for row in rows:
                                                            if str(bettype_name) in str(row):
                                                                no_bettype = row[0]
                                                                break
                                                            else:
                                                                pass
                                                except:
                                                    no_bettype = str(re.findall(r"'BetTypeId': (.+), 'BetChoice",bet_result)[0])
                                            bets_dict[self.sport].append(bet_result)
                                        if retry_betting == True:
                                            retry += 1
                                        else:
                                            break
                                except Exception as e:
                                    self.log.error('%s Api Fail : %s'%(self.sport,str(e)))
                                    bets_dict[self.sport].append('%s Api Fail %s'%(self.sport,market))
                                    betting_result = False 
                                    retry += 1
        else:
            self.parlay = True
            if single_sport_parlay == True: 
                single_sport = True
            elif single_sport_parlay == False:
                single_sport = False
            try:
                bets_dict = self.test_parlay_betting(single_sport=single_sport)
            except Exception as e:
                self.log.error('%s Api Fail : %s'%(self.sport,str(e)))
                bets_dict[self.sport].append('%s Betting Fail'%"Single Sports Parlay")
                betting_result = False 
        #由 success_list 抓取最後一個成功的注單
        betting_info = ''
        bets_dict_values = list(bets_dict.values())
        for get_bets_list in range (len(bets_dict_values)-1,-1,-1):
            if single_sport_parlay != '':
                print(bets_dict_values[get_bets_list])
                if "TransId" in str(bets_dict_values[get_bets_list]) and "'TransId_Cash': '0'" not in str(bets_dict_values[get_bets_list]):
                    betting_info = str(bets_dict_values[get_bets_list])
                    break
            else:
                for get_bets in bets_dict_values[get_bets_list]:
                    if "TransId" in get_bets and "'TransId_Cash': '0'" not in get_bets:
                        betting_info = get_bets
                        break
                if betting_info != '':
                    break
        if betting_info != '':
            self.log.info("抓取 %s Statement 資訊"%self.sport)
            #解析出下注成功的 TransId_Cash
            try:
                if single_sport_parlay != '':
                    transid = str(re.findall(r"TransId_Cash': '(.+)', 'BetTypeId_list'",betting_info)[0])
                    statement_info = self.get_statement_info(transid)
                else:
                    transid = str(re.findall(r"TransId_Cash': '(.+)', 'oddsid':",betting_info)[0])
                    statement_info = self.get_statement_info(transid)
            except Exception as e:
                self.log.error("抓取 %s Statement 資訊錯誤 : %s"%(self.sport,str(e)))
                allure.attach("抓取 %s Statement 資訊錯誤"%self.sport)
                assert False
        else:
            pass
        for sport in list(bets_dict):
            self.sport = sport
            with allure.step("%s 下注"%self.sport):
                pass
            if self.parlay == True:
                bets_info = [bets_dict[sport]]
            else:
                bets_info = bets_dict[self.sport]
            for idx,betslip in enumerate(bets_info):
                if self.sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']:
                    if idx == 0:
                        with allure.step("非 More Bettype 下注:"):
                            pass
                    elif idx == 7:
                        with allure.step("More Bettype 下注:"):
                            pass
                if betting_info != '':
                    try:
                        self.report_generate(betslip)
                        self.log.info("比較 Quick Bet / Statement Info")
                        try:
                            if self.parlay == True:
                                CompareDict(self.sport,betslip,statement_info,True)
                            else:
                                CompareDict(self.sport,betslip,statement_info)
                        except Exception as e:
                            print(str(e))
                            continue
                    except Exception as e:
                        if self.result == 'Except': #如果 Result == Except 不會判定為 Fail
                            pass
                        else:
                            betting_result = False
                            self.log.error(str(e))
                            self.log.error(str(bets_info))
                        continue            
                else:
                    try:
                        if betslip == False:
                            with allure.step("下注失敗，確認 Log 下注錯誤資訊 "):
                                betting_result = False
                        else:
                            self.report_generate(betslip)
                    except Exception as e:
                        if self.result == 'Except': #如果 Resulr == Except 不會判定為 Fail
                            pass
                        else:
                            betting_result = False
                            self.log.error(str(e))
                        continue 
        if single_sport_parlay == '':
            if betting_result == False:
                if self.sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports','Number Game','Turbo Number Game','Happy 5']:
                    allure.dynamic.title("%s 下注有 Fail!"%self.sport)
                    assert False
                else:
                    allure.dynamic.title("Virtual Sports 下注有 Fail!")
                    assert False
            else:
                if self.sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports','Number Game','Turbo Number Game','Happy 5']:
                    allure.dynamic.title("%s 下注 All Pass!"%self.sport)
                    assert True
                else:
                    allure.dynamic.title("Virtual Sports 下注 All Pass!")
                    assert True
        else:
            if single_sport_parlay == True:
                if betting_result == False:
                    allure.dynamic.title("Soccer Cross Market Parlay 下注有 Fail!")
                    assert False
                else:
                    allure.dynamic.title("Soccer Cross Market Parlay 下注 All Pass!")
                    assert True
            else:
                if betting_result == False:
                    allure.dynamic.title("Cross Sports & Market Parlay 下注有 Fail!")
                    assert False
                else:
                    allure.dynamic.title("Cross Sports & Market Parlay 下注 All Pass!")
                    assert True

    def test_parlay_betting(self,single_sport=True):
        self.mobile_api.set_odds_type(odds_type='Dec')
        bettype_class_list = ['parlaymore','parlay','parlay']
        parlay_result_dict = {}
        if single_sport != True:
            sport_list = ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']
            parlay_type_list = ['1','3']
            for parlay_type in parlay_type_list:
                parlay_dict = {}
                if parlay_type != '3':
                    market_list = ['Early','Today','Live']
                else:
                    market_list = ['Early','Early','Early']
                retry = 0
                while retry < 10:
                    if retry > 5: #代表嘗試了五次還是失敗，把所有改成 Early
                        market_list = ['Early','Early','Early']
                    get_market_count = 0
                    do_sports_list = []
                    for sport in sport_list :
                        self.sport = sport
                        if len(list(parlay_dict)) == 3:
                            break
                        market = market_list[int(get_market_count%3)]
                        self.log.info("開始抓取 %s %s 注單"%(self.sport,market))
                        showallodds_result = self.mobile_api.ShowAllOdds(type='',market=[str(market[0]).lower()],sport=self.sport,bet_type=bettype_class_list[int(get_market_count%3)])
                        if showallodds_result == True or showallodds_result == 'False':
                            pass
                        else:
                            if showallodds_result == "No Market":
                                self.log.info("%s 無 %s Market"%(self.sport,market))
                                get_market_count += 1
                                continue
                            else:
                                self.log.info("打 Show All Odds API 發生錯誤")
                                get_market_count += 1
                                continue
                        get_market_result = self.mobile_api.GetMarket(urgent_use=True)
                        if "No " in str(get_market_result) :
                            continue
                        elif get_market_result == False :
                            self.log.info("打 GetMarket API Fail 發生錯誤")
                            return "GetMarket API Fail"
                        else:
                            print(len(list(parlay_dict)))
                            parlay_dict.update({len(list(parlay_dict)) : get_market_result})
                            get_market_count += 1
                            do_sports_list.append(self.sport)
                    betting_result = self.mobile_api.DoplaceBet(already_list=[],parlay_type=parlay_type,new_match_key_dict=parlay_dict,sport_list = do_sports_list) #not_bettype_id 用來排除不要下到的注單
                    if betting_result  == False or any(fail_info in str(betting_result) for fail_info in  ['closed','HDP/OU','updating odds','Odds has changed','Live score'] ):
                        self.log.error('Odds Closed Retry Betting')
                        parlay_dict = {}
                        retry += 1 
                    else:
                        break
                if retry != 10 :
                    if parlay_type == '1':
                        parlay_result_dict['%s Mix Parlay'%"、".join(do_sports_list)] = betting_result
                    elif parlay_type == '3':
                        parlay_result_dict['%s Lucky Parlay'%"、".join(do_sports_list)] = betting_result
                else:
                    if parlay_type == '1':
                        parlay_result_dict['Cross Sports/Markets Mix Parlay'] = False
                    elif parlay_type == '2':
                        parlay_result_dict['Cross Sports/Markets System Parlay'] = False

        else:
            sport_list = ['Soccer']
            parlay_type_list = ['1','2']
            for parlay_type in parlay_type_list:
                parlay_dict = {}
                market_list = ['Early','Today','Live']
                for sport in sport_list :
                    retry = 0
                    while retry < 10:
                        self.sport = sport
                        get_market_count = 0
                        while True :
                            if len(list(parlay_dict)) == 3:
                                break
                            market = market_list[int(get_market_count%3)]
                            self.log.info("開始抓取 %s %s 注單"%(self.sport,market))
                            showallodds_result = self.mobile_api.ShowAllOdds(type='',market=[str(market[0]).lower()],sport=self.sport,bet_type=bettype_class_list[int(get_market_count%3)])
                            if showallodds_result == True or showallodds_result == 'False':
                                pass
                            else:
                                if showallodds_result == "No Market":
                                    self.log.info("%s 無 %s Market"%(self.sport,market))
                                    get_market_count += 1
                                    continue
                                else:
                                    self.log.info("打 Show All Odds API 發生錯誤")
                                    get_market_count += 1
                                    continue
                            get_market_result = self.mobile_api.GetMarket(urgent_use=True)
                            if "No " in str(get_market_result) :
                                return get_market_result
                            elif get_market_result == False :
                                self.log.info("打 GetMarket API Fail 發生錯誤")
                                return "GetMarket API Fail"
                            else:
                                print(len(list(parlay_dict)))
                                parlay_dict.update({len(list(parlay_dict)) : get_market_result})
                                get_market_count += 1
                        betting_result = self.mobile_api.DoplaceBet(already_list=[],parlay_type=parlay_type,new_match_key_dict=parlay_dict) #not_bettype_id 用來排除不要下到的注單
                        if betting_result  == False or any(fail_info in str(betting_result) for fail_info in  ['closed','HDP/OU','updating odds','Odds has changed','Live score'] ):
                            parlay_dict = {}
                            retry += 1 
                        else:
                            break
                    if retry != 10 :
                        if parlay_type == '1':
                            parlay_result_dict['Soccer Mix Parlay'] = betting_result
                        elif parlay_type == '2':
                            parlay_result_dict['Soccer System Parlay'] = betting_result
                    else:
                        if parlay_type == '1':
                            parlay_result_dict['Soccer Mix Parlay'] = False
                        elif parlay_type == '2':
                            parlay_result_dict['Soccer System Parlay'] = False
        return parlay_result_dict
    
    def statement_responce_generate(self,settled_info):
        if "Fail" in settled_info:
            with allure.step("於抓取 %s 時發生錯誤" %settled_info.split('Fail')[0]):
                self.statement_result = False
                assert False
        elif "No Settle Betlist" in settled_info or "No Result" in settled_info:
            with allure.step(settled_info):
                raise NoTestException
        else:
            for settled_result in settled_info:
                if "Responce Fail" not in settled_info[settled_result]:
                    with allure.step("%s Info 正確回傳" %settled_result):
                        allure.attach(settled_info[settled_result],"Responce Info")
                else:
                    with allure.step("%s Info 回傳有誤" %settled_result):
                        allure.attach(settled_info[settled_result],"Responce Info")
                        self.statement_result = False
                        assert False
    
    def settle_check(self):
        self.statement_result = True
        check_bfday_dict = {
            '1' : 'Today',
            '2' : 'Last 2 Days',
            '14' : 'Last 7 Days'
        }
        for check_bfday in list(check_bfday_dict): 
            self.log.info("開始抓取 %s Settled 資訊"%check_bfday_dict[check_bfday])
            settled_result_info = self.mobile_api.get_settled_info(bfday=check_bfday)
            with allure.step("Check Settled %s 資訊"%check_bfday_dict[check_bfday]):
                try:
                    self.statement_responce_generate(settled_result_info)
                except Exception as e:
                    print(str(e))
                    pass
        if self.statement_result == True:
            allure.dynamic.title("Check Settled 資訊 All Pass!")
            assert True
        else:
            allure.dynamic.title("Check Settled 資訊有錯誤!")
            assert False

    def result_check(self):
        self.statement_result = True
        filter_game_list = ["Normal","Outright"]
        for filter_game in filter_game_list:
            #此 list 第一個為 today 第二個為 昨天
            if filter_game == "Normal":
                days_list = [str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()), "%Y-%m-%d"))),str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()-datetime.timedelta(days=1) ), "%Y-%m-%d")))]
            else:
                days_list = [str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()), "%Y-%m-%d"))) + " to " + str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()-datetime.timedelta(days=11) ), "%Y-%m-%d")))]
            for days in days_list:
                self.log.info("Check Result %s %s 資訊"%(filter_game,days))
                result_info = self.mobile_api.get_result_info(filter_game,days)
                with allure.step("Check Result %s %s 資訊"%(filter_game,days)):
                    try:
                        self.statement_responce_generate(result_info)
                    except Exception as e:
                        print(str(e))
                        pass
        if self.statement_result == True:
            allure.dynamic.title("Check Result 資訊 All Pass!")
            assert True
        else:
            allure.dynamic.title("Check Result 資訊有錯誤!")
            assert False

class TestRegression:   

    def test_numbergame_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Number Game')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_soccer_parlay_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay')
        mobile_api_betting_test.process_betting(single_sport_parlay=True)

    def test_cross_sport_parlay_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay')
        mobile_api_betting_test.process_betting(single_sport_parlay=False)

    def test_soccer_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [1,3] #如果是 Soccer,Basketball,E-Sports 3 個運動就值接指定 HDP，OU
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Soccer')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_basketball_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [1,3]
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Basketball')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_tennis_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Tennis')
        mobile_api_betting_test.process_betting()

    def test_baseball_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Baseball')
        mobile_api_betting_test.process_betting()
    
    def test_cricket_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Cricket')
        mobile_api_betting_test.process_betting()

    def test_volleyball_betting(self):
        allure.dynamic.story("Betting 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Volleyball')
        mobile_api_betting_test.process_betting()

    def test_esports_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [1,3] 
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='E-Sports')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_happyfive_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Happy 5')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_virtual_sport_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [2705,2707] 
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        mobile_api_betting_test.process_betting(bettype_id_list = bettype_id_list)

    def test_settled_check(self):
        allure.dynamic.story("Statement 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        mobile_api_betting_test.settle_check()

    def test_result_check(self):
        allure.dynamic.story("Statement 測試")
        mobile_api_betting_test = mobile_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        mobile_api_betting_test.result_check()

    def Exec_Test(self,case='All'):# 執行測試案例, exe_type 為打包pyinstaller 的參數
        if case == 'All':# 預設執行全部
            pytest.main(['-s', '-v', 'mobile_urgent.py::TestRegression','-q', '--alluredir', './reports'])
        
        elif '-k' in case:# 指定相關字元 testcase , Ex: case: -k Soccer
            pytest.main(['%s'%case,'mobile_urgent.py','-s', '-v',
            '-q', '--alluredir', './reports'])
        
        else:# 指定 一個testcase ,Ex: case: test_TopMenuLeftSportsMenu
            pytest.main(['-s', '-v',  'mobile_urgent.py::TestRegression::%s'%case, '--alluredir', './reports'])
    

if __name__ == "__main__":
    TestRegression().Exec_Test(case= 'All')
    Env.Allure_Report