import requests
import json
import base64
from typing import Dict

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from zeep import Client
from zeep.transports import Transport
import xmltodict
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

URL = "https://oa.jiagouyun.com"
ID = "453324"
APPID = "be43d81d-759b-430f-b068-d309f8afed31"
NAME = "上海观测未来信息技术有限公司"
ZDJ_USERID = "601"  # 张董君的 OA userid
# 公钥(RSA)，调用create_rsa_pair函数生成，生成一次即可
PUB_KEY = b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz5A0baFycGDfQd/DMkQ2\n7+If588CAIrjeprRhIpBp3j2wgDD241ot+C8UrrXEBrQjkQy61+NJSZSZ+Ow6BCc\npyB+0ZTp/kAJFw+zNEud8ByUnDcEpjrxTvxcYkqvMRiHi51ZN+18MAfeQvxJuULE\nhItU4gj/Ymqxye3VgVKjJ1ebwKXKD00oZrDwDOEiHQdW+C9VHvYhS/xnig5ZnD+d\n06iinubHaX9DXN6tEltCd2EAGdko8b3iJ9Nf70l7fcGg/dof/iTty06txGg5TSGN\nTBC1T3lEdyiw7YfKzy4oP6VmtGagJdcRyLR1FGWxJz5KaxOjHC1ONj8MH3s9ckK3\nMQIDAQAB\n-----END PUBLIC KEY-----"
# 私钥(RSA)，同上
PRIV_KEY = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAz5A0baFycGDfQd/DMkQ27+If588CAIrjeprRhIpBp3j2wgDD\n241ot+C8UrrXEBrQjkQy61+NJSZSZ+Ow6BCcpyB+0ZTp/kAJFw+zNEud8ByUnDcE\npjrxTvxcYkqvMRiHi51ZN+18MAfeQvxJuULEhItU4gj/Ymqxye3VgVKjJ1ebwKXK\nD00oZrDwDOEiHQdW+C9VHvYhS/xnig5ZnD+d06iinubHaX9DXN6tEltCd2EAGdko\n8b3iJ9Nf70l7fcGg/dof/iTty06txGg5TSGNTBC1T3lEdyiw7YfKzy4oP6VmtGag\nJdcRyLR1FGWxJz5KaxOjHC1ONj8MH3s9ckK3MQIDAQABAoIBAE1P/mdTeofnXWFx\nEoj3parmhFHY5nsDQMYbQq1mvhu+T9Nla46s9nN/T0ZVd+P0yPgk6P6JIc7TnmA6\nDFv0TBVoYjR4jkv42Cnx3CM/gz27t5MUXzP3wohUMake/nCAHYTggCn32IkfdSdo\nR6Gs//wK1fw3s8CZ001OvHcmK8VsDX/8BNnUMyRmJPT6m8x71q1OG6x7xjmpaGNm\nsE61ADO600mf2eqDGj8Ua66fLdECp2rpSkhc0Tj/jNkuK4io70wyT2jzW6MXtFl5\nYitYYZ1LtY2Hz/VJul3wV5IXbrYF1uEKad1uYIuoHKPiOgi8XWaNULiNIcaPaT3X\nn6AOgY0CgYEA2WUDp9UDziSQJ/17YYne/606vUmUkZAVc2x/6SpSpH9kZ9jNdRb7\nYsF/25qxWIe8CIGE42pbF6tgrkkGe6NqilBRIW5Fvk6CTvaateIv01wnJy4FNqql\nX7qs7UX8ySEwi3Ghxu7sA26Os7TLnfZp42iJ+qdPosm6olk+cG6kJn8CgYEA9Gw/\n+fV69O0IbUBTAPGLiVtJPAiwjZxsftcqlZi5gRuwPww+2WGt5CDv8N2EAkj9RjtP\n2BGCl5Vzm6EiIswwLpZHZt/L11bCE+9P0aonkUAtUFPsfiq2DqliByeRklKU+rvZ\ngk9MUD346NYbccN6Dgcnr1ZhqsGGBRB3aH+2Kk8CgYArxdcymAWoIFyWcMfDIAuy\n16KYMpSjqqtnDlXDES6KyMvizRixlusPO38PLNrAxLPr0oh7chLddTiGX1Xa11DA\ngOOVI6sPYqeCVs1YCi8vE8MedHnARCQAXoorTIhVx0ULDtpQQBNtrXk2XhURvWgc\nzhPaUI4MbSoTPn0ADocm6QKBgQCLHZWoOhz6jHLQY90aW2B1FFzxa2y5nP9vjh2x\nuZRTtKOyrtCSv3LOtiR67kl1V3+4WofOTeELT8fWG3cnYRpHWcdX+Sa28K1T1VCT\n4AnXNTTVVH71LHAklimyMsY7Bv++We6pqWKhBTTHqR1DueOdWlsvA7ZhDvatqTqd\nYpsXJwKBgQCnK9FhbVPU0Ml2Dh6urw7v3rDdmnnx6f/0QYj/yJHsBiDdNv9nInLz\nlJSxkaGiEN4vgtm1aubC4BhLKfQ2Kqtc0V9+8fk2IFS0VHKf+CfxQpvMU8GnuuRu\nJBCx5pwXAH5QymWm1W3j69J8l+xjf64Ro/vCNnbLpZOV0tuq6JgzUg==\n-----END RSA PRIVATE KEY-----"
# 调用regist函数获取，调用一次即可，后续调用得到相同数据
SECRET = b"e5b4257a-255a-4e3a-89d3-b770330c9e97"
# 服务端公钥，同上
SPK = b"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnwc+BmBlWNd06P78W+R1qgK+PJERelIRSfRdbg6NJcnPWwAKGuIL3DP/v5u18qrCbvF/iDzNK4CkbB59tlUNtJTQ0XJZXAr/xv2+1DjpVV9XQOY+JLDNrNr7IgbqlpKWSblcsSJ14mhWRJfs0bzrLOIZ8MMgFHrYYf10AnlJa+8Cur58KL6a7SBKC1mQ8pk33aRMLnZzu4xR7wU+hT6QXLLFC8CA8xzketr4vlGHZdmCS8XmGr1LleJQ9uiHcJ2EH9emhspSlL97zidr33mb3v5/h1nDjv66gtEl/KnK2C2Xe0iK6cd879fRRZ+B4fo5ngeAuEh3ZzX+op/ll3NOwQIDAQAB"

