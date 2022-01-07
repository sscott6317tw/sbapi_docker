'''
這裡是用來 呼叫 api_object 腳本的地放 

'''
#In[]



#In[]
from re import L
import Api_Object

api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device='mobile', user= 'twqa09',
 url = 'https://ismart.playbooksb.com/apilogin',
 central_account='web.desktop',central_password='1q2w3e4r' )


#In[]
api.url


#In[]
api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device='Pc', user= 'twqa09',
 url = 'http://mkt.11bet.com/onelogin.aspx',
 central_account='',central_password='' )


 

#In[]
# 使用 指定 match id 用法
sport = 'Soccer'
market = ['e']
api.ShowAllOdds(type='test' ,market=market , filter = [48598912,48598925,48418744], sport =sport, bet_type='parlay')

#In[]
api.ShowAllOdds( )

#In[]
api.GetMarket()

#In[]
api.DoplaceBet()

#In[]


api.threads(func_name_list = [   api.ShowAllOdds ] )



#In[]

api.statement_running()


#In[]
