import multiprocessing
from multiprocessing.dummy import Process
import Api_Object
import re 
import time 
import asyncio
import pytest,allure
from datetime import datetime
from Common import Env,NoTestException
from aiowebsocket.converses import AioWebSocket
import datetime,time
import json
import demjson
import sys

from Logger import create_logger

log = create_logger(r"\AutoTest", 'common')
AlreadyLogin = ""


url = sys.argv[1]
'''
url = 'http://www.athena000.com/'
id='autoqa02'
'''
pw='1q2w3e4r'


virtual_sports_bettype_list_dict = {
    'Virtual Soccer' : [1201],
    'Virtual Tennis': [1220],
    'Virtual Basketball': [2805 , 2806],
}

class desktop_urgent_controller:
    def __init__(self,url,id,pw,central_account,central_password,sport):
        super().__init__()
        self.url = url #測試用
        self.id = id
        self.pw = pw
        self.central_account = central_account
        self.central_password = central_password
        self.log = create_logger(r"\AutoTest", 'desktop_api_betting')
        self.sport = sport

    def login(self):
        global AlreadyLogin,global_desktop_api
        retry = 0 
        while retry < 3:
            self.desktop_api = Api_Object.Login().login_api(device='Pc driver', user=self.id, url=self.url,central_account='web.desktop',central_password='1q2w3e4r')
            if self.desktop_api == False:
                self.log.info("登入失敗，重新登入")
                retry += 1
            elif 'Login Too Often' in str(self.desktop_api):
                self.log.info("Login Too Often，等待 60 秒後再重新登入")
                time.sleep(60)
                retry += 1
            else:
                AlreadyLogin = 'success'
                self.log.info('%s 已成功登入'%self.sport)
                global_desktop_api = self.desktop_api
                return self.desktop_api

def test_betting(Match_dict='',desktop_api='',sport='',market='',bettype_class='OU',bettype_id='',no_bettype=''): #no_bettype 用來判斷是否有不要重複下注的 Bettype ID
    log.info("開始下注 %s %s 下注"%(sport,market))
    betting_result = desktop_api.DoplaceBet(sport=sport,Match_dict=Match_dict,already_list=[],bettype_id=bettype_id,not_bettype_id=no_bettype)
    return betting_result

def test_parlay_betting(desktop_api,single_sport=True):
    parlay_result_dict = {}
    if single_sport != True:
        parlay_type_list = ['1','3'] #['1','3']
        for parlay_type in parlay_type_list:
            retry = 0
            while retry < 10:
                do_sports_list = []
                reget = 0
                while reget < 3:
                    log.info("開始抓取 %s %s 注單"%('Cross Sports','Cross market'))
                    websocket_info_result = desktop_api.get_websocket_info(sport='Cross Sports',market='Cross market',bet_type="parlay",parlay_type=parlay_type )
                    if websocket_info_result == False:
                        reget += 1
                    else:
                        do_sports_list.append('Soccer')
                        from random import shuffle #用來把 list 打亂可以不用一值下同一場比賽
                        sport_list = list(websocket_info_result)
                        shuffle(sport_list)
                        for sport in list(sport_list):
                            if sport == 'Soccer':
                                pass
                            else:
                                if len(do_sports_list) < 3:
                                    do_sports_list.append(sport)
                                else:
                                    break
                        if len(do_sports_list) == 3:
                            break
                betting_result = desktop_api.DoplaceBet(sport=sport,Match_dict=websocket_info_result,parlay_type=parlay_type,sport_list=do_sports_list) #not_bettype_id 用來排除不要下到的注單
                if betting_result  == False or any(fail_info in str(betting_result) for fail_info in  ['closed','HDP/OU','updating odds','Odds has changed','Live score'] ):
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
            market = 'parlay'
            for sport in sport_list :
                reget = 0
                while reget < 3:
                    log.info("開始抓取 %s %s 注單"%(sport,market))
                    websocket_info_result = desktop_api.get_websocket_info(sport = sport,market = market,bet_type="parlay")
                    if websocket_info_result == False:
                        reget += 1 
                    else:
                        break
                retry = 0
                while retry < 10:
                    betting_result = desktop_api.DoplaceBet(sport=sport,Match_dict=websocket_info_result,parlay_type=parlay_type) #not_bettype_id 用來排除不要下到的注單
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

