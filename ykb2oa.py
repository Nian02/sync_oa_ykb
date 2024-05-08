'''同步易快报数据到OA'''
import time
import json
from datetime import datetime
import base64
import requests
import urllib.parse

import oa
import ykb

# 油卡报销类型映射
fuelcard_map = {
    "油卡": "0",
    "现金": "1",
}

# 项目类型映射
project_map = {
    "售前": "0",
    "交付": "1",
}

# 报销类型映射
expense_map = {
    "一般": "0",
    "团建": '1',
    "行政": "2",
}

# 团建活动类型映射
teamactivity_map = {
    "团建": "0",
    "旅游": "1",
}

# 是否映射
yes_or_not_map = {
    "是": "0",
    "否": "1",
}

# 加班种类映射
extrawork_map = {
    "出差": "0",
    "日常": "1",
}

# 客户类型映射
client_map = {
    "客户": "0",
    "供应商": "1",
    "合作伙伴": "2",
}

# 招待类型映射
serve_map = {
    "出差招待": "0",
    "⽇常招待": "1",
}

# 行程规划映射：ykb_code->name
route_map = {
    "ID01oASd5OZ30b": "飞机",
    "ID01oASd5OZ7Nt": "用车",
    "ID01oASd5OZ4Bh": "住宿",
    "ID01oASd5OZ6cn": "火车",
    "ID01rqNl3OWfcX": "大巴",
    "ID01rqNBjNWeOH": "自驾",
}

# 航空舱位映射：ykb_code->name
flight_map = {
    "ECONOMY": "经济舱",
    "BUSINESS": "商务舱",
    "FIRST": "头等舱",
}

# 火车席别映射：ykb_code->name
train_map = {
    "DW2": "动卧",
    "ED": "二等座",
    "GJRW": "高级软卧",
    "DW": "高铁动卧",
    "RW": "软卧",
    "RWDRZ": "软卧代软座",
    "RZ": "软座",
    "SW": "商务座",
    "XKTRW": "新空调软卧",
    "XKTYW": "新空调硬卧",
    "XKTYZ": "新空调硬座",
    "YD": "一等座",
    "YW": "硬卧",
    "YZ": "硬座",
}

# 轮船舱型映射：ykb_code->name
ship_map = {
    "ER": "二等舱",
    "SAN": "三等舱",
    "SI": "四等舱",
    "YI": "一等舱",
}

# 合思订单code
hesi_order_code = {
    "COST210",  # 火车
    "COST211",  # 飞机
    "COST212",  # 用车
    "COST214",  # 酒店
}

# 差旅补贴code
travel_subsidy_code = {
    "COST1213",
    "COST215",
}


# 将时间戳格式转换成 %Y-%m-%d %H:%M格式
def ykb_date_2_oa_datetime(timestamp: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp / 1000))


def ykb_date_2_oa_date(timestamp: int) -> str:
    # 毫秒级时间戳要除于1000
    return time.strftime("%Y-%m-%d", time.localtime(timestamp / 1000))


# 将时间戳格式转换成 %H:%M 格式
def ykb_date_2_oa_time(timestamp: int) -> str:
    # 毫秒级时间戳要除于1000
    return time.strftime("%H:%M", time.localtime(timestamp / 1000))


# 处理客户/供应商/合作伙伴这几个多选字段，传入的应当是类似ID01reWPCQiYh1的列表，比如：
"""
"u_客户可多选": [
    "ID01tzFFLkFVRt",
    "ID01sQVo5X0hv9",
    "ID01tzGDfpJJzp"
]

"u_具体加班人员": [
    "ID01owxnVpp2h1:ID01qD9zkapWwv"
],
"""


# 返回","拼接的字符串
def handle_multi_dimension(dimensions: list) -> str:
    l = []
    for item in dimensions:
        # 处理易快报多选字段
        if (item.find(":") != -1):
            staffCustomForm = ykb.get_staff_by_id(item)["staffCustomForm"]
            if staffCustomForm != None and "u_OAid" in staffCustomForm:
                l.append(staffCustomForm["u_OAid"])
            else:
                l.append("")
        else:
            l.append(ykb.get_dimension_by_id(item)[
                         "code"])  # code字段是类似KH4871的信息
    return ",".join(l)


# 处理附件同步
def handle_attachments(attachments: list):
    if len(attachments) == 0:
        return None
    data = []
    for attachment in attachments:
        data.append({
            "id": attachment["fileId"],
            "key": attachment["key"],
            "expiration": 1800
        })
    ykb_files = ykb.download_attachment(data)
    oa_files = []
    for f in ykb_files:
        r = requests.get(f["url"])
        oa_files.append({
            "filePath": f"base64:{base64.b64encode(r.content).decode()}",
            "fileName": f["key"],
        })
    return oa_files


# 获取name
def get_dimension_name(id: str):
    return ykb.get_dimension_by_id(id)["name"]


economy_codes = ["Y", "S", "B", "H", "K", "L", "M", "N", "Q", "T", "X", "U", "E", "W", "G"]

# 飞机席别映射
flight_type_map = {
    "F": "头等舱",
    "A": "头等舱",
    "C": "公务舱",
    "D": "公务舱",
    "V": "常旅专用舱",
    "R1": "商务舱",
}


def get_seat_type(code):
    if code in economy_codes:
        return "经济舱"
    else:
        return flight_type_map.get(code, code)


