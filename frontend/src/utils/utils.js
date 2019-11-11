const config = require('config')

export const getOauthUserUri = () => config.oauth_user_uri;
export const getOauthGuildUri = (guildId) => `${config.oauth_guild_uri}&guild_id=${guildId}&redirect_uri=${config.redirect_uri}/auth/guild/discord`;



