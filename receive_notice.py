import traceback

import oa2ykb
import ykb2oa


# @DFF.API('接收OA通知')
def receive_oa_notice(workflowId:str, requestId:str, userId:str, status:str = ""):
    print(f'workflowId:{workflowId}, requestId:{requestId}, userId:{userId}, status:{status}')
    if workflowId in oa2ykb.dimension_item_field_map_conf:
        oa2ykb.sync_dimension_item(workflowId, requestId, userId)
    elif workflowId in oa2ykb.workflow_mapping:
        oa2ykb.update_flow(workflowId, requestId, userId)
    else:
        raise Exception(f"未处理的OA流程ID:{workflowId}")
    return {"code":200, "msg":"success"}


# @DFF.API('接收易快报通知')
def receive_ykb_notice(flowId:str, formSpecification:dict, nodeId:str = "", messageId:str = "", corporationId:str = ""):
    print(f'flowId:{flowId}, nodeId:{nodeId}, messageId:{messageId}, corporationId:{corporationId}, formSpecification:{formSpecification}')
    if flowId == "":
        return {"code":200, "msg":"success"}
    data = ykb2oa.sync_flow(flowId, formSpecification["specificationName"])
    return {"code":200, "msg":"success", "data":data}


if __name__ == "__main__":
    print(receive_ykb_notice("ID01u0aADbUUXR",{
        "specificationId": "",
        "specificationName": "招待费申请"
    }))
    # print(receive_oa_notice("168", "87301", "601"))
    