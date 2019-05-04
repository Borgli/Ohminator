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