MODE_DATA_URL = "https://oa.jiagouyun.com/services/ModeDateService?wsdl"

# OA各流程ID
WORKFLOW_ID_MAP = {
    "采购申请流程": "58",
    "油卡充值申请流程": "68",
    "出差申请流程": "199",
    "招待费申请流程": "200",
    "出差周末加班补贴申请流程": "201",
    "部门活动申请流程": "202",

    "日常费用报销流程": "70",
    "差旅费用报销流程": "81",
    "日常项目报销流程": "165",
    "招待费报销申请流程": "204",
    "团队共享激励报销申请流程": "121",
    "付款申请流程（无合同）": "86",
    "付款申请流程（有合同）": "76",
    "薪金支出申请流程": "222",

    "新客户申请流程": "189",
    "客户信息修改流程": "192",

    "新供应商申请流程": "190",

    "观测云合作伙伴申请流程": "168",
    "传统云资源合作伙伴申请流程": "142",
    "云资源返利申请流流程": "143",
    "CloudCare云资源大使申请流程": "170",

    "立项审批流程": "120",
    "研发立项审批流程": "180",
    "观测云客户立项流程": "169",

    "收入类合同审批": "194",
}

MAIN_TABLE = "mainTable"
DETAIL_TABLES = "detailTables"


def create_rsa_pair():
    f = RSA.generate(2048)
    pub_key = f.publickey().exportKey()  # 公钥
    print(pub_key)
    priv_key = f.exportKey("PEM")  # 私钥
    print(priv_key)


def regist():
    r = requests.post(URL + "/api/ec/dev/auth/regist", verify=False,
                      headers={"appid": APPID, "cpk": base64.b64encode(PUB_KEY)})
    rsp = json.loads(r.text)
    print(rsp["secret"])
    print(rsp["spk"])


def get_token():
    spk = RSA.importKey(b"-----BEGIN PUBLIC KEY-----\n" + SPK +
                        b"\n-----END PUBLIC KEY-----")  # 输入必须bytes类型，且必须带前缀后缀
    cipher_public = PKCS1_v1_5.new(spk)
    text_encrypted = cipher_public.encrypt(SECRET)
    r = requests.post(URL + "/api/ec/dev/auth/applytoken", verify=False,
                      headers={"appid": APPID, "secret": base64.b64encode(text_encrypted)})
    rsp = r.json()
    print(f"oa.get_token: {rsp}")
    return rsp["token"]


