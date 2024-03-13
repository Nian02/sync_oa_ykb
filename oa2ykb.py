'''同步OA数据到易快报'''
import oa
import ykb
import time
from datetime import datetime

# 费用类型ID映射，通过这个id可以查询明细表比如expense的specificationId
fee_type_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: "ID01vviQDN7OSH",  # 对公付款
    oa.WORKFLOW_ID_MAP["采购申请流程"]: "ID01vviQDN7OSH",  # 对公付款
}

# 主表费用类型ID映射
specificationId_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "ID01vvkw4qlJ7x:dc1aee0a9fb5033cc40de5c7653ea475495d8511",
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "ID01vvkP5k18Qf:cdafd0125a88866fcf83a7cde223d17558d0415c",
    oa.WORKFLOW_ID_MAP["云资源返利申请流流程"]: "ID01vvj29Ns2Av:f831bbbc7f180a0d1f1801c79b721aa675329670",
    oa.WORKFLOW_ID_MAP["采购申请流程"]: "ID01vviQDN7OSH:requisition:0080529e1ee89b5acdcd3eac730ce0458b387513",
}

# 表单名映射
title_map = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: "付款单(有合同)",
    oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"]: "付款单(无合同)",
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
    return ykb.get_dimension_by_code(code)["id"]


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


# OA相关流程数据 -> 易快报流程数据
workflow_map_conf = {
    oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"]: {
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
    },
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
            "u_返佣方式": lambda form: get_corporationId_by_name(rebate_map[form["fyfs"]["fieldValue"]], "返佣⽅式"),
            # 返利周期
            "u_返利周期": lambda form: rebate_cycle_map[form["htflzq"]["fieldValue"]],
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
            "expenseDate": lambda form: oa_date_2_ykb_date(form["sqrq"]["fieldValue"]),
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
    ykb_data["form"]["specificationId"] = specificationId_map[oa_workflowId]
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
        "specificationId": ykb.get_specificationId_by_id(fee_type_map[oa_workflowId]),
        "feeTypeForm": {},
    }
    for name, mapper in workflow_map_conf[oa_workflowId]["detailData"].items():
        amount = mapper(oa_data[oa.MAIN_TABLE])
        detail["feeTypeForm"][name] = create_amount_structure(amount)
    details.append(detail)

    return details


def sync_flow(oa_workflowId: str, oa_requestId: str, oa_userId: str, oa_status: str):
    oa_data = oa.get_workflow(oa_workflowId, oa_requestId, oa_userId)
    if oa_workflowId not in workflow_map_conf:
        return
    ykb_data = prepare_ykb_data(oa_data, oa_workflowId)
    return ykb.create_flow_data("true", ykb_data)


if __name__ == "__main__":
    update_flow("81","93969","601","withdrawed")
    # print("201" in workflow_mapping)
    # print(get_corporationId_by_name("上海观测未来信息技术有限公司北京分公司"))
    # sync_flow("143", "92585", "57", "archived")