# 获取行程订单数据
def get_travelmanagement_data(Id: str, code: str, type: str):
    data = ykb.get_travelmanagement_by_id(Id)["items"][0]["form"]

    # 创建映射字典
    code_type_map = {
        "COST210": {  # 火车
            "cfd": "E_cb1044a29ce187b83bc0_出发车站",
            "mdd": "E_cb1044a29ce187b83bc0_到达车站",
            "xb": "E_cb1044a29ce187b83bc0_火车坐席",
            "cfsj": "E_cb1044a29ce187b83bc0_出发时间",
            "ddsj": "E_cb1044a29ce187b83bc0_到达时间",
            "zflx": "E_cb1044a29ce187b83bc0_支付方式"
        },
        "COST211": {  # 飞机
            "cfd": "E_cb1044a29ce187b83bc0_出发机场",
            "mdd": "E_cb1044a29ce187b83bc0_到达机场",
            "xb": get_seat_type("E_cb1044a29ce187b83bc0_舱位类型"),
            "cfsj": "E_cb1044a29ce187b83bc0_出发时间",
            "ddsj": "E_cb1044a29ce187b83bc0_到达时间",
            "zflx": "E_cb1044a29ce187b83bc0_支付方式"
        },
        "COST212": {  # 用车
            "cfd": "E_cb1044a29ce187b83bc0_实际出发地点",
            "mdd": "E_cb1044a29ce187b83bc0_实际到达地点",
            "cfsj": "E_cb1044a29ce187b83bc0_出发时间",
            "ddsj": "E_cb1044a29ce187b83bc0_到达时间",
            "zflx": "E_cb1044a29ce187b83bc0_支付方式"
        },
        "COST214": {  # 酒店
            "cfsj": "E_cb1044a29ce187b83bc0_入住日期",
            "ddsj": "E_cb1044a29ce187b83bc0_离店日期",
            "jdmc": "E_cb1044a29ce187b83bc0_酒店名称",
            "zflx": "E_cb1044a29ce187b83bc0_支付方式"
        }
    }

    # 使用映射字典获取数据
    if code in code_type_map and type in code_type_map[code]:
        return data[code_type_map[code][type]]
    else:
        return ""


# 处理发票同步
def handle_invoices(invoices: list):
    if len(invoices) == 0:
        return None
    invoiceIds = []
    for invoice in invoices:
        invoiceIds.append(invoice["invoiceId"])
    ykb_rsp = ykb.download_invoices({"invoiceId": invoiceIds})
    oa_files = []
    for item in ykb_rsp["items"]:
        r = requests.get(item["url"])
        decoded_filename = urllib.parse.unquote(item["fileName"])
        filename_parts = decoded_filename.split('-')
        filename = '-'.join(filename_parts[5:])
        if not filename:
            filename = decoded_filename
        oa_files.append({
            "filePath": f"base64:{base64.b64encode(r.content).decode()}",
            "fileName": filename,
        })
    return oa_files


# 定义一个缓存字典用于存储已经获取过的privatecar信息
privatecar_cache = {}


def process_privatecar_info(item):
    if "u_行车记录" in item["feeTypeForm"]:
        if item["feeTypeForm"]["u_行车记录"] in privatecar_cache:
            return privatecar_cache[item["feeTypeForm"]["u_行车记录"]]
        else:
            privatecar_info = ykb.get_privatecar_by_id(
                item["feeTypeForm"]["u_行车记录"])
            # 进行额外处理
            # ...
            privatecar_cache[item["feeTypeForm"]["u_行车记录"]] = privatecar_info
            return privatecar_info
    return ""