def gen_headers(user_id: str):
    spk = RSA.importKey(b"-----BEGIN PUBLIC KEY-----\n" + SPK +
                        b"\n-----END PUBLIC KEY-----")  # 输入必须bytes类型，且必须带前缀后缀
    cipher_public = PKCS1_v1_5.new(spk)
    userid_encrypted = cipher_public.encrypt(user_id.encode())
    return {
        "token": get_token(),
        "appid": APPID,
        "userid": base64.b64encode(userid_encrypted),
    }


def get_workflow(workflow_id: str, request_id: str, user_id: str) -> dict:
    r = requests.get(
        URL + f"/api/workflow/paService/getWorkflowRequest?workflowId={workflow_id}&requestId={request_id}",
        headers=gen_headers(user_id))
    # print(f"oa.get_workflow: {r.text}")
    rsp = r.json()
    if rsp["code"] is None or rsp["code"] != "SUCCESS":
        raise Exception(f"oa.get_workflow: {rsp}")
    data = rsp["data"]

    # 解析主表字段，构建 字段名->字段 map 方便查询
    data[MAIN_TABLE] = {}
    main_table_fields = data["workflowMainTableInfo"]["requestRecords"][0]["workflowRequestTableFields"]
    for field in main_table_fields:
        data[MAIN_TABLE][field["fieldName"]] = field

    # 解析明细表字段，构建 字段名->字段 map 方便查询
    # 明细表有多个，是个数组
    data[DETAIL_TABLES] = []
    if "workflowDetailTableInfos" in data:
        for table in data["workflowDetailTableInfos"]:
            detailTableMap = {}
            if len(table["workflowRequestTableRecords"]) > 0:
                fields = table["workflowRequestTableRecords"][0]["workflowRequestTableFields"]
                for field in fields:
                    detailTableMap[field["fieldName"]] = field
            data[DETAIL_TABLES].append(detailTableMap)

    print(f"oa.get_workflow:{json.dumps(data, ensure_ascii=False)}")

    return data


def get_multi_workflow(workflow_id: str, request_id: str, user_id: str) -> dict:
    r = requests.get(
        URL + f"/api/workflow/paService/getWorkflowRequest?workflowId={workflow_id}&requestId={request_id}",
        headers=gen_headers(user_id))
    # print(f"oa.get_workflow: {r.text}")
    rsp = r.json()
    if rsp["code"] is None or rsp["code"] != "SUCCESS":
        raise Exception(f"oa.get_workflow: {rsp}")
    data = rsp["data"]

    # 解析主表字段，构建 字段名->字段 map 方便查询
    data[MAIN_TABLE] = {}
    main_table_fields = data["workflowMainTableInfo"]["requestRecords"][0]["workflowRequestTableFields"]
    for field in main_table_fields:
        data[MAIN_TABLE][field["fieldName"]] = field

    # 解析明细表字段，构建 字段名->字段 map 方便查询
    # 明细表有多个，是个数组
    data[DETAIL_TABLES] = []
    if "workflowDetailTableInfos" in data:
        for table in data["workflowDetailTableInfos"]:
            detailTableMap = []
            # 获取多个fields，比如table["workflowRequestTableRecords"][0]["workflowRequestTableFields"]、table["workflowRequestTableRecords"][1]["workflowRequestTableFields"]
            for record in table["workflowRequestTableRecords"]:
                fields = record["workflowRequestTableFields"]
                detailFields = {}
                for field in fields:
                    detailFields[field["fieldName"]] = field
                detailTableMap.append(detailFields)
            data[DETAIL_TABLES].append(detailTableMap)

    print(f"oa.get_multi_workflow:{json.dumps(data, ensure_ascii=False)}")

    return data


def create_workflow(data: Dict, user_id: str):
    r = requests.post(URL + f"/api/workflow/paService/doCreateRequest",
                      headers=gen_headers(user_id), data=json.dumps(data))
    print(f"oa.create_workflow data: {r.request.body}")
    rsp = r.json()
    if rsp["code"] is None or rsp["code"] != "SUCCESS":
        raise Exception(f"oa创建失败! oa.create_workflow rsp: {rsp}")
    # print(rsp["data"])
    return rsp["data"]  # 接口状态为SUCCESS,则data中包含生成的requestid


