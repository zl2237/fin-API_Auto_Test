from flask import Blueprint, jsonify

MARKERS = [
    {"name": "link1", "description": "链路1：新建"},
    {"name": "link2", "description": "链路2：新建、分发"},
    {"name": "link3", "description": "链路3：新建、分发、查询、暂存"},
    {"name": "link4", "description": "链路4：新建、分发、查询、暂存、提交"},
    {"name": "link5", "description": "链路5：新建、分发、查询、暂存、提交、生成子订单"},
    {"name": "link6", "description": "链路6：新建…生成子订单、录费用"},
    {"name": "link7", "description": "链路7：新建…录费用、资产推送审批"},
    {"name": "link8", "description": "链路8：新建…资产推送审批、订单锁定审批"},
    {"name": "link9", "description": "链路9：新建…订单锁定审批、未放款开票申请审批"},
    {"name": "link10", "description": "链路10：新建…未放款开票申请审批、供应商垫付申请审批"},
    {"name": "link11", "description": "链路11：新建…供应商垫付申请审批、生成费用通知单"},
    {"name": "link12", "description": "链路12：新建…生成费用通知单、生成费用确认单"},
    {"name": "link13", "description": "链路13：新建…生成费用确认单、发起应收对账批次"},
    {"name": "link14", "description": "链路14：新建…发起应收对账批次、确认应收对账"},
    {"name": "link15", "description": "链路15：新建…确认应收对账、发起应收开票批次审批"},
    {"name": "link16", "description": "链路16：新建…发起应收开票批次审批、审核生成开票申请"},
    {"name": "link17", "description": "链路17：新建…审核生成开票申请、发票上传与登记"},
    {"name": "link18", "description": "链路18：新建…发票上传与登记、应收核销"},
    {"name": "link19", "description": "链路19：新建…应收核销、发起应付对账批次"},
    {"name": "link20", "description": "链路20：新建…发起应付对账批次、确认应付对账"},
    {"name": "link21", "description": "链路21：新建…确认应付对账、发起应付开票批次申请"},
    {"name": "link22", "description": "链路22：新建…发起应付开票批次申请、应付发票上传与登记"},
    {"name": "link23", "description": "链路23：新建…应付发票上传与登记、发起付款需求"},
    {"name": "link24", "description": "链路24：新建…发起付款需求、审核生成付款单"},
    {"name": "link25", "description": "链路25：新建…审核生成付款单、付款单核销"},
]

bp = Blueprint("markers", __name__)


@bp.route("/api/markers", methods=["GET"])
def list_markers():
    return jsonify({"markers": MARKERS})