def process_betting(desktop_api,sport,bettype_id_list='',single_sport_parlay=''):
    
    reduce_idx = 0 #這是為了建立 Report 美關的參數，用於讓 More/ Single 能夠正確分類
    bets_dict = {}
    parlay = False
    betting_result = True
    desktop_api.set_odds_type()
    if single_sport_parlay == '':
        if sport == "Virtual Sports":
            #['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Soccer','Virtual Basketball','Virtual Tennis']
            betradar_vs_sports = ['Soccer Euro Cup','Soccer Champions Cup','Soccer Asian Cup','Soccer League','Soccer World Cup','Soccer Nation','Virtual Basketball']
            sports_list = []
            import random
            random.shuffle(betradar_vs_sports) 
            for i in range(2):#隨機取兩個 betradar Sports
                sports_list.append(betradar_vs_sports[i])  
            sports_list.append('Virtual Soccer')
            sports_list.append('Virtual Tennis')
        else:
            sports_list = []
            sports_list.append(sport)
        for sport in sports_list:
            sport = sport
            bets_dict[sport] = []
            first_get = True #用來判斷是否第一次至 Websocket 抓取 Info，要清空給 More 抓取的 Match id list 
            if sport not in ['Soccer','Basketball','Tennis','Cricket','E-Sports'] :
                bettype_class_list =  ['OU']
            else:
                bettype_class_list =  ['OU','more'] #['OU','more']
            for bettype_class in bettype_class_list:
                if sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']:
                    if bettype_class == 'OU':
                        market_list = ['Live','Today','Early','Outright'] #['Live','Today','Early','Outright']
                    else:
                        market_list = ['Live','Today','Early'] #['Live','Today','Early']
                elif "Number Game" in sport or "Happy 5" in sport:
                    market_list = ['Live']
                else:
                    market_list = ['Today']
                #['Live','Today','Early']['Outright']
                for market in market_list:
                    if "Number Game" in sport or "Happy 5" in sport:
                        reget_int = 5 #Number Game 有可能在 No More Bettype 的情況下，所以常識五次
                    else:
                        reget_int = 2
                    reget = 0
                    while reget < reget_int:
                        get_info_result = desktop_api.get_websocket_info(sport = sport,market = market,bet_type=bettype_class,first_get=first_get)
                        first_get = False #用來判斷是否第一次至 Websocket 抓取 Info，要清空給 More 抓取的 Match id list
                        if get_info_result != 'No Odds' and get_info_result != False and get_info_result != 'No Market':
                            if market != 'Outright' :
                                if bettype_id_list == '' or bettype_class == 'more':
                                    bettype_id_list = ['','']
                                elif "Virtual" in sport :
                                    bettype_id_list = virtual_sports_bettype_list_dict[sport]
                                elif "Happy 5" in sport :
                                    bettype_id_list = [8101,8102]
                            else:
                                bettype_id_list = ['']
                            no_bettype = ''
                            for bettype_id in bettype_id_list:
                                retry = 0
                                while retry <= 5: #為了讓下注時發生 Odds 變更的可以 Retry 下注
                                    retry_betting = False
                                    try:
                                        bet_result = test_betting(Match_dict=get_info_result,desktop_api=desktop_api,sport=sport,market=market,bettype_class=bettype_class,bettype_id=bettype_id,no_bettype=no_bettype)
                                        if bet_result == "No BetType ID":
                                            bets_dict[sport].append('%s No BetType ID%s'%(market,bettype_id))
                                            break
                                        elif bet_result == "No More BetType":
                                            bets_dict[sport].append('%s No More BetType%s'%(market,bettype_id))
                                            break
                                        elif "No Other BetType ID" in bet_result:
                                            bets_dict[sport].append('%s %s'%(market,bet_result))
                                            break
                                        elif "API Fail" in bet_result:
                                            bets_dict[sport].append('%s %s'%(bet_result,market))
                                            break
                                        else:
                                            if any(fail_info in str(bet_result) for fail_info in  ['closed','HDP/OU','updating odds','Odds has changed','Live score','None'] ) and retry < 5 and sport not in ['Turbo Number Game','Number Game','Baseball']:
                                                log.error('Odds Closed Retry Betting')
                                                time.sleep(1) #進去後打太快，會造成 Logout，不等的話一秒內可以打到四次，這時候就會被判定為 Robot
                                                retry_betting = True
                                            else:
                                                bet_result = bet_result.replace("}"," ,'market' : '%s'}"%market)
                                                if market != "Outright" :
                                                    try:
                                                        no_bettype = str(re.findall(r"'BetTypeId': '(.+)', 'BetChoice",bet_result)[0])
                                                    except:
                                                        bettype_name = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",bet_result)[0])
                                                bets_dict[sport].append(bet_result)
                                            if retry_betting == True:
                                                retry += 1
                                            else:
                                                break
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
                                        if "Number Game" in sport:
                                            reget = 2 #為了讓資料寫成 No Market
                                            break
                                        else:
                                            retry += 1
                                            print(bet_result)
                            if retry_betting != True:
                                break
                        elif 'No Odds' in str(get_info_result) or 'No Market' in str(get_info_result):
                            reget = 2
                        else:
                            reget += 1
                    if reget == 2:
                        if get_info_result == None:
                            bets_dict[sport].append('%s No More BetType%s'%(market,bettype_id))
                        else:
                            if market != 'Outright' :
                                reduce_idx += 1
                            bets_dict[sport].append('%s No %s'%(sport,market)) 
    else:
        sport = parlay
        parlay = True
        if single_sport_parlay == True: 
            single_sport = True
        elif single_sport_parlay == False:
            single_sport = False
        try:
            bets_dict = test_parlay_betting(desktop_api,single_sport=single_sport)
        except Exception as e:
            log.error('%s Api Fail : %s'%(sport,str(e)))
            bets_dict[sport].append('%s Betting Fail'%"Single Sports Parlay")
            betting_result = False 

    #bets_dict = {'Soccer':["{'TransId_Cash': '115062746603', 'oddsid': '414103429', 'odds_type': 'MY', 'Line': 0.5, 'LeagueName': 'SABA CLUB FRIENDLY Virtual PES 21 - 15 Mins Play', 'BettypeName': 'Handicap', 'BetTypeId': '1', 'BetChoice': 'Arminia Bielefeld (V)', 'Odds': '0.68' ,'market' : 'Live'}","{'TransId_Cash': '115062747243', 'oddsid': '414132720', 'odds_type': 'MY', 'Line': 0.5, 'LeagueName': 'SABA ELITE FRIENDLY Virtual PES 21 - 5 Mins Play', 'BettypeName': 'Over/Under', 'BetTypeId': '3', 'BetChoice': 'Over', 'Odds': '0.27' ,'market' : 'Live'}","{'TransId_Cash': '115062747717', 'oddsid': '414111687', 'odds_type': 'MY', 'Line': -0.25, 'LeagueName': 'SABA CLUB FRIENDLY Virtual PES 21 - 15 Mins Play', 'BettypeName': 'Handicap', 'BetTypeId': '1', 'BetChoice': 'Olympique de Marseille (V)', 'Odds': '0.95' ,'market' : 'Today'}","{'TransId_Cash': '115062748026', 'oddsid': '414186719', 'odds_type': 'MY', 'Line': 2, 'LeagueName': 'SABA CLUB FRIENDLY Virtual PES 21 - 15 Mins Play', 'BettypeName': 'Over/Under', 'BetTypeId': '3', 'BetChoice': 'Over', 'Odds': '0.64' ,'market' : 'Today'}","{'TransId_Cash': '115062748901', 'oddsid': '413722725', 'odds_type': 'MY', 'Line': -0.25, 'LeagueName': 'ARGENTINA PRIMERA B NACIONAL', 'BettypeName': 'Handicap', 'BetTypeId': '1', 'BetChoice': 'CA Alvarado', 'Odds': '0.95' ,'market' : 'Early'}","{'TransId_Cash': '115062749300', 'oddsid': '413741187', 'odds_type': 'MY', 'Line': 2.25, 'LeagueName': 'AUSTRALIA A-LEAGUE', 'BettypeName': 'Over/Under', 'BetTypeId': '3', 'BetChoice': 'Over', 'Odds': '0.67' ,'market' : 'Early'}","{'TransId_Cash': '115062749632', 'oddsid': '7479386', 'odds_type': 'Dec', 'Line': 0, 'LeagueName': '*FIFA WORLD CUP 2022 (IN QATAR) - WINNER', 'BettypeName': 'Outright', 'Odds': '201' ,'market' : 'Outright'}","{'TransId_Cash': '115062750300', 'oddsid': '414114196', 'odds_type': 'Dec', 'Line': 0, 'LeagueName': 'SABA CLUB FRIENDLY Virtual FIFA 21 - 16 Mins Play', 'BettypeName': 'Double Chance', 'BetTypeId': '24', 'BetChoice': 'Home or Draw', 'Odds': '1.29' ,'market' : 'Live'}","{'TransId_Cash': '115062750470', 'oddsid': '414114167', 'odds_type': 'Dec', 'Line': 0, 'LeagueName': 'SABA CLUB FRIENDLY Virtual FIFA 21 - 16 Mins Play', 'BettypeName': 'Winning Margin', 'BetTypeId': '171', 'BetChoice': 'Home to Win by 1 Goal', 'Odds': '4.05' ,'market' : 'Live'}","{'TransId_Cash': '115062751553', 'oddsid': '414222925', 'odds_type': 'MY', 'Line': 0, 'LeagueName': 'AUSTRALIA CUP QUALIFIERS', 'BettypeName': '1H Odd/Even', 'BetTypeId': '12', 'BetChoice': 'Odd', 'Odds': '-0.99' ,'market' : 'Today'}","{'TransId_Cash': '115062751977', 'oddsid': '414222913', 'odds_type': 'Dec', 'Line': 0, 'LeagueName': 'AUSTRALIA CUP QUALIFIERS', 'BettypeName': '1H 1X2', 'BetTypeId': '15', 'BetChoice': 'Bentleigh Greens', 'Odds': '1.56' ,'market' : 'Today'}","{'TransId_Cash': '115062752629', 'oddsid': '413959797', 'odds_type': 'Dec', 'Line': 0, 'LeagueName': 'BRAZIL CAMPEONATO PAULISTA', 'BettypeName': 'Double Chance', 'BetTypeId': '24', 'BetChoice': 'Home or Draw', 'Odds': '1.03' ,'market' : 'Early'}","{'TransId_Cash': '115062752703', 'oddsid': '413959781', 'odds_type': 'Dec', 'Line': -1, 'LeagueName': 'BRAZIL CAMPEONATO PAULISTA', 'BettypeName': '3-Way Handicap', 'BetTypeId': '28', 'BetChoice': 'Home', 'Odds': '2.15' ,'market' : 'Early'}" ]}
    #由 success_list 抓取最後一個成功的注單
    betting_info = ''
    bets_dict_values = list(bets_dict.values())
    if single_sport_parlay != '':
        for get_bets_list in range (len(bets_dict_values)-1,-1,-1):
            print(bets_dict_values[get_bets_list])
            if "TransId" in str(bets_dict_values[get_bets_list]) and "'TransId_Cash': '0'" not in str(bets_dict_values[get_bets_list]):
                betting_info = str(bets_dict_values[get_bets_list])
                break
    else:
        for get_bets_list in range (len(bets_dict_values[0])-1,-1,-1):
            if "TransId" in bets_dict_values[0][get_bets_list] and "'TransId_Cash': '0'" not in bets_dict_values[0][get_bets_list]:
                betting_info = bets_dict_values[0][get_bets_list]
                break
    if betting_info != '':
        log.info("抓取 %s Statement 資訊"%sport)
        #解析出下注成功的 TransId_Cash
        try:
            if single_sport_parlay != '':
                transid = str(re.findall(r"TransId_Cash': '(.+)', 'BetTypeId_list'",betting_info)[0])
                bet_list_mini_info = get_bet_list_mini(desktop_api,transid)
            else:
                transid = str(re.findall(r"TransId_Cash': '(.+)', 'oddsid':",betting_info)[0])
                bet_list_mini_info = get_bet_list_mini(desktop_api,transid)
        except Exception as e:
            log.error("抓取 %s Bet list mini 資訊錯誤 : %s"%(sport,str(e)))
            allure.attach("抓取 %s Bet list mini 資訊錯誤"%sport)
            assert False
        try:
            if single_sport_parlay != '':
                transid = str(re.findall(r"TransId_Cash': '(.+)', 'BetTypeId_list'",betting_info)[0])
                bet_list_full_info = get_bet_list_full(desktop_api,transid)
            else:
                transid = str(re.findall(r"TransId_Cash': '(.+)', 'oddsid':",betting_info)[0])
                bet_list_full_info = get_bet_list_full(desktop_api,transid)
        except Exception as e:
            log.error("抓取 %s Bet list full 資訊錯誤 : %s"%(sport,str(e)))
            allure.attach("抓取 %s Bet list full 資訊錯誤"%sport)
            assert False
    else:
        pass
    
    for sport in list(bets_dict):
        with allure.step("%s 下注"%sport):
            pass
        if parlay == True:
            bets_info = [bets_dict[sport]]
        else:
            bets_info = bets_dict[sport]
        for idx,betslip in enumerate(bets_info):
            if sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports']:
                if idx == 0:
                    with allure.step("非 More Bettype 下注:"):
                        pass
                elif idx == 7 - reduce_idx:
                    with allure.step("More Bettype 下注:"):
                        pass
            if betting_info != '':
                try:
                    report_generate(parlay,sport,betslip)
                    log.info("比較 Quick Bet / Statement Info")
                    try:
                        if parlay == True:
                            CompareDict(sport,betslip,bet_list_mini_info,bet_list_full_info,True)
                        else:
                            CompareDict(sport,betslip,bet_list_mini_info,bet_list_full_info)
                    except Exception as e:
                        print(str(e))
                        continue
                except Exception as e:
                    if "False" in str(e): #如果 Result == Except 不會判定為 Fail
                        betting_result = False
                        log.error(str(e))
                        log.error(str(bets_info))
                    else:
                        pass
                    continue            
            else:
                try:
                    if betslip == False:
                        with allure.step("下注失敗，確認 Log 下注錯誤資訊 "):
                            betting_result = False
                    else:
                        report_generate(parlay,sport,betslip)
                except Exception as e:
                    if "False" in str(e): #如果 Result == Except 不會判定為 Fail
                        betting_result = False
                        log.error(str(e))
                        log.error(str(bets_info))
                    else:
                        pass
                    continue 
    if single_sport_parlay == '':
        if betting_result == False:
            if sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports','Number Game','Turbo Number Game','Happy 5']:
                allure.dynamic.title("%s 下注有 Fail!"%sport)
                assert False
            else:
                allure.dynamic.title("Virtual Sports 下注有 Fail!")
                assert False
        else:
            if sport in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports','Number Game','Turbo Number Game','Happy 5']:
                allure.dynamic.title("%s 下注 All Pass!"%sport)
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

