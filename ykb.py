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
    r = requests.post(URL+"/api/openapi/v1/auth/getAccessToken",
                      headers={"content-type": "application/json"},
                      data=json.dumps({"appKey": APP_KEY, "appSecurity": APP_SECURITY}))
    rsp = r.json()
    print(f"ykb.get_access_token: {rsp}")
    return rsp["value"]["accessToken"]


# TODO: 应当定义请求数据对应的class，这样data指明该类型，能够更加明了
def add_dimension_item(data: Dict) -> str:
    r = requests.post(URL+f"/api/openapi/v1.1/dimensions/items?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.add_dimension_item url: {r.request.url}")
    print(f"ykb.add_dimension_item data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.add_dimension_item: {r.status_code}-{r.text}")
    rsp = r.json()
    return rsp["id"]


def get_dimension_by_id(id: str) -> Dict:
    r = requests.get(URL+f"/api/openapi/v1/dimensions/getDimensionById?accessToken={get_access_token()}&id={id}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    print(f"ykb.get_dimension_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.get_dimension_by_id: {r.status_code}-{r.text}")
    print(f"ykb.get_dimension_by_id: {r.text}")
    return r.json()["value"]


def get_staff_by_id(id: str) -> Dict:
    r = requests.post(URL+f"/api/openapi/v1/staffs/getStaffIds?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps({"type": "STAFFID", "conditionIds": [id]}))
    print(f"ykb.get_staff_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.staff: {r.status_code}-{r.text}")
    print(f"ykb.get_staff_by_id: {r.text}")
    return r.json()["items"][0]


def get_payee_by_id(id: str) -> Dict:
    r = requests.get(URL+f"/api/openapi/v2.1/payeeInfos?accessToken={get_access_token(
    )}&start=0&count=100&names&cardNos&ids={id}&active=true&orderBy=updateTime&orderByType=desc")
    print(f"ykb.get_payee_by_id url: {r.request.url}")
    if r.status_code != 200:
        raise Exception(f"ykb.payee: {r.status_code}-{r.text}")
    print(f"ykb.get_payee_by_id: {r.text}")
    return r.json()["items"][0]


def get_flow_details(flowId: str) -> Dict:
    r = requests.get(URL+f"/api/openapi/v1.1/flowDetails?accessToken={get_access_token()}&flowId={flowId}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_flow_details: {r.status_code}-{r.text}")
    print(f"ykb.get_flow_details: {r.text}")
    rsp = r.json()
    return rsp["value"]


def get_flow_details_by_code(code: str) -> Dict:
    r = requests.get(URL+f"/api/openapi/v1.1/flowDetails/byCode?accessToken={get_access_token()}&code={code}",
                     headers={"content-type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise Exception(f"ykb.get_flow_details_by_code: {
                        r.status_code}-{r.text}")
    print(f"ykb.get_flow_details_by_code: {r.text}")
    rsp = r.json()
    return rsp["value"]


# def get_specifications(type: str) -> List[Dict]:
#     r = requests.get(URL+f"/api/openapi/v1/specifications/latestByType?accessToken={get_access_token()}&type={type}",
#                      headers={"content-type": "application/json", "Accept": "application/json"})
#     if r.status_code != 200:
#         raise Exception(f"ykb.get_specifications: {r.status_code}-{r.text}")
#     rsp = r.json()
#     return rsp["items"]


# def get_specification_by_id(id: str) -> List[Dict]:
#     r = requests.get(URL+f"/api/openapi/v2/specifications/byIds/[{id}]?accessToken={get_access_token()}",
#                      headers={"content-type": "application/json", "Accept": "application/json"})
#     if r.status_code != 200:
#         raise Exception(f"ykb.get_specification_by_id: {r.status_code}-{r.text}")
#     rsp = r.json()
#     return rsp["items"]


def update_flow_state(flow_id: str, data: Dict):
    r = requests.post(URL+f"/api/openapi/v1/backlog/data/[{flow_id}]?" +
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


def update_flow_data(flow_id: str, editor_id: str, data: Dict):
    r = requests.put(URL+f"/api/openapi/v2.2/flow/data/${flow_id}?" +
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


def download_attachment(data: List):
    r = requests.post(URL+f"/api/openapi/v2/attachment/downloadurls?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.download_attachment data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.download_attachment: {r.status_code}-{r.text}")
    print(f"ykb.download_attachment rsp: {r.text}")
    return r.json()


def download_invoices(data: Dict) -> Dict:
    r = requests.post(URL+f"/api/openapi/v2/extension/INVOICE/url?accessToken={get_access_token()}",
                      headers={"content-type": "application/json",
                               "Accept": "application/json"},
                      data=json.dumps(data))
    print(f"ykb.download_invoices data: {r.request.body}")
    if r.status_code != 200:
        raise Exception(f"ykb.download_invoices: {r.status_code}-{r.text}")
    print(f"ykb.download_invoices rsp: {r.text}")
    return r.json()


def main():
    # add_dimension_item({
    #     "dimensionId": DIMENSION_ID_MAP["客户"],
    #     "name": "测试测试",
    #     "code": "KH4808",
    #     "parentId": "",
    #     "form": None
    # })

    # get_specifications("expense")

    # get_specification_by_id(data["form"]["specificationId"].split(":")[0])

    # print(get_access_token())

    # get_flow_details("ID01u0aADbUUXR")
    # get_flow_details_by_code("S23000049")
    # get_payee_by_id("ID01syImG6G2mj")
    update_flow_state("ID01ueSLt6olwr", {"approveId": "ID01owxnVpp2h1:ID01oycg2jFrIP", "action": {"name": "freeflow.reject","resubmitMethod": "TO_REJECTOR"}})
    # get_staff_by_id("ID01owxnVpp2h1:ID01oycg2jFvs3")
    # get_flow_details("ID01udai5Ud9Rt")


if __name__ == "__main__":
    main()
