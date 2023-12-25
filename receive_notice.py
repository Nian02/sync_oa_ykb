import traceback

import oa2ykb
import ykb2oa
import ykb
import multiprocessing


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
# def receive_ykb_notice(flowId:str, formSpecification:dict, nodeId:str = "", messageId:str = "", corporationId:str = ""):
#     print(f'flowId:{flowId}, nodeId:{nodeId}, messageId:{messageId}, corporationId:{corporationId}, formSpecification:{formSpecification}')
#     if flowId == "":
#         return {"code":200, "msg":"success"}
#     data = ykb2oa.sync_flow(flowId, formSpecification["specificationName"])
#     return {"code":200, "msg":"success", "data":data}

# @DFF.API('接收易快报通知', timeout=60, api_timeout=60)
# def receive_ykb_notice(flowId:str, formSpecification:dict, nodeId:str = "", messageId:str = "", corporationId:str = ""):
#     print(f'flowId:{flowId}, nodeId:{nodeId}, messageId:{messageId}, corporationId:{corporationId}, formSpecification:{formSpecification}')
#     if flowId == "":
#         return {"code":200, "msg":"success"}

#     # Start a separate process for further processing
#     p = billiard.Process(target=process_ykb_notice, args=(flowId, formSpecification))
#     p.start()

#     return {"code":200, "msg":"success"}

# def process_ykb_notice(flowId:str, formSpecification:dict):
#     try:
#         # ykb.notice_Ebot(flowId, nodeId, "accept", "同意")
#         data = ykb2oa.sync_flow(flowId, formSpecification["specificationName"])# data是OA的id
#         print(data)
#     except Exception as e:
#         action = {
#             "comment": str(e),
#             "name": "freeflow.reject",
#             "resubmitMethod": "FROM_START"
#         }
#         ykb.update_flow_state(flowId, {
#             "approveId": ykb.ZDJ_ID,
#             "action": action
#         })

def receive_ykb_notice(flowId:str, formSpecification:dict, nodeId:str = "", messageId:str = "", corporationId:str = ""):
    print(f'flowId:{flowId}, nodeId:{nodeId}, messageId:{messageId}, corporationId:{corporationId}, formSpecification:{formSpecification}')

    try:
        # ykb.notice_Ebot(flowId, nodeId, "accept", "同意")
        data = ykb2oa.sync_flow(flowId, formSpecification["specificationName"])# data是OA的id
        print(data)
    except Exception as e:
        print(e)
        action = {
            "comment": "同步失败，失败报错：" + str(e),
            "name": "freeflow.reject",
            "resubmitMethod": "FROM_START"
        }
        ykb.update_flow_state(flowId, {
            "approveId": ykb.ZDJ_ID,
            "action": action
        })

# def process_ykb_notice(flowId:str, formSpecification:dict):
    




if __name__ == "__main__":
    receive_ykb_notice("ID01vjoQQBSd9t",{'specificationId': 'ID01oxvkARxDAP:e5e064ef6572a5c037aa2a170696b85a77af526a', 'specificationName': '差旅报销单'},"5CE35AE8-1E2F-4C91-86AD-1B7F87E62F1F","ID01vrwGicxFOD","ID01owxnVpp2h1")
    # print(receive_oa_notice("168", "87301", "601"))
    