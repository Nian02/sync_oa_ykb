'''同步OA数据到易快报'''
import oa
import ykb
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

CUSTOMER_DIMENSION_ID = "ID01owxnVpp2h1:客户"
PROVIDER_DIMENSION_ID = "ID01owxnVpp2h1:供应商"
PARTNER_DIMENSION_ID = "ID01owxnVpp2h1:合作伙伴"
INCOME_DIMENSION_MODE_ID = "ID01owxnVpp2h1:收入合同"
EXPENDITURE_DIMENSION_MODE_ID = "ID01owxnVpp2h1:支出合同"
RELEVANT_DIMENSION_MODE_ID = "ID01owxnVpp2h1:相关立项申请"

# 费用类型ID映射，通过这个id可以查询明细表比如expense的specificationId
fee_type_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["薪金支出申请流程"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["采购申请流程"]: "ID01vviQDN7OSH",  # 对公付款
}

# 主表费用类型ID映射，通过这个id可以查询主表的specificationId
specificationId_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "ID01vvkw4qlJ7x",
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "ID01vvkP5k18Qf",
    oa.WORKFLOW_ID_MAP["薪金支出申请流程"]: "ID01vvkP5k18Qf",
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: "ID01vvj29Ns2Av",
    oa.WORKFLOW_ID_MAP["采购申请流程"]: "ID01wBiqmTV183",
}

# 表单名映射
title_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "付款单(有合同)",
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "付款单(无合同)",
    oa.WORKFLOW_ID_MAP["薪金支出申请流程"]: "付款单(无合同)",
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: "云资源返利单",
    oa.WORKFLOW_ID_MAP["采购申请流程"]: "采购申请单",
}

# 返佣方式映射
rebate_map = {
    "0": "银⾏",
    "1": "储值卡",
    "2": "云资源账号",
}

# 返利周期映射
rebate_cycle_map = {
    "0": "季度",
    "1": "半年",
    "2": "年度",
    "3": "月度",
}


def handle_multi_dimension(code: str) -> str:
    if not code:
        return ""
    return ykb.get_dimension_by_code(code)[0]["id"]


# 将时间戳格式转换成 %Y-%m-%d 格式
def oa_date_2_ykb_date(date_str: str) -> int:
    if not date_str:
        return 0
    # 检查日期字符串的长度以确定格式
    if len(date_str) == 7:
        dt = datetime.strptime(date_str, "%Y-%m")  # 将日期字符串转换为datetime对象
    else:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    # 将datetime对象转换为时间戳，并乘以1000得到毫秒级的时间戳
    timestamp = int(time.mktime(dt.timetuple()) * 1000)
    return timestamp


# 通过name获取对应ykb里dimension_name的id
def get_corporationId_by_name(name: str, dimension_name: str) -> str:
    if not name:
        return ""
    form = ykb.get_dimension_by_name(name)
    # 遍历form字段，若字段"dimensionId"的:后面是对应dimension_name比如"法人实体"，则返回该字段的"id"
    for item in form:
        if item["dimensionId"].split(":")[1] == dimension_name:
            return item["id"]
    return ""


# 通过code获取对应ykb里dimension_name的id
def get_corporationId_by_code(code: str, dimension_name: str) -> str:
    if not code:
        return ""
    form = ykb.get_dimension_by_code(code)
    # 遍历form字段，若字段"dimensionId"的:后面是对应dimension_name比如"法人实体"，则返回该字段的"id"
    for item in form:
        if item["dimensionId"].split(":")[1] == dimension_name:
            return item["id"]
    return ""


# 格式化金额
def create_amount_structure(amount: str) -> dict:
    return {
        "standard": amount,
        "standardUnit": "元",
        "standardScale": 2,
        "standardSymbol": "¥",
        "standardNumCode": "156",
        "standardStrCode": "CNY"
    }