# update oa流程必须指定"Content-Type": "text/plain"，否则容易出现一些问题比如附件上传失败
def update_workflow(data: Dict, user_id: str):
    # data=json.dumps(data, ensure_ascii=False)
    headers = gen_headers(user_id)
    headers["Content-Type"] = "text/plain"
    r = requests.post(URL + f"/api/workflow/paService/submitRequest",
                      headers=headers, data=json.dumps(data))
    print(f"oa.update_workflow data: {r.request.body}")

    # 将r.request.body存储进文件oa_download.json里
    # filename='bycode.json'
    # with open(filename,'w') as file_obj:
    #     json.dump(data,file_obj)

    rsp = r.json()
    if rsp["code"] is None or rsp["code"] != "SUCCESS":
        raise Exception(f"oa更新失败! oa.update_workflow rsp: {rsp}")
    return rsp["code"]


# --------------------------------- 以下为获取mode数据的函数 -----------------------------------------

CUSTOMER_MODE_ID = 1  # 客户
PROVIDER_MODE_ID = 46  # 供应商
PARTNER_MODE_ID = 47  # 合作伙伴
INCOME_CONTRACT_MODE_ID = 20  # 收入合同
EXPENDITURE_CONTRACT_MODE_ID = 7  # 支出合同
RELEVANT_PROJECT_MODE_ID = 61  # 相关立项申请

session = requests.Session()
session.verify = False  # 取消 https 认证
transport = Transport(session=session)
mode_data_client = Client(MODE_DATA_URL, transport=transport)

DEBUG = False  # 是否开启调试


def parse_response_to_dict(rsp) -> list:
    if 'data' not in xmltodict.parse(rsp)['ROOT'].keys():
        return []
    """
    data_list:
    [
        {
            '@id': ...,
            'handlers': {...},
            'maintable': {...},
            'detail':{...},
        },
        ...
    ]    
    """
    data_list = xmltodict.parse(rsp)['ROOT']['data']
    # data = json.loads(json.dumps(data_ordereddict)) # 有序字典转无序字典
    return data_list if type(data_list) is list else [data_list]


def process_data(data):
    mode = {}
    """
    mode:
    {
        'id': ...,
        'sqr': {
            'label': ...,
            'dbtype': ...,
            'value': ...,
            'showname': ...
        },
    }
    """
    mode['id'] = data['@id']
    fields = data['maintable']['field']
    for field in fields:
        mode[field['filedname']] = {
            "label": field['filedlabel'],
            "dbtype": field['fileddbtype'],
            "value": field['filedvalue'],
            "showname": field['fieldshowname']
        }
    return mode


def process_detail(data, mode):
    mode['details'] = []
    DEBUG and print(data['detail'])
    if type(data['detail']) is dict:
        if type(data['detail']['detailtable']) is not list:
            data['detail']['detailtable'] = [data['detail']['detailtable']]
        """
        detailtable:
        [
            {
              '@id': '0'
            },
            {
                '@id': '...',
                'row': [
                    {
                        '@id': '...',
                        'field': [
                            {
                            'filedname': '...',
                            'filedlabel': '...',
                            'fileddbtype': '...',
                            'filedvalue': '...',
                            'fieldshowname': '...'
                            },
                            ...
                        ]
                    },
                    ...
                ]
            },
            ...
        ]
        """
        for detailtable in data['detail']['detailtable']:
            detail = []
            if type(detailtable) is str or 'row' not in detailtable.keys():
                continue
            row_data = detailtable['row']
            row_list = row_data if type(row_data) is list else [row_data]
            for r in row_list:
                row = {}
                row['id'] = r['@id']
                for field in r['field']:
                    DEBUG and print(field)
                    row[field['filedname']] = {
                        "label": field['filedlabel'],
                        "dbtype": field['fileddbtype'],
                        "value": field['filedvalue'],
                        "showname": field['fieldshowname']
                    }
                detail.append(row)
            mode['details'].append(detail)
    """
    mode:
    {
        'id': ...,
        'sqr': {
            'label': ...,
            'dbtype': ...,
            'value': ...,
            'showname': ...
        },
        ...
        'details': [
            [
                {
                    'id': ...,
                    'field1': {
                        'label': ...,
                        'dbtype': ...,
                        'value': ...,
                        'showname': ...
                    },
                    ...
                },
                ...
            ],
            ...
        ]
    }
    """
    return mode