def get_bet_list_mini(desktop_api,transid):
    try:
        statement_info = desktop_api.get_bet_list_mini(transid=transid)
        return statement_info
    except:
        log.info('抓取 Total Statement Info Fail')

def get_bet_list_full(desktop_api,transid):
    try:
        statement_info = desktop_api.get_bet_list_full(transid=transid)
        return statement_info
    except:
        log.info('抓取 Total Statement Info Fail')

def report_generate(parlay,sport,result_info):
    if parlay == True:
        #result_info = json.loads(result_info.replace("'",'"'))
        with allure.step("下注 %s %s " %(sport,"Cross Market")):
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
                market = result_info.split(' No BetType ID')[0]
                with allure.step("%s %s 無 %s " %(sport,market,BetTypeId)):
                    result = 'Except'
                    raise NoTestException
            elif "No Other BetType ID" in result_info:
                BetTypeId = result_info.split(' No Other BetType ID ')[1]
                market = result_info.split(' No Other BetType ID')[0]
                with allure.step("%s %s 無 %s 之外的 Bettype" %(sport,market,BetTypeId)):
                    result = 'Except'
                    raise NoTestException
            elif "No More BetType" in result_info:
                market = result_info.split(' No More BetType')[0]
                with allure.step("%s %s 無 More Bettype" %(sport,market)):
                    result = 'Except'
                    raise NoTestException
            else:
                with allure.step("%s 無 %s Market" %(sport,result_info.split(' No ')[1])):
                    result = 'Except'
                    raise NoTestException
        elif "api fail" in result_info.lower():
            with allure.step("%s %s %s" %(sport,result_info.split(' API Fail')[1],result_info)):
                assert False
        elif sport not in ['Soccer','Basketball','Tennis','Baseball','Cricket','Volleyball','E-Sports'] and ("TransId_Cash': '0'" in result_info or "'TransId_Cash': None" in result_info or "TransId" not in result_info):
            try:
                BetTypeId = str(re.findall(r"'BetTypeId': (.+), 'BetChoice",result_info)[0])
            except:
                BetTypeId = str(re.findall(r"'BettypeName': '(.+)', 'BetChoice",result_info)[0])
            market = str(re.findall(r"'market' : '(.+)'.+",result_info)[0])
            with allure.step("下注 %s %s %s " %(sport,market,BetTypeId)):
                allure.attach(result_info,"下注失敗注單")
                result = 'Except'
                raise NoTestException    
        elif "TransId_Cash': '0'" in result_info or "'TransId_Cash': None" in result_info or "TransId" not in result_info:
            try:
                BetTypeId = str(re.findall(r"'BetTypeId': (.+),",result_info)[0])
            except:
                BetTypeId = str(re.findall(r"'BettypeName': (.+),",result_info)[0])
            market = str(re.findall(r"'market' : '(.+)'.+",result_info)[0])
            with allure.step("下注 %s %s %s " %(sport,market,BetTypeId)):
                allure.attach(result_info,"下注失敗注單")
                result = 'Fail'
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
            with allure.step("下注 %s %s %s " %(sport,market,BetTypeId)):
                allure.attach(result_info,"下注成功注單")
                if odds_check(odds,check_odds_type=check_odds_type) == True:
                    allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認正確為 %s Odds Type"%check_odds_type)
                    assert True
                else:
                    allure.attach("%s : %s"%(check_odds_type,odds),"Odds 確認錯誤不為 %s Odds Type"%check_odds_type)
                    assert False