# 易快报档案项字段 -> OA流程字段 映射关系
dimension_item_field_map_conf = {
    oa.WORKFLOW_ID_MAP["新客户申请流程"]: {
        "dimensionId": ykb.DIMENSION_ID_MAP["客户"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["khmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["新供应商申请流程"]: {
        "dimensionId": ykb.DIMENSION_ID_MAP["供应商"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["khmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["观测云合作伙伴申请流程"]: {
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"][
            "fieldShowValue"] == "新建" else False,
        "dimensionId": ykb.DIMENSION_ID_MAP["合作伙伴"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["hzhbmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["传统云资源合作伙伴申请流程"]: {
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"][
            "fieldShowValue"] == "新建" else False,
        "dimensionId": ykb.DIMENSION_ID_MAP["合作伙伴"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["khmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["CloudCare云资源大使申请流程"]: {
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"][
            "fieldShowValue"] == "新建" else False,
        "dimensionId": ykb.DIMENSION_ID_MAP["合作伙伴"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["hzhbmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["立项审批流程"]: {
        "dimensionId": ykb.DIMENSION_ID_MAP["项目"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["xmmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["xmbh"]["fieldValue"],
        # "form": {
        #     "projectType": lambda oa_data: oa_data[oa.MAIN_TABLE]["ywlx"]["fieldValue"],
        # },
        # 二级档案
        "child": {
            "dimensionId": ykb.DIMENSION_ID_MAP["项目"],
            # 对应OA项目编码
            "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["xmbh"]["fieldValue"],
            # 对应OA立项流程ID
            "code": lambda oa_data: oa_data["requestId"],
        }
    },
    oa.WORKFLOW_ID_MAP["收入类合同审批"]: {
        "dimensionId": ykb.DIMENSION_ID_MAP["收入合同"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["htmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["htbh"]["fieldValue"],
        # 二级档案
        "child": {
            "dimensionId": ykb.DIMENSION_ID_MAP["收入合同"],
            # 对应OA合同编码
            "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["htbh"]["fieldValue"],
            # 对应OA model数据ID
            "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
        }
    }
}


# OA相关流程数据 -> 易快报档案项
def sync_dimension_item(oa_workflowId: str, oa_requestId: str, oa_userId: str):
    oa_data = oa.get_workflow(oa_workflowId, oa_requestId, oa_userId)

    # 获取字段映射关系
    field_mapper = dimension_item_field_map_conf[oa_workflowId]

    # 构建易快报中新建档案项所需的数据
    if "checker" in field_mapper and field_mapper["checker"](oa_data) == False:
        print("checker False when sync_dimension_item")
        return
    dim_item = {
        "dimensionId": field_mapper["dimensionId"],
        "name": field_mapper["name"](oa_data),
        "code": field_mapper["code"](oa_data),
        "parentId": "",
    }

    # 调用易快报新建档案项接口
    id = ykb.add_dimension_item(dim_item)
    print(id)

    # 如果有二级档案，则创建二级档案
    if "child" in field_mapper:
        child_dim_item = {
            "dimensionId": field_mapper["child"]["dimensionId"],
            "name": field_mapper["child"]["name"](oa_data),
            "code": field_mapper["child"]["code"](oa_data),
            "parentId": id,
        }
        id = ykb.add_dimension_item(child_dim_item)
        print(id)


payment_with_contract_value = {
    "mainData": {
        # 提交人
        "submitterId": lambda form: ykb.get_staff_by_code(form["sqrgh"]["fieldValue"]),
        # "submitterId": lambda form: ykb.get_staff_by_code("SX230502"),
        # 申请人
        # "u_申请人ID": lambda form: form["sqr"]["fieldValue"],
        # 申请部门
        # "u_部门编码": lambda form: form["sqbm"]["fieldValue"],
        # 申请日期
        "expenseDate": lambda form: oa_date_2_ykb_date(form["sqrq"]["fieldValue"]),
        # 供应商名称
        "u_供应商": lambda form: handle_multi_dimension(form["gysmc"]["fieldValue"]),
        # 付款主体
        "法人实体": lambda form: get_corporationId_by_name(form["fpttwf"]["fieldShowValue"], "法人实体"),
        # 合作伙伴名称
        "u_合作伙伴": lambda form: handle_multi_dimension(form["hzhbmc"]["fieldValue"]),
        # 付款编号
        "u_付款编号": lambda form: form["fkbh"]["fieldValue"],
        # PO订单号
        "u_PO订单号": lambda form: form["podd"]["fieldValue"],
        # 对应收款合同编号
        "u_收⼊合同编号": lambda form: form["ydskht"]["fieldValue"],
        # 合同编号
        "u_⽀出合同编号": lambda form: form["htbh"]["fieldValue"],
        # 出纳付款日期
        "u_出纳付款日期": lambda form: oa_date_2_ykb_date(form["fkrq"]["fieldValue"]),
        # 备注说明
        "u_备注": lambda form: form["bzsm"]["fieldValue"],
        # 流程编号
        "u_OA流程编号": lambda form: form["lcbh"]["fieldValue"],

    },
    # 同步到ykb的明细表
    "detailData": {
        # 本次付款金额
        "amount": lambda form: form["bcfkje"]["fieldValue"],
        # 税额
        "taxAmount": lambda form: form["se"]["fieldValue"],
        # 金额/不含税
        "noTaxAmount": lambda form: form["jebhs"]["fieldValue"],
    },
}

# OA相关流程数据 -> 易快报流程数据
workflow_map_conf = {
    # 付款申请流程（有合同）拆分为3个不同的流程，对应同一个同步流程
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: payment_with_contract_value,
    oa.WORKFLOW_ID_MAP["企业运营支出申请"]: payment_with_contract_value,
    oa.WORKFLOW_ID_MAP["合作伙伴结算申请"]: payment_with_contract_value,

    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: {
        "mainData": {
            # 提交人
            "submitterId": lambda form: ykb.get_staff_by_code(form["sqrgh"]["fieldValue"]),
            # "submitterId": lambda form: ykb.get_staff_by_code("SX230502"),
            # 申请日期
            "expenseDate": lambda form: oa_date_2_ykb_date(form["sqrq"]["fieldValue"]),
            # 供应商名称
            "u_供应商": lambda form: handle_multi_dimension(form["gysmc"]["fieldValue"]),
            # 付款主体
            "法人实体": lambda form: get_corporationId_by_name(form["fpttwf"]["fieldShowValue"], "法人实体"),
            # 付款编号
            "u_付款编号": lambda form: form["fkbh"]["fieldValue"],
            # 出纳付款日期
            "u_出纳付款日期": lambda form: oa_date_2_ykb_date(form["fkrq"]["fieldValue"]),
            # 付款事由
            "u_备注": lambda form: form["fksy"]["fieldValue"],
            # 流程编号
            "u_OA流程编号": lambda form: form["lcbh"]["fieldValue"],
        },
        "detailData": {
            # 本次付款金额
            "amount": lambda form: form["jexe"]["fieldValue"],
            # 税额
            "taxAmount": lambda form: form["se"]["fieldValue"],
            # 金额/不含税
            "noTaxAmount": lambda form: form["je"]["fieldValue"],
        },
    },
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: {
        "mainData": {
            # 提交人
            "submitterId": lambda form: ykb.get_staff_by_code(form["sqrgh"]["fieldValue"]),
            # "submitterId": lambda form: ykb.get_staff_by_code("SX230502"),
            # 申请日期
            "expenseDate": lambda form: oa_date_2_ykb_date(form["sqrq"]["fieldValue"]),
            # 付款主体
            "法人实体": lambda form: get_corporationId_by_name(form["fpttwf"]["fieldShowValue"], "法人实体"),
            # 客户
            "u_客户": lambda form: get_corporationId_by_name(form["zhmc"]["fieldValue"], "客户"),
            # 付款编号
            "u_付款编号": lambda form: form["fkbh"]["fieldValue"],
            # 返利开始月份
            "u_返利开始月份": lambda form: oa_date_2_ykb_date(form["flnyks"]["fieldValue"]),
            # 返利结束月份
            "u_返利结束月份": lambda form: oa_date_2_ykb_date(form["flnyjs"]["fieldValue"]),
            # 返佣方式
            "u_返佣方式": lambda form: get_corporationId_by_name(rebate_map[form["fyfs"]["fieldValue"]], "返佣⽅式") if form["fyfs"]["fieldValue"] in rebate_map else "",
            # 返利周期
            "u_返利周期": lambda form: rebate_cycle_map[form["htflzq"]["fieldValue"]] if form["htflzq"]["fieldValue"] in rebate_cycle_map else "",
            # 云资源账号
            "u_云资源账号": lambda form: form["yzyzh"]["fieldValue"],
            # 账号UID
            "u_账号UID": lambda form: form["zhuid"]["fieldValue"],
            # 所属分销账号
            "u_所属分销账号": lambda form: form["szfxzh"]["fieldValue"],
            # 出纳付款日期
            "u_出纳付款日期": lambda form: oa_date_2_ykb_date(form["cnfkrq"]["fieldValue"]),
            # 付款事由
            "u_备注": lambda form: form["fksy"]["fieldValue"],
            # 流程编号
            "u_OA流程编号": lambda form: form["lcbh"]["fieldValue"],

        },
        "detailData": {
            # 本次付款金额
            "amount": lambda form: form["fkje"]["fieldValue"],
            # 税额
            "taxAmount": lambda form: form["se"]["fieldValue"],
            # 不计税金额
            "noTaxAmount": lambda form: form["je"]["fieldValue"],
        },
    },
    oa.WORKFLOW_ID_MAP["采购申请流程"]: {
        "mainData": {
            # 提交人
            "submitterId": lambda form: ykb.get_staff_by_code(form["sqrgh"]["fieldValue"]),
            # "submitterId": lambda form: ykb.get_staff_by_code("SX230502"),
            # 申请日期
            "requisitionDate": lambda form: oa_date_2_ykb_date(form["sqrq"]["fieldValue"]),
            # 备注说明
            "u_备注": lambda form: form["sgyy"]["fieldValue"],
            # 流程编号
            "u_OA流程编号": lambda form: form["lcbh"]["fieldValue"],
        },
        "detailData": {
            # 申请金额
            "amount": lambda form: form["je"]["fieldValue"],
        },
    },
}

multi_workflow_map_conf = {
    oa.WORKFLOW_ID_MAP["薪金支出申请流程"]: {
        "mainData": {
            # 申请日期
            "expenseDate": lambda form: oa_date_2_ykb_date(form[oa.MAIN_TABLE]["sqrq"]["fieldValue"]),
            # 出纳付款日期
            "u_出纳付款日期": lambda form: oa_date_2_ykb_date(form[oa.MAIN_TABLE]["cnfkrq"]["fieldValue"]),
            # 付款事由
            "u_备注": lambda form: form[oa.MAIN_TABLE]["fksy"]["fieldValue"],
            # 流程编号
            "u_OA流程编号": lambda form: form[oa.MAIN_TABLE]["lcbh"]["fieldValue"],
            # 申请人
            "submitterId": lambda form: ykb.get_staff_by_code(form[oa.DETAIL_TABLES]["ysbmfzrgh"]["fieldValue"]),
            # "submitterId": lambda form: ykb.get_staff_by_code("SX230502"),
            # "submitterId": lambda form: ykb.get_staff_by_code("00000602"),
            # 申请部门
            "expenseDepartment": lambda form:
            ykb.get_department_by_id(
                form[oa.DETAIL_TABLES]["ysbmid"]["fieldValue"], "code")["id"],
        },
        "detailData": {
            # 申请金额
            "amount": lambda form: form[oa.DETAIL_TABLES]["zyje"]["fieldValue"],
        },
    },
}

"""
差旅报销单和私车公用报销单存储对应OA的流程ID的字段是u_OA报销流程ID
"""
workflow_mapping = {
    oa.WORKFLOW_ID_MAP["出差申请流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["招待费申请流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["出差周末加班补贴申请流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["部门活动申请流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["差旅费用报销流程"]: "u_OA报销流程ID",
    oa.WORKFLOW_ID_MAP["日常费用报销流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["日常项目报销流程"]: "u_OA流程ID",
    oa.WORKFLOW_ID_MAP["油卡充值申请流程"]: "u_OA报销流程ID",
    oa.WORKFLOW_ID_MAP["招待费报销申请流程"]: "u_OA流程ID",
}


def update_flow(oa_workflowId: str, oa_requestId: str, oa_userId: str, oa_status: str):
    oa_data = oa.get_workflow(oa_workflowId, oa_requestId, oa_userId)
    ykb_flowid = oa_data[oa.MAIN_TABLE]["ykbflowld"]["fieldValue"]

    if ykb_flowid == None or ykb_flowid == "":
        raise Exception("ykbflowld字段值为空")
    form = {"u_流程编号": oa_data[oa.MAIN_TABLE]["lcbh"]["fieldValue"]}
    # if oa_workflowId == oa.WORKFLOW_ID_MAP["出差申请流程"]:
    #     form["u_OA出差流程ID"] = oa_data["requestId"]
    if (workflow_mapping.get(oa_workflowId) != None):
        form[workflow_mapping.get(oa_workflowId)] = oa_data["requestId"]
    # 若修改人ID设置成员工自己，在提交申请后，可以自己在易快报审批自己的单据，因此修改人ID暂时定为董君ID
    # ykb_data = ykb.get_flow_details(ykb_flowid)
    # ykb_form = ykb_data["form"]
    # id = ykb_form["submitterId"]
    action = {}
    if oa_status == "archived":
        action = {
            "comment": "OA批准",
            "name": "freeflow.agree",
        }
    elif oa_status == "withdrawed":
        action = {
            "comment": "OA退回",
            "name": "freeflow.reject",
            "resubmitMethod": "FROM_START"
        }
    ykb.update_flow_data(ykb_flowid, ykb.ZDJ_ID, {"form": form})
    ykb.update_flow_state(ykb_flowid, {
        "approveId": ykb.ZDJ_ID,
        "action": action
    })


def prepare_ykb_data(oa_data, oa_workflowId):
    ykb_data = {
        "form": {
            "details": prepare_detail_data(oa_data, oa_workflowId),
        }
    }
    # 在form表单里添加字段，相当于是mainTable部分
    for name, mapper in workflow_map_conf[oa_workflowId]["mainData"].items():
        ykb_data["form"][name] = mapper(oa_data[oa.MAIN_TABLE])
    # 添加其余的字段
    ykb_data["form"]["title"] = title_map[oa_workflowId]
    ykb_data["form"]["specificationId"] = ykb.get_specification_by_id(
        specificationId_map[oa_workflowId])["id"]
    ykb_data["form"]["u_OA流程ID"] = oa_data["requestId"]

    return ykb_data


def prepare_multi_data(oa_data, oa_workflowId):
    ykb_data = {
        "form": {
            "details": prepare_multi_detail_data(oa_data, oa_workflowId),
        }
    }
    # 在form表单里添加字段，相当于是mainTable部分
    for name, mapper in multi_workflow_map_conf[oa_workflowId]["mainData"].items():
        ykb_data["form"][name] = mapper(oa_data)
    # 添加其余的字段
    ykb_data["form"]["title"] = title_map[oa_workflowId]
    ykb_data["form"]["specificationId"] = ykb.get_specification_by_id(
        specificationId_map[oa_workflowId])["id"]
    ykb_data["form"]["u_OA流程ID"] = oa_data["requestId"]

    return ykb_data


def prepare_detail_data(oa_data, oa_workflowId):
    details = []
    # 遍历传过来的oa表单的"detailTables"的表单
    # for table in oa_data[oa.DETAIL_TABLES]:
    #     detail = {
    #         "feeTypeId": fee_type_map[oa_workflowId],
    #         "specificationId": ykb.get_specificationId_by_id(fee_type_map[oa_workflowId]),
    #         "feeTypeForm": {},
    #     }
    #     for name, mapper in workflow_map_conf[oa_workflowId]["detailData"].items():
    #         amount = mapper(table)
    #         detail["feeTypeForm"][name] = create_amount_structure(amount)
    #     details.append(detail)

    # 如果oa_workflowId是"付款申请流程（有合同）"，其oa_data是没有明细表的，要将其主表的字段值赋给明细表的字段
    # if oa_workflowId == oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]:
    detail = {
        "feeTypeId": fee_type_map[oa_workflowId],
        "specificationId": ykb.get_specificationId_by_id(fee_type_map[oa_workflowId],
                                                         "requisitionSpecificationId") if oa_workflowId ==
        oa.WORKFLOW_ID_MAP[
            "采购申请流程"]
        else ykb.get_specificationId_by_id(fee_type_map[oa_workflowId], "expenseSpecificationId"),
        "feeTypeForm": {},
    }
    for name, mapper in workflow_map_conf[oa_workflowId]["detailData"].items():
        if oa_workflowId == oa.WORKFLOW_ID_MAP["采购申请流程"]:
            amount = mapper(oa_data[oa.DETAIL_TABLES][0])
        else:
            amount = mapper(oa_data[oa.MAIN_TABLE])
        detail["feeTypeForm"][name] = create_amount_structure(amount)
    details.append(detail)

    return details


def prepare_multi_detail_data(oa_data, oa_workflowId):
    details = []
    detail = {
        "feeTypeId": fee_type_map[oa_workflowId],
        "specificationId": ykb.get_specificationId_by_id(fee_type_map[oa_workflowId], "expenseSpecificationId"),
        "feeTypeForm": {},
    }
    for name, mapper in multi_workflow_map_conf[oa_workflowId]["detailData"].items():
        amount = mapper(oa_data)
        detail["feeTypeForm"][name] = create_amount_structure(amount)
        detail["feeTypeForm"]["taxAmount"] = create_amount_structure("0")
        detail["feeTypeForm"]["noTaxAmount"] = create_amount_structure("0")

    details.append(detail)

    return details


def sync_flow(oa_workflowId: str, oa_requestId: str, oa_userId: str, oa_status: str):
    oa_data = oa.get_workflow(oa_workflowId, oa_requestId, oa_userId)
    if oa_workflowId not in workflow_map_conf:
        return
    ykb_data = prepare_ykb_data(oa_data, oa_workflowId)
    return ykb.create_flow_data("true", ykb_data)


def sync_multi_flow(oa_workflowId: str, oa_requestId: str, oa_userId: str, oa_status: str):
    oa_data = oa.get_multi_workflow(oa_workflowId, oa_requestId, oa_userId)
    if oa_workflowId not in multi_workflow_map_conf:
        return
    # 将oa明细表的多个条目在ykb中创建多个单据

    # 对应薪金支出申请流程的formtable_main_235_dt2
    detailtables = oa_data[oa.DETAIL_TABLES][1]
    for item in detailtables:
        if item["ysbmid"]["fieldValue"] == "无":
            continue
        oa_data_item = oa_data
        oa_data_item[oa.DETAIL_TABLES] = item
        ykb_data = prepare_multi_data(oa_data_item, oa_workflowId)
        ykb.create_flow_data("true", ykb_data)


# ----------------------------------------同步档案项---------------------------------------------


# 装饰器函数，当使用 @func_log 装饰一个函数时，会自动调用wrapper，打印日志
def func_log(func):
    def wrapper(*args, **kwargs):
        print(f"++++++++++++ {func.__name__} begin ++++++++++++")
        print(f"===> args:{args}, kwargs:{kwargs}")
        ret = func(*args, **kwargs)
        print(f"<=== return:{ret}")
        print(f"------------ {func.__name__} end ------------")
        return ret

    return wrapper


@func_log
def sync_customer_mode_data():
    # 获取客户mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    customers = oa.get_customer_mode_data(0, oa.get_customer_count(),
                                          conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    for customer in customers:
        data = {
            "name": customer["khmc"]["value"],
            "code": customer["id"],
            "parentId": "",
        }
        id = get_corporationId_by_code(data["code"], "客户")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(CUSTOMER_DIMENSION_ID, data_list)
    else:
        print("没有需要同步的客户mode数据")


@func_log
def sync_provider_mode_data():
    # 获取供应商mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    providers = oa.get_provider_mode_data(0, oa.get_provider_count(),
                                          conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    for provider in providers:
        data = {
            "name": provider["gysmc"]["value"],
            "code": provider["id"],
            "parentId": "",
        }
        id = get_corporationId_by_code(data["code"], "供应商")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(PROVIDER_DIMENSION_ID, data_list)
    else:
        print("没有需要同步的供应商mode数据")


@func_log
def sync_partner_mode_data():
    # 获取合作伙伴mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    partners = oa.get_partner_mode_data(0, oa.get_partner_count(),
                                        conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    for partner in partners:
        data = {
            "name": partner["hzhbmc"]["value"],
            "code": partner["id"],
            "parentId": "",
        }
        id = get_corporationId_by_code(data["code"], "合作伙伴")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(PARTNER_DIMENSION_ID, data_list)
    else:
        print("没有需要同步的合作伙伴mode数据")


@func_log
def sync_income_contract_mode_data():
    # 获取收入合同mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    income_contracts = oa.get_income_contract_mode_data(0, oa.get_income_contract_count(),
                                                        conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    children_data_list = []
    code_id_dict = {}  # 存储合同的id值，以该合同的合同编号作为key
    for income_contract in income_contracts:
        data = {
            "name": income_contract["htmc"]["value"],  # 合同名称
            "code": income_contract["htbh"]["value"],  # 合同编号
            "parentId": "",
        }
        code_id_dict[data["code"]] = income_contract["id"]
        id = get_corporationId_by_code(data["code"], "收入合同")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(INCOME_DIMENSION_MODE_ID, data_list)
        # 为刚刚添加的档案项添加子项
        for data in data_list:
            id = get_corporationId_by_code(data["code"], "收入合同")
            child_data = {
                "name": data["code"],  # 合同编号
                "code": code_id_dict[data["code"]],  # 合同id值
                "parentId": id,  # 档案项的id值
            }
            children_data_list.append(child_data)
        ykb.add_dimension_items_by_batch(
            INCOME_DIMENSION_MODE_ID, children_data_list)
    else:
        print("没有需要同步的收入合同mode数据")


@func_log
def sync_expenditure_contract_mode_data():
    # 获取支出合同mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    expenditure_contracts = oa.get_expenditure_contract_mode_data(0, oa.get_expenditure_contract_count(),
                                                                  conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    children_data_list = []
    code_id_dict = {}  # 存储合同的id值，以该合同的合同编号作为key
    for expenditure_contract in expenditure_contracts:
        data = {
            "name": expenditure_contract["htmc"]["value"],  # 合同名称
            "code": expenditure_contract["htbh"]["value"],  # 合同编号
            "parentId": "",
        }
        code_id_dict[data["code"]] = expenditure_contract["id"]
        id = get_corporationId_by_code(data["code"], "支出合同")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(
            EXPENDITURE_DIMENSION_MODE_ID, data_list)
        # 为刚刚添加的档案项添加子项
        for data in data_list:
            id = get_corporationId_by_code(data["code"], "支出合同")
            child_data = {
                "name": data["code"],  # 合同编号
                "code": code_id_dict[data["code"]],  # 合同id值
                "parentId": id,  # 档案项的id值
            }
            children_data_list.append(child_data)
        ykb.add_dimension_items_by_batch(
            EXPENDITURE_DIMENSION_MODE_ID, children_data_list)
    else:
        print("没有需要同步的支出合同mode数据")


@func_log
def sync_relevant_project_mode_data():
    # 获取相关立项申请mode数据
    start_date = (datetime.today() - relativedelta(days=2)
                  ).strftime("%Y-%m-%d")
    expenditure_contracts = oa.get_relevant_project_mode_data(0, oa.get_relevant_project_count(),
                                                              conditions=f'modedatacreatedate > \'{start_date}\'')
    data_list = []
    children_data_list = []
    code_id_dict = {}  # 存储OA立项流程值，以该项目的项目编号作为key
    for expenditure_contract in expenditure_contracts:
        data = {
            "name": expenditure_contract["xmmc"]["value"],  # 项目名称
            "code": expenditure_contract["xmbh"]["value"],  # 项目编号
            "parentId": "",
        }
        code_id_dict[data["code"]] = expenditure_contract["oalxlcid"]["value"]
        id = get_corporationId_by_code(data["code"], "相关立项申请")
        # 说明该档案项没有存储过，且name和code不为空
        if id == "" and data["name"] and data["code"]:
            data_list.append(data)
        # 跳过这个档案项
        else:
            continue
    if len(data_list) > 0:
        ykb.add_dimension_items_by_batch(RELEVANT_DIMENSION_MODE_ID, data_list)
        # 为刚刚添加的档案项添加子项
        for data in data_list:
            id = get_corporationId_by_code(data["code"], "相关立项申请")
            child_data = {
                "name": data["code"],  # 项目编号
                "code": code_id_dict[data["code"]],  # OA立项流程ID
                "parentId": id,  # 档案项的id值
            }
            children_data_list.append(child_data)
        ykb.add_dimension_items_by_batch(
            RELEVANT_DIMENSION_MODE_ID, children_data_list)
    else:
        print("没有需要同步的相关立项申请mode数据")


if __name__ == "__main__":
    # sync_relevant_project_mode_data()
    # 	ZY20231222617	ZY20240219654
    # sync_expenditure_contract_mode_data()
    # sync_income_contract_mode_data()
    # sync_provider_mode_data()
    # sync_partner_mode_data()
    # sync_customer_mode_data()
    # print(ykb.get_staff_by_code("SX230502"))
    # print(get_corporationId_by_name("上海观测未来信息技术有限公司北京分公司"))
    # oa.get_multi_workflow("222", "98520", "601")
    oa.get_workflow("143", "93036", "1010")
    # sync_multi_flow("222", "98520", "601", "archived")
    # update_flow("81", "98162", "844", "withdrawed")
    # get_corporationId_by_name("友邦人寿23年9-11月+pe运维服务项目", "相关立项申请")