# OA流程字段: 易快报单据字段 映射关系
workflow_map_conf = {
    "出差申请单": {
        "workflowId": oa.WORKFLOW_ID_MAP["出差申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["requisitionDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 对象类型
            "dxlx": lambda form: form["u_客户类型多选"][0] if "u_客户类型多选" in form else "",
            # 客户名称
            "khmc": lambda form: handle_multi_dimension(form["u_客户可多选"]) if "u_客户可多选" in form else "",
            # 供应商名称
            "gysmc": lambda form: handle_multi_dimension(form["u_供应商可多选"]) if "u_供应商可多选" in form else "",
            # 合作伙伴名称
            "hzhbmc": lambda form: handle_multi_dimension(
                form["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in form else "",
            # 客户编号
            # "khbh": lambda form: form["u_客户可多选"],
            # 供应商编号
            # "gysbh": lambda form: form["法人实体"],
            # 合作伙伴编号
            # "hzhbbh": None,
            # 出差天数
            "ccts": lambda form: (datetime.fromtimestamp(form["u_出差起止日期"]["end"] / 1000) -
                                  datetime.fromtimestamp(form["u_出差起止日期"]["start"] / 1000)).days,
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 出差性质
            "ccxz": lambda form: form["u_出差性质"],
            # 收入合同
            "srht": lambda form: form["u_model数据ID"] if "u_model数据ID" in form else "",
            # 收入合同编号
            "srhtbh": lambda form: form["u_收⼊合同编号"] if "u_收⼊合同编号" in form else "",
            # 相关立项申请
            "xglxlc": lambda form: form["u_OA⽴项流程ID"] if "u_OA⽴项流程ID" in form else "",
            # 项目编号
            "xmbhx": lambda form: form["u_项目编号"] if "u_项目编号" in form else "",
            # 出差事由
            "ccsy": lambda form: form["u_事由"],
            # 备注
            "bz": lambda form: form["description"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
            # 发票抬头
            "fpttx": lambda form: form["u_发票抬头txt"],
            # 申请金额
            "sqje": lambda form: form["requisitionMoney"]["standard"],
            # 总金额
            "zje": lambda form: form["requisitionMoney"]["standard"],
        },
        "detailData": {
            "formtable_main_53_dt1": {
                "ykb_field_name": "u_行程规划",  # 该明细表对应在易快报数据中的字段
                "checker": lambda item: True,  # 检测易快报明细数据项是否满足要求
                "field_map": {
                    # 出行方式
                    "cxfsx": lambda item: route_map[item["dataLinkTemplateId"]] if "dataLinkTemplateId" in item else "",
                    # 行程类型
                    "xclxx": lambda item: "",
                    # 出差城市
                    "cccs": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_住宿地"])[0][
                        "label"] if "E_fa1044a29ce187343bc0_住宿地" in item["dataLinkForm"] else "",
                    # 出发城市
                    "cfcsx": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_出发地"])[0][
                        "label"] if "E_fa1044a29ce187343bc0_出发地" in item["dataLinkForm"] else "",
                    # 目的城市
                    "mdcsx": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_目的地"])[0][
                        "label"] if "E_fa1044a29ce187343bc0_目的地" in item["dataLinkForm"] else "",
                    # 开始日期
                    "ccksrq": lambda item: ykb_date_2_oa_date(
                        item["dataLinkForm"]["E_fa1044a29ce187343bc0_入住日期"]) if "E_fa1044a29ce187343bc0_入住日期" in
                                                                                    item["dataLinkForm"] else "",
                    # 结束日期
                    "ccjsrq": lambda item: ykb_date_2_oa_date(
                        item["dataLinkForm"]["E_fa1044a29ce187343bc0_离店日期"]) if "E_fa1044a29ce187343bc0_离店日期" in
                                                                                    item["dataLinkForm"] else "",
                },
            }
        }
    },
    "招待费申请": {
        "workflowId": oa.WORKFLOW_ID_MAP["招待费申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["requisitionDate"]),
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 客户名称
            "khmcx": lambda form: handle_multi_dimension(form["u_客户可多选"]) if "u_客户可多选" in form else "",
            # 供应商名称
            "gysmc": lambda form: handle_multi_dimension(form["u_供应商可多选"]) if "u_供应商可多选" in form else "",
            # 合作伙伴名称
            "hzhbmc": lambda form: handle_multi_dimension(
                form["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in form else "",
            # 预计招待日期
            "zdrq": lambda form: ykb_date_2_oa_date(form["u_招待日期"]),
            # 预计金额
            "yjje": lambda form: form["requisitionMoney"]["standard"],
            # 招待人数
            "zdrs": lambda form: int(form["u_人数"]),
            # 招待事由
            "zdsy": lambda form: form["u_事由"],
            # 备注
            "bz": lambda form: form["description"],
            # 招待人员
            "zdry": lambda form: form["u_招待人员"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
        },
        "detailData": {

        },
    },
    "加班补贴申请单": {
        "workflowId": oa.WORKFLOW_ID_MAP["出差周末加班补贴申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["requisitionDate"]),
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 相关出差流程
            "xgccsq": lambda form: form["u_OA流程ID"],
            # 加班类型
            "lb": lambda form: extrawork_map[get_dimension_name(form["details"][0]["feeTypeForm"]["u_加班类型"])],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["details"][0]["feeTypeForm"]["attachments"]),
            # 备注
            "bz": lambda form: form["description"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
        },
        "detailData": {
            # 明细表
            "formtable_main_37_dt1": {
                "ykb_field_name": "details",  # 该明细表对应在易快报数据中的字段
                "checker": lambda item: True,  # 检测易快报明细数据项是否满足要求
                "field_map": {
                    # 开始日期
                    "ksrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_加班起止时间"]["start"]) if "u_加班起止时间" in item[
                        "feeTypeForm"] else "",
                    # 开始时间
                    "kssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_加班起止时间"]["start"]) if "u_加班起止时间" in item[
                        "feeTypeForm"] else "",
                    # 结束日期
                    "jsrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_加班起止时间"]["end"]) if "u_加班起止时间" in item[
                        "feeTypeForm"] else "",
                    # 结束时间
                    "jssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_加班起止时间"]["end"]) if "u_加班起止时间" in item[
                        "feeTypeForm"] else "",
                    # 补贴金额
                    "btje": lambda item: item["feeTypeForm"]["amount"]["standard"] if "amount" in item[
                        "feeTypeForm"] else "",
                    # 具体加班人员
                    "jtjbry": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_具体加班人员"]) if "u_具体加班人员" in item["feeTypeForm"] else "",
                    # 相关流程
                    "xglc": lambda item: item["feeTypeForm"]["u_OA出差流程ID"] if "u_OA出差流程ID" in item[
                        "feeTypeForm"] else "",
                },
            }
        },
    },
    "团建费申请单": {
        "workflowId": oa.WORKFLOW_ID_MAP["部门活动申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["requisitionDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
        },
        "detailData": {
            "formtable_main_27_dt1": {
                "ykb_field_name": "details",
                "checker": lambda item: True,
                "field_map": {
                    # 开始日期
                    "ksrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_活动起止日期"]["start"]) if "u_活动起止日期" in item[
                        "feeTypeForm"] else "",
                    # 开始时间
                    "kssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_活动起止日期"]["start"]) if "u_活动起止日期" in item[
                        "feeTypeForm"] else "",
                    # 结束日期
                    "jsrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_活动起止日期"]["end"]) if "u_活动起止日期" in item[
                        "feeTypeForm"] else "",
                    # 结束时间
                    "jssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_活动起止日期"]["end"]) if "u_活动起止日期" in item[
                        "feeTypeForm"] else "",
                    # 活动类型
                    "hdlx": lambda item: teamactivity_map[
                        get_dimension_name(item["feeTypeForm"]["u_活动类型"])] if "u_活动类型" in item[
                        "feeTypeForm"] else "",
                    # 是否自驾
                    "sfzj": lambda item: yes_or_not_map[
                        get_dimension_name(item["feeTypeForm"]["u_是否"])] if "u_是否" in item["feeTypeForm"] else "",
                    # 参与人员
                    "cyry": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_团建人员"]) if "u_团建人员" in
                                                                                                      item[
                                                                                                          "feeTypeForm"] else "",
                    # 事由说明
                    "sqsy": lambda item: item["feeTypeForm"]["consumptionReasons"] if "consumptionReasons" in item[
                        "feeTypeForm"] else "",
                    # 活动费用
                    "hdfy": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) if "amount" in item[
                        "feeTypeForm"] else 0,
                    # 参与人数
                    "cyrs": lambda item: item["feeTypeForm"]["u_人数"] if "u_人数" in item["feeTypeForm"] else "",
                },
            },
        },
    },
    "差旅报销单": {
        "workflowId": oa.WORKFLOW_ID_MAP["差旅费用报销流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["expenseDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
            # 相关出差流程（特殊处理）
            "xgcclc": lambda form: form["u_OA流程ID"] if "u_OA流程ID" in form else None,
            # 备注
            "bz": lambda form: form["description"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
            # 银行卡号
            "yhkh": lambda form: ykb.get_payee_by_id(form["payeeId"])["cardNo"],
        },
        "detailData": {
            # 明细表2
            "formtable_main_57_dt2": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: item["feeType"]["code"] not in hesi_order_code and item["feeType"][
                    "code"] not in travel_subsidy_code,
                "field_map": {
                    # 费用发生日期
                    "fyrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用发生时间
                    "fysj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用类型
                    "fylxx": lambda item: item["feeType"]["code"] if "feeType" in item else "",
                    # 费用说明
                    "zysm": lambda item: item["feeTypeForm"]["consumptionReasons"] if "consumptionReasons" in item[
                        "feeTypeForm"] else "",
                    # 附件数
                    "fpzs": lambda item: int(
                        item["feeTypeForm"]["u_附件数"] if "u_附件数" in item["feeTypeForm"] else 0),
                    # 其他附件
                    "qtfj": lambda item: handle_attachments(item["feeTypeForm"]["attachments"]) if "attachments" in
                                                                                                   item[
                                                                                                       "feeTypeForm"] else "",
                    # 发票类型
                    "fplx": lambda item: item["feeTypeForm"]["u_发票类型txt"] if "u_发票类型txt" in item[
                        "feeTypeForm"] else "",
                    # 不含税金额
                    "jebhs": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) - float(
                        item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item["feeTypeForm"] else float(
                        item["feeTypeForm"]["amount"]["standard"]),
                    # 税额
                    "se": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item[
                        "feeTypeForm"] else 0,
                    # 费用小计
                    "fyje": lambda item: float(item["feeTypeForm"]["amount"]["standard"]),
                    # 发票附件（差旅补贴没有invoiceForm字段）
                    "fjsc": lambda item: handle_invoices(item["feeTypeForm"]["invoiceForm"]["invoices"]) if (
                            "invoiceForm" in item["feeTypeForm"] and "invoices" in item["feeTypeForm"][
                        "invoiceForm"]) else "",
                    # 火车席别/航空舱位/轮船舱型
                    "hczbhkcw": lambda item: \
                        train_map[item["feeTypeForm"]["u_火车席别"]] if "u_火车席别" in item["feeTypeForm"] \
                            else flight_map[item["feeTypeForm"]["u_航班舱型"]] if "u_航班舱型" in item["feeTypeForm"] \
                            else ship_map[item["feeTypeForm"]["u_轮船舱型"]] if "u_轮船舱型" in item["feeTypeForm"] \
                            else "",
                },
            },
            "formtable_main_57_dt3": {  # 差旅补贴，选择这种类型的数据只需要上传这个明细表
                "ykb_field_name": "details",
                "checker": lambda item: item["feeType"]["code"] in travel_subsidy_code,
                "field_map": {
                    # 出差开始日期
                    "ksrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_出差起止日期"]["start"]) if "u_出差起止日期" in item[
                        "feeTypeForm"] else "",
                    # 出差开始时间
                    "kssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_出差起止日期"]["start"]) if "u_出差起止日期" in item[
                        "feeTypeForm"] else "",
                    # 出差结束日期
                    "jsrq": lambda item: ykb_date_2_oa_date(
                        item["feeTypeForm"]["u_出差起止日期"]["end"]) if "u_出差起止日期" in item[
                        "feeTypeForm"] else "",
                    # 出差结束时间
                    "jssj": lambda item: ykb_date_2_oa_time(
                        item["feeTypeForm"]["u_出差起止日期"]["end"]) if "u_出差起止日期" in item[
                        "feeTypeForm"] else "",
                    # 补贴金额
                    "btje": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) if "amount" in item[
                        "feeTypeForm"] else 0,
                    # 最终补贴金额
                    "zzbtje": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) if "amount" in item[
                        "feeTypeForm"] else 0,
                    # 相关流程
                    "xglc": lambda item: item["feeTypeForm"]["u_OA加班流程ID"] if "u_OA加班流程ID" in item[
                        "feeTypeForm"] else "",
                },
            },
            "formtable_main_57_dt4": {  # 行车记录，只有选择汽油费的时候会关联行车记录
                "ykb_field_name": "details",
                "checker": lambda item: item["feeType"]["code"] == "772" or item["feeType"]["code"] == "765",
                # 汽油费的code
                "field_map": {
                    # 用车日期
                    "ycrq": lambda item: ykb_date_2_oa_date(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 用车时间
                    "ycsj": lambda item: ykb_date_2_oa_time(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 返回日期
                    "fhrq": lambda item: ykb_date_2_oa_date(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 返回时间
                    "fhsj": lambda item: ykb_date_2_oa_time(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 出发地点
                    "cfdd": lambda item: process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 返回地点
                    "fhdd": lambda item: process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 公里数
                    "gls": lambda item: float(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 汽油费
                    "qyf": lambda item: float(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 同行人
                    "txr": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_同行人"]) if "u_同行人" in item[
                        "feeTypeForm"] else "",
                },
            },
            "formtable_main_57_dt5": {  # 火车-合思订单这种类型的数据只需要上传这个明细表
                "ykb_field_name": "details",
                "checker": lambda item: item["feeType"]["code"] in hesi_order_code,
                "field_map": {
                    # 订单类型
                    "ddlx": lambda item: item["feeType"]["name"][:2] if "feeType" in item else "",
                    # 费用发生日期
                    "fyfsrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 金额
                    "je": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) if "amount" in item[
                        "feeTypeForm"] else "",
                    # 税率
                    "sl": lambda item: float(item["feeTypeForm"]["taxRate"]) if "taxRate" in item[
                        "feeTypeForm"] else "",
                    # 可抵扣税额
                    "kdkse": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item[
                        "feeTypeForm"] else "",
                    # 出发地
                    "cfd": lambda item: get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"],
                                                                  item["feeType"]["code"], "cfd") if "u_行程订单" in
                                                                                                     item[
                                                                                                         "feeTypeForm"] else "",
                    # 目的地
                    "mdd": lambda item: get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"],
                                                                  item["feeType"]["code"], "mdd") if "u_行程订单" in
                                                                                                     item[
                                                                                                         "feeTypeForm"] else "",
                    # 出发时间
                    "cfsj": lambda item: ykb_date_2_oa_datetime(
                        get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"], item["feeType"]["code"],
                                                  "cfsj")) if "u_行程订单" in item["feeTypeForm"] else "",
                    # 到达时间
                    "ddsj": lambda item: ykb_date_2_oa_datetime(
                        get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"], item["feeType"]["code"],
                                                  "ddsj")) if "u_行程订单" in item["feeTypeForm"] else "",
                    # 席别
                    "xb": lambda item: get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"],
                                                                 item["feeType"]["code"], "xb") if "u_行程订单" in item[
                        "feeTypeForm"] else "",
                    # 酒店名称
                    "jdmc": lambda item: get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"],
                                                                   item["feeType"]["code"], "jdmc") if "u_行程订单" in
                                                                                                       item[
                                                                                                           "feeTypeForm"] else "",
                    # 支付类型
                    "zflx": lambda item: get_travelmanagement_data(item["feeTypeForm"]["u_行程订单"],
                                                                   item["feeType"]["code"], "zflx") if "u_行程订单" in
                                                                                                       item[
                                                                                                           "feeTypeForm"] else "",
                }
            }
        },
    },
    "日常费用报销单": {
        "workflowId": oa.WORKFLOW_ID_MAP["日常费用报销流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["expenseDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
            # 报销类型
            "bxlx": lambda form: expense_map[get_dimension_name(form["u_报销类型"])],
            # TODO：选择团建的时候会有别的数据
            # 备注说明
            "bzsm": lambda form: form["description"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
            # 银行卡号
            "yhkh": lambda form: ykb.get_payee_by_id(form["payeeId"])["cardNo"],
        },
        "detailData": {
            "formtable_main_35_dt1": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: True,
                "field_map": {
                    # 费用发生日期
                    "fyfsje": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用发生时间
                    "fyfssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用科目
                    "fykm": lambda item: item["feeType"]["code"] if "feeType" in item else "",
                    # 费用说明
                    "fysm": lambda item: item["feeTypeForm"]["consumptionReasons"] if "consumptionReasons" in item[
                        "feeTypeForm"] else "",
                    # 附件数
                    "fjs": lambda item: int(
                        item["feeTypeForm"]["u_附件数"] if "u_附件数" in item["feeTypeForm"] else 0),
                    # 其他附件
                    "qtfj": lambda item: handle_attachments(item["feeTypeForm"]["attachments"]) if "attachments" in
                                                                                                   item[
                                                                                                       "feeTypeForm"] else "",
                    # 发票类型
                    "fplx": lambda item: item["feeTypeForm"]["u_发票类型txt"] if "u_发票类型txt" in item[
                        "feeTypeForm"] else "",
                    # 不含税金额
                    "je": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) - float(
                        item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item["feeTypeForm"] else float(
                        item["feeTypeForm"]["amount"]["standard"]),
                    # 税额
                    "se": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item[
                        "feeTypeForm"] else 0,
                    # 费用小计
                    "fyje": lambda item: float(item["feeTypeForm"]["amount"]["standard"]),
                    # 费用所属客户类型
                    "fysskhlx": lambda item: client_map[
                        get_dimension_name(item["feeTypeForm"]["u_客户类型"])] if "u_客户类型" in item[
                        "feeTypeForm"] else "",
                    # 客户名称
                    "szkhdx": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_客户可多选"]) if "u_客户可多选" in item["feeTypeForm"] else "",
                    # 供应商名称
                    "szgysdx": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_供应商可多选"]) if "u_供应商可多选" in item["feeTypeForm"] else "",
                    # 合作伙伴名称
                    "szhzhbdx": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in item["feeTypeForm"] else "",
                    # 发票附件
                    "fj": lambda item: handle_invoices(item["feeTypeForm"]["invoiceForm"]["invoices"]) if (
                            "invoiceForm" in item["feeTypeForm"] and "invoices" in item["feeTypeForm"][
                        "invoiceForm"]) else "",
                    # 相关流程
                    "xglc": lambda item: item["feeTypeForm"]["u_OA流程ID"] if "u_OA流程ID" in item[
                        "feeTypeForm"] else "",
                    # 客户档案URL
                    "khdabh": lambda item: item["feeTypeForm"]["u_客户档案URL"] if "u_客户档案URL" in item[
                        "feeTypeForm"] else "",

                },
            },
            "formtable_main_35_dt3": {  # 行车记录，只有选择汽油费的时候会关联行车记录
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: item["feeType"]["code"] == "772" or item["feeType"]["code"] == "765",
                # 汽油费的code
                "field_map": {
                    # 用车日期
                    "ycrq": lambda item: ykb_date_2_oa_date(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 用车时间
                    "ycsj": lambda item: ykb_date_2_oa_time(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 返回日期
                    "fhrq": lambda item: ykb_date_2_oa_date(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 返回时间
                    "fhsj": lambda item: ykb_date_2_oa_time(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"]["time"]) if "u_行车记录" in item[
                        "feeTypeForm"] else "",
                    # 出发地点
                    "cfdd": lambda item: process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_出发地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 返回地点
                    "fhdd": lambda item: process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_目的地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 公里数
                    "gls": lambda item: float(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 汽油费
                    "qyf": lambda item: float(
                        process_privatecar_info(item)["E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 所属客户
                    "szkh": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_客户可多选"]) if "u_客户可多选" in item["feeTypeForm"] else "",
                    # 所属供应商
                    "szgys": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_供应商可多选"]) if "u_供应商可多选" in item["feeTypeForm"] else "",
                    # 所属合作伙伴
                    "szhzhb": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in item["feeTypeForm"] else "",
                    # 同行人
                    "txr": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_同行人"]) if "u_同行人" in item[
                        "feeTypeForm"] else "",
                }
            }
        },
    },
    "项目报销单": {
        "workflowId": oa.WORKFLOW_ID_MAP["日常项目报销流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["expenseDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
            # 项目类型
            "xmlx": lambda form: project_map[get_dimension_name(form["u_项目类型"])],
            # 项目编号
            "xmbh": lambda form: form["u_项目编号"] if "u_项目编号" in form else "",
            # 相关立项流程
            "xglxsqlc": lambda form: form["u_OA⽴项流程ID"] if "u_OA⽴项流程ID" in form else "",
            # 相关收入合同
            "xgsrht": lambda form: form["u_model数据ID"] if "u_model数据ID" in form else "",
            # 备注说明
            "bzsm": lambda form: form["description"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
            # 银行卡号
            "yhkh": lambda form: ykb.get_payee_by_id(form["payeeId"])["cardNo"],
            # 明细金额合计
            "mxjehj": lambda form: float(form["payMoney"]["standard"]),
            # 本次应付金额
            "bcyfje": lambda form: float(form["payMoney"]["standard"]),
        },
        "detailData": {
            "formtable_main_183_dt1": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: True,
                "field_map": {
                    # 费用发生日期
                    "fyfsrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用发生时间
                    "fyfssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用科目
                    "fykm": lambda item: item["feeType"]["code"] if "feeType" in item else "",
                    # 相关流程
                    "xglc": lambda item: item["feeTypeForm"]["u_OA招待流程ID"] if "u_OA招待流程ID" in item[
                        "feeTypeForm"] else "",
                    # 费用说明
                    "fysm": lambda item: item["feeTypeForm"]["consumptionReasons"] if "consumptionReasons" in item[
                        "feeTypeForm"] else "",
                    # 附件数
                    "fjs": lambda item: int(
                        item["feeTypeForm"]["u_附件数"] if "u_附件数" in item["feeTypeForm"] else 0),
                    # 其他附件
                    "qtfj": lambda item: handle_attachments(item["feeTypeForm"]["attachments"]) if "attachments" in
                                                                                                   item[
                                                                                                       "feeTypeForm"] else "",
                    # 发票类型
                    "fplx": lambda item: item["feeTypeForm"]["u_发票类型txt"] if "u_发票类型txt" in item[
                        "feeTypeForm"] else "",
                    # 不含税金额
                    "jebhs": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) - float(
                        item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item["feeTypeForm"] else float(
                        item["feeTypeForm"]["amount"]["standard"]),
                    # 税额
                    "se": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item[
                        "feeTypeForm"] else 0,
                    # 费用小计
                    "fyxj": lambda item: float(item["feeTypeForm"]["amount"]["standard"]),
                    # 发票附件
                    "fj": lambda item: handle_invoices(item["feeTypeForm"]["invoiceForm"]["invoices"]) if (
                            "invoiceForm" in item["feeTypeForm"] and "invoices" in item["feeTypeForm"][
                        "invoiceForm"]) else "",
                    # 相关出差流程
                    "xgccsq": lambda item: item["feeTypeForm"]["u_OA出差流程ID"] if "u_OA出差流程ID" in item[
                        "feeTypeForm"] else "",
                },
            },
        },
    },
    "私车公用报销单": {
        "workflowId": oa.WORKFLOW_ID_MAP["油卡充值申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["expenseDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 报销类型
            "bxlx": lambda form: fuelcard_map[get_dimension_name(form["u_私车公用报销类型"])],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
            # 备注
            "bz": lambda form: form["description"],
            # 合计金额
            "hjje": lambda form: float(form["details"][0]["feeTypeForm"]["amount"]["standard"]),
            # 最终补贴金额
            "zzbtje": lambda form: float(form["details"][0]["feeTypeForm"]["amount"]["standard"]),
            # 相关出差申请（特殊处理）
            "xgccsq": lambda form: form["u_OA流程ID"] if "u_OA流程ID" in form else None,
            # 相关立项申请
            "xglxsq": lambda form: form["u_项目ID"] if "u_项目ID" in form else None,

        },
        "detailData": {
            "formtable_main_31_dt1": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: True,
                "field_map": {
                    # 用车日期
                    "ycrq": lambda item: ykb_date_2_oa_date(
                        ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_出发地"][
                            "time"]) if "u_行车记录" in item["feeTypeForm"] else "",
                    # 用车时间
                    "ycsj": lambda item: ykb_date_2_oa_time(
                        ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_出发地"][
                            "time"]) if "u_行车记录" in item["feeTypeForm"] else "",
                    # 返回日期
                    "fhrq": lambda item: ykb_date_2_oa_date(
                        ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_目的地"][
                            "time"]) if "u_行车记录" in item["feeTypeForm"] else "",
                    # 返回时间
                    "jssj": lambda item: ykb_date_2_oa_time(
                        ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_目的地"][
                            "time"]) if "u_行车记录" in item["feeTypeForm"] else "",
                    # 始发地
                    "sfd": lambda item:
                    ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_出发地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 返回地点
                    "fhdd": lambda item:
                    ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])["E_fa10f678286c6d8c8bc0_目的地"][
                        "address"] if "u_行车记录" in item["feeTypeForm"] else "",
                    # 客户名称
                    # "sskh":
                    # 公里数
                    "gls": lambda item: float(ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])[
                                                  "E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 汽油费
                    "qyf": lambda item: float(ykb.get_privatecar_by_id(item["feeTypeForm"]["u_行车记录"])[
                                                  "E_fa10f678286c6d8c8bc0_行驶总里程"]) if "u_行车记录" in item[
                        "feeTypeForm"] else 0,
                    # 所属客户
                    "szkh": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_客户可多选"]) if "u_客户可多选" in item["feeTypeForm"] else "",
                    # 所属供应商
                    "szgys": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_供应商可多选"]) if "u_供应商可多选" in item["feeTypeForm"] else "",
                    # 所属合作伙伴
                    "szhzhb": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in item["feeTypeForm"] else "",
                    # 同行人
                    "txr": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_同行人"]) if "u_同行人" in item[
                        "feeTypeForm"] else "",
                },
            },
        },
    },
    "招待报销单": {
        "workflowId": oa.WORKFLOW_ID_MAP["招待费报销申请流程"],
        "requestName": "title",
        "mainData": {
            # 申请人
            "sqr": lambda form: form["u_申请人ID"],
            # 申请日期
            "sqrq": lambda form: ykb_date_2_oa_date(form["expenseDate"]),
            # 申请部门
            "sqbm": lambda form: form["u_部门编码"],
            # 招待类型
            "zdlx": lambda form: serve_map[get_dimension_name(form["u_招待类型"])],
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 开票主体
            "kpzt": lambda form: form["u_开票主体txt"] if "u_开票主体txt" in form else None,
            # 备注
            "bzsm": lambda form: form["u_备注"],
            # 明细金额合计
            "mxjehj": lambda form: float(form["payMoney"]["standard"]),
            # 本次应付金额
            "bcyfje": lambda form: float(form["payMoney"]["standard"]),
            # 银行卡号
            "yhkh": lambda form: ykb.get_payee_by_id(form["payeeId"])["cardNo"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
        },
        "detailData": {
            "formtable_main_218_dt1": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: True,
                "field_map": {
                    # 费用发生日期
                    "fyfsrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用发生时间
                    "fyfssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["feeDate"]) if "feeDate" in item[
                        "feeTypeForm"] else "",
                    # 费用科目
                    "fykm": lambda item: item["feeType"]["code"] if "feeType" in item else "",
                    # 费用说明
                    "fysm": lambda item: item["feeTypeForm"]["consumptionReasons"] if "consumptionReasons" in item[
                        "feeTypeForm"] else "",
                    # 附件数
                    "zzfjs": lambda item: int(
                        item["feeTypeForm"]["u_附件数"] if "u_附件数" in item["feeTypeForm"] else 0),
                    # 其他附件
                    "qtfj": lambda item: handle_attachments(item["feeTypeForm"]["attachments"]) if "attachments" in
                                                                                                   item[
                                                                                                       "feeTypeForm"] else "",
                    # 发票类型
                    "fplx": lambda item: item["feeTypeForm"]["u_发票类型txt"] if "u_发票类型txt" in item[
                        "feeTypeForm"] else "",
                    # 不含税金额
                    "jebhs": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) - float(
                        item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item["feeTypeForm"] else float(
                        item["feeTypeForm"]["amount"]["standard"]),
                    # 税额
                    "se": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]) if "taxAmount" in item[
                        "feeTypeForm"] else 0,
                    # 费用小计
                    "fyxj": lambda item: float(item["feeTypeForm"]["amount"]["standard"]),
                    # 发票附件
                    "fpfj": lambda item: handle_invoices(item["feeTypeForm"]["invoiceForm"]["invoices"]) if (
                            "invoiceForm" in item["feeTypeForm"] and "invoices" in item["feeTypeForm"][
                        "invoiceForm"]) else "",
                    # 客户名称
                    "khmc": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_客户可多选"]) if "u_客户可多选" in item["feeTypeForm"] else "",
                    # 供应商名称
                    "gysmc": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_供应商可多选"]) if "u_供应商可多选" in item["feeTypeForm"] else "",
                    # 合作伙伴名称
                    "hzhbmc": lambda item: handle_multi_dimension(
                        item["feeTypeForm"]["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in item["feeTypeForm"] else "",
                    # 相关出差流程
                    "xgcclc": lambda item: item["feeTypeForm"]["u_OA出差流程ID"] if "u_OA出差流程ID" in item[
                        "feeTypeForm"] else "",
                    # 相关招待申请
                    "xgzdsq": lambda item: item["feeTypeForm"]["u_OA招待流程ID"] if "u_OA招待流程ID" in item[
                        "feeTypeForm"] else "",
                    # 客户档案URL
                    "khdaurl": lambda item: item["feeTypeForm"]["u_客户档案URL"] if "u_客户档案URL" in item[
                        "feeTypeForm"] else "",
                },
            },
        },
    },
}


