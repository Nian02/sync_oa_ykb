'''同步易快报数据到OA'''
import time
import json
from datetime import datetime
import base64
import requests

import oa
import ykb

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


# 将时间戳格式转换成 %Y-%m-%d 格式
def ykb_date_2_oa_date(timestamp: int) -> str:
    # 毫秒级时间戳要除于1000
    return time.strftime("%Y-%m-%d", time.localtime(timestamp/1000))


# 将时间戳格式转换成 %H:%M 格式
def ykb_date_2_oa_time(timestamp: int) -> str:
    # 毫秒级时间戳要除于1000
    return time.strftime("%H:%M", time.localtime(timestamp/1000))


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
            "filePath": f"base64: {base64.b64encode(r.content).decode()}",
            "fileName": f["key"],
        })
    return oa_files


# 获取name
def get_dimension_name(id:str):
    return ykb.get_dimension_by_id(id)["name"]

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
        oa_files.append({
            "filePath": f"base64: {base64.b64encode(r.content).decode()}",
            "fileName": item["fileName"],
        })
    return oa_files


# OA流程字段: 易快报单据字段 映射关系
workflow_field_map_conf = {
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
            "dxlx": lambda form: form["u_客户类型多选"][0] if "u_客户类型多选" in form else None,
            # 客户名称
            "khmc": lambda form: handle_multi_dimension(form["u_客户可多选"]) if "u_客户可多选" in form else None,
            # 供应商名称
            "gysmc": lambda form: handle_multi_dimension(form["u_供应商可多选"]) if "u_供应商可多选" in form else None,
            # 合作伙伴名称
            "hzhbmc": lambda form: handle_multi_dimension(form["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in form else None,
            # 客户编号
            # "khbh": lambda form: form["u_客户可多选"],
            # 供应商编号
            # "gysbh": lambda form: form["法人实体"],
            # 合作伙伴编号
            # "hzhbbh": None,
            # 出差天数
            "ccts": lambda form: (datetime.fromtimestamp(form["u_出差起止日期"]["end"]/1000) -
                                  datetime.fromtimestamp(form["u_出差起止日期"]["start"]/1000)).days,
            # 劳动关系
            "ldgx": lambda form: form["u_劳动关系txt"],
            # 出差性质
            "ccxz": lambda form: form["u_出差性质"],
            # 收入合同
            "srht": lambda form: form["u_model数据ID"] if "u_model数据ID" in form else None,
            # 收入合同编号
            "srhtbh": lambda form: form["u_收⼊合同编号"] if "u_收⼊合同编号" in form else None,
            # 相关立项申请
            "xglxlc": lambda form: form["u_OA⽴项流程ID"] if "u_OA⽴项流程ID" in form else None,
            # 项目编号
            "xmbhx": lambda form: form["u_项目编号"] if "u_项目编号" in form else None,
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
        },
        "detailData": {
            "formtable_main_53_dt1": {
                "ykb_field_name": "u_行程规划",  # 该明细表对应在易快报数据中的字段
                "checker": lambda item: True,  # 检测易快报明细数据项是否满足要求
                "field_map": {
                    # 出行方式
                    "cxfsx": lambda item: route_map[item["dataLinkTemplateId"]],
                    # 行程类型
                    "xclxx": lambda item: None,
                    # 出差城市
                    "cccs": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_住宿地"])[0]["label"],
                    # 出发城市
                    "cfcsx": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_出发地"])[0]["label"] if "E_fa1044a29ce187343bc0_出发地" in item["dataLinkForm"] else None,
                    # 目的城市
                    "mdcsx": lambda item: json.loads(item["dataLinkForm"]["E_fa1044a29ce187343bc0_目的地"])[0]["label"] if "E_fa1044a29ce187343bc0_目的地" in item["dataLinkForm"] else None,
                    # 开始日期
                    "ccksrq": lambda item: ykb_date_2_oa_date(item["dataLinkForm"]["E_fa1044a29ce187343bc0_入住日期"]),
                    # 结束日期
                    "ccjsrq": lambda item: ykb_date_2_oa_date(item["dataLinkForm"]["E_fa1044a29ce187343bc0_离店日期"]),
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
            "khmcx": lambda form: handle_multi_dimension(form["u_客户可多选"]) if "u_客户可多选" in form else None,
            # 供应商名称
            "gysmc": lambda form: handle_multi_dimension(form["u_供应商可多选"]) if "u_供应商可多选" in form else None,
            # 合作伙伴名称
            "hzhbmc": lambda form: handle_multi_dimension(form["u_合作伙伴可多选"]) if "u_合作伙伴可多选" in form else None,
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
    "加班申请单": {
        "workflowId": oa.WORKFLOW_ID_MAP["加班申请流程"],
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
                    "ksrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["u_加班起止时间"]["start"]),
                    # 开始时间
                    "kssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["u_加班起止时间"]["start"]),
                    # 结束日期
                    "jsrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["u_加班起止时间"]["end"]),
                    # 结束时间
                    "jssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["u_加班起止时间"]["end"]),
                    # 补贴金额
                    "btje": lambda item: item["feeTypeForm"]["amount"]["standard"],
                    # 具体加班人员
                    "jtjbry": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_具体加班人员"]) if "u_具体加班人员" in item["feeTypeForm"] else None,
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
                    "ksrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["u_活动起止日期"]["start"]),
                    # 开始时间
                    "kssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["u_活动起止日期"]["start"]),
                    # 结束日期
                    "jsrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["u_活动起止日期"]["end"]),
                    # 结束时间
                    "jssj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["u_活动起止日期"]["end"]),
                    # 活动类型
                    "hdlx": lambda item: teamactivity_map[get_dimension_name(item["feeTypeForm"]["u_活动类型"])],
                    # 是否自驾
                    "sfzj": lambda item: yes_or_not_map[get_dimension_name(item["feeTypeForm"]["u_是否"])],
                    # 参与人员
                    "cyry": lambda item: handle_multi_dimension(item["feeTypeForm"]["u_团建人员"]),
                    # 事由说明
                    "sqsy": lambda item: item["feeTypeForm"]["consumptionReasons"],
                    # 活动费用
                    "hdfy": lambda item: item["feeTypeForm"]["amount"]["standardScale"],
                    # 参与人数
                    "cyrs": lambda item: item["feeTypeForm"]["u_人数"],
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
            # 相关出差流程
            "xgcclc": lambda form: form["u_OA出差流程ID"],
            # 备注
            "bz": lambda form: form["description"],
            # 附件上传
            "fjsc": lambda form: handle_attachments(form["attachments"]),
        },
        "detailData": {
            # 明细表2
            "formtable_main_57_dt2": {  # OA中明细表的tableDBName
                "ykb_field_name": "details",  # 该明细表对应在易快报 form 数据中的字段
                "checker": lambda item: True,
                "field_map": {
                    # 费用发生日期
                    "fyrq": lambda item: ykb_date_2_oa_date(item["feeTypeForm"]["feeDate"]),
                    # 费用发生时间
                    "fysj": lambda item: ykb_date_2_oa_time(item["feeTypeForm"]["feeDate"]),
                    # 费用类型
                    "fylxx": lambda item: item["feeType"]["code"],
                    # 费用说明
                    "zysm": lambda item: item["feeTypeForm"]["consumptionReasons"],
                    # 附件数
                    "fpzs": lambda item: int(item["feeTypeForm"]["u_附件数"] if "u_附件数" in item["feeTypeForm"] else 0),
                    # 发票类型
                    "fplx": lambda item: item["feeTypeForm"]["u_发票类型txt"],
                    # 不含税金额
                    "jebhs": lambda item: float(item["feeTypeForm"]["amount"]["standard"]),
                    # 税额
                    "se": lambda item: float(item["feeTypeForm"]["taxAmount"]["standard"]),
                    # 费用小计
                    "fyje": lambda item: float(item["feeTypeForm"]["amount"]["standard"]) + float(item["feeTypeForm"]["taxAmount"]["standard"]),
                    # 发票附件
                    "fjsc": lambda item: handle_invoices(item["feeTypeForm"]["invoiceForm"]["invoices"]),
                    # 火车席别/航空舱位/轮船舱型
                    "hczbhkcw": lambda item: \
                    train_map[item["feeTypeForm"]["u_火车席别"]] if "u_火车席别" in item["feeTypeForm"]\
                    else flight_map[item["feeTypeForm"]["u_航班舱型"]] if "u_航班舱型" in item["feeTypeForm"]\
                    else ship_map[item["feeTypeForm"]["u_轮船舱型"]] if "u_轮船舱型" in item["feeTypeForm"]\
                    else "",
                },
            },
        },
    },
    
}


def sync_flow(flow_id: str, spec_name: str):
    ykb_data = ykb.get_flow_details(flow_id)

    # ykb表单中的form字段数据
    ykb_form = ykb_data["form"]
    # 如果不在字段映射的配置中，报错
    if spec_name not in workflow_field_map_conf:
        raise Exception(f"未定义的表单: {spec_name}")
    # 对应spec_name的字段映射表
    field_map = workflow_field_map_conf[spec_name]
    oa_data = {
        "workflowId": field_map["workflowId"],
        # field_map["requestName"]字段是"title"
        "requestName": ykb_form[field_map["requestName"]],
        "mainData": [],
        "detailData": [],
    }

    # 把易快报 flowID 填到 OA 主表的 ykbflowld 字段中
    oa_data["mainData"].append({
        "fieldName": "ykbflowld",
        "fieldValue": flow_id,
    })

    # 遍历OA主表的字段，找到易快报对应字段
    for name, mapper in field_map["mainData"].items():
        oa_data["mainData"].append({
            "fieldName": name,
            "fieldValue": mapper(ykb_form),
        })
    
    # 遍历OA的明细表（可能有多个比如formtable_main_57_dt2+formtable_main_57_dt3）
    for detail_table_name, detail_table_field_map in field_map["detailData"].items():
        oa_detail_table = {
            "tableDBName": detail_table_name,
            "workflowRequestTableRecords": [],
        }

        # 遍历易快报数据中与该OA明细表对应的明细数据项
        if detail_table_field_map["ykb_field_name"] not in ykb_form:
            print(f'ykb中没有对应{detail_table_field_map["ykb_field_name"]}的明细表字段名称')
            continue
        for ykb_detail in ykb_form[detail_table_field_map["ykb_field_name"]]:
            # 若与当前OA明细表不对应，则跳过
            if not detail_table_field_map["checker"](ykb_detail):
                continue
            oa_detail_table_fields = []
            # 遍历当前OA明细表的字段，找到易快报明细数据项中的对应字段
            for name, mapper in detail_table_field_map["field_map"].items():
                oa_detail_table_fields.append({
                    "fieldName": name,
                    "fieldValue": mapper(ykb_detail),
                })
            # 将明细表记录追加到当前OA明细表中
            oa_detail_table["workflowRequestTableRecords"].append({
                "recordOrder": 0,
                "workflowRequestTableFields": oa_detail_table_fields
            })
        # 将OA明细表追加到OA明细数据中
        oa_data["detailData"].append(oa_detail_table)

    # 调用OA新建流程接口
    # print(json.dumps(oa_data))
    return oa.create_workflow(oa_data)


if __name__ == "__main__":
    # sync_flow("ID01txI5PMNVi7", "出差申请单")
    # sync_flow("ID01u0aADbUUXR", "招待费申请")
    # sync_flow("ID01u9TFKywdKT", "加班申请单")
    sync_flow("ID01ua4jQTi0I7", "团建费申请单")