def statement_responce_generate(settled_info,statment_result = False):
    if "Fail" in settled_info:
        with allure.step("於抓取 %s 時發生錯誤" %settled_info.split('Fail')[0]):
            statement_result = False
            return statement_result
    elif "No Settle Betlist" in settled_info or ("No " in settled_info and "Result" in settled_info):
        with allure.step(settled_info):
            raise NoTestException
    else:
        if statment_result == True:
            for settled_result in settled_info:
                with allure.step("Check %s Info" %settled_result):
                    for settled_sport in list(settled_info[settled_result]):
                        if "Responce Fail" not in settled_info[settled_result][settled_sport]:
                            with allure.step("%s Info 正確回傳" %settled_sport):
                                allure.attach(settled_info[settled_result][settled_sport],"Responce Info")
                        else:
                            with allure.step("%s Info 回傳有誤" %settled_sport):
                                allure.attach(settled_info[settled_result],"Responce Info")
                                statement_result = False
                                return statement_result
        else:
            for settled_result in settled_info:
                if "Responce Fail" not in settled_info[settled_result]:
                    with allure.step("%s Info 正確回傳" %settled_result):
                        allure.attach(settled_info[settled_result],"Responce Info")
                else:
                    with allure.step("%s Info 回傳有誤" %settled_result):
                        allure.attach(settled_info[settled_result],"Responce Info")
                        statement_result = False
                        return statement_result

