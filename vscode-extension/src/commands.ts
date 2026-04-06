export const COMMAND_OPEN_AI_STUDIO = "kortana.openAIStudio";
export const COMMAND_OPEN_DEPLOY_PAGE = "kortana.openDeployPage";
export const COMMAND_UNSEAL_RUNTIME = "kortana.unsealRuntime";
export const COMMAND_CHECK_HEALTH = "kortana.checkHealth";
export const COMMAND_VIEW_METRICS = "kortana.viewMetrics";
export const COMMAND_OPEN_AUTONOMY_AUDIT = "kortana.autonomy.audit.open"; export const COMMAND_KILL_SWITCH = "kortana.killSwitch";
export const DASHBOARD_COMMAND_MAP: Record<string, string> = {
    openAIStudio: COMMAND_OPEN_AI_STUDIO,
    openDeployPage: COMMAND_OPEN_DEPLOY_PAGE,
    unsealRuntime: COMMAND_UNSEAL_RUNTIME,
    checkHealth: COMMAND_CHECK_HEALTH,
    viewMetrics: COMMAND_VIEW_METRICS,
    openAutonomyAudit: COMMAND_OPEN_AUTONOMY_AUDIT,
    killSwitch: COMMAND_KILL_SWITCH,
    [COMMAND_OPEN_AI_STUDIO]: COMMAND_OPEN_AI_STUDIO,
    [COMMAND_OPEN_DEPLOY_PAGE]: COMMAND_OPEN_DEPLOY_PAGE,
    [COMMAND_UNSEAL_RUNTIME]: COMMAND_UNSEAL_RUNTIME,
    [COMMAND_CHECK_HEALTH]: COMMAND_CHECK_HEALTH,
    [COMMAND_VIEW_METRICS]: COMMAND_VIEW_METRICS,
    [COMMAND_OPEN_AUTONOMY_AUDIT]: COMMAND_OPEN_AUTONOMY_AUDIT,
    [COMMAND_KILL_SWITCH]: COMMAND_KILL_SWITCH,
};
