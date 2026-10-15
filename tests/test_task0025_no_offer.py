import json
from tools.task0017_official_only import classify

def wrap(value,success=True):
 return json.dumps({"success":success,"errorCode":0,"value":value},ensure_ascii=False).encode()

def test_known_sale_closed_payload_is_not_error():
 cfg={"offLineSaleStatus":1,"onLineSaleStatus":1,"onLineStopMessage":"抱歉，本彩种已停止销售"}
 assert classify(wrap({"vtoolsConfig":cfg}))[0:2]==("no_offer",0)
 assert classify(wrap({"matchInfoList":[]}))[0:2]==("no_offer",0)

def test_missing_match_list_without_sale_closed_is_schema_error():
 assert classify(wrap({"vtoolsConfig":{"onLineSaleStatus":0}}))[0]=="schema_error"
 assert classify(wrap({}))[0]=="schema_error"
 assert classify(wrap({"matchInfoList":"wrong"}))[0]=="schema_error"
 assert classify(wrap({"vtoolsConfig":{"onLineSaleStatus":1}},False))[0]=="source_error"
