import discord
from discord.ext import commands, tasks
import random
import os
import json
import asyncio
import re
import logging
import math
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ombre")

# ══════════════════════════════════════════════════════
#  TOKEN
# ══════════════════════════════════════════════════════
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN introuvable. Définis la variable d'environnement.")

# ══════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════
OWNER_ROLES = ["owner", "co owner"]
MOD_ROLES = [
    "owner", "co owner", "admin", "super staff",
    "Staff ໒꒱ིྀ༝⁺", "Staff test ღ", "Super staff", "Admin"
]

SPAM_LIMIT    = 5
SPAM_INTERVAL = 5
MUTE_DURATION = 5
DAILY_AMOUNT  = 200

BOT_SIGNATURE = "𝕭𝖔𝖙 ◈ Ombre"

# Palette dark / violet / gold
C_VIOLET = 0x7B2FBE
C_GOLD   = 0xC9A84C
C_RED    = 0xC0392B
C_GREEN  = 0x1ABC9C
C_YELLOW = 0xF1C40F
C_BLUE   = 0x2C3E7A
C_DARK   = 0x0D0D1A

DEFAULT_SHOP = {"VIP": 500, "Casino Pro": 1000, "Rôle Chanceux": 300}

# XP & Niveaux
XP_MIN          = 5
XP_MAX          = 15
XP_COOLDOWN_SEC = 60

LEVEL_ROLES = {
    # Modifie ces noms de rôles selon ton serveur
    5:  "Niveau 5",
    10: "Niveau 10",
    20: "Niveau 20",
    50: "Niveau 50",
}

# Succès / achievements
ACHIEVEMENTS = {
    "first_msg":   ("Premier pas",      "◈", "Envoyer ton premier message"),
    "level_5":     ("En route",         "⭐", "Atteindre le niveau 5"),
    "level_10":    ("Habitué",          "🌟", "Atteindre le niveau 10"),
    "level_25":    ("Vétéran",          "💫", "Atteindre le niveau 25"),
    "level_50":    ("Légende",          "👑", "Atteindre le niveau 50"),
    "rich_1k":     ("Petit fortune",    "💰", "Avoir 1 000 pièces"),
    "rich_10k":    ("Grande fortune",   "💎", "Avoir 10 000 pièces"),
    "gambler":     ("Joueur",           "🎰", "Utiliser !gamble"),
    "thief_ok":    ("Voleur",           "🦹", "Réussir un vol"),
    "thief_fail":  ("Maladroit",        "😅", "Échouer un vol"),
    "collector":   ("Collectionneur",   "📚", "Avoir 10 cartes"),
    "warned":      ("Mauvais élève",    "⚠️", "Recevoir 3 avertissements"),
    "daily_7":     ("Régulier",         "📅", "Faire !daily 7 jours"),
}

# Footers variés par catégorie
FOOTERS_MOD  = ["⚔ Modération", "⚔ Action modérateur", "⚔ Log de modération"]
FOOTERS_ECO  = ["✦ Économie", "✦ Système monétaire", "✦ Transaction"]
FOOTERS_FUN  = ["◇ Fun", "◇ Divertissement", "◇ Jeux"]
FOOTERS_LVL  = ["◈ Niveaux", "◈ Progression", "◈ Rang"]

CHARACTERS = [
    ("Naruto", "⭐⭐⭐", "🦊"),    ("Goku", "⭐⭐⭐⭐⭐", "🐉"),
    ("Luffy", "⭐⭐⭐", "🍖"),     ("Ichigo", "⭐⭐⭐", "⚔️"),
    ("Levi", "⭐⭐⭐⭐", "🗡️"),   ("Eren", "⭐⭐⭐", "🔑"),
    ("Sakura", "⭐⭐", "🌸"),      ("Hinata", "⭐⭐", "💜"),
    ("Gojo", "⭐⭐⭐⭐⭐", "♾️"), ("Itachi", "⭐⭐⭐⭐⭐", "🌙"),
    ("Zoro", "⭐⭐⭐⭐", "⚔️"),   ("Kakashi", "⭐⭐⭐⭐", "📖"),
    ("Rem", "⭐⭐⭐", "💙"),       ("Zero Two", "⭐⭐⭐⭐", "🌹"),
    ("Mikasa", "⭐⭐⭐⭐", "🧣"), ("Killua", "⭐⭐⭐⭐", "⚡"),
    ("Nezuko", "⭐⭐⭐", "🌸"),   ("Tanjiro", "⭐⭐⭐", "💧"),
    ("Edward", "⭐⭐⭐", "⚗️"),   ("Vegeta", "⭐⭐⭐⭐", "👑"),
]

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# ══════════════════════════════════════════════════════
#  PERSISTANCE JSON (avec sauvegarde différée)
# ══════════════════════════════════════════════════════
os.makedirs("data", exist_ok=True)
_pending_saves: dict = {}
_cache: dict = {}

def _load(filename: str, default):
    if filename in _cache:
        return _cache[filename]
    path = f"data/{filename}.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _cache[filename] = data
                return data
        except Exception as e:
            logger.error(f"Erreur lecture {filename}.json : {e}")
    val = default.copy() if isinstance(default, (dict, list)) else default
    _cache[filename] = val
    return val

def _write(filename: str, data):
    path = f"data/{filename}.json"
    tmp  = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        _cache[filename] = data
    except Exception as e:
        logger.error(f"Erreur écriture {filename}.json : {e}")

async def _delayed(filename: str, data):
    await asyncio.sleep(2)
    _write(filename, data)
    _pending_saves.pop(filename, None)

def save(filename: str, data):
    loop = asyncio.get_event_loop()
    if filename in _pending_saves:
        _pending_saves[filename].cancel()
    _pending_saves[filename] = loop.create_task(_delayed(filename, data))

# ── Données persistées ───────────────────────────────
balances      = _load("balances",      {})
warns         = _load("warns",         {})
shop_items    = _load("shop",          DEFAULT_SHOP)
cards         = _load("cards",         {})
auto_roles    = _load("auto_roles",    {})
reaction_roles= _load("reaction_roles",{})
auto_responses= _load("auto_responses",{})
word_filter   = _load("word_filter",   {})
link_filter   = _load("link_filter",   {})

# ── Nouvelles données persistées ────────────────────
xp_data        = _load("xp",           {})
achievements_d = _load("achievements",  {})
daily_streak   = _load("daily_streak",  {})

# ── Données en mémoire uniquement ───────────────────
spam_tracker: dict  = {}
snipe_cache:  dict  = {}
reminders:    list  = []
cooldowns:    dict  = {}
xp_cooldowns: dict  = {}   # anti-spam XP

# ══════════════════════════════════════════════════════
#  BOT
# ══════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members         = True
intents.guilds          = True
intents.voice_states    = True
intents.reactions       = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════════════
#  HELPERS — RÔLES & SOLDE
# ══════════════════════════════════════════════════════
def is_mod(member: discord.Member) -> bool:
    roles = {r.name.lower() for r in member.roles}
    return any(r.lower() in roles for r in MOD_ROLES)

def get_bal(uid: str) -> int:
    balances.setdefault(uid, 100)
    return balances[uid]

def set_bal(uid: str, amount: int):
    balances[uid] = max(0, amount)
    save("balances", balances)

def add_bal(uid: str, amount: int):
    set_bal(uid, get_bal(uid) + amount)

async def send_log(guild: discord.Guild, embed: discord.Embed):
    ch = (discord.utils.get(guild.text_channels, name="mod-logs")
          or discord.utils.get(guild.text_channels, name="logs"))
    if ch:
        try:
            await ch.send(embed=embed)
        except discord.Forbidden:
            pass

