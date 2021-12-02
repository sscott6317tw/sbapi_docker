'''
這裡是用來 呼叫 api_object 腳本的地放 

'''
#In[]
from re import L
import Api_Object

#In[]


api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device='mobile', user= 'twqa09',
 url = 'http://qasb2.athena000.com:50026/',
 central_account='',central_password='' )


#In[]
api = Api_Object.Login(sec_times = 1 ,stop_times = 1 ).login_api(device='Pc', user= 'twqa09',
 url = 'http://mkt.11bet.com/onelogin.aspx',
 central_account='',central_password='' )

#In[]



#In[]


api.threads(func_name_list = [   api.ShowAllOdds ] )



#In[]

api.UpdateOdds()


#In[]