def prepare_oa_data(ykb_form, workflow_map, flow_id: str):
    oa_data = {
        "workflowId": workflow_map["workflowId"],
        "requestName": ykb_form[workflow_map["requestName"]],
        "mainData": prepare_main_data(ykb_form, workflow_map, flow_id),
        "detailData": prepare_detail_data(ykb_form, workflow_map),
    }
    return oa_data


def prepare_main_data(ykb_form, workflow_map, flow_id):
    main_data = [{
        "fieldName": "ykbflowld",
        "fieldValue": flow_id,
    }]

    for name, mapper in workflow_map["mainData"].items():
        main_data.append({
            "fieldName": name,
            "fieldValue": mapper(ykb_form),
        })

    return main_data


def prepare_detail_data(ykb_form, workflow_map):
    detail_data = []

    for formtable_main_name, formtable_main_table in workflow_map["detailData"].items():
        oa_detail_table = {
            "tableDBName": formtable_main_name,
            "workflowRequestTableRecords": prepare_detail_records(ykb_form, formtable_main_table),
        }
        detail_data.append(oa_detail_table)

    return detail_data


def prepare_detail_records(ykb_form, formtable_main_table):
    records = []

    # ykb_form[formtable_main_table["ykb_field_name"]: ykb_form["detail"]
    if formtable_main_table["ykb_field_name"] not in ykb_form:
        print(f'ykb中没有对应{formtable_main_table["ykb_field_name"]}的明细表字段名称')
        return records

    for ykb_detail in ykb_form[formtable_main_table["ykb_field_name"]]:
        if formtable_main_table["checker"](ykb_detail):
            record_fields = prepare_record_fields(
                ykb_detail, formtable_main_table["field_map"])
            records.append({
                "recordOrder": 0,
                "workflowRequestTableFields": record_fields,
            })

    return records