# ══════════════════════════════════════════════════════
#  HELPERS — EMBEDS
# ══════════════════════════════════════════════════════
def _em(title: str, desc=None, color: int = C_VIOLET) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color,
                      timestamp=datetime.utcnow())
    e.set_footer(text=BOT_SIGNATURE)
    return e

def em_ok(t, d=None):   return _em(f"✦ {t}", d, C_GREEN)
def em_err(t, d=None):  return _em(f"✗ {t}", d, C_RED)
def em_warn(t, d=None): return _em(f"◈ {t}", d, C_YELLOW)
def em_info(t, d=None): return _em(f"◇ {t}", d, C_BLUE)
def em_gold(t, d=None): return _em(f"✦ {t}", d, C_GOLD)
def em_mod(t, d=None):  return _em(f"⚔ {t}", d, C_VIOLET)
def em_dark(t, d=None): return _em(f"◈ {t}", d, C_DARK)

def _foot(e: discord.Embed, m: discord.Member):
    e.set_footer(text=f"{BOT_SIGNATURE}  •  {m.display_name}",
                 icon_url=m.display_avatar.url)
    return e

async def no_perm(ctx):
    await ctx.send(embed=_foot(em_err("Accès refusé",
        "```\nVous ne disposez pas des permissions nécessaires.\n```"), ctx.author),
        delete_after=6)

# ══════════════════════════════════════════════════════
#  HELPERS — XP / NIVEAUX / SUCCÈS
# ══════════════════════════════════════════════════════
def calc_level(xp: int) -> int:
    return int(math.sqrt(xp / 100))

def xp_for_level(lvl: int) -> int:
    return lvl * lvl * 100

def xp_for_next(lvl: int) -> int:
    return xp_for_level(lvl + 1)

def get_xp_info(uid: str) -> dict:
    xp_data.setdefault(uid, {"xp": 0, "level": 0})
    return xp_data[uid]

def grant_achievement(uid: str, key: str) -> bool:
    """Octroie un succès. Retourne True si c'est nouveau."""
    achievements_d.setdefault(uid, [])
    if key not in achievements_d[uid]:
        achievements_d[uid].append(key)
        save("achievements", achievements_d)
        return True
    return False

def check_balance_achievements(uid: str):
    bal = get_bal(uid)
    if bal >= 1000:  grant_achievement(uid, "rich_1k")
    if bal >= 10000: grant_achievement(uid, "rich_10k")

def xp_bar(xp: int, level: int, bar_len: int = 12) -> str:
    needed = xp_for_next(level)
    current = xp_for_level(level)
    prog = xp - current
    total = needed - current
    filled = int((prog / max(total, 1)) * bar_len)
    return "█" * filled + "░" * (bar_len - filled)

def em_lvl(t, d=None):
    e = discord.Embed(title=f"◈ {t}", description=d, color=C_VIOLET,
                      timestamp=datetime.utcnow())
    e.set_footer(text=random.choice(FOOTERS_LVL) + f"  •  {BOT_SIGNATURE}")
    return e

# ══════════════════════════════════════════════════════
#  ÉVÉNEMENTS
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="le serveur 👁️"),
        status=discord.Status.do_not_disturb
    )
    reminder_task.start()
    logger.info(f"Connecté : {bot.user} ({bot.user.id})")


@bot.event
async def on_member_join(member: discord.Member):
    gid = str(member.guild.id)
    if gid in auto_roles:
        role = discord.utils.get(member.guild.roles, name=auto_roles[gid])
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                pass


@bot.event
async def on_message_delete(message: discord.Message):
    if not message.author.bot:
        snipe_cache[message.channel.id] = {
            "content": message.content,
            "author":  str(message.author),
            "avatar":  str(message.author.display_avatar.url),
            "time":    datetime.utcnow().strftime("%H:%M:%S")
        }


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return
    key = str(reaction.message.id)
    if key in reaction_roles:
        role_name = reaction_roles[key].get(str(reaction.emoji))
        if role_name:
            role = discord.utils.get(reaction.message.guild.roles, name=role_name)
            if role:
                try:
                    await user.add_roles(role)
                except discord.Forbidden:
                    pass


@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return
    key = str(reaction.message.id)
    if key in reaction_roles:
        role_name = reaction_roles[key].get(str(reaction.emoji))
        if role_name:
            role = discord.utils.get(reaction.message.guild.roles, name=role_name)
            if role:
                try:
                    await user.remove_roles(role)
                except discord.Forbidden:
                    pass


@bot.event
async def on_voice_state_update(member: discord.Member, before, after):
    if before.channel is None and after.channel is not None:
        uid = str(member.id)
        add_bal(uid, random.randint(5, 20))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    gid     = str(message.guild.id)
    content = message.content.lower()

    # Filtre mots
    for word in word_filter.get(gid, []):
        if word in content:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                await message.channel.send(
                    embed=em_err("Message supprimé",
                        f"{message.author.mention}, ce mot est interdit ici."),
                    delete_after=4)
            except discord.Forbidden:
                pass
            return

    # Filtre liens
    if link_filter.get(gid) and URL_PATTERN.search(message.content):
        if not is_mod(message.author):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                await message.channel.send(
                    embed=em_err("Lien supprimé",
                        f"{message.author.mention}, les liens ne sont pas autorisés."),
                    delete_after=4)
            except discord.Forbidden:
                pass
            return

    # Anti-spam
    uid  = str(message.author.id)
    now  = datetime.utcnow()
    skey = f"{gid}_{uid}"
    spam_tracker.setdefault(skey, [])
    spam_tracker[skey] = [t for t in spam_tracker[skey]
                          if (now - t).total_seconds() < SPAM_INTERVAL]
    spam_tracker[skey].append(now)

    if len(spam_tracker[skey]) >= SPAM_LIMIT and not is_mod(message.author):
        spam_tracker[skey] = []
        try:
            await message.author.timeout(timedelta(minutes=MUTE_DURATION),
                                         reason="Anti-spam automatique")
            await message.channel.send(embed=em_warn(
                "Anti-Spam",
                f"{message.author.mention} a été muté `{MUTE_DURATION} min` pour spam."))
        except discord.Forbidden:
            pass
        return

    # ─── Gain XP (une fois par XP_COOLDOWN_SEC par utilisateur) ───
    now_ts = now.timestamp()
    if now_ts - xp_cooldowns.get(uid, 0) >= XP_COOLDOWN_SEC:
        xp_cooldowns[uid] = now_ts
        xp_gain    = random.randint(XP_MIN, XP_MAX)
        info       = get_xp_info(uid)
        old_level  = info["level"]
        info["xp"] += xp_gain
        new_level  = calc_level(info["xp"])
        info["level"] = new_level
        save("xp", xp_data)

        # Premier message
        if info["xp"] <= xp_gain:
            grant_achievement(uid, "first_msg")

        # Level-up
        if new_level > old_level:
            try:
                e = discord.Embed(
                    title="◈  Niveau supérieur !",
                    description=(
                        f"{message.author.mention} est passé au niveau **{new_level}** ! 🎉\n"
                        f"> XP total : `{info['xp']:,}`"
                    ),
                    color=C_GOLD, timestamp=datetime.utcnow()
                )
                e.set_footer(text=random.choice(FOOTERS_LVL) + f"  •  {BOT_SIGNATURE}")
                e.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=e)
            except discord.Forbidden:
                pass

            # Rôle de niveau
            role_name = LEVEL_ROLES.get(new_level)
            if role_name:
                role = discord.utils.get(message.guild.roles, name=role_name)
                if role:
                    try:
                        await message.author.add_roles(role)
                    except discord.Forbidden:
                        pass

            # Succès de niveau
            if new_level >= 5:  grant_achievement(uid, "level_5")
            if new_level >= 10: grant_achievement(uid, "level_10")
            if new_level >= 25: grant_achievement(uid, "level_25")
            if new_level >= 50: grant_achievement(uid, "level_50")

    # Réponses automatiques (ignorées si le message est une commande)
    is_command = message.content.startswith(bot.command_prefix)
    if not is_command:
        for trigger, response in auto_responses.get(gid, {}).items():
            if trigger in content:
                try:
                    await message.channel.send(response)
                except discord.Forbidden:
                    pass
                break

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=em_err("Argument manquant",
            f"```\n!help {ctx.command.name}\n```"), delete_after=6)
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=em_err("Argument invalide",
            "Vérifie la syntaxe avec `!help`."), delete_after=6)
    elif isinstance(error, commands.CommandOnCooldown):
        remaining = int(error.retry_after)
        # Message spécial pour !daily (affiche heures et minutes)
        if ctx.command and ctx.command.name == "daily":
            h = remaining // 3600
            m = (remaining % 3600) // 60
            e = em_err("Déjà réclamé", f"Reviens dans **{h}h {m}min** pour ta prochaine récompense.")
            _foot(e, ctx.author)
            await ctx.send(embed=e, delete_after=8)
        else:
            await ctx.send(embed=em_err("Cooldown",
                f"Attends encore `{remaining}s` avant de réutiliser cette commande."),
                delete_after=5)
    else:
        logger.error(f"Erreur {ctx.command} : {error}")