def statement_check(desktop_api):
    statement_result = True
    statement_remark_dict = {"Betting Statement" : 1 ,"Outstanding Bet" : 3, "Void & Cancelled Bet Statement" : 2} #{"Betting Statement" : 1 ,"Outstanding Bet" : 3, "Void & Cancelled Bet Statement" : 2}
    for statement_remark in list(statement_remark_dict):
        #此 list 第一個為 today 第二個為 昨天
        log.info("Check Statement %s 資訊"%(statement_remark))
        statement_info = desktop_api.get_statement_info(statement_remark_dict[statement_remark])
        with allure.step("Check Statement %s 資訊"%(statement_remark)):
            try:
                statement_result = statement_responce_generate(statement_info,statment_result=True)
            except Exception as e:
                print(str(e))
                break
    if statement_result != False:
        allure.dynamic.title("Check Statement 資訊 All Pass!")
        assert True
    else:
        allure.dynamic.title("Check Statement 資訊有錯誤!")
        assert False

def result_check(desktop_api):
    statement_result = True
    filter_game_list = ["Normal","Outright"] #["Normal","Outright"]
    for filter_game in filter_game_list:
        #此 list 第一個為 today 第二個為 昨天
        if filter_game == "Normal":
            days_list = [str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()), "%Y-%m-%d"))),str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()-datetime.timedelta(days=1) ), "%Y-%m-%d")))]
        else:
            days_list = [str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()), "%Y-%m-%d"))) + " to " + str(time.strftime("%m/%d/%Y", time.strptime(str(datetime.date.today()-datetime.timedelta(days=11) ), "%Y-%m-%d")))]
        for days in days_list:
            log.info("Check Result %s %s 資訊"%(filter_game,days))
            result_info = desktop_api.get_result_info(filter_game,days)
            with allure.step("Check Result %s %s 資訊"%(filter_game,days)):
                try:
                    statement_responce_generate(result_info)
                except Exception as e:
                    print(str(e))
                    pass
    if statement_result == True:
        allure.dynamic.title("Check Result 資訊 All Pass!")
        assert True
    else:
        allure.dynamic.title("Check Result 資訊有錯誤!")
        assert False

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