"""
Args:
    mode_id: 表单ID
    page_no: 当前页数
    page_size: 每页记录数
    record_count: 记录总数（小于等于0时自动计算记录总数）
    userid: 当前用户
    conditions: 查询条件
    right: (y/n)是否受权限控制
    is_return_detail: (y/n)是否返回明细表数据
"""


# 获取mode表单数据列表（分页）
def get_all_mode_data_list(mode_id, page_no, page_size, record_count=0, userid=0, conditions="", right="n",
                           is_return_detail="y"):
    modes = []
    # 返回的是一个xml文件
    rsp = mode_data_client.service.getAllModeDataList(mode_id, page_no, page_size, record_count, userid, conditions,
                                                      right, is_return_detail)
    data_list = parse_response_to_dict(rsp)
    """
    data:
    {
        '@id': ...,
        'handlers': {...},
        'maintable': {...},
        'detail':{...},
    }
    """
    for data in data_list:
        mode = process_data(data)
        mode = process_detail(data, mode)
        modes.append(mode)
    time.sleep(1)
    return modes


# 获取mode表单数据总数
def get_all_mode_data_count(mode_id, user_id=0, conditions="", right="n"):
    rsp = mode_data_client.service.getAllModeDataCount(mode_id, user_id, conditions, right)
    DEBUG and print(rsp)
    return rsp


# 获取客户mode数据
def get_customer_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(CUSTOMER_MODE_ID, page_no, page_size, conditions=conditions)


# 获取客户mode数量
def get_customer_count(conditions=""):
    return get_all_mode_data_count(CUSTOMER_MODE_ID, conditions=conditions)


# 获取供应商mode数据
def get_provider_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(PROVIDER_MODE_ID, page_no, page_size, conditions=conditions)


# 获取供应商mode数量
def get_provider_count(conditions=""):
    return get_all_mode_data_count(PROVIDER_MODE_ID, conditions=conditions)


# 获取合作伙伴mode数据
def get_partner_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(PARTNER_MODE_ID, page_no, page_size, conditions=conditions)


# 获取合作伙伴mode数量
def get_partner_count(conditions=""):
    return get_all_mode_data_count(PARTNER_MODE_ID, conditions=conditions)


# 获取收入合同mode数据
def get_income_contract_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(INCOME_CONTRACT_MODE_ID, page_no, page_size, conditions=conditions)


# 获取收入合同mode数量
def get_income_contract_count(conditions=""):
    return get_all_mode_data_count(INCOME_CONTRACT_MODE_ID, conditions=conditions)


# 获取支出合同mode数据
def get_expenditure_contract_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(EXPENDITURE_CONTRACT_MODE_ID, page_no, page_size, conditions=conditions)


# 获取支出合同mode数量
def get_expenditure_contract_count(conditions=""):
    return get_all_mode_data_count(EXPENDITURE_CONTRACT_MODE_ID, conditions=conditions)


# 获取相关立项申请mode数据
def get_relevant_project_mode_data(page_no, page_size, conditions=""):
    return get_all_mode_data_list(RELEVANT_PROJECT_MODE_ID, page_no, page_size, conditions=conditions)


# 获取相关立项申请mode数量
def get_relevant_project_count(conditions=""):
    return get_all_mode_data_count(RELEVANT_PROJECT_MODE_ID, conditions=conditions)


def main():
    # print(get_token())
    # print(gen_headers("601"))
    # update_workflow()
    # get_workflow(WORKFLOW_ID_MAP["差旅费用报销流程"], "92581", ZDJ_USERID)
    start_date = (datetime.today() - relativedelta(months=1)).strftime("%Y-%m-%d")
    get_expenditure_contract_mode_data(0, get_expenditure_contract_count(),
                                       conditions=f'modedatacreatedate > \'{start_date}\'')
    # get_workflow(WORKFLOW_ID_MAP["观测云合作伙伴申请流程"], "87301", ZDJ_USERID)
    # get_workflow(WORKFLOW_ID_MAP["部门活动申请流程"], "87796", ZDJ_USERID)
    # get_workflow(WORKFLOW_ID_MAP["出差周末加班补贴申请流程"], "88332", ZDJ_USERID)


if __name__ == "__main__":
    main()