# ══════════════════════════════════════════════════════
#  TÂCHE — RAPPELS
# ══════════════════════════════════════════════════════
@tasks.loop(seconds=30)
async def reminder_task():
    now = datetime.utcnow()
    for r in reminders[:]:
        if now >= r["time"]:
            ch   = bot.get_channel(r["channel_id"])
            user = bot.get_user(r["user_id"])
            if ch and user:
                try:
                    await ch.send(embed=em_info(
                        "Rappel",
                        f"{user.mention}\n```\n{r['message']}\n```"))
                except Exception:
                    pass
            reminders.remove(r)

@reminder_task.before_loop
async def before_reminder():
    await bot.wait_until_ready()

# ══════════════════════════════════════════════════════
#  AIDE — DONNÉES
# ══════════════════════════════════════════════════════
HELP_CATS = {
    "mod": {
        "title": "⚔  Modération", "color": C_VIOLET, "emoji": "⚔",
        "cmds": [
            ("!kick <membre> [raison]",         "Expulse un membre"),
            ("!ban <membre> [raison]",           "Bannit un membre"),
            ("!unban <id>",                      "Débannit par ID"),
            ("!mute <membre> [min] [raison]",    "Timeout temporaire"),
            ("!unmute <membre>",                 "Retire le mute"),
            ("!warn <membre> [raison]",          "Avertissement (cd 5 s)"),
            ("!warns [membre]",                  "Voir les warns"),
            ("!clear [nombre]",                  "Supprime des messages"),
            ("!slowmode [secondes]",             "Slowmode"),
            ("!lock / !unlock",                  "Verrouille/déverrouille"),
        ]
    },
    "eco": {
        "title": "✦  Économie", "color": C_GOLD, "emoji": "✦",
        "cmds": [
            ("!balance [membre]",               "Voir son solde"),
            ("!daily",                          "Récompense journalière (cd 24h)"),
            ("!don <membre> <montant>",         "Donner des pièces"),
            ("!leaderboard",                    "Top 10 richesse"),
            ("!shop",                           "Voir la boutique"),
            ("!buy <article>",                  "Acheter un article"),
            ("!gamble <montant>",               "Pari 50/50 (cd 10s)"),
            ("!slots <montant>",                "Machine à sous (cd 15s)"),
            ("!vol <membre>",                   "Tentative de vol (cd 1h, risqué)"),
        ]
    },
    "fun": {
        "title": "◇  Fun & Jeux", "color": C_DARK, "emoji": "◇",
        "cmds": [
            ("!roll",                           "Invoquer un perso (cd 30s)"),
            ("!inventory [membre]",             "Ta collection de cartes"),
            ("!blackjack <montant>",            "Jouer au blackjack (cd 15s)"),
            ("!8ball <question>",               "Oracle mystique"),
            ("!de [faces]",                     "Lancer un dé"),
            ("!coinflip",                       "Pile ou face"),
            ("!snipe",                          "Dernier message supprimé"),
            ("!avatar [membre]",                "Voir un avatar"),
            ("!serverinfo",                     "Infos serveur"),
            ("!userinfo [membre]",              "Infos membre"),
        ]
    },
    "niveau": {
        "title": "◈  Niveaux & XP", "color": C_VIOLET, "emoji": "◈",
        "cmds": [
            ("!niveau [membre]",                "Voir son niveau et XP"),
            ("!topxp",                          "Classement XP du serveur"),
            ("!profil [membre]",                "Profil complet (niveau, éco, cartes)"),
            ("!succes [membre]",                "Voir les succès débloqués"),
            ("",                                "XP gagné : 5–15 par message (cd 60s)"),
            ("",                                "Niveau = √(XP ÷ 100)"),
        ]
    },
    "admin": {
        "title": "🛡  Admin (mod only)", "color": C_RED, "emoji": "🛡",
        "cmds": [
            ("!addmoney <membre> <montant>",     "Ajouter des pièces à un membre"),
            ("!removemoney <membre> <montant>",  "Retirer des pièces à un membre"),
            ("!say <message>",                   "Faire parler le bot"),
            ("!additem <prix> <nom>",            "Ajouter article boutique"),
            ("!removeitem <nom>",                "Retirer article boutique"),
        ]
    },
    "config": {
        "title": "⚙  Configuration", "color": C_VIOLET, "emoji": "⚙",
        "cmds": [
            ("!setautorole <rôle>",             "Rôle auto nouveaux membres"),
            ("!addrr <msg_id> <emoji> <rôle>",  "Ajouter reaction role"),
            ("!removerr <msg_id> <emoji>",       "Retirer reaction role"),
            ("!addresponse <trigger> <rep>",     "Réponse automatique"),
            ("!removeresponse <trigger>",         "Supprimer réponse auto"),
            ("!addword <mot>",                   "Ajouter mot banni"),
            ("!removeword <mot>",                "Retirer mot banni"),
            ("!linkfilter <on/off>",             "Filtre de liens"),
        ]
    },
    "remind": {
        "title": "◈  Rappels", "color": C_DARK, "emoji": "🔔",
        "cmds": [
            ("!reminder <durée> <message>",     "Créer un rappel"),
            ("",                                "Unités : s, m, h, j"),
            ("",                                "Ex : !reminder 30m Réunion"),
        ]
    },
    "embeds": {
        "title": "🎨  Embeds", "color": C_GOLD, "emoji": "🎨",
        "cmds": [
            ("!embed <couleur> <titre> | <desc>",        "Embed simple"),
            ("",                                          "Couleurs : violet, gold, rouge, vert, bleu, dark, jaune"),
            ("!panel <titre>",                            "Embed multi-sections"),
            ("",                                          "Sépare les sections avec ---"),
            ("!embedraw #salon <couleur> <titre> | <desc>","Envoie dans un autre salon"),
        ]
    },
}

def _build_help_cat_embed(key: str) -> discord.Embed:
    data  = HELP_CATS[key]
    lines = [f"`{cmd}` — {desc}" if cmd else f"↳ *{desc}*"
             for cmd, desc in data["cmds"]]
    e = discord.Embed(title=data["title"], color=data["color"],
                      description="\n".join(lines),
                      timestamp=datetime.utcnow())
    e.set_footer(text=f"{BOT_SIGNATURE}  •  Préfixe : !")
    return e