def CompareDict(sport,Dict1Key,bet_list_mini_info='',bet_list_full_info='',is_parlay=False):
    compare_bet_list = ["Bet List Mini","Bet List Full"]
    origin_Dict1Key = Dict1Key
    cross_sport = sport
    for idx,all_str2Key in enumerate([bet_list_mini_info,bet_list_full_info]):
        try:
            if idx == 1:
                bets_list = all_str2Key.replace(' ','').split('"TransId"')
                del bets_list[0] #移除第 0 個原因是由於分割出來的第一筆是最新下注，可能會影響到後續的判斷
                comparekey = ['TransId_Cash', 'odds_type','Line','LeagueName','BettypeName','Odds'] #比較的資訊
            else:
                bets_list = all_str2Key.replace(' ','').split('TransId')
                comparekey = ['TransId_Cash','Line','BettypeName','Odds'] #比較的資訊
            str2Key = ''
            try:
                origin_Dict1Key = json.loads(origin_Dict1Key.replace("'",'"')) #由於字串格式為 ' ' 無法轉
            except:
                pass
            for bets_info in bets_list:
                if origin_Dict1Key['TransId_Cash'] in bets_info:
                    str2Key = bets_info
                    break
            if str2Key == '':
                return False
            if is_parlay == True:
                comparekey = ['TransId_Cash','Line','LeagueName','BettypeName','odds']
                result_info_list = origin_Dict1Key['BetTypeId_list']
                sport_list = ''
                if "、" in cross_sport:
                    sport_list = cross_sport.split(" ")[0].split("、")
                for result_info in result_info_list:
                    if sport_list != '':
                        sport = sport_list[result_info_list.index(result_info)]
                    else:
                        sport = 'Soccer'
                    AssertDict = {}
                    same_list = []
                    Dict1Key = result_info
                    with allure.step("比較 %s %s %s Quick Bet / Statement Info"%(compare_bet_list[idx],sport,Dict1Key['BettypeName'])):
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
                                    if str(data1).replace(" ","").replace(',','') in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                        same_list.append(key)
                                    else:
                                        AssertDict[key] = 'Not same'
                        if len(AssertDict) == 0:# AssertDict 為空 代表比對ok
                            allure.attach(str(same_list),"%s %s 比較資訊皆正確"%(Dict1Key['LeagueName'],Dict1Key['BettypeName']))
                            assert True
                        else:
                            allure.attach(str(AssertDict),"%s %s 比較資訊有誤"%(Dict1Key['LeagueName'],Dict1Key['BettypeName']))
                            allure.attach(str(str2Key),"比較錯誤資料")
                            assert False
            else:
                AssertDict = {}
                same_list = []
                if isinstance(Dict1Key,dict):
                    pass
                elif isinstance(Dict1Key,str):
                    Dict1Key = demjson.decode(Dict1Key)                
                with allure.step("比較 %s %s %s Quick Bet / Statement Info"%(compare_bet_list[idx],sport,Dict1Key['BettypeName'])):
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
                            if str(data1).replace(" ","") in str(data2).replace(',',''):# 兩個相等 #,刪掉是怕 odds 大於 1000 時，下注不會顯示 ,
                                same_list.append(key)
                            else:
                                AssertDict[key] = 'Not same'
                    if len(AssertDict) == 0:# AssertDict 為空 代表比對ok
                        allure.attach(str(same_list),"%s 比較資訊皆正確"%compare_bet_list[idx])
                        assert True
                    else:
                        log.info(all_str2Key + "%s 比較資訊有誤"%compare_bet_list[idx])
                        allure.attach(str(AssertDict),"%s 比較資訊有誤"%compare_bet_list[idx])
                        allure.attach(str(str2Key),"比較錯誤資料")
                        assert False
        except Exception as e:
            print(str(e))
        