def prepare_record_fields(ykb_detail, field_map):
    record_fields = []

    for name, mapper in field_map.items():
        record_fields.append({
            "fieldName": name,
            "fieldValue": mapper(ykb_detail),
        })

    return record_fields


def update_oa_workflow(oa_data, oa_workflow_id, user_id):
    oa_update_data = {
        "mainData": oa_data["mainData"],
        "detailData": oa_data["detailData"],
        # "otherParams": {"src": "save"},
        "requestId": oa_workflow_id,
    }

    # 遍历detailData中的每个表单，并添加"deleteAll" = "1"
    for oa_detail_table in oa_update_data["detailData"]:
        oa_detail_table["deleteAll"] = "1"
    return oa.update_workflow(oa_update_data, user_id)


def sync_flow(flow_id: str, spec_name: str):
    ykb_data = ykb.get_flow_details(flow_id)
    ykb_form = ykb_data["form"]

    if spec_name not in workflow_map_conf:
        return

    workflow_map = workflow_map_conf[spec_name]
    oa_data = prepare_oa_data(ykb_form, workflow_map, flow_id)

    user_id = ykb_form["u_申请人ID"]

    """
    特殊处理差旅报销单和私车公用报销单的逻辑：
    这两个单子在单据中都有一个关联出差申请的字段, 会带出出差申请的"OA流程ID"。而易快报里出差申请单中的"OA流程ID"想要同步带出到差旅报销单/私车公用报销单中, 对应的字段在这两个单据中必须也叫"OA流程ID"。
    因此这两个单子不能拿"OA流程ID"当作判断create_workflow/update_workflow的依据, 而是要拿"OA报销流程ID"当作判断create_workflow/update_workflow的依据。
    """
    if spec_name == "差旅报销单" or spec_name == "私车公用报销单":  # 对应这两个表单的更新操作
        if "u_OA报销流程ID" in ykb_form and ykb_form["u_OA报销流程ID"] != '':
            return update_oa_workflow(oa_data, ykb_form["u_OA报销流程ID"], user_id)
    elif "u_OA流程ID" in ykb_form and ykb_form["u_OA流程ID"] != '':  # 其余的表单的更新操作
        return update_oa_workflow(oa_data, ykb_form["u_OA流程ID"], user_id)
    return oa.create_workflow(oa_data, user_id)