def _build_help_main_embed(ctx) -> discord.Embed:
    e = discord.Embed(
        title="◈  Ombre — Aide",
        description=(
            "```\nBot dark & élégant — Préfixe : !\n```\n"
            "Clique sur un bouton **ou** tape `!help <catégorie>` pour les détails.\n\u200b"
        ),
        color=C_VIOLET, timestamp=datetime.utcnow()
    )
    e.set_thumbnail(url=bot.user.display_avatar.url)
    for key, data in HELP_CATS.items():
        e.add_field(name=f"{data['emoji']}  {data['title'].split('  ',1)[-1]}",
                    value=f"`!help {key}`", inline=True)
    e.set_footer(text=BOT_SIGNATURE,
                 icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    return e

class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.msg  = None
        for key, data in HELP_CATS.items():
            btn = discord.ui.Button(
                label=data["title"].split("  ", 1)[-1],
                style=discord.ButtonStyle.secondary
            )
            btn.callback = self._make_callback(key)
            self.add_item(btn)

    def _make_callback(self, key: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                return await interaction.response.send_message(
                    "Ce menu ne t'appartient pas.", ephemeral=True)
            await interaction.response.edit_message(
                embed=_build_help_cat_embed(key), view=self)
        return callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.msg:
            try:
                await self.msg.edit(view=self)
            except Exception:
                pass

# ══════════════════════════════════════════════════════
#  AIDE — COMMANDE
# ══════════════════════════════════════════════════════
@bot.command(aliases=["aide", "commands"])
async def help(ctx, category: str = None):
    if category and category.lower() in HELP_CATS:
        return await ctx.send(embed=_build_help_cat_embed(category.lower()))
    view = HelpView(ctx)
    msg  = await ctx.send(embed=_build_help_main_embed(ctx), view=view)
    view.msg = msg

# ══════════════════════════════════════════════════════
#  MODÉRATION
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=em_err("Permission refusée"))
    e = em_mod("Membre expulsé")
    e.add_field(name="◈ Membre",    value=member.mention,     inline=True)
    e.add_field(name="◈ Modérateur",value=ctx.author.mention, inline=True)
    e.add_field(name="◈ Raison",    value=f"```{reason}```",  inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)
    await ctx.message.add_reaction("⚔")
    log = em_mod("Kick")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Modérateur",value=str(ctx.author))
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)


@bot.command()
@commands.guild_only()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=em_err("Permission refusée"))
    e = em_err("Membre banni")
    e.add_field(name="◈ Membre",    value=member.mention,     inline=True)
    e.add_field(name="◈ Modérateur",value=ctx.author.mention, inline=True)
    e.add_field(name="◈ Raison",    value=f"```{reason}```",  inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)
    await ctx.message.add_reaction("🔨")
    log = em_err("Ban")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Modérateur",value=str(ctx.author))
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)


@bot.command()
@commands.guild_only()
async def unban(ctx, user_id: int):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        e = em_ok("Membre débanni", f"{user.mention} a été débanni.")
        _foot(e, ctx.author); await ctx.send(embed=e)
    except discord.NotFound:
        await ctx.send(embed=em_err("Introuvable", "Aucun ban pour cet ID."))


@bot.command()
@commands.guild_only()
async def mute(ctx, member: discord.Member, minutes: int = 10, *, reason="Aucune raison"):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try:
        await member.timeout(timedelta(minutes=minutes), reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=em_err("Permission refusée"))
    e = em_warn("Membre muté")
    e.add_field(name="◈ Membre", value=member.mention, inline=True)
    e.add_field(name="◈ Durée",  value=f"`{minutes} min`", inline=True)
    e.add_field(name="◈ Raison", value=f"```{reason}```",  inline=False)
    _foot(e, ctx.author); await ctx.send(embed=e)
    log = em_warn("Timeout")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Durée",     value=f"{minutes} min")
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)


@bot.command()
@commands.guild_only()
async def unmute(ctx, member: discord.Member):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try:
        await member.timeout(None)
        e = em_ok("Membre démuté", f"{member.mention} peut de nouveau écrire.")
        _foot(e, ctx.author); await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))


@bot.command()
@commands.guild_only()
async def clear(ctx, amount: int = 10):
    if not is_mod(ctx.author): return await no_perm(ctx)
    amount = min(max(amount, 1), 100)
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(embed=em_ok("Messages supprimés",
            f"`{len(deleted) - 1}` messages supprimés."))
        await msg.delete(delay=4)
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))


@bot.command()
@commands.guild_only()
async def warn(ctx, member: discord.Member, *, reason="Comportement inapproprié"):
    if not is_mod(ctx.author): return await no_perm(ctx)
    uid = str(member.id)
    warns.setdefault(uid, [])
    warns[uid].append({"reason": reason, "by": str(ctx.author)})
    save("warns", warns)
    count = len(warns[uid])
    e = em_warn(f"Avertissement #{count}")
    e.add_field(name="◈ Membre",      value=member.mention,      inline=True)
    e.add_field(name="◈ Total warns", value=f"`{count}`",         inline=True)
    e.add_field(name="◈ Raison",      value=f"```{reason}```",   inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)
    await ctx.message.add_reaction("⚠️")
    # Succès "Mauvais élève" au 3e warn
    if count >= 3:
        grant_achievement(str(member.id), "warned")
    log = em_warn(f"Warn #{count}")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Modérateur",value=str(ctx.author))
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)


