"""GraphQL query and mutation strings for the Verisure alarm API."""

# GraphQL queries and mutations (extracted from alarm_client for maintainability)

PANEL_STATUS_QUERY = """
query Status($numinst: String!) {
    xSStatus(numinst: $numinst) {
        status
    }
}
"""

CHECK_ALARM_QUERY = """
query CheckAlarm($numinst: String!, $panel: String!) {
    xSCheckAlarm(numinst: $numinst, panel: $panel) {
        res
        msg
        referenceId
    }
}
"""

ARM_PANEL_MUTATION = """
mutation xSArmPanel(
    $numinst: String!,
    $request: ArmCodeRequest!,
    $panel: String!,
    $currentStatus: String,
    $forceArmingRemoteId: String,
    $armAndLock: Boolean
) {
    xSArmPanel(
        numinst: $numinst
        request: $request
        panel: $panel
        currentStatus: $currentStatus
        forceArmingRemoteId: $forceArmingRemoteId
        armAndLock: $armAndLock
    ) {
        res
        msg
        referenceId
    }
}
"""

ARM_STATUS_QUERY = """
query ArmStatus(
    $numinst: String!,
    $request: ArmCodeRequest,
    $panel: String!,
    $referenceId: String!,
    $counter: Int!,
    $forceArmingRemoteId: String,
    $armAndLock: Boolean
) {
    xSArmStatus(
        numinst: $numinst
        panel: $panel
        referenceId: $referenceId
        counter: $counter
        request: $request
        forceArmingRemoteId: $forceArmingRemoteId
        armAndLock: $armAndLock
    ) {
        res
        msg
        status
        protomResponse
        protomResponseDate
        numinst
        requestId
        error {
            code
            type
            allowForcing
            exceptionsNumber
            referenceId
            suid
        }
        smartlockStatus {
            state
            deviceId
            updatedOnArm
        }
    }
}
"""

DISARM_PANEL_MUTATION = """
mutation xSDisarmPanel(
    $numinst: String!,
    $request: DisarmCodeRequest!,
    $panel: String!
) {
    xSDisarmPanel(numinst: $numinst, request: $request, panel: $panel) {
        res
        msg
        referenceId
    }
}
"""

DISARM_STATUS_QUERY = """
query DisarmStatus(
    $numinst: String!,
    $panel: String!,
    $referenceId: String!,
    $counter: Int!,
    $request: DisarmCodeRequest
) {
    xSDisarmStatus(
        numinst: $numinst
        panel: $panel
        referenceId: $referenceId
        counter: $counter
        request: $request
    ) {
        res
        msg
        status
        protomResponse
        protomResponseDate
        numinst
        requestId
        error {
            code
            type
            allowForcing
            exceptionsNumber
            referenceId
            suid
        }
    }
}
"""

CHECK_ALARM_STATUS_QUERY = """
query CheckAlarmStatus(
    $numinst: String!,
    $idService: String!,
    $panel: String!,
    $referenceId: String!
) {
    xSCheckAlarmStatus(
        numinst: $numinst
        idService: $idService
        panel: $panel
        referenceId: $referenceId
    ) {
        res
        msg
        status
        numinst
        protomResponse
        protomResponseDate
        forcedArmed
    }
}
"""