class TestRegression_soccer:   
    def test_soccer_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa11',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Soccer' ).login()
        bettype_id_list = [1,3] #如果是 Soccer,Basketball,E-Sports 3 個運動就值接指定 HDP，OU
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Soccer')
        process_betting(desktop_api,sport='Soccer',bettype_id_list = bettype_id_list)

class TestRegression_basketball:   
    def test_basketball_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa02',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Basketball').login()
        bettype_id_list = [1,3]
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Basketball')
        process_betting(desktop_api,sport='Basketball',bettype_id_list = bettype_id_list)

class TestRegression_tennis:   
    def test_tennis_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa03',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Tennis').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Tennis')
        process_betting(desktop_api,sport='Tennis')

class TestRegression_baseball:   
    def test_baseball_betting(self):
            allure.dynamic.story("Betting 測試")
            desktop_api = desktop_urgent_controller(url= url,id='autoqa04',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Baseball').login()
            ##desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Baseball')
            process_betting(desktop_api,sport='Baseball')

class TestRegression_cricket:  
    def test_cricket_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa07',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Cricket').login()
        ##desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Cricket')
        process_betting(desktop_api,sport='Cricket')

class TestRegression_volleyball:  
    def test_volleyball_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa08',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Volleyball').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Volleyball')
        process_betting(desktop_api,sport='Volleyball')