@bot.command(name="warns")
@commands.guild_only()
async def show_warns(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid    = str(target.id)
    wlist  = warns.get(uid, [])
    if not wlist:
        return await ctx.send(embed=em_info(
            f"Avertissements — {target.display_name}",
            "✦ Aucun avertissement."))
    lines = [f"`{i+1}.` {w['reason']} — *{w['by']}*" for i, w in enumerate(wlist)]
    e = em_warn(f"Avertissements — {target.display_name}", "\n".join(lines))
    e.set_thumbnail(url=target.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def slowmode(ctx, seconds: int = 0):
    if not is_mod(ctx.author): return await no_perm(ctx)
    await ctx.channel.edit(slowmode_delay=seconds)
    label = f"`{seconds}s`" if seconds > 0 else "désactivé"
    e = em_ok("Slowmode", f"Slowmode {label} sur {ctx.channel.mention}")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def lock(ctx):
    if not is_mod(ctx.author): return await no_perm(ctx)
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    e = em_err("Salon verrouillé", f"{ctx.channel.mention} est verrouillé.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def unlock(ctx):
    if not is_mod(ctx.author): return await no_perm(ctx)
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    e = em_ok("Salon déverrouillé", f"{ctx.channel.mention} est déverrouillé.")
    _foot(e, ctx.author); await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  ÉCONOMIE
# ══════════════════════════════════════════════════════
@bot.command(aliases=["bal", "solde"])
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal    = get_bal(str(target.id))
    e = em_gold(f"Portefeuille — {target.display_name}",
                f"```\n✦  {bal:,} pièces\n```")
    e.set_thumbnail(url=target.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    uid = str(ctx.author.id)
    add_bal(uid, DAILY_AMOUNT)
    e = em_gold("Récompense quotidienne",
        f"Tu as reçu **{DAILY_AMOUNT:,}** pièces !\n```\n✦  Solde : {get_bal(uid):,} pièces\n```")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["give"])
async def don(ctx, member: discord.Member, amount: int):
    uid_f = str(ctx.author.id)
    uid_t = str(member.id)
    if amount <= 0:
        return await ctx.send(embed=em_err("Montant invalide"))
    if get_bal(uid_f) < amount:
        return await ctx.send(embed=em_err("Fonds insuffisants",
            f"Ton solde : `{get_bal(uid_f):,}` pièces."))
    if member.bot or member == ctx.author:
        return await ctx.send(embed=em_err("Cible invalide"))
    set_bal(uid_f, get_bal(uid_f) - amount)
    add_bal(uid_t, amount)
    e = em_ok("Transfert effectué")
    e.add_field(name="◈ Envoyeur",     value=ctx.author.mention, inline=True)
    e.add_field(name="◈ Destinataire", value=member.mention,     inline=True)
    e.add_field(name="◈ Montant",      value=f"`{amount:,}` pièces", inline=False)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["lb", "top"])
async def leaderboard(ctx):
    if not balances:
        return await ctx.send(embed=em_info("Classement", "Aucun joueur."))
    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["◈"] * 7
    lines = []
    for i, (uid, bal) in enumerate(top):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except Exception:
            name = f"`{uid}`"
        lines.append(f"{medals[i]} **{name}** — `{bal:,}` pièces")
    e = em_gold("Classement — Top 10", "\n".join(lines))
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["boutique"])
async def shop(ctx):
    if not shop_items:
        return await ctx.send(embed=em_info("Boutique", "La boutique est vide."))
    lines = [f"◈ **{n}** — `{p:,}` pièces" for n, p in shop_items.items()]
    e = em_gold("Boutique", "\n".join(lines))
    await ctx.send(embed=e)


@bot.command(aliases=["acheter"])
async def buy(ctx, *, item_name: str):
    uid  = str(ctx.author.id)
    item = next((k for k in shop_items if k.lower() == item_name.lower()), None)
    if not item:
        return await ctx.send(embed=em_err("Article introuvable",
            f"`{item_name}` n'existe pas."))
    price = shop_items[item]
    if get_bal(uid) < price:
        return await ctx.send(embed=em_err("Fonds insuffisants",
            f"Il te manque `{price - get_bal(uid):,}` pièces."))
    set_bal(uid, get_bal(uid) - price)
    role = discord.utils.get(ctx.guild.roles, name=item)
    if role:
        try: await ctx.author.add_roles(role)
        except discord.Forbidden: pass
    e = em_ok(f"Achat — {item}",
        f"Tu as acheté **{item}** pour `{price:,}` pièces !\n"
        f"```\n✦  Solde restant : {get_bal(uid):,} pièces\n```")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["pari", "bet"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def gamble(ctx, amount: int):
    uid = str(ctx.author.id)
    bal = get_bal(uid)
    if amount <= 0:
        return await ctx.send(embed=em_err("Montant invalide"))
    if bal < amount:
        return await ctx.send(embed=em_err("Fonds insuffisants",
            f"Ton solde : `{bal:,}` pièces."))
    won = random.random() > 0.5
    if won:
        add_bal(uid, amount)
        e = em_gold("Victoire !",
            f"Tu as gagné `{amount:,}` pièces 🎉\n"
            f"```\n✦  Solde : {get_bal(uid):,} pièces\n```")
    else:
        set_bal(uid, bal - amount)
        e = em_err("Défaite",
            f"Tu as perdu `{amount:,}` pièces 💀\n"
            f"```\n✦  Solde : {get_bal(uid):,} pièces\n```")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(name="add_money", aliases=["addmoney"])
@commands.guild_only()
async def add_money(ctx, member: discord.Member, amount: int):
    if not is_mod(ctx.author): return await no_perm(ctx)
    add_bal(str(member.id), amount)
    e = em_ok("Pièces ajoutées",
        f"`{amount:,}` pièces ajoutées à {member.mention}.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(name="remove_money", aliases=["removemoney"])
@commands.guild_only()
async def remove_money(ctx, member: discord.Member, amount: int):
    if not is_mod(ctx.author): return await no_perm(ctx)
    set_bal(str(member.id), get_bal(str(member.id)) - amount)
    e = em_ok("Pièces retirées",
        f"`{amount:,}` pièces retirées de {member.mention}.")
    _foot(e, ctx.author); await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  FUN
# ══════════════════════════════════════════════════════
@bot.command()
async def snipe(ctx):
    data = snipe_cache.get(ctx.channel.id)
    if not data:
        return await ctx.send(embed=em_info("Snipe", "Aucun message récent à sniffer."))
    e = em_dark("Message supprimé",
                f"```\n{data['content'] or '(pas de texte)'}\n```")
    e.set_author(name=data["author"], icon_url=data["avatar"])
    e.set_footer(text=f"Supprimé à {data['time']}")
    await ctx.send(embed=e)


@bot.command(name="8ball", aliases=["boule"])
async def eight_ball(ctx, *, question: str):
    reponses = [
        "Absolument.", "C'est certain.", "Sans aucun doute.", "Oui, définitivement.",
        "Non, clairement.", "Très peu probable.", "Mes sources disent non.", "N'y compte pas.",
        "Difficile à dire.", "Concentre-toi et redemande.", "C'est flou.", "Les signes sont contradictoires."
    ]
    e = em_dark("◈ Oracle")
    e.add_field(name="Question", value=f"*{question}*",               inline=False)
    e.add_field(name="Réponse",  value=f"**{random.choice(reponses)}**", inline=False)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["invoke", "pull"])
@commands.cooldown(1, 30, commands.BucketType.user)
async def roll(ctx):
    character, rarity, emoji = random.choice(CHARACTERS)
    uid = str(ctx.author.id)
    cards.setdefault(uid, [])
    cards[uid].append(character)
    save("cards", cards)
    e = em_gold(f"{emoji} Invocation",
        f"**{character}**\nRareté : {rarity}\n```\nAjouté à ta collection !\n```")
    e.set_footer(text=f"Collection : {len(cards[uid])} carte(s)")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["cards", "collection"])
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid    = str(target.id)
    col    = cards.get(uid, [])
    if not col:
        return await ctx.send(embed=em_info(
            f"Collection — {target.display_name}",
            "Aucune carte. Utilise `!roll` pour invoquer !"))
    from collections import Counter
    count = Counter(col)
    lines = [f"◈ {c} × {n}" for c, n in sorted(count.items(), key=lambda x: -x[1])]
    e = em_gold(f"Collection — {target.display_name}", "\n".join(lines[:20]))
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_footer(text=f"Total : {len(col)} carte(s)")
    await ctx.send(embed=e)


@bot.command(aliases=["dice"])
async def de(ctx, faces: int = 6):
    if faces < 2:
        return await ctx.send(embed=em_err("Dé invalide", "Minimum 2 faces."))
    e = em_info(f"Dé à {faces} faces", f"```\n✦  {random.randint(1, faces)}\n```")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["flip", "piece"])
async def coinflip(ctx):
    result = random.choice(["Pile", "Face"])
    emoji  = "🌑" if result == "Pile" else "☀️"
    e = em_info("Pile ou Face", f"```\n{emoji}  {result}\n```")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def say(ctx, *, message: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    try: await ctx.message.delete()
    except discord.Forbidden: pass
    await ctx.send(message)


@bot.command(aliases=["av", "pfp"])
async def avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    e = em_dark(f"Avatar — {target.display_name}")
    e.set_image(url=target.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["si"])
@commands.guild_only()
async def serverinfo(ctx):
    g = ctx.guild
    e = em_dark(f"◈ {g.name}")
    e.set_thumbnail(url=g.icon.url if g.icon else None)
    e.add_field(name="Membres",    value=f"`{g.member_count}`",                            inline=True)
    e.add_field(name="Salons",     value=f"`{len(g.channels)}`",                           inline=True)
    e.add_field(name="Rôles",      value=f"`{len(g.roles)}`",                              inline=True)
    e.add_field(name="Boosts",     value=f"`{g.premium_subscription_count}`",              inline=True)
    e.add_field(name="Création",   value=f"<t:{int(g.created_at.timestamp())}:D>",         inline=True)
    e.add_field(name="Propriétaire",value=g.owner.mention if g.owner else "Inconnu",       inline=True)
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command(aliases=["ui"])
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    target = member or ctx.author
    e = em_dark(f"◈ {target.display_name}")
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="Pseudo",      value=str(target),                                    inline=True)
    e.add_field(name="ID",          value=f"`{target.id}`",                               inline=True)
    e.add_field(name="Rejoint le",  value=f"<t:{int(target.joined_at.timestamp())}:D>",   inline=True)
    e.add_field(name="Compte créé", value=f"<t:{int(target.created_at.timestamp())}:D>",  inline=True)
    top = target.top_role.mention if target.top_role != ctx.guild.default_role else "Aucun"
    e.add_field(name="Rôle principal", value=top, inline=True)
    _foot(e, ctx.author); await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
