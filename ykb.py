import requests
import json
from typing import Dict, List

URL = "https://app.ekuaibao.com"
APP_KEY = "9c47248f-0ceb-4c21-9880-774d5f433afa"
APP_SECURITY = "0a2cdb31-854b-40b6-a7d4-ad3826416dc5"
ZDJ_ID = "ID01owxnVpp2h1:ID01oycg2jFrIP"  # 张董君的ID
MY_ID = "ID01owxnVpp2h1:ID01qD9zkapWwv"

DIMENSION_ID_MAP = {
    "客户": "ID01owxnVpp2h1:客户",
    "供应商": "ID01owxnVpp2h1:供应商",
    "合作伙伴": "ID01owxnVpp2h1:合作伙伴",
    "项目": "ID01owxnVpp2h1:项目",
    "收入合同": "ID01owxnVpp2h1:收入合同"
}


def get_access_token():
    r = requests.post(URL + "/api/openapi/v1/auth/getAccessToken",
                      headers={"content-type": "application/json"},
                      data=json.dumps({"appKey": APP_KEY, "appSecurity": APP_SECURITY}))
    rsp = r.json()
    print(f"ykb.get_access_token: {rsp}")
    return rsp["value"]["accessToken"]


# TODO: 应当定义请求数据对应的class，这样data指明该类型，能够更加明了
def add_dimension_item(data: Dict) -> str:
    r = requests.post(URL + f"/api/openapi/v1.1/dimensions/items?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.add_dimension_item url: {r.request.url}")
    print(f"ykb.add_dimension_item data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.add_dimension_item: {r.status_code}-{r.text}")
    rsp = r.json()
    return rsp["id"]


