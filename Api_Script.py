'''
這裡是用來 呼叫 api_object 腳本的地放 

'''

import Api_Object



#In[]
import Api_Object
url =  'http://qasb1.athena000.com:50039/' #'http://athena000smart.playthefun.com:3021/' 

user = 'autoqa11'
mobile_api = Api_Object.Mobile_Api(device='app',  password =  '1q2w3e4r', url=url )
mobile_api.mobile_login(user=user)

#In[]
'''
filter 帶陣列, 裡面 的matchid 就是 只要抓出這些 matchid 的相關賽事
type 帶test 可忽略 Test 比賽 , 帶空字串,就 不能找test賽事
filter 如果有list ,就是指定 matchid , 空字串 就是找 現在有的
'''
sport = 'Soccer'
market = ['e','e','e']
mobile_api.ShowAllOdds(type='' ,market=market,filter= '', sport =sport)


#In[]
'''
透過 ShowAllOdds 接口 回傳 matchid , 再傳給 GetMarket 得到相關 odds 資訊
BetType 可帶 parlaymore
'''
mobile_api.GetMarket(BetType='parlay')


#In[]
assign_list = []
for i in range(10):
    result = mobile_api.DoplaceBet(user= 'autoqa11',bet_team_index= '0' ,
    parlay_type='1')
