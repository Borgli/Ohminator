export const updatePluginPage = (plugin, discord) => ({
    type: 'UPDATE_PLUGIN_PAGE',
    plugin,
    discord
});

export const pluginDisabled = () => ({
    type: 'PLUGIN_DISABLED'
});

export const updateDiscord = (discord) => ({
    type: 'UPDATE_DISCORD',
    discord
});

export const updateOauthUserUri = (user_uri) => ({
    type: 'UPDATE_OAUTH_USER_URI',
    user_uri
});

export const updateOauthBotUri = (bot_uri) => ({
    type: 'UPDATE_OAUTH_BOT_URI',
    bot_uri
});