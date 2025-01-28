
SIP_VERSION = '2.0'
USER_AGENT = 'DnakeVoip v1.0'

class CSeq:
    OPTION = 20
    EVENT = 20
    MESSAGE = 20

class METHOD:
    MESSAGE = 'MESSAGE'

class PARAMS:
    PARAMS = 'params'
    EVENT_URL = 'event_url'
    TO = 'to'
    ELEV = 'elev'
    DIRECT = 'direct'
    BUILD = 'build'
    UNIT = 'unit'
    FLOOR = 'floor'
    FAMILY = 'family'
    APP = 'app'
    EVENT = 'event'
    HOST = 'host'

class EVENT:
    APPOINT = 'appoint'
    UNLOCK = 'unlock'
    PERMIT = 'permit'

class EVENT_URL:
    JOIN = '/elev/join'
    APPOINY = '/elev/appoint'
    UNLOCK = '/talk/unlock'
    PERMIT = '/elev/permit'

class APP:
    ELEV = 'elev'
    TALK = 'talk'

class SIP_HEADER:
    def MESSAGE(src_id, src_ip, src_port, dst_id, dst_ip, dst_port, branch, tag, call_id, body_length):
        return {
            "Via" : f"SIP/{SIP_VERSION}/UDP {src_ip}:{src_port};rport;branch={branch}",
            "From" : f"<sip:{src_id}@{src_ip}:{src_port}>;tag={tag}",
            "To" : f"<sip:{dst_id}@{dst_ip}:{dst_port}>",
            "Call-ID" : call_id,
            "CSeq" : f"{CSeq.MESSAGE} {METHOD.MESSAGE}",
            "Content-Type" : "text/plain",
            "Max-Forwards" : 70,
            "User-Agent" : USER_AGENT,
            "Content-Length" : body_length
        }

class SIP_LINE:
    def MESSAGE(dst_id, dst_ip, dst_port):
        return f'{METHOD.MESSAGE} sip:{dst_id}@{dst_ip}:{dst_port} SIP/{SIP_VERSION}'

class SIP_BODY:
    def JOIN(): 
        return {
            PARAMS.EVENT_URL: EVENT_URL.JOIN
        }
    def APPOINT(dst_id, dst_ip, dst_port, elev, direct, build, unit, floor, family):
        return {
            PARAMS.TO: f'sip:{dst_id}@{dst_ip}:{dst_port}',
            PARAMS.ELEV: elev,
            PARAMS.DIRECT: direct,
            PARAMS.BUILD: build,
            PARAMS.UNIT: unit,
            PARAMS.FLOOR: floor,
            PARAMS.FAMILY: family,
            PARAMS.APP: APP.ELEV,
            PARAMS.EVENT: EVENT.APPOINT,
            PARAMS.EVENT_URL: EVENT_URL.APPOINY
        }
    def UNLOCK(src_id, build, unit, floor, family):
        return {
            PARAMS.APP: APP.TALK,
            PARAMS.EVENT: EVENT.UNLOCK,
            PARAMS.EVENT_URL: EVENT_URL.UNLOCK,
            PARAMS.HOST: src_id,
            PARAMS.BUILD: build,
            PARAMS.UNIT: unit,
            PARAMS.FLOOR: floor,
            PARAMS.FAMILY: family
        }
    def PERMIT(dst_id, dst_ip, dst_port, elev, build, unit, floor, family):
        return {
            PARAMS.APP: APP.ELEV,
            PARAMS.EVENT: EVENT.PERMIT,
            PARAMS.EVENT_URL: EVENT_URL.PERMIT,
            PARAMS.TO: f'sip:{dst_id}@{dst_ip}:{dst_port}',
            PARAMS.ELEV: elev,
            PARAMS.BUILD: build,
            PARAMS.UNIT: unit,
            PARAMS.FLOOR: floor,
            PARAMS.FAMILY: family
        }