async def setautorole(ctx, *, role_name: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send(embed=em_err("Rôle introuvable", f"`{role_name}` n'existe pas."))
    auto_roles[str(ctx.guild.id)] = role_name
    save("auto_roles", auto_roles)
    e = em_ok("Auto-rôle configuré",
        f"Le rôle **{role.mention}** sera attribué aux nouveaux membres.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def addrr(ctx, message_id: int, emoji: str, *, role_name: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send(embed=em_err("Rôle introuvable", f"`{role_name}` n'existe pas."))
    key = str(message_id)
    reaction_roles.setdefault(key, {})
    reaction_roles[key][emoji] = role_name
    save("reaction_roles", reaction_roles)
    e = em_ok("Reaction role ajouté", f"Emoji {emoji} → **{role.mention}**")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def removerr(ctx, message_id: int, emoji: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    key = str(message_id)
    if key in reaction_roles and emoji in reaction_roles[key]:
        del reaction_roles[key][emoji]
        if not reaction_roles[key]: del reaction_roles[key]
        save("reaction_roles", reaction_roles)
        e = em_ok("Reaction role supprimé", f"Emoji {emoji} retiré.")
    else:
        e = em_err("Introuvable", "Ce reaction role n'existe pas.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def addresponse(ctx, trigger: str, *, response: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    auto_responses.setdefault(gid, {})
    auto_responses[gid][trigger.lower()] = response
    save("auto_responses", auto_responses)
    e = em_ok("Réponse automatique ajoutée", f"Trigger : `{trigger}`")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def removeresponse(ctx, trigger: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    if gid in auto_responses and trigger.lower() in auto_responses[gid]:
        del auto_responses[gid][trigger.lower()]
        save("auto_responses", auto_responses)
        e = em_ok("Réponse supprimée", f"Trigger `{trigger}` retiré.")
    else:
        e = em_err("Introuvable", f"Le trigger `{trigger}` n'existe pas.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def addword(ctx, *, word: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    word_filter.setdefault(gid, [])
    if word.lower() not in word_filter[gid]:
        word_filter[gid].append(word.lower())
        save("word_filter", word_filter)
    e = em_ok("Mot banni ajouté", f"`{word}` ajouté au filtre.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def removeword(ctx, *, word: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    gid = str(ctx.guild.id)
    if gid in word_filter and word.lower() in word_filter[gid]:
        word_filter[gid].remove(word.lower())
        save("word_filter", word_filter)
        e = em_ok("Mot retiré", f"`{word}` retiré du filtre.")
    else:
        e = em_err("Introuvable", f"`{word}` n'est pas dans le filtre.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def linkfilter(ctx, state: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    gid     = str(ctx.guild.id)
    enabled = state.lower() in ("on", "1", "true", "oui")
    link_filter[gid] = enabled
    save("link_filter", link_filter)
    label = "activé" if enabled else "désactivé"
    e = em_ok("Filtre liens", f"Filtre de liens **{label}**.")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def additem(ctx, price: int, *, item_name: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    shop_items[item_name] = price
    save("shop", shop_items)
    e = em_ok("Article ajouté", f"**{item_name}** → `{price:,}` pièces")
    _foot(e, ctx.author); await ctx.send(embed=e)


@bot.command()
@commands.guild_only()
async def removeitem(ctx, *, item_name: str):
    if not is_mod(ctx.author): return await no_perm(ctx)
    item = next((k for k in shop_items if k.lower() == item_name.lower()), None)
    if item:
        del shop_items[item]
        save("shop", shop_items)
        e = em_ok("Article supprimé", f"**{item}** retiré de la boutique.")
    else:
        e = em_err("Introuvable", f"`{item_name}` n'est pas dans la boutique.")
    _foot(e, ctx.author); await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  RAPPELS
# ══════════════════════════════════════════════════════
def parse_duration(duration: str):
    units = {"s": 1, "m": 60, "h": 3600, "j": 86400, "d": 86400}
    try:
        unit  = duration[-1].lower()
        value = int(duration[:-1])
        return timedelta(seconds=value * units.get(unit, 60))
    except (ValueError, IndexError):
        return None


@bot.command(aliases=["remind", "rappel"])
async def reminder(ctx, duration: str, *, message: str):
    delta = parse_duration(duration)
    if not delta:
        return await ctx.send(embed=em_err(
            "Format invalide",
            "Exemple : `!reminder 10m Mon message`\nUnités : `s`, `m`, `h`, `j`"))
    reminders.append({
        "user_id":    ctx.author.id,
        "channel_id": ctx.channel.id,
        "message":    message,
        "time":       datetime.utcnow() + delta
    })
    e = em_ok("Rappel configuré")
    e.add_field(name="◈ Message", value=f"```{message}```", inline=False)
    e.add_field(name="◈ Dans",    value=f"`{duration}`",    inline=True)
    _foot(e, ctx.author); await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  EMBEDS PERSONNALISÉS
# ══════════════════════════════════════════════════════

# Couleurs disponibles pour !embed
EMBED_COLORS = {
    "violet": C_VIOLET,
    "gold":   C_GOLD,
    "rouge":  C_RED,
    "vert":   C_GREEN,
    "bleu":   C_BLUE,
    "dark":   C_DARK,
    "jaune":  C_YELLOW,
}


@bot.command(name="embed")
@commands.guild_only()
async def custom_embed(ctx, couleur: str = "violet", *, contenu: str):
    """
    Envoie un embed stylé dans le salon.
    Utilisation : !embed <couleur> <titre> | <description>

    Couleurs : violet, gold, rouge, vert, bleu, dark, jaune
    Exemple   : !embed gold Équipe officielle | Voici notre équipe...

    Tu peux aussi utiliser des sauts de ligne avec \\n
    """
    if not is_mod(ctx.author):
        return await no_perm(ctx)

    # Supprimer le message de commande
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    color = EMBED_COLORS.get(couleur.lower(), C_VIOLET)

    # Séparer titre et description avec " | "
    if " | " in contenu:
        titre, desc = contenu.split(" | ", 1)
    else:
        titre = contenu
        desc  = None

    # Remplacer \n par de vrais sauts de ligne
    if desc:
        desc = desc.replace("\\n", "\n")

    e = discord.Embed(title=titre.strip(), description=desc, color=color)
    e.set_footer(text=BOT_SIGNATURE)
    await ctx.send(embed=e)


@bot.command(name="panel")
@commands.guild_only()
async def panel_embed(ctx, *, contenu: str):
    """
    Crée un embed multi-sections style panel d'équipe.
    Sépare les sections avec --- sur une nouvelle ligne.

    Utilisation :
    !panel Titre principal
    ---
    🔑 Section 1 : sous-titre
    Description de la section
    • Point 1
    • Point 2
    ---
    🛡️ Section 2 : sous-titre
    Description
    • Point 1
    """
    if not is_mod(ctx.author):
        return await no_perm(ctx)

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    lignes = contenu.split("\n")
    titre_principal = lignes[0].strip() if lignes else "Panel"

    # Reconstruire le texte sans la première ligne
    reste = "\n".join(lignes[1:]).strip()

    # Séparer les sections par ---
    sections = [s.strip() for s in reste.split("---") if s.strip()]

    e = discord.Embed(title=titre_principal, color=C_VIOLET)

    if sections:
        for section in sections:
            lignes_sec = section.split("\n")
            # La première ligne de la section = nom du champ
            nom_champ = lignes_sec[0].strip() if lignes_sec else "◈"
            valeur    = "\n".join(lignes_sec[1:]).strip() if len(lignes_sec) > 1 else "\u200b"
            e.add_field(name=nom_champ, value=valeur, inline=False)
    else:
        e.description = reste

    e.set_footer(text=BOT_SIGNATURE)
    await ctx.send(embed=e)


@bot.command(name="embedraw")
@commands.guild_only()
async def embed_raw(ctx, salon: discord.TextChannel = None, couleur: str = "violet", *, contenu: str):
    """
    Envoie un embed dans un salon spécifique.
    Utilisation : !embedraw #salon <couleur> <titre> | <description>
    """
    if not is_mod(ctx.author):
        return await no_perm(ctx)

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    destination = salon or ctx.channel
    color = EMBED_COLORS.get(couleur.lower(), C_VIOLET)

    if " | " in contenu:
        titre, desc = contenu.split(" | ", 1)
    else:
        titre = contenu
        desc  = None

    if desc:
        desc = desc.replace("\\n", "\n")

    e = discord.Embed(title=titre.strip(), description=desc, color=color)
    e.set_footer(text=BOT_SIGNATURE)

    try:
        await destination.send(embed=e)
        confirm = em_ok("Embed envoyé", f"Embed envoyé dans {destination.mention}")
        await ctx.send(embed=confirm, delete_after=4)
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée",
            f"Je ne peux pas écrire dans {destination.mention}"))


# ══════════════════════════════════════════════════════
#  VOL — SYSTÈME
# ══════════════════════════════════════════════════════
@bot.command(aliases=["steal", "rob"])
@commands.guild_only()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def vol(ctx, cible: discord.Member = None):
    if cible is None:
        return await ctx.send(embed=em_err("Cible manquante", "Mentionne quelqu'un à voler."), delete_after=6)
    if cible.id == ctx.author.id or cible.bot:
        return await ctx.send(embed=em_err("Cible invalide", "Tu ne peux pas te voler toi-même ni un bot."), delete_after=6)

    uid_voleur = str(ctx.author.id)
    uid_cible  = str(cible.id)
    bal_cible  = get_bal(uid_cible)
    bal_voleur = get_bal(uid_voleur)

    if bal_cible < 50:
        return await ctx.send(embed=em_info("Trop pauvre",
            f"{cible.mention} n'a que `{bal_cible}` pièces, ça ne vaut pas le risque."))

    succes = random.random() < 0.40

    if succes:
        vol_pct   = random.uniform(0.10, 0.30)
        vol_montant = max(1, int(bal_cible * vol_pct))
        add_bal(uid_voleur, vol_montant)
        add_bal(uid_cible, -vol_montant)
        check_balance_achievements(uid_voleur)
        grant_achievement(uid_voleur, "thief_ok")
        e = discord.Embed(
            title="🦹  Vol réussi !",
            description=(
                f"{ctx.author.mention} a subtilisé **{vol_montant:,} pièces** à {cible.mention} !\n\n"
                f"> Ton nouveau solde : `{get_bal(uid_voleur):,}` pièces"
            ),
            color=C_GREEN, timestamp=datetime.utcnow()
        )
        e.set_footer(text=random.choice(FOOTERS_ECO) + f"  •  {BOT_SIGNATURE}")
        await ctx.send(embed=e)
        await ctx.message.add_reaction("🦹")
    else:
        amende_pct = random.uniform(0.10, 0.20)
        amende     = max(1, int(bal_voleur * amende_pct))
        add_bal(uid_voleur, -amende)
        grant_achievement(uid_voleur, "thief_fail")
        e = discord.Embed(
            title="😅  Vol échoué !",
            description=(
                f"{ctx.author.mention} s'est fait **attraper** en essayant de voler {cible.mention} !\n"
                f"Amende : **{amende:,} pièces** perdues.\n\n"
                f"> Ton solde : `{get_bal(uid_voleur):,}` pièces"
            ),
            color=C_RED, timestamp=datetime.utcnow()
        )
        e.set_footer(text=random.choice(FOOTERS_ECO) + f"  •  {BOT_SIGNATURE}")
        await ctx.send(embed=e)
        await ctx.message.add_reaction("😅")


# ══════════════════════════════════════════════════════
#  SLOTS — MACHINE À SOUS
# ══════════════════════════════════════════════════════
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
SLOT_MULT    = {"🍒": 1.5, "🍋": 2.0, "🍊": 2.5, "⭐": 3.0, "💎": 5.0, "7️⃣": 10.0}

@bot.command(aliases=["machine", "casino"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def slots(ctx, montant: int = 0):
    if montant < 10:
        return await ctx.send(embed=em_err("Mise invalide", "Mise minimum : `10 pièces`."), delete_after=6)
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants",
            f"Tu n'as que `{get_bal(uid):,}` pièces."), delete_after=6)

    add_bal(uid, -montant)
    rouleaux = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    grant_achievement(uid, "gambler")

    if rouleaux[0] == rouleaux[1] == rouleaux[2]:
        gain = int(montant * SLOT_MULT[rouleaux[0]])
        add_bal(uid, gain)
        check_balance_achievements(uid)
        resultat = f"JACKPOT ✨  +**{gain:,}** pièces !"
        color    = C_GOLD
        react    = "🎰"
    elif rouleaux[0] == rouleaux[1] or rouleaux[1] == rouleaux[2] or rouleaux[0] == rouleaux[2]:
        gain = int(montant * 1.2)
        add_bal(uid, gain)
        resultat = f"Paire !  +**{gain:,}** pièces"
        color    = C_GREEN
        react    = "✅"
    else:
        gain     = 0
        resultat = f"Perdu.  -**{montant:,}** pièces"
        color    = C_RED
        react    = "💸"

    e = discord.Embed(
        title="🎰  Machine à sous",
        description=(
            f"```\n| {rouleaux[0]}  {rouleaux[1]}  {rouleaux[2]} |\n```\n"
            f"{resultat}\n\n"
            f"> Solde : `{get_bal(uid):,}` pièces"
        ),
        color=color, timestamp=datetime.utcnow()
    )
    e.set_footer(text=random.choice(FOOTERS_ECO) + f"  •  {BOT_SIGNATURE}")
    msg = await ctx.send(embed=e)
    await msg.add_reaction(react)


# ══════════════════════════════════════════════════════
#  BLACKJACK
# ══════════════════════════════════════════════════════
def _bj_deck():
    vals = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
    random.shuffle(vals)
    return vals

def _bj_total(hand: list[int]) -> int:
    total = sum(hand)
    aces  = hand.count(11)
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, deck, player, dealer, mise, uid):
        super().__init__(timeout=60)
        self.ctx = ctx; self.deck = deck
        self.player = player; self.dealer = dealer
        self.mise = mise; self.uid = uid

    def _embed(self, titre, desc, color):
        e = discord.Embed(title=titre, description=desc, color=color, timestamp=datetime.utcnow())
        e.set_footer(text=random.choice(FOOTERS_FUN) + f"  •  {BOT_SIGNATURE}")
        return e

    def _status(self, reveal=False):
        d_shown = f"`{self.dealer[0]}` + `?`" if not reveal else " + ".join(f"`{c}`" for c in self.dealer)
        p_shown = " + ".join(f"`{c}`" for c in self.player)
        d_tot   = _bj_total(self.dealer) if reveal else "?"
        p_tot   = _bj_total(self.player)
        return (f"**Croupier :** {d_shown} = **{d_tot}**\n"
                f"**Toi :** {p_shown} = **{p_tot}**")

    async def end_game(self, interaction):
        ptot = _bj_total(self.player)
        while _bj_total(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        dtot = _bj_total(self.dealer)

        if ptot > 21:
            result = "Tu as dépassé 21. Perdu !"; color = C_RED; gain = 0
        elif dtot > 21 or ptot > dtot:
            gain = self.mise * 2; add_bal(self.uid, gain)
            result = f"Victoire ! +**{gain:,}** pièces"; color = C_GOLD
            check_balance_achievements(self.uid)
        elif ptot == dtot:
            add_bal(self.uid, self.mise)
            result = "Égalité. Mise remboursée."; color = C_BLUE; gain = self.mise
        else:
            result = f"Croupier gagne. -**{self.mise:,}** pièces"; color = C_RED; gain = 0

        for child in self.children:
            child.disabled = True
        e = self._embed("🃏  Blackjack — Fin", self._status(reveal=True) + f"\n\n{result}", color)
        react = "🏆" if color == C_GOLD else ("⚖️" if color == C_BLUE else "💸")
        await interaction.response.edit_message(embed=e, view=self)
        await interaction.message.add_reaction(react)

    @discord.ui.button(label="Tirer", emoji="🃏", style=discord.ButtonStyle.primary)
    async def tirer(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Ce n'est pas ta partie.", ephemeral=True)
        self.player.append(self.deck.pop())
        if _bj_total(self.player) > 21:
            return await self.end_game(interaction)
        e = self._embed("🃏  Blackjack", self._status(), C_DARK)
        await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Rester", emoji="🛑", style=discord.ButtonStyle.danger)
    async def rester(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Ce n'est pas ta partie.", ephemeral=True)
        await self.end_game(interaction)

@bot.command(aliases=["bj"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def blackjack(ctx, montant: int = 0):
    if montant < 10:
        return await ctx.send(embed=em_err("Mise invalide", "Mise minimum : `10 pièces`."), delete_after=6)
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants",
            f"Tu n'as que `{get_bal(uid):,}` pièces."), delete_after=6)

    add_bal(uid, -montant)
    grant_achievement(uid, "gambler")
    deck   = _bj_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    view = BlackjackView(ctx, deck, player, dealer, montant, uid)

    if _bj_total(player) == 21:
        gain = int(montant * 2.5)
        add_bal(uid, gain)
        check_balance_achievements(uid)
        e = discord.Embed(
            title="🃏  Blackjack naturel !",
            description=f"**21 dès le départ !** +**{gain:,}** pièces 🎉",
            color=C_GOLD, timestamp=datetime.utcnow()
        )
        e.set_footer(text=random.choice(FOOTERS_FUN) + f"  •  {BOT_SIGNATURE}")
        return await ctx.send(embed=e)

    d_shown = f"`{dealer[0]}` + `?`"
    p_shown = " + ".join(f"`{c}`" for c in player)
    e = discord.Embed(
        title="🃏  Blackjack",
        description=(
            f"**Croupier :** {d_shown}\n"
            f"**Toi :** {p_shown} = **{_bj_total(player)}**\n\n"
            f"Mise : `{montant:,}` pièces\n\u200b"
        ),
        color=C_DARK, timestamp=datetime.utcnow()
    )
    e.set_footer(text=random.choice(FOOTERS_FUN) + f"  •  {BOT_SIGNATURE}")
    await ctx.send(embed=e, view=view)


# ══════════════════════════════════════════════════════
#  NIVEAUX — COMMANDES
# ══════════════════════════════════════════════════════
@bot.command(aliases=["level", "rank", "xp"])
@commands.guild_only()
async def niveau(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid    = str(target.id)
    info   = get_xp_info(uid)
    lvl    = info["level"]
    xp     = info["xp"]
    needed = xp_for_next(lvl)
    curr   = xp_for_level(lvl)
    bar    = xp_bar(xp, lvl)
    pct    = int(((xp - curr) / max(needed - curr, 1)) * 100)

    e = em_lvl(
        f"Niveau {lvl} — {target.display_name}",
        f"```\n{bar}  {pct}%\n```\n"
        f"> **XP :** `{xp:,}` / `{needed:,}`\n"
        f"> **Prochain niveau :** encore `{needed - xp:,}` XP"
    )
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="◈ Niveau actuel", value=f"`{lvl}`", inline=True)
    e.add_field(name="◈ XP total",      value=f"`{xp:,}`", inline=True)
    _foot(e, ctx.author)
    await ctx.send(embed=e)


@bot.command(aliases=["classementxp", "rankingxp"])
@commands.guild_only()
async def topxp(ctx):
    uid_list = ctx.guild.members
    scores   = []
    for m in uid_list:
        if m.bot: continue
        info = get_xp_info(str(m.id))
        if info["xp"] > 0:
            scores.append((m.display_name, info["xp"], info["level"]))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:10]
    if not top:
        return await ctx.send(embed=em_info("Classement XP", "Aucun joueur enregistré."))

    medals = ["🥇", "🥈", "🥉"] + ["◈"] * 7
    lines  = [
        f"{medals[i]}  **{name}** — Niv. `{lvl}`  •  `{xp:,}` XP"
        for i, (name, xp, lvl) in enumerate(top)
    ]
    e = em_lvl("Classement XP", "\n".join(lines))
    _foot(e, ctx.author)
    await ctx.send(embed=e)


@bot.command(aliases=["profile", "card"])
@commands.guild_only()
async def profil(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid    = str(target.id)
    info   = get_xp_info(uid)
    lvl    = info["level"]
    xp     = info["xp"]
    bal    = get_bal(uid)
    inv    = cards.get(uid, [])
    achiev = achievements_d.get(uid, [])
    bar    = xp_bar(xp, lvl)
    needed = xp_for_next(lvl)
    pct    = int(((xp - xp_for_level(lvl)) / max(needed - xp_for_level(lvl), 1)) * 100)

    badges = " ".join(ACHIEVEMENTS[k][1] for k in achiev if k in ACHIEVEMENTS) or "Aucun"

    e = discord.Embed(
        title=f"◈  Profil — {target.display_name}",
        color=C_VIOLET, timestamp=datetime.utcnow()
    )
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(
        name="◈  Niveau & XP",
        value=f"**Niveau {lvl}**\n`{bar}` {pct}%\n`{xp:,}` / `{needed:,}` XP",
        inline=False
    )
    e.add_field(name="✦  Pièces",    value=f"`{bal:,}` pièces",        inline=True)
    e.add_field(name="📚  Cartes",   value=f"`{len(inv)}` carte(s)",    inline=True)
    e.add_field(name="🏆  Succès",   value=f"`{len(achiev)}`",          inline=True)
    e.add_field(name="🎖  Badges",   value=badges,                      inline=False)
    e.set_footer(text=f"{BOT_SIGNATURE}  •  {target.display_name}",
                 icon_url=target.display_avatar.url)
    await ctx.send(embed=e)


@bot.command(aliases=["achievements", "badges", "trophees"])
@commands.guild_only()
async def succes(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid    = str(target.id)
    unlocked = achievements_d.get(uid, [])

    lines = []
    for key, (name, emoji, desc) in ACHIEVEMENTS.items():
        if key in unlocked:
            lines.append(f"{emoji}  **{name}** — {desc}")
        else:
            lines.append(f"🔒  ~~{name}~~ — {desc}")

    e = discord.Embed(
        title=f"🏆  Succès — {target.display_name}",
        description="\n".join(lines),
        color=C_GOLD, timestamp=datetime.utcnow()
    )
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_footer(text=f"{len(unlocked)}/{len(ACHIEVEMENTS)} débloqués  •  {BOT_SIGNATURE}")
    await ctx.send(embed=e)


# ══════════════════════════════════════════════════════
#  DÉMARRAGE
# ══════════════════════════════════════════════════════
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
