'''同步OA数据到易快报'''
import oa
import ykb


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
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"]["fieldShowValue"] == "新建"  else False,
        "dimensionId": ykb.DIMENSION_ID_MAP["合作伙伴"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["hzhbmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["传统云资源合作伙伴申请流程"]: {
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"]["fieldShowValue"] == "新建"  else False,
        "dimensionId": ykb.DIMENSION_ID_MAP["合作伙伴"],
        "name": lambda oa_data: oa_data[oa.MAIN_TABLE]["khmc"]["fieldValue"],
        "code": lambda oa_data: oa_data[oa.MAIN_TABLE]["jmsjid"]["fieldValue"],
    },
    oa.WORKFLOW_ID_MAP["CloudCare云资源大使申请流程"]: {
        "checker": lambda oa_data: True if "sqlx" in oa_data[oa.MAIN_TABLE] and oa_data[oa.MAIN_TABLE]["sqlx"]["fieldShowValue"] == "新建"  else False,
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
def sync_dimension_item(oa_workflowId: str, oa_requestId: str, oa_userId:str):
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


# update_ykb_flow_state_oa_workflowId = {
#     oa.WORKFLOW_ID_MAP["出差申请流程"],
#     oa.WORKFLOW_ID_MAP["招待费申请流程"],
#     oa.WORKFLOW_ID_MAP["出差周末加班补贴申请流程"],
#     oa.WORKFLOW_ID_MAP["差旅费用报销流程"],
#     oa.WORKFLOW_ID_MAP["部门活动申请流程"],
#     oa.WORKFLOW_ID_MAP["日常费用报销流程"],
#     oa.WORKFLOW_ID_MAP["日常项目报销流程"],
#     oa.WORKFLOW_ID_MAP["油卡充值申请流程"],
#     oa.WORKFLOW_ID_MAP["团队共享激励报销申请流程"],
#     oa.WORKFLOW_ID_MAP["付款申请流程（无合同）"],
#     oa.WORKFLOW_ID_MAP["付款申请流程（有合同）"],
# }

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

def update_flow(oa_workflowId: str, oa_requestId: str, oa_userId:str, oa_status:str):
    oa_data = oa.get_workflow(oa_workflowId, oa_requestId, oa_userId)
    ykb_flowid = oa_data[oa.MAIN_TABLE]["ykbflowld"]["fieldValue"]
    if ykb_flowid == None or ykb_flowid == "":
        raise Exception("ykbflowld字段值为空")
    form = {"u_流程编号": oa_data[oa.MAIN_TABLE]["lcbh"]["fieldValue"]}
    # if oa_workflowId == oa.WORKFLOW_ID_MAP["出差申请流程"]:
    #     form["u_OA出差流程ID"] = oa_data["requestId"]
    if(workflow_mapping.get(oa_workflowId) != None):
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


if __name__ == "__main__":
    # update_flow("199","84023","601")
    # print("201" in workflow_mapping)
    update_flow("199","88917","57","archived")