if __name__ == "__main__":
    # sync_flow("ID01vow3pux1Cv", "XXX")
    # sync_flow("ID01v9iEnlZ3YP", "日常费用报销单")
    # sync_flow("ID01u9TFKywdKT", "加班申请单")
    # sync_flow("ID01ua4jQTi0I7", "团建费申请单")
    # sync_flow("ID01y48xqXusAn", "差旅报销单")
    # print(get_dimension_name("ID01te5KrbJSnJ"))
    # print(ykb_date_2_oa_date(1699286400000))
    # print(serve_map['日常招待'])
    # invoices = [
    #     {
    #         "itemIds": [
    #             "ID01v9ierrCoaz"
    #         ],
    #         "taxRate": 0,
    #         "invoiceId": "ID01owxnVpp2h1:031002200411:66950805",
    #         "taxAmount": {
    #             "standard": 2.45,
    #             "standardUnit": "元",
    #             "standardScale": 2,
    #             "standardSymbol": "¥",
    #             "standardNumCode": "156",
    #             "standardStrCode": "CNY"
    #         },
    #         "approveAmount": {
    #             "standard": "84.28",
    #             "standardUnit": "元",
    #             "standardScale": 2,
    #             "standardSymbol": "¥",
    #             "standardNumCode": "156",
    #             "standardStrCode": "CNY"
    #         }
    #     }
    # ]
    # print(handle_invoices(invoices))
    print(ykb_date_2_oa_time(1710205004000))