# 获取自定义档案类别（即合思桌面端 档案设置 > 扩展档案 界面列表中展示的那些档案大类。例如 项目 就是一个自定义档案类别。）
def get_dimension() -> Dict:
    r = requests.get(URL + f"/api/openapi/v1/dimensions?accessToken={get_access_token()}&start=0&count=100",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension: {r.text}")
    return r.json()


# 获取自定义档案项（dimensionId对应的多个档案项）
def get_dimension_by_dimensionid(dimensionId: str) -> Dict:
    r = requests.get(
        URL + f"/api/openapi/v1/dimensions/items?accessToken={get_access_token()}&start=0&count=100&dimensionId={dimensionId}&orderBy=code&orderByType=asc",
        headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension_by_id: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension_by_id: {r.text}")
    return r.json()


# 批量新增自定义档案项
def add_dimension_items_by_batch(dimensionId: str, data: List[Dict]) -> List:
    r = requests.post(URL + f"/api/openapi/v1.1/dimensions/items/batch?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps({"dimensionId": dimensionId, "itemListRequest": data}))
    print(f"ykb.add_dimension_items_by_batch url: {r.request.url}")
    print(f"ykb.add_dimension_items_by_batch data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.add_dimension_items_by_batch: {r.status_code}-{r.text}")
    rsp = r.json()
    return rsp["items"]


# 更新自定义档案项（可以用id也可以用code）
def update_dimension_item(id: str, data: Dict):
    r = requests.put(URL + f"/api/openapi/v1.1/dimensions/items/${id}?accessToken={get_access_token()}",
                     headers={"content-type": "application/json",
                              "Accept": "application/json"},
                     data=json.dumps(data))
    print(f"ykb.update_dimension_item url: {r.request.url}")
    print(f"ykb.update_dimension_item data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.update_dimension_item: {r.status_code}-{r.text}")
    print(f"ykb.update_dimension_item rsp: {r.text}")


# 根据ID获取自定义档案项（查询id对应的单个档案项）
def get_dimension_by_id(id: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v1/dimensions/getDimensionById?accessToken={get_access_token()}&id={id}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension_by_id url: {r.request.url}")
    print(f"ykb.get_dimension_by_id data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension_by_id: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension_by_id: {r.text}")
    return r.json()["value"]


# 根据编码获取自定义档案项
def get_dimension_by_code(code: str) -> Dict:
    r = requests.get(
        URL + f"/api/openapi/v1/dimensions/getDimensionByCode?accessToken={get_access_token()}&code={code}",
        headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension_by_code url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension_by_code: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension_by_code: {r.text}")
    return r.json()["items"]


# 根据名称获取自定义档案项
def get_dimension_by_name(name: str) -> Dict:
    r = requests.get(
        URL + f"/api/openapi/v1/dimensions/getDimensionByName?accessToken={get_access_token()}&name={name}",
        headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension_by_name url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension_by_name: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension_by_name: {r.text}")
    return r.json()["items"]


# 通过id（比如ID01owxnVpp2h1:ID01oycg2jFrIP）请求员工数据
def get_staff_by_id(id: str) -> Dict:
    r = requests.post(URL + f"/api/openapi/v1/staffs/getStaffIds?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps({"type": "STAFFID", "conditionIds": [id]}))
    print(f"ykb.get_staff_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.staff: {r.status_code}-{r.text}")
    print(f"ykb.get_staff_by_id: {r.text}")
    return r.json()["items"][0]


# 通过code获取员工id字段
def get_staff_by_code(id: str) -> Dict:
    r = requests.post(URL + f"/api/openapi/v1/staffs/getStaffIds?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps({"type": "CODE", "conditionIds": [id]}))
    print(f"ykb.get_staff_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.staff: {r.status_code}-{r.text}")
    print(f"ykb.get_staff_by_id: {r.text}")
    return r.json()["items"][0]["id"]


def get_payee_by_id(id: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v2.1/payeeInfos?accessToken={get_access_token(
    )}&start=0&count=100&names&cardNos&ids={id}&active=true&orderBy=updateTime&orderByType=desc")
    print(f"ykb.get_payee_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.payee: {r.status_code}-{r.text}")
    print(f"ykb.get_payee_by_id: {r.text}")
    return r.json()["items"][0]


# 根据实例ID获取行程管理/订单管理业务对象实例
def get_travelmanagement_by_id(id: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v2/datalink/TRAVEL_MANAGEMENT/byDataLinkIds?accessToken={get_access_token(
    )}", headers={"content-type": "application/json", "Accept": "application/json"}, data=json.dumps({"ids": [id]}))
    print(f"ykb.get_travelmanagement_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.travelmanagement: {r.status_code}-{r.text}")
    print(f"ykb.get_travelmanagement_by_id: {r.text}")
    return r.json()


# 根据实例编号获取行程管理/订单管理业务对象实例
def get_travelmanagement_by_code(entityId: str, codes: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v2.1/datalink/TRAVEL_MANAGEMENT/byDataLinkCodes?accessToken={get_access_token(
    )}&entityId={entityId}&codes={codes}", headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_travelmanagement_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.travelmanagement: {r.status_code}-{r.text}")
    print(f"ykb.get_travelmanagement_by_id: {r.text}")
    return r.json()


# 获取行程管理/订单管理业务对象列表
def get_travelmanagement_by_entityid(id: str) -> Dict:
    r = requests.post(URL + f"/api/openapi/v2.1/datalink/TRAVEL_MANAGEMENT/searchOrders?accessToken={get_access_token(
    )}", headers={"content-type": "application/json", "Accept": "application/json"},
                      data=json.dumps({"entityId": id, "start": "0", "end": "100"}))
    print(f"ykb.get_travelmanagement_by_entityid url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.travelmanagement: {r.status_code}-{r.text}")
    print(f"ykb.get_travelmanagement_by_entityid: {r.text}")
    return r.json()


def get_privatecar_by_id(id: str) -> Dict:
    r = requests.post(
        URL + f"/api/openapi/v2/extension/PRIVATE_CAR/object/drivingRecord/search?accessToken={get_access_token(
        )}", headers={"content-type": "application/json", "Accept": "application/json"}, data=json.dumps({"ids": [id]}))
    print(f"ykb.get_privatecar_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.privatecar: {r.status_code}-{r.text}")
    print(f"ykb.get_privatecar_by_id: {r.text}")
    return r.json()["items"][0]


def get_flow_details(flowId: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v1.1/flowDetails?accessToken={get_access_token()}&flowId={flowId}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_flow_details: {r.status_code}-{r.text}")
    print(f"ykb.get_flow_details: {r.text}")
    rsp = r.json()
    return rsp["value"]


def get_flow_details_by_code(code: str) -> Dict:
    r = requests.get(URL + f"/api/openapi/v1.1/flowDetails/byCode?accessToken={get_access_token()}&code={code}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_flow_details_by_code: {
        r.status_code}-{r.text}")
    print(f"ykb.get_flow_details_by_code: {r.text}")
    rsp = r.json()
    return rsp["value"]


# 通过id获取费用类型明细表的SpecificationId
def get_specificationId_by_id(data: str) -> str:
    r = requests.post(
        URL + f"/api/openapi/v2/specifications/feeType/byIdsAndCodes?accessToken={get_access_token(
        )}", headers={"content-type": "application/json", "Accept": "application/json"},
        data=json.dumps({"ids": [data]}))
    if r.status_code != 200:
        raise Exception(f"ykb.get_specificationId_by_id: {
        r.status_code}-{r.text}")
    print(f"ykb.get_specificationId_by_id: {r.text}")
    rsp = r.json()
    return rsp["items"][0]["expenseSpecificationId"]


# # 通过id获取费用类型主表的specificationId
# def get_specificationId_by_name(name: str) -> Dict:
#     r = requests.get(
#         URL + f"/api/openapi/v1/specifications/getByName?name={name}&accessToken={get_access_token(
#         )}", headers={"content-type": "application/json", "Accept": "application/json"})
#     print(f"ykb.get_specificationId_by_name url: {r.request.url}")
#     if r.status_code != 200:
#         raise Exception(f"ykb.get_specificationId_by_name: {r.status_code}-{r.text}")
#     print(f"ykb.get_specificationId_by_name: {r.text}")
#     return r.json()


# 获取当前版本单据模板列表
def get_specifications(type: str) -> List[Dict]:
    r = requests.get(URL+f"/api/openapi/v1/specifications/latestByType?accessToken={get_access_token()}&type={type}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_specifications: {r.status_code}-{r.text}")
    print(f"ykb.get_specifications: {r.text}")

    rsp = r.json()
    return rsp["items"]


# 根据模板ID获取模板信息（主表的）
def get_specification_by_id(id: str) -> Dict:
    r = requests.get(URL+f"/api/openapi/v2/specifications/byIds/[{id}]?accessToken={get_access_token()}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_specification_by_id: {r.status_code}-{r.text}")
    print(f"ykb.get_specification_by_id: {r.text}")
    rsp = r.json()
    return rsp["items"][0]


# 审批单据，更新ykb表单状态
def update_flow_state(flow_id: str, data: Dict):
    r = requests.post(URL + f"/api/openapi/v1/backlog/data/[{flow_id}]?" +
                      f"accessToken={
                      get_access_token()}&messageCode=debug&powerCode=TICKET_AUDIT_switch",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.update_flow_state url: {r.request.url}")
    print(f"ykb.update_flow_state data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.update_flow_state: {r.status_code}-{r.text}")
    print(f"ykb.update_flow_state rsp: {r.text}")


# 更新单据
def update_flow_data(flow_id: str, editor_id: str, data: Dict):
    r = requests.put(URL + f"/api/openapi/v2.2/flow/data/${flow_id}?" +
                     f"accessToken={get_access_token()}&editorId={
                     editor_id}&editFlag=increment",
                     headers={"content-type": "application/json",
                              "Accept": "application/json"},
                     data=json.dumps(data))
    print(f"ykb.update_flow_data url: {r.request.url}")
    print(f"ykb.update_flow_data data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.update_flow_data: {r.status_code}-{r.text}")
    print(f"ykb.update_flow_data rsp: {r.text}")


# 创建单据
def create_flow_data(commit, data: Dict):
    r = requests.post(URL + f"/api/openapi/v2.2/flow/data?" +
                      f"accessToken={get_access_token()}&isCommit={commit}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.create_flow_data url: {r.request.url}")
    print(f"ykb.create_flow_data data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.create_flow_data: {r.status_code}-{r.text}")
    print(f"ykb.create_flow_data rsp: {r.text}")


def download_attachment(data: List):
    r = requests.post(URL + f"/api/openapi/v2/attachment/downloadurls?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.download_attachment data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.download_attachment: {r.status_code}-{r.text}")
    print(f"ykb.download_attachment rsp: {r.text}")
    return r.json()


def download_invoices(data: Dict) -> Dict:
    r = requests.post(URL + f"/api/openapi/v2/extension/INVOICE/url?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.download_invoices data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.download_invoices: {r.status_code}-{r.text}")
    print(f"ykb.download_invoices rsp: {r.text}")
    return r.json()


# def download_invoices(data: Dict) -> Dict:
#     r = requests.post(URL+f"/api/openapi/v2/extension/INVOICE/object/invoice/detailBatch?accessToken={get_access_token()}",
#                       headers={"content-type": "application/json",
#                                "Accept": "application/json"},
#                       data=json.dumps(data))
#     print(f"ykb.download_invoices data: {r.request.body}")
#     if r.status_code != 200:
#         raise Exception(f"ykb.download_invoices: {r.status_code}-{r.text}")
#     print(f"ykb.download_invoices rsp: {r.text}")
#     return r.json()


# 外部服务回调审批，通知Ebot执行"同意"或"驳回"操作
def notice_Ebot(flowId: str, nodeId: str, action: str, comment: str):
    payload = {
        "signKey": "8lUv6O1gb0UE",
        "flowId": flowId,
        "nodeId": nodeId,
        "action": action,
        "comment": comment,
        "rejectTo": ""
    }
    headers = {
        "content-type": "application/json",
        "Accept": "application/json"
    }
    url = URL + f"/api/outbound/v1/approval?accessToken={get_access_token()}"
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"ykb.notice_Ebot data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.notice_Ebot: {r.status_code}-{r.text}")
    print(f"ykb.notice_Ebot rsp: {r.text}")
    return r.json()


if __name__ == "__main__":
    # add_dimension_item({
    #     "dimensionId": DIMENSION_ID_MAP["客户"],
    #     "name": "测试测试",
    #     "code": "KH4808",
    #     "parentId": "",
    #     "form": None
    # })

    # get_specifications("expense")

    # get_specification_by_id(data["form"]["specificationId"].split(":")[0])

    # get_specification_by_id("ID01vvcdW1HMzd")

    # get_dimension_by_code("ID01xSUX1atUyX")
    # get_dimension_by_name("上海观测未来信息技术有限公司北京分公司")
    # get_dimension_by_dimensionid("ID01owxnVpp2h1:客户")
    # print(get_dimension_by_name("中国联合网络通信有限公司重庆市分公司"))
    # get_fee_type_by_data("ID01vviQDN7OSH")
    # get_specificationId_by_id("ID01vviQDN7OSH")
    # get_dimension_by_name("阿里云计算有限公司")
    # get_dimension_by_name("银⾏")
    # get_flow_details_by_code("B24000501")
    # get_specifications("requisition")
    print(get_specification_by_id("ID01wBiqmTV183")["id"])
    # get_payee_by_id("ID01wpu8vhsUh1")
    # update_flow_state("ID01v4uWhIC95l", {"approveId": "ID01owxnVpp2h1:ID01oycg2jFrIP", "action": {"name": "freeflow.reject","resubmitMethod": "TO_REJECTOR"}})
    # get_staff_by_code("00000602")
    # add_dimension_items_by_batch("ID01owxnVpp2h1:客户",[])
    # update_dimension_item("ID01owxnVpp2h1:客户",{"name":"上海捷信医药科技股份有限公司","code":"100","parentId":""})
    # get_staff_by_userid("601")
    # get_travelmanagement_by_entityid("fa10f678286c6d8c8bc0")
    # update_flow_data("ID01xT2OPLzkT5", ZDJ_ID, {"form": {"u_\u6d41\u7a0b\u7f16\u53f7": "CLFYBX-20240318-0006"}})
    # update_flow_state("ID01uUDRzEALaD","")
    # get_flow_details("ID01uW3aQDxSLd")
    # get_flow_details("ID01uTfb0DSTxB")
    # get_travelmanagement_by_id("ID01wpu8vhsUh1")
    # download_invoices({"invoiceIds": ["ID01owxnVpp2h1::24312000000016744470"]})
    # print((get_privatecar_by_id("ID01ubOHugFdsr"))["E_fa10f678286c6d8c8bc0_出发地"])
    # notice_Ebot("ID01v4C5wSPswD","FLOW:1179438128:1858968873","refuse","驳回")