class TestRegression_esports:  
    def test_esports_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [1,3] 
        desktop_api = desktop_urgent_controller(url= url,id='autoqa09',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='E-Sports').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='E-Sports')
        process_betting(desktop_api,sport='E-Sports',bettype_id_list = bettype_id_list)

class TestRegression_numbergame:  
    def test_numbergame_betting(self):
        desktop_api = desktop_urgent_controller(url= url,id='autoqa10',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Number Game').login()
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Number Game')
        process_betting(desktop_api,sport='Number Game',bettype_id_list = bettype_id_list)
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Turbo Number Game')
        process_betting(desktop_api,sport='Turbo Number Game',bettype_id_list = bettype_id_list)
'''
class TestRegression_turbonumbergame:  
    def test_turbonumbergame_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        desktop_api = desktop_urgent_controller(url= url,id='autoqa11',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Number Game').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Turbo Number Game')
        process_betting(desktop_api,sport='Turbo Number Game',bettype_id_list = bettype_id_list)
'''
class TestRegression_happyfive:  
    def test_happyfive_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [85,90] 
        desktop_api = desktop_urgent_controller(url= url,id='autoqa15',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Happy 5').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Happy 5')
        process_betting(desktop_api,sport='Happy 5',bettype_id_list = bettype_id_list)

class TestRegression_virtualsport:  
    def test_virtual_sport_betting(self):
        allure.dynamic.story("Betting 測試")
        bettype_id_list = [2705,2707] 
        desktop_api = desktop_urgent_controller(url= url,id='autoqa12',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports').login()
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        process_betting(desktop_api,sport='Virtual Sports',bettype_id_list = bettype_id_list)
        
class TestRegression_soccer_parlay:  
    def test_soccer_parlay_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa13',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay').login()
        ##desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay')
        process_betting(desktop_api,sport='soccer parlay',single_sport_parlay=True)

class TestRegression_cross_parlay:  
    def test_cross_sport_parlay_betting(self):
        allure.dynamic.story("Betting 測試")
        desktop_api = desktop_urgent_controller(url= url,id='autoqa14',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay').login()
        ##desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='soccer parlay')
        process_betting(desktop_api,sport='soccer parlay',single_sport_parlay=False)

class TestRegression_statement:  
    def test_statement_check(self):
        desktop_api = desktop_urgent_controller(url= url,id='autoqa01',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='').login()
        allure.dynamic.story("Statement 測試")
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        statement_check(desktop_api)
    def test_result_check(self):
        desktop_api = desktop_urgent_controller(url= url,id='autoqa01',pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='').login()
        allure.dynamic.story("Statement 測試")
        #desktop_api_betting_test = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r',sport='Virtual Sports')
        result_check(desktop_api)

def pymain_func(version):
    args = ["-s",  "desktop_urgent.py::TestRegression_%s"%version, "-q", "--alluredir", "./reports"]
    pytest.main(args=args)   


if __name__ == "__main__":
    from multiprocessing import Process
    multiprocessing.freeze_support()

    #desktop_api = desktop_urgent_controller(url= url,id=id,pw=pw,central_account='web.desktop',central_password='1q2w3e4r').login()
    
    sports_list = ['soccer','basketball','tennis','baseball','cricket','volleyball','esports','numbergame','happyfive','virtualsport','soccer_parlay','cross_parlay','statement'] #['soccer','basketball','tennis','baseball','cricket','volleyball','esports','numbergame','happyfive','virtualsport','soccer_parlay','cross_parlay','statement']
    #sports_list = ['soccer']

    threads = []
    for enu,sport in enumerate(sports_list):
        log.info('sport : %s'%sport)
        t = Process(target=pymain_func, args=(sport,))
        threads.append(t)
    log.info('threads : %s'%threads)
    for i in threads:
        i.start()
        time.sleep(2)
    for i in threads:
        i.join()

    