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
SPAM_LIMIT    = 5
SPAM_INTERVAL = 5
MUTE_DURATION = 5
DAILY_AMOUNT  = 200

BOT_SIGNATURE = "𝕭𝖔𝖙 ◈ Ombre"

# Super-owner : permissions absolues, indépendamment du serveur
SUPER_OWNER_ID = 790162204128313364

# ── Illustrations pour les activités (URLs stables) ─────
ASSETS = {
    "blackjack": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Atelier_Karuta.jpg/640px-Atelier_Karuta.jpg",
    "blackjack_thumb": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Card_back_01.svg/240px-Card_back_01.svg.png",
    "roulette": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Roulette_-_detail.jpg/640px-Roulette_-_detail.jpg",
    "roulette_thumb": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/European_roulette_wheel.png/240px-European_roulette_wheel.png",
    "slots": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Caesars_Slots_Machine.jpg/640px-Caesars_Slots_Machine.jpg",
    "slots_thumb": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Slot_machine.svg/240px-Slot_machine.svg.png",
    "gamble": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Gambling_chips.jpg/640px-Gambling_chips.jpg",
    "vol": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Mask_thief.png/240px-Mask_thief.png",
    "braquage": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Bank_robbery_1933.jpg/640px-Bank_robbery_1933.jpg",
    "treasure": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Treasure_chest.png/240px-Treasure_chest.png",
    "duel": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Duel_with_swords.jpg/640px-Duel_with_swords.jpg",
    "rps": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Rock-paper-scissors.svg/240px-Rock-paper-scissors.svg.png",
    "quiz": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Brain_in_a_jar.png/240px-Brain_in_a_jar.png",
    "daily": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Gold_coins.jpg/240px-Gold_coins.jpg",
    "shop": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Shopping_cart_icon.png/240px-Shopping_cart_icon.png",
    "gift": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Gift_box.png/240px-Gift_box.png",
    "clan": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Castle_icon.png/240px-Castle_icon.png",
    "quest": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Map_icon.png/240px-Map_icon.png",
    "ship": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Heart_icon_red_hollow.svg/240px-Heart_icon_red_hollow.svg.png",
    "level_up": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Star_icon_stylized.svg/240px-Star_icon_stylized.svg.png",
    "ban": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Hammer_icon.png/240px-Hammer_icon.png",
    "warn": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Warning_icon.svg/240px-Warning_icon.svg.png",
}

# Palette dark / violet / gold
C_VIOLET = 0x7B2FBE
C_GOLD   = 0xC9A84C
C_RED    = 0xC0392B
C_GREEN  = 0x1ABC9C
C_YELLOW = 0xF1C40F
C_BLUE   = 0x2C3E7A
C_DARK   = 0x0D0D1A

DEFAULT_SHOP = {
    "VIP":            {"price": 500,  "type": "role",      "desc": "Rôle VIP cosmétique"},
    "Casino Pro":     {"price": 1000, "type": "role",      "desc": "Rôle prestige du casino"},
    "Rôle Chanceux":  {"price": 300,  "type": "role",      "desc": "Petit boost de chance"},
    "Bouclier":       {"price": 400,  "type": "shield",    "desc": "Bloque le prochain vol/braquage"},
    "Boost XP":       {"price": 600,  "type": "xpboost",   "desc": "x2 XP pendant 1h"},
    "Double Casino":  {"price": 800,  "type": "casinox2",  "desc": "Double les gains casino pendant 1h"},
    "Alarme":         {"price": 350,  "type": "alarm",     "desc": "Réduit la chance qu'on te vole (3 utilisations)"},
}

# XP & Niveaux
XP_MIN          = 5
XP_MAX          = 15
XP_COOLDOWN_SEC = 60

# Catégories de permissions personnalisables
PERM_CATEGORIES = ["mod", "eco", "admin", "events"]

# Rôles de niveau (par défaut, configurable via !setlevelrole)
DEFAULT_LEVEL_ROLES = {
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
    "rich_100k":   ("Magnat",           "🏦", "Avoir 100 000 pièces"),
    "gambler":     ("Joueur",           "🎰", "Utiliser !gamble"),
    "thief_ok":    ("Voleur",           "🦹", "Réussir un vol"),
    "thief_fail":  ("Maladroit",        "😅", "Échouer un vol"),
    "robber":      ("Braqueur",         "💣", "Réussir un braquage"),
    "duelist":     ("Duelliste",        "⚔️", "Gagner un duel"),
    "popular":     ("Populaire",        "💖", "Recevoir 10 réputations"),
    "clan_member": ("Membre de clan",   "🏰", "Rejoindre un clan"),
    "quest_done":  ("Aventurier",       "🗺️", "Compléter une quête"),
    "collector":   ("Collectionneur",   "📚", "Avoir 10 cartes"),
    "warned":      ("Mauvais élève",    "⚠️", "Recevoir 3 avertissements"),
    "daily_7":     ("Régulier",         "📅", "Faire !daily 7 jours"),
    "treasure":    ("Chasseur de trésor","💰", "Attraper un trésor aléatoire"),
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

# Quêtes journalières disponibles
QUEST_TEMPLATES = [
    {"id": "msg_20",   "desc": "Envoyer 20 messages",          "target": 20, "type": "messages",  "reward": 250},
    {"id": "msg_50",   "desc": "Envoyer 50 messages",          "target": 50, "type": "messages",  "reward": 500},
    {"id": "cmd_5",    "desc": "Utiliser 5 commandes",         "target": 5,  "type": "commands",  "reward": 200},
    {"id": "win_3",    "desc": "Gagner 3 jeux casino",         "target": 3,  "type": "wins",      "reward": 400},
    {"id": "rep_1",    "desc": "Donner 1 réputation",          "target": 1,  "type": "reps",      "reward": 150},
    {"id": "vol_1",    "desc": "Réussir un vol/braquage",      "target": 1,  "type": "thefts",    "reward": 350},
    {"id": "daily_1",  "desc": "Réclamer ta récompense daily", "target": 1,  "type": "dailies",   "reward": 100},
]

# ══════════════════════════════════════════════════════
#  PERSISTANCE JSON
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
    try:
        loop = asyncio.get_event_loop()
        if filename in _pending_saves:
            _pending_saves[filename].cancel()
        _pending_saves[filename] = loop.create_task(_delayed(filename, data))
    except RuntimeError:
        _write(filename, data)

# ── Données persistées ──────────────────────────────
balances       = _load("balances",       {})
warns          = _load("warns",          {})
shop_items     = _load("shop",           DEFAULT_SHOP)
cards          = _load("cards",          {})
auto_roles     = _load("auto_roles",     {})
reaction_roles = _load("reaction_roles", {})
auto_responses = _load("auto_responses", {})
word_filter    = _load("word_filter",    {})
link_filter    = _load("link_filter",    {})

xp_data        = _load("xp",             {})
achievements_d = _load("achievements",   {})
daily_streak   = _load("daily_streak",   {})

# ── Nouveau : permissions, config, social ───────────
# guild_perms[gid] = {"mod": [role_id,...], "eco": [...], "admin": [...], "events": [...]}
guild_perms    = _load("guild_perms",    {})
# guild_config[gid] = {"levelup_channel": id, "levelup_enabled": bool, "log_channel": id,
#                      "level_roles": {"5": role_id, ...}, "self_roles": [role_id,...]}
guild_config   = _load("guild_config",   {})
# Réputation : reputation[uid] = int
reputation     = _load("reputation",     {})
rep_cooldowns  = _load("rep_cooldowns",  {})  # uid -> last_ts
# Inventaire d'objets : inventory[uid] = {"shield": 1, "alarm": 3, ...}
inventory      = _load("inventory",      {})
# Buffs actifs : buffs[uid] = {"xpboost": ts_end, "casinox2": ts_end}
buffs          = _load("buffs",          {})
# Clans : clans[clan_name] = {"owner": uid, "members": [...], "bank": int, "level": int, "xp": int, "guild": gid, "desc": str}
clans          = _load("clans",          {})
# Quêtes : quests[uid] = {"date": "YYYY-MM-DD", "active": [{"id":..,"type":..,"target":..,"progress":..,"reward":..,"desc":..,"done":False}]}
quests         = _load("quests",         {})
# Banque protégée du vol : bank[uid] = int
bank_data      = _load("bank",           {})
# Mariage : marriages[uid] = {"spouse": uid_spouse, "since": "YYYY-MM-DD"}
marriages      = _load("marriages",      {})
# Demandes de mariage en attente : marriage_requests[target_uid] = proposer_uid (mémoire)
# AFK : afk[uid] = {"reason": str, "since": ts, "guild": gid}
afk_data       = _load("afk",            {})
# Codes promo : promo_codes[code] = {"amount": int, "max_uses": int, "used_by": [uid,...]}
promo_codes    = _load("promo_codes",    {})

# ── Données en mémoire uniquement ───────────────────
spam_tracker: dict  = {}
snipe_cache:  dict  = {}
reminders:    list  = []
xp_cooldowns: dict  = {}
treasure_state: dict = {}   # gid -> {"active": True, "amount": int, "channel": id}

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
#  HELPERS — CONFIG / PERMISSIONS DYNAMIQUES (PAR ID)
# ══════════════════════════════════════════════════════
def get_gconf(gid: str) -> dict:
    guild_config.setdefault(gid, {
        "levelup_channel":  None,
        "levelup_enabled":  True,
        "log_channel":      None,
        "level_roles":      {},     # "5": role_id
        "self_roles":       [],     # role_ids attribuables via !role
        "treasure_channel": None,   # salon dédié aux trésors (None = auto)
        "treasure_next":    0,      # timestamp du prochain spawn
    })
    # rétro-compat
    guild_config[gid].setdefault("treasure_channel", None)
    guild_config[gid].setdefault("treasure_next", 0)
    return guild_config[gid]

def get_gperms(gid: str) -> dict:
    guild_perms.setdefault(gid, {cat: [] for cat in PERM_CATEGORIES})
    # garantir que toutes les clés existent
    for cat in PERM_CATEGORIES:
        guild_perms[gid].setdefault(cat, [])
    return guild_perms[gid]

def is_super_owner(user) -> bool:
    """Permission absolue : le bot owner principal."""
    try:
        return int(getattr(user, "id", 0)) == SUPER_OWNER_ID
    except Exception:
        return False

def is_owner(member: discord.Member) -> bool:
    """
    Permission "owner" :
    - SUPER_OWNER_ID : toujours autorisé (toi)
    - le propriétaire du serveur Discord
    - un admin Discord natif (administrator)
    """
    if is_super_owner(member):
        return True
    if member.guild and member.guild.owner_id == member.id:
        return True
    return bool(member.guild_permissions.administrator)

def has_perm(member: discord.Member, category: str) -> bool:
    """
    Vérifie si un membre a la permission pour une catégorie donnée.
    Sécurisé : utilise l'ID des rôles, pas le nom.
    """
    if is_owner(member):
        return True
    if not member.guild:
        return False
    gperms = get_gperms(str(member.guild.id))
    allowed_ids = set(gperms.get(category, []))
    # ainsi que les permissions admin (super-set)
    allowed_ids |= set(gperms.get("admin", []))
    member_role_ids = {r.id for r in member.roles}
    return bool(allowed_ids & member_role_ids)

def is_mod(member: discord.Member) -> bool:
    """Raccourci : permission de modération."""
    if is_owner(member):
        return True
    if member.guild_permissions.manage_messages or member.guild_permissions.kick_members:
        return True
    return has_perm(member, "mod")

def role_is_safe_to_manage(guild: discord.Guild, target_role: discord.Role,
                           actor: discord.Member) -> tuple[bool, str]:
    """
    Vérifie qu'un rôle est sûr à manipuler :
    - pas @everyone
    - pas un rôle géré (booster, intégration, bot)
    - pas plus haut que le top role de l'acteur (sauf owner)
    - pas plus haut que le top role du bot
    """
    if target_role.is_default():
        return False, "Impossible de manipuler le rôle @everyone."
    if target_role.managed:
        return False, "Ce rôle est géré par Discord (booster/bot/intégration)."
    me = guild.me
    if me and target_role >= me.top_role:
        return False, "Ce rôle est au-dessus du rôle du bot."
    if not is_owner(actor):
        if target_role >= actor.top_role:
            return False, "Tu ne peux pas manipuler un rôle ≥ à ton rôle le plus haut."
    if target_role.permissions.administrator:
        return False, "Refus : ce rôle est administrateur (trop sensible)."
    return True, "ok"

# ══════════════════════════════════════════════════════
#  HELPERS — SOLDE / XP
# ══════════════════════════════════════════════════════
def get_bal(uid: str) -> int:
    balances.setdefault(uid, 100)
    return balances[uid]

def set_bal(uid: str, amount: int):
    balances[uid] = max(0, amount)
    save("balances", balances)

def add_bal(uid: str, amount: int):
    set_bal(uid, get_bal(uid) + amount)

async def send_log(guild: discord.Guild, embed: discord.Embed):
    gconf = get_gconf(str(guild.id))
    ch = None
    if gconf.get("log_channel"):
        ch = guild.get_channel(gconf["log_channel"])
    if not ch:
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

async def no_perm(ctx, category: str = None):
    msg = "Vous ne disposez pas des permissions nécessaires."
    if category:
        msg += f"\nCatégorie requise : `{category}`"
    await ctx.send(embed=_foot(em_err("Accès refusé",
        f"```\n{msg}\n```"), ctx.author),
        delete_after=8)

# ══════════════════════════════════════════════════════
#  HELPERS — XP / NIVEAUX / SUCCÈS / BUFFS
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
    achievements_d.setdefault(uid, [])
    if key not in achievements_d[uid]:
        achievements_d[uid].append(key)
        save("achievements", achievements_d)
        return True
    return False

def check_balance_achievements(uid: str):
    bal = get_bal(uid)
    if bal >= 1000:    grant_achievement(uid, "rich_1k")
    if bal >= 10000:   grant_achievement(uid, "rich_10k")
    if bal >= 100000:  grant_achievement(uid, "rich_100k")

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

def get_buff(uid: str, key: str) -> bool:
    b = buffs.get(uid, {})
    end = b.get(key, 0)
    if end and end > datetime.utcnow().timestamp():
        return True
    return False

def add_buff(uid: str, key: str, seconds: int):
    buffs.setdefault(uid, {})
    base = max(buffs[uid].get(key, 0), datetime.utcnow().timestamp())
    buffs[uid][key] = base + seconds
    save("buffs", buffs)

def get_inv(uid: str) -> dict:
    inventory.setdefault(uid, {})
    return inventory[uid]

def add_item(uid: str, key: str, qty: int = 1):
    inv = get_inv(uid)
    inv[key] = inv.get(key, 0) + qty
    save("inventory", inventory)

def use_item(uid: str, key: str) -> bool:
    inv = get_inv(uid)
    if inv.get(key, 0) > 0:
        inv[key] -= 1
        if inv[key] <= 0:
            inv.pop(key, None)
        save("inventory", inventory)
        return True
    return False

# ══════════════════════════════════════════════════════
#  HELPERS — QUÊTES
# ══════════════════════════════════════════════════════
def today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def get_quests(uid: str) -> dict:
    q = quests.get(uid)
    if not q or q.get("date") != today_str():
        # Génère 3 nouvelles quêtes
        chosen = random.sample(QUEST_TEMPLATES, 3)
        q = {
            "date": today_str(),
            "active": [
                {**c, "progress": 0, "done": False, "claimed": False}
                for c in chosen
            ]
        }
        quests[uid] = q
        save("quests", quests)
    return q

def progress_quest(uid: str, qtype: str, amount: int = 1):
    q = get_quests(uid)
    changed = False
    for it in q["active"]:
        if it["type"] == qtype and not it["done"]:
            it["progress"] = min(it["progress"] + amount, it["target"])
            if it["progress"] >= it["target"]:
                it["done"] = True
            changed = True
    if changed:
        save("quests", quests)

# ══════════════════════════════════════════════════════
#  ÉVÉNEMENTS
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="le serveur 👁️"),
        status=discord.Status.do_not_disturb
    )
    if not reminder_task.is_running():
        reminder_task.start()
    if not random_event_task.is_running():
        random_event_task.start()
    logger.info(f"Connecté : {bot.user} ({bot.user.id})")

@bot.event
async def on_member_join(member: discord.Member):
    gid = str(member.guild.id)
    # auto_roles : on supporte ID (nouveau) et nom (ancien) pour rétro-compat
    val = auto_roles.get(gid)
    role = None
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        role = member.guild.get_role(int(val))
    elif isinstance(val, str):
        role = discord.utils.get(member.guild.roles, name=val)
    if role:
        try:
            await member.add_roles(role, reason="Auto-role")
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
        role_ref = reaction_roles[key].get(str(reaction.emoji))
        if role_ref and reaction.message.guild:
            role = None
            if isinstance(role_ref, int) or (isinstance(role_ref, str) and str(role_ref).isdigit()):
                role = reaction.message.guild.get_role(int(role_ref))
            else:
                role = discord.utils.get(reaction.message.guild.roles, name=role_ref)
            if role:
                try:
                    await user.add_roles(role, reason="Reaction role")
                except discord.Forbidden:
                    pass

@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return
    key = str(reaction.message.id)
    if key in reaction_roles:
        role_ref = reaction_roles[key].get(str(reaction.emoji))
        if role_ref and reaction.message.guild:
            role = None
            if isinstance(role_ref, int) or (isinstance(role_ref, str) and str(role_ref).isdigit()):
                role = reaction.message.guild.get_role(int(role_ref))
            else:
                role = discord.utils.get(reaction.message.guild.roles, name=role_ref)
            if role:
                try:
                    await user.remove_roles(role, reason="Reaction role")
                except discord.Forbidden:
                    pass

@bot.event
async def on_voice_state_update(member: discord.Member, before, after):
    if before.channel is None and after.channel is not None:
        uid = str(member.id)
        add_bal(uid, random.randint(5, 20))

@bot.event
async def on_command_completion(ctx):
    progress_quest(str(ctx.author.id), "commands")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    gid     = str(message.guild.id)
    content = message.content.lower()

    # ── AFK : retire le statut quand l'utilisateur reparle ──
    uid_msg = str(message.author.id)
    if uid_msg in afk_data:
        info = afk_data.pop(uid_msg)
        save("afk", afk_data)
        try:
            since = int(info.get("since", 0))
            await message.channel.send(
                embed=em_ok("◇ De retour",
                    f"{message.author.mention}, ton AFK est retiré (depuis <t:{since}:R>)."),
                delete_after=8)
        except discord.Forbidden:
            pass

    # ── AFK : prévient quand quelqu'un mentionne un AFK ──
    if message.mentions:
        notified = set()
        for m in message.mentions:
            mid = str(m.id)
            if mid in afk_data and mid != uid_msg and mid not in notified:
                notified.add(mid)
                info = afk_data[mid]
                since = int(info.get("since", 0))
                reason = info.get("reason") or "Aucune raison"
                try:
                    e = em_info(f"💤 {m.display_name} est AFK",
                        f"> **Raison :** {reason}\n> **Depuis :** <t:{since}:R>")
                    await message.channel.send(embed=e, delete_after=15)
                except discord.Forbidden:
                    pass

    # Filtre mots
    for word in word_filter.get(gid, []):
        if word in content:
            try: await message.delete()
            except discord.Forbidden: pass
            try:
                await message.channel.send(
                    embed=em_err("Message supprimé",
                        f"{message.author.mention}, ce mot est interdit ici."),
                    delete_after=4)
            except discord.Forbidden: pass
            return

    # Filtre liens
    if link_filter.get(gid) and URL_PATTERN.search(message.content):
        if not is_mod(message.author):
            try: await message.delete()
            except discord.Forbidden: pass
            try:
                await message.channel.send(
                    embed=em_err("Lien supprimé",
                        f"{message.author.mention}, les liens ne sont pas autorisés."),
                    delete_after=4)
            except discord.Forbidden: pass
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

    # Quêtes — messages
    progress_quest(uid, "messages")

    # ─── Gain XP ───
    now_ts = now.timestamp()
    if now_ts - xp_cooldowns.get(uid, 0) >= XP_COOLDOWN_SEC:
        xp_cooldowns[uid] = now_ts
        xp_gain    = random.randint(XP_MIN, XP_MAX)
        if get_buff(uid, "xpboost"):
            xp_gain *= 2
        info       = get_xp_info(uid)
        old_level  = info["level"]
        info["xp"] += xp_gain
        new_level  = calc_level(info["xp"])
        info["level"] = new_level
        save("xp", xp_data)

        if info["xp"] <= xp_gain:
            grant_achievement(uid, "first_msg")

        if new_level > old_level:
            gconf = get_gconf(gid)
            target_ch = message.channel
            if gconf.get("levelup_enabled", True):
                if gconf.get("levelup_channel"):
                    ch = message.guild.get_channel(gconf["levelup_channel"])
                    if ch: target_ch = ch
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
                    e.set_thumbnail(url=ASSETS["level_up"])
                    e.set_image(url=message.author.display_avatar.url)
                    await target_ch.send(embed=e)
                except discord.Forbidden:
                    pass

            # Rôles de niveau (par ID, configuré via !setlevelrole)
            level_roles = get_gconf(gid).get("level_roles", {})
            role_id = level_roles.get(str(new_level))
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Niveau {new_level}")
                    except discord.Forbidden:
                        pass

            if new_level >= 5:  grant_achievement(uid, "level_5")
            if new_level >= 10: grant_achievement(uid, "level_10")
            if new_level >= 25: grant_achievement(uid, "level_25")
            if new_level >= 50: grant_achievement(uid, "level_50")

    # Trésor aléatoire — premier qui clique
    tre = treasure_state.get(gid)
    if tre and tre.get("active") and tre.get("channel") == message.channel.id:
        if "!claim" in content or "claim" == content.strip():
            tre["active"] = False
            amt = tre["amount"]
            add_bal(uid, amt)
            grant_achievement(uid, "treasure")
            try:
                await message.channel.send(embed=em_gold(
                    "Trésor capturé !",
                    f"{message.author.mention} a attrapé le trésor de **{amt:,} pièces** ! 💰"
                ))
            except discord.Forbidden:
                pass

    # Réponses automatiques
    is_command = message.content.startswith(bot.command_prefix)
    if not is_command:
        for trigger, response in auto_responses.get(gid, {}).items():
            if trigger in content:
                try: await message.channel.send(response)
                except discord.Forbidden: pass
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
#  TÂCHES — RAPPELS / ÉVÉNEMENTS ALÉATOIRES
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

TREASURE_MIN_DELAY = 2 * 3600   # 2h minimum entre 2 spawns
TREASURE_MAX_DELAY = 8 * 3600   # 8h maximum

def _schedule_next_treasure(gconf: dict):
    """Planifie le prochain spawn dans 2h à 8h."""
    delay = random.randint(TREASURE_MIN_DELAY, TREASURE_MAX_DELAY)
    gconf["treasure_next"] = datetime.utcnow().timestamp() + delay
    save("guild_config", guild_config)

@tasks.loop(minutes=2)
async def random_event_task():
    """Spawne un trésor à intervalle aléatoire (2h-8h) par serveur, dans le salon configuré."""
    now = datetime.utcnow().timestamp()
    for guild in bot.guilds:
        gid = str(guild.id)
        gconf = get_gconf(gid)
        # Initialisation : planifie un premier spawn si jamais configuré
        if not gconf.get("treasure_next"):
            _schedule_next_treasure(gconf)
            continue
        if now < gconf["treasure_next"]:
            continue
        if treasure_state.get(gid, {}).get("active"):
            continue
        # Choix du salon : configuré OU auto-détection
        ch = None
        if gconf.get("treasure_channel"):
            ch = guild.get_channel(int(gconf["treasure_channel"]))
        if ch is None:
            ch = (discord.utils.get(guild.text_channels, name="général")
                  or discord.utils.get(guild.text_channels, name="general")
                  or discord.utils.get(guild.text_channels, name="chat")
                  or (guild.text_channels[0] if guild.text_channels else None))
        if not ch:
            _schedule_next_treasure(gconf)
            continue
        amount = random.randint(150, 800)
        treasure_state[gid] = {"active": True, "amount": amount, "channel": ch.id}
        _schedule_next_treasure(gconf)  # planifie le suivant immédiatement
        try:
            e = em_gold("Un trésor est apparu !",
                f"💰 Un trésor de **{amount:,} pièces** est caché dans ce salon !\n"
                f"Tape `!claim` pour l'attraper en premier !")
            e.set_thumbnail(url=ASSETS["treasure"])
            await ch.send(embed=e)
        except discord.Forbidden:
            pass
        await asyncio.sleep(120)
        if treasure_state.get(gid, {}).get("active"):
            treasure_state[gid]["active"] = False
            try:
                await ch.send(embed=em_dark("Trésor disparu",
                    "💨 Personne n'a réclamé le trésor à temps..."))
            except discord.Forbidden:
                pass

@random_event_task.before_loop
async def before_event():
    await bot.wait_until_ready()

# ══════════════════════════════════════════════════════
#  AIDE
# ══════════════════════════════════════════════════════
HELP_CATS = {
    "perm": {
        "title": "🔐  Permissions", "color": C_RED, "emoji": "🔐",
        "cmds": [
            ("!perms",                              "Voir la config des permissions"),
            ("!permadd <cat> <@rôle>",              "Autoriser un rôle (mod/eco/admin/events)"),
            ("!permremove <cat> <@rôle>",           "Retirer un rôle d'une catégorie"),
            ("!role <@membre> <@rôle>",             "Donner/enlever un rôle (whitelist)"),
            ("!selfrole add/remove <@rôle>",        "Configurer rôles auto-attribuables"),
            ("",                                    "Owner/Admin Discord uniquement"),
        ]
    },
    "mod": {
        "title": "⚔  Modération", "color": C_VIOLET, "emoji": "⚔",
        "cmds": [
            ("!kick <membre> [raison]",         "Expulse un membre"),
            ("!ban <membre> [raison]",           "Bannit un membre"),
            ("!unban <id>",                      "Débannit par ID"),
            ("!mute <membre> [min] [raison]",    "Timeout temporaire"),
            ("!unmute <membre>",                 "Retire le mute"),
            ("!warn <membre> [raison]",          "Avertissement"),
            ("!warns [membre]",                  "Voir les warns"),
            ("!clear [nombre]",                  "Supprime des messages"),
            ("!slowmode [secondes]",             "Slowmode"),
            ("!lock / !unlock",                  "Verrouille/déverrouille le salon"),
            ("!nuke",                            "Recrée le salon (nettoyage total)"),
            ("!emojis <:nom:id> ...",            "Vol d'emojis customs (ou réponse à un msg)"),
            ("!stickers [nom]",                  "Vol de stickers (en réponse à un message)"),
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
            ("!use <objet>",                    "Utiliser un objet d'inventaire"),
            ("!inv",                            "Voir ton inventaire d'objets"),
            ("!gift <@membre>",                 "Cadeau aléatoire à un ami (cd 12h)"),
            ("!work",                           "Petit job honnête (cd 1h)"),
            ("!crime",                          "Crime risqué (cd 2h, +/-)"),
            ("!fish",                           "Pêche aléatoire (cd 5min)"),
            ("!bank",                           "État de ta banque protégée"),
            ("!bank deposit/withdraw <montant>","Déposer/retirer (à l'abri du vol)"),
            ("!redeem <code>",                  "Utiliser un code promo"),
        ]
    },
    "casino": {
        "title": "🎰  Casino", "color": C_GOLD, "emoji": "🎰",
        "cmds": [
            ("!gamble <montant>",               "Pari 50/50 (cd 10s)"),
            ("!slots <montant>",                "Machine à sous (cd 15s)"),
            ("!blackjack <montant>",            "Blackjack (cd 15s)"),
            ("!roulette <montant> <choix>",     "Rouge/noir/pair/impair/<nombre 0-36>"),
            ("!vol <membre>",                   "Vol (cd 1h, risqué)"),
            ("!braquage <membre>",              "Braquage (cd 3h, très risqué, gros gains)"),
        ]
    },
    "social": {
        "title": "💖  Social", "color": C_VIOLET, "emoji": "💖",
        "cmds": [
            ("!rep <@membre>",                  "Donner un point de réputation (cd 24h)"),
            ("!reps [membre]",                  "Voir la réputation"),
            ("!duel <@membre> <montant>",       "Défier en duel pile/face"),
            ("!rps <@membre>",                  "Pierre/Feuille/Ciseaux"),
            ("!quiz",                           "Mini-quiz culture (gain pièces)"),
            ("!conseil",                        "Reçois un conseil aléatoire"),
            ("!ship <@a> <@b>",                 "Compatibilité amoureuse"),
            ("!afk [raison]",                   "Te marquer AFK (notifie les pings)"),
            ("!marry <@membre>",                "Demande en mariage / accepte"),
            ("!divorce",                        "Mettre fin au mariage"),
            ("!couple [membre]",                "Voir l'état marital"),
        ]
    },
    "clan": {
        "title": "🏰  Clans", "color": C_BLUE, "emoji": "🏰",
        "cmds": [
            ("!clan create <nom>",              "Créer un clan (coût 1000)"),
            ("!clan info [nom]",                "Voir un clan"),
            ("!clan invite <@membre>",          "Inviter (owner du clan)"),
            ("!clan join <nom>",                "Rejoindre (si invité)"),
            ("!clan leave",                     "Quitter ton clan"),
            ("!clan deposit <montant>",         "Déposer dans la banque du clan"),
            ("!clan top",                       "Classement des clans"),
        ]
    },
    "quest": {
        "title": "🗺️  Quêtes", "color": C_GREEN, "emoji": "🗺️",
        "cmds": [
            ("!quetes",                         "Voir tes quêtes du jour"),
            ("!claim_quest <id>",               "Réclamer la récompense d'une quête"),
        ]
    },
    "fun": {
        "title": "◇  Fun & Jeux", "color": C_DARK, "emoji": "◇",
        "cmds": [
            ("!roll",                           "Invoquer un perso (cd 30s)"),
            ("!inventory [membre]",             "Ta collection de cartes"),
            ("!8ball <question>",               "Oracle mystique"),
            ("!de [faces]",                     "Lancer un dé"),
            ("!coinflip",                       "Pile ou face"),
            ("!snipe",                          "Dernier message supprimé"),
            ("!avatar [membre]",                "Voir un avatar"),
            ("!serverinfo",                     "Infos serveur"),
            ("!userinfo [membre]",              "Infos membre"),
            ("!banner [membre]",                "Voir une bannière de profil"),
            ("!poll Q? | opt1 | opt2 | ...",    "Sondage à réactions (jusqu'à 10 options)"),
            ("!claim",                          "Attraper le trésor aléatoire"),
        ]
    },
    "niveau": {
        "title": "◈  Niveaux & XP", "color": C_VIOLET, "emoji": "◈",
        "cmds": [
            ("!niveau [membre]",                "Voir son niveau et XP"),
            ("!topxp",                          "Classement XP du serveur"),
            ("!profil [membre]",                "Profil complet stylé"),
            ("!succes [membre]",                "Voir les succès débloqués"),
        ]
    },
    "promo": {
        "title": "🎟️  Codes promo", "color": C_GOLD, "emoji": "🎟️",
        "cmds": [
            ("!redeem <code>",                  "Utiliser un code promo"),
            ("!createcode <code> <montant> [usages]", "Créer un code (admin)"),
            ("!deletecode <code>",              "Supprimer un code (admin)"),
            ("!codes",                          "Lister les codes existants (admin)"),
        ]
    },
    "config": {
        "title": "⚙  Configuration", "color": C_VIOLET, "emoji": "⚙",
        "cmds": [
            ("!setlevelchan #salon",            "Salon des messages level-up"),
            ("!setlogchan #salon",              "Salon des logs de modération"),
            ("!setlevelrole <niv> <@rôle>",     "Rôle attribué à un niveau"),
            ("!setautorole <@rôle>",            "Rôle auto nouveaux membres"),
            ("!settreasure [#salon]",           "Salon des trésors aléatoires (vide = auto)"),
            ("!treasureinfo",                   "Salon + estimation du prochain trésor"),
            ("!addrr <msg_id> <emoji> <@rôle>", "Reaction role"),
            ("!removerr <msg_id> <emoji>",      "Retirer reaction role"),
            ("!rolemenu <titre>",               "Menu boutons pour self-roles"),
            ("!addresponse / !removeresponse",  "Réponses automatiques"),
            ("!addword / !removeword",          "Mots bannis"),
            ("!linkfilter on/off",              "Filtre de liens"),
        ]
    },
    "embeds": {
        "title": "🎨  Embeds", "color": C_GOLD, "emoji": "🎨",
        "cmds": [
            ("!embed <couleur> <titre> | <desc>",        "Embed simple"),
            ("!panel <titre>",                            "Embed multi-sections (sections séparées par ---)"),
            ("!embedraw #salon <couleur> <titre> | <desc>","Envoie dans un autre salon"),
            ("!say <message>",                            "Faire parler le bot"),
        ]
    },
    "remind": {
        "title": "🔔  Rappels", "color": C_DARK, "emoji": "🔔",
        "cmds": [
            ("!reminder <durée> <message>",     "Rappel ; unités s/m/h/j"),
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
    if bot.user and bot.user.display_avatar:
        e.set_thumbnail(url=bot.user.display_avatar.url)
    for key, data in HELP_CATS.items():
        e.add_field(name=f"{data['emoji']}  {data['title'].split('  ',1)[-1]}",
                    value=f"`!help {key}`", inline=True)
    e.set_footer(text=BOT_SIGNATURE,
                 icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    return e

class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.msg  = None
        # Discord limite à 25 boutons / 5 par ligne — on a < 15 catégories
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
            try: await self.msg.edit(view=self)
            except Exception: pass

@bot.command(aliases=["aide", "commands"])
async def help(ctx, category: str = None):
    if category and category.lower() in HELP_CATS:
        return await ctx.send(embed=_build_help_cat_embed(category.lower()))
    view = HelpView(ctx)
    msg  = await ctx.send(embed=_build_help_main_embed(ctx), view=view)
    view.msg = msg

# ══════════════════════════════════════════════════════
#  PERMISSIONS — COMMANDES
# ══════════════════════════════════════════════════════
@bot.command(name="perms", aliases=["showperms"])
@commands.guild_only()
async def show_perms(ctx):
    gid = str(ctx.guild.id)
    gp  = get_gperms(gid)
    e = discord.Embed(title="🔐  Permissions configurées",
                      color=C_VIOLET, timestamp=datetime.utcnow())
    for cat in PERM_CATEGORIES:
        ids = gp.get(cat, [])
        if ids:
            mentions = []
            for rid in ids:
                r = ctx.guild.get_role(int(rid))
                mentions.append(r.mention if r else f"`{rid}` (rôle supprimé)")
            value = " ".join(mentions)
        else:
            value = "*(aucun)*"
        e.add_field(name=f"◈ {cat.upper()}", value=value, inline=False)
    e.set_footer(text=BOT_SIGNATURE)
    await ctx.send(embed=e)

@bot.command(name="permadd")
@commands.guild_only()
async def perm_add(ctx, category: str, role: discord.Role):
    if not is_owner(ctx.author):
        return await no_perm(ctx, "owner/admin Discord")
    cat = category.lower()
    if cat not in PERM_CATEGORIES:
        return await ctx.send(embed=em_err("Catégorie invalide",
            f"Catégories : `{'`, `'.join(PERM_CATEGORIES)}`"))
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))
    gp = get_gperms(str(ctx.guild.id))
    if role.id in gp[cat]:
        return await ctx.send(embed=em_warn("Déjà autorisé",
            f"{role.mention} a déjà la permission `{cat}`."))
    gp[cat].append(role.id)
    save("guild_perms", guild_perms)
    e = em_ok("Permission ajoutée",
        f"Le rôle {role.mention} a maintenant la permission `{cat}`.")
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(name="permremove")
@commands.guild_only()
async def perm_remove(ctx, category: str, role: discord.Role):
    if not is_owner(ctx.author):
        return await no_perm(ctx, "owner/admin Discord")
    cat = category.lower()
    if cat not in PERM_CATEGORIES:
        return await ctx.send(embed=em_err("Catégorie invalide"))
    gp = get_gperms(str(ctx.guild.id))
    if role.id not in gp.get(cat, []):
        return await ctx.send(embed=em_warn("Introuvable",
            f"{role.mention} n'a pas la permission `{cat}`."))
    gp[cat].remove(role.id)
    save("guild_perms", guild_perms)
    e = em_ok("Permission retirée",
        f"Le rôle {role.mention} n'a plus la permission `{cat}`.")
    _foot(e, ctx.author); await ctx.send(embed=e)

# ── !role : ajouter/enlever un rôle d'un membre ────────
@bot.command(name="role")
@commands.guild_only()
async def role_toggle(ctx, member: discord.Member, role: discord.Role):
    """
    Ajoute le rôle s'il ne l'a pas, sinon le retire.
    Sécurité :
    - Owner/admin Discord : peut tout (sauf rôles ≥ que le sien)
    - Avec perm 'mod' ou 'admin' : seulement les rôles whitelist self_roles
    - Empêche auto-attribution d'un rôle non whitelisté
    """
    gconf = get_gconf(str(ctx.guild.id))
    is_admin_action = is_owner(ctx.author) or has_perm(ctx.author, "admin")
    is_mod_action   = has_perm(ctx.author, "mod")

    # Vérification de sécurité
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))

    # Si pas admin, on n'autorise que les rôles whitelistés
    if not is_admin_action:
        if not is_mod_action:
            return await no_perm(ctx, "mod/admin")
        if role.id not in gconf.get("self_roles", []):
            return await ctx.send(embed=em_err("Rôle non autorisé",
                "Ce rôle n'est pas dans la whitelist `selfrole`. "
                "Demande à un admin de l'ajouter via `!selfrole add`."))

    # Anti auto-attribution de rôle de pouvoir : si le membre est l'auteur
    # et que le rôle accorde des permissions sensibles, on bloque (sauf owner Discord).
    if member.id == ctx.author.id and not is_owner(ctx.author):
        sensitive = (role.permissions.manage_guild or role.permissions.manage_roles
                     or role.permissions.kick_members or role.permissions.ban_members
                     or role.permissions.manage_channels)
        if sensitive:
            return await ctx.send(embed=em_err("Refusé",
                "Tu ne peux pas t'auto-attribuer un rôle avec permissions sensibles."))

    try:
        if role in member.roles:
            await member.remove_roles(role, reason=f"!role par {ctx.author}")
            verb = "retiré"
        else:
            await member.add_roles(role, reason=f"!role par {ctx.author}")
            verb = "ajouté"
    except discord.Forbidden:
        return await ctx.send(embed=em_err("Permission Discord",
            "Le bot n'a pas les droits pour gérer ce rôle."))
    e = em_ok(f"Rôle {verb}", f"{role.mention} → {member.mention}")
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(name="selfrole")
@commands.guild_only()
async def selfrole(ctx, action: str, role: discord.Role):
    if not is_owner(ctx.author):
        return await no_perm(ctx, "owner/admin Discord")
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))
    gconf = get_gconf(str(ctx.guild.id))
    sr = gconf.setdefault("self_roles", [])
    a = action.lower()
    if a == "add":
        if role.id in sr:
            return await ctx.send(embed=em_warn("Déjà présent"))
        sr.append(role.id)
        save("guild_config", guild_config)
        return await ctx.send(embed=em_ok("Self-role ajouté", role.mention))
    if a == "remove":
        if role.id not in sr:
            return await ctx.send(embed=em_warn("Absent"))
        sr.remove(role.id)
        save("guild_config", guild_config)
        return await ctx.send(embed=em_ok("Self-role retiré", role.mention))
    await ctx.send(embed=em_err("Action", "`!selfrole add|remove <@rôle>`"))

# ══════════════════════════════════════════════════════
#  CONFIG — SALONS & RÔLES
# ══════════════════════════════════════════════════════
@bot.command(name="setlevelchan")
@commands.guild_only()
async def set_level_chan(ctx, channel: discord.TextChannel = None):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    g = get_gconf(str(ctx.guild.id))
    if channel is None:
        g["levelup_channel"] = None
        save("guild_config", guild_config)
        return await ctx.send(embed=em_ok("Salon level-up désactivé",
            "Les level-up s'afficheront dans le salon courant."))
    g["levelup_channel"] = channel.id
    save("guild_config", guild_config)
    e = em_ok("Salon level-up configuré", f"Les level-up iront dans {channel.mention}")
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(name="settreasure", aliases=["settreasurechan", "settresorchan"])
@commands.guild_only()
async def set_treasure_chan(ctx, channel: discord.TextChannel = None):
    """Configure le salon où apparaîtront les trésors aléatoires (auto si vide)."""
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    g = get_gconf(str(ctx.guild.id))
    if channel is None:
        g["treasure_channel"] = None
        save("guild_config", guild_config)
        return await ctx.send(embed=em_ok("Salon trésors — auto",
            "Les trésors apparaîtront dans le salon principal détecté."))
    g["treasure_channel"] = channel.id
    save("guild_config", guild_config)
    # Re-planifie pour bénéficier tout de suite du changement
    _schedule_next_treasure(g)
    nxt = int(g["treasure_next"])
    e = em_ok("Salon trésors configuré",
        f"💰 Les trésors apparaîtront désormais dans {channel.mention}.\n"
        f"> Intervalle aléatoire : **2h à 8h**\n"
        f"> Prochain spawn estimé : <t:{nxt}:R>")
    e.set_thumbnail(url=ASSETS["treasure"])
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(name="treasureinfo", aliases=["tresorinfo"])
@commands.guild_only()
async def treasure_info(ctx):
    """Affiche le salon configuré et l'estimation du prochain trésor."""
    g = get_gconf(str(ctx.guild.id))
    ch_id = g.get("treasure_channel")
    ch = ctx.guild.get_channel(int(ch_id)) if ch_id else None
    nxt = int(g.get("treasure_next") or 0)
    desc = (
        f"> **Salon :** {ch.mention if ch else '*(auto)*'}\n"
        f"> **Intervalle :** entre **2h** et **8h** (aléatoire)\n"
        f"> **Prochain spawn :** {('<t:'+str(nxt)+':R>') if nxt else '*à planifier*'}"
    )
    e = em_info("💰 Trésors aléatoires", desc)
    e.set_thumbnail(url=ASSETS["treasure"])
    await ctx.send(embed=e)

@bot.command(name="setlogchan")
@commands.guild_only()
async def set_log_chan(ctx, channel: discord.TextChannel):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    g = get_gconf(str(ctx.guild.id))
    g["log_channel"] = channel.id
    save("guild_config", guild_config)
    await ctx.send(embed=em_ok("Salon de logs", f"Logs envoyés dans {channel.mention}"))

@bot.command(name="setlevelrole")
@commands.guild_only()
async def set_level_role(ctx, niveau: int, role: discord.Role):
    if not is_owner(ctx.author):
        return await no_perm(ctx, "owner/admin Discord")
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))
    g = get_gconf(str(ctx.guild.id))
    g.setdefault("level_roles", {})[str(niveau)] = role.id
    save("guild_config", guild_config)
    await ctx.send(embed=em_ok("Rôle de niveau",
        f"Niveau **{niveau}** → {role.mention}"))

# ══════════════════════════════════════════════════════
#  MODÉRATION
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    if member.top_role >= ctx.author.top_role and not is_owner(ctx.author):
        return await ctx.send(embed=em_err("Hiérarchie",
            "Tu ne peux pas modérer un membre avec un rôle ≥ au tien."))
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
    log = em_mod("Kick")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Modérateur",value=str(ctx.author))
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
@commands.guild_only()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    if member.top_role >= ctx.author.top_role and not is_owner(ctx.author):
        return await ctx.send(embed=em_err("Hiérarchie",
            "Tu ne peux pas modérer un membre avec un rôle ≥ au tien."))
    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=em_err("Permission refusée"))
    e = em_err("Membre banni")
    e.add_field(name="◈ Membre",    value=member.mention,     inline=True)
    e.add_field(name="◈ Modérateur",value=ctx.author.mention, inline=True)
    e.add_field(name="◈ Raison",    value=f"```{reason}```",  inline=False)
    e.set_thumbnail(url=ASSETS["ban"])
    e.set_image(url=member.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)
    log = em_err("Ban")
    log.add_field(name="Membre",    value=f"{member} `{member.id}`")
    log.add_field(name="Modérateur",value=str(ctx.author))
    log.add_field(name="Raison",    value=reason, inline=False)
    await send_log(ctx.guild, log)

@bot.command()
@commands.guild_only()
async def unban(ctx, user_id: int):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
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
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    if member.top_role >= ctx.author.top_role and not is_owner(ctx.author):
        return await ctx.send(embed=em_err("Hiérarchie",
            "Tu ne peux pas modérer un membre ≥ à toi."))
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
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    try:
        await member.timeout(None)
        e = em_ok("Membre démuté", f"{member.mention} peut de nouveau écrire.")
        _foot(e, ctx.author); await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

@bot.command()
@commands.guild_only()
async def clear(ctx, amount: int = 10):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
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
@commands.cooldown(1, 5, commands.BucketType.user)
async def warn(ctx, member: discord.Member, *, reason="Comportement inapproprié"):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    uid = str(member.id)
    warns.setdefault(uid, [])
    warns[uid].append({"reason": reason, "by": str(ctx.author)})
    save("warns", warns)
    count = len(warns[uid])
    e = em_warn(f"Avertissement #{count}")
    e.add_field(name="◈ Membre",      value=member.mention,      inline=True)
    e.add_field(name="◈ Total warns", value=f"`{count}`",         inline=True)
    e.add_field(name="◈ Raison",      value=f"```{reason}```",   inline=False)
    e.set_thumbnail(url=ASSETS["warn"])
    _foot(e, ctx.author); await ctx.send(embed=e)
    if count >= 3:
        grant_achievement(uid, "warned")
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
async def slowmode(ctx, secondes: int = 0):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    secondes = max(0, min(secondes, 21600))
    try:
        await ctx.channel.edit(slowmode_delay=secondes)
        await ctx.send(embed=em_ok("Slowmode", f"Délai = `{secondes}s`"))
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

@bot.command()
@commands.guild_only()
async def lock(ctx):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=em_warn("🔒 Salon verrouillé", "Personne ne peut écrire."))
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

@bot.command()
@commands.guild_only()
async def unlock(ctx):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=em_ok("🔓 Salon déverrouillé"))
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

@bot.command()
@commands.guild_only()
async def nuke(ctx):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    ch = ctx.channel
    try:
        new = await ch.clone(reason=f"Nuke par {ctx.author}")
        await new.edit(position=ch.position)
        await ch.delete()
        await new.send(embed=em_warn("💥 Salon recréé",
            f"Le salon a été nettoyé par {ctx.author.mention}."))
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

# ══════════════════════════════════════════════════════
#  ÉCONOMIE
# ══════════════════════════════════════════════════════
@bot.command(aliases=["bal", "argent"])
@commands.guild_only()
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid    = str(target.id)
    bal    = get_bal(uid)
    e = em_gold(f"Solde — {target.display_name}",
        f"```\n{bal:,} pièces\n```")
    e.set_thumbnail(url=target.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    uid = str(ctx.author.id)
    streak = daily_streak.get(uid, {"streak": 0, "last": None})
    last = streak.get("last")
    today = today_str()
    if last:
        last_dt = datetime.strptime(last, "%Y-%m-%d")
        delta = (datetime.utcnow() - last_dt).days
        if delta == 1:
            streak["streak"] += 1
        elif delta > 1:
            streak["streak"] = 1
    else:
        streak["streak"] = 1
    streak["last"] = today
    daily_streak[uid] = streak
    save("daily_streak", daily_streak)
    bonus = min(streak["streak"] * 50, 500)
    total = DAILY_AMOUNT + bonus
    add_bal(uid, total)
    check_balance_achievements(uid)
    if streak["streak"] >= 7:
        grant_achievement(uid, "daily_7")
    progress_quest(uid, "dailies")
    e = em_gold("Récompense journalière",
        f"```\n+ {total:,} pièces\n```\n"
        f"> Streak : **{streak['streak']} jour(s)** (bonus +{bonus})\n"
        f"> Solde : `{get_bal(uid):,}`")
    e.set_thumbnail(url=ASSETS["daily"])
    e.set_image(url=ctx.author.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(aliases=["pay"])
@commands.guild_only()
async def don(ctx, member: discord.Member, montant: int):
    if member.bot or member.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    if montant <= 0:
        return await ctx.send(embed=em_err("Montant invalide"))
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -montant)
    add_bal(str(member.id), montant)
    e = em_ok("Don envoyé",
        f"{ctx.author.mention} a donné **{montant:,}** pièces à {member.mention}.")
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(aliases=["lb", "top"])
@commands.guild_only()
async def leaderboard(ctx):
    rows = []
    for m in ctx.guild.members:
        if m.bot: continue
        b = get_bal(str(m.id))
        if b > 100:
            rows.append((m.display_name, b))
    rows.sort(key=lambda x: x[1], reverse=True)
    rows = rows[:10]
    if not rows:
        return await ctx.send(embed=em_info("Classement", "Aucune fortune notable."))
    medals = ["🥇", "🥈", "🥉"] + ["✦"] * 7
    lines = [f"{medals[i]}  **{n}** — `{b:,}` pièces" for i, (n, b) in enumerate(rows)]
    e = em_gold("Classement richesse", "\n".join(lines))
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def shop(ctx):
    if not shop_items:
        return await ctx.send(embed=em_info("Boutique vide"))
    lines = []
    for name, data in shop_items.items():
        if isinstance(data, dict):
            lines.append(f"`{data['price']:>6,}` — **{name}**  *({data.get('desc','')})*")
        else:
            lines.append(f"`{data:>6,}` — **{name}**")
    e = em_gold("Boutique", "\n".join(lines) + "\n\n*Achète avec* `!buy <nom>`")
    e.set_thumbnail(url=ASSETS["shop"])
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def buy(ctx, *, item_name: str):
    item = next((k for k in shop_items if k.lower() == item_name.lower()), None)
    if not item:
        return await ctx.send(embed=em_err("Article inconnu"))
    data = shop_items[item]
    price = data["price"] if isinstance(data, dict) else data
    typ   = data.get("type", "role") if isinstance(data, dict) else "role"
    uid = str(ctx.author.id)
    if get_bal(uid) < price:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -price)
    if typ == "role":
        role = discord.utils.get(ctx.guild.roles, name=item)
        if role:
            try: await ctx.author.add_roles(role, reason="Achat boutique")
            except discord.Forbidden: pass
        msg = f"Tu as acheté le rôle **{item}** !"
    elif typ == "shield":
        add_item(uid, "shield"); msg = "🛡 Bouclier ajouté à ton inventaire."
    elif typ == "alarm":
        add_item(uid, "alarm", 3); msg = "🚨 Alarme x3 ajoutée."
    elif typ == "xpboost":
        add_buff(uid, "xpboost", 3600); msg = "✨ Boost XP x2 actif pendant 1h."
    elif typ == "casinox2":
        add_buff(uid, "casinox2", 3600); msg = "🎰 Double gains casino actifs 1h."
    else:
        msg = "Article ajouté."
    e = em_ok("Achat", f"{msg}\n> Solde : `{get_bal(uid):,}`")
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(name="inv", aliases=["sac"])
@commands.guild_only()
async def show_inv(ctx, member: discord.Member = None):
    target = member or ctx.author
    inv = get_inv(str(target.id))
    b   = buffs.get(str(target.id), {})
    if not inv and not b:
        return await ctx.send(embed=em_info(f"Inventaire — {target.display_name}",
            "Inventaire vide."))
    lines = []
    icons = {"shield":"🛡 Bouclier", "alarm":"🚨 Alarme", "xpboost":"✨ Boost XP", "casinox2":"🎰 Casino x2"}
    for k, v in inv.items():
        lines.append(f"{icons.get(k, k)}  ×{v}")
    now = datetime.utcnow().timestamp()
    for k, end in b.items():
        if end > now:
            mins = int((end - now) // 60)
            lines.append(f"⏱ Buff `{k}` actif encore **{mins} min**")
    e = em_dark(f"Inventaire — {target.display_name}", "\n".join(lines))
    e.set_thumbnail(url=target.display_avatar.url)
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def use(ctx, *, objet: str):
    uid = str(ctx.author.id)
    key = objet.lower()
    aliases = {"bouclier":"shield", "alarme":"alarm", "xpboost":"xpboost",
               "boost":"xpboost", "casino":"casinox2"}
    key = aliases.get(key, key)
    if not get_inv(uid).get(key):
        return await ctx.send(embed=em_err("Objet introuvable", "Tu n'as pas cet objet."))
    use_item(uid, key)
    if key == "shield":
        add_buff(uid, "shield_active", 86400 * 7)
        msg = "🛡 Bouclier activé pour 7 jours (bloque le prochain vol)."
    elif key == "alarm":
        add_buff(uid, "alarm_active", 86400 * 3)
        msg = "🚨 Alarme active 3 jours (réduit la chance qu'on te vole)."
    elif key == "xpboost":
        add_buff(uid, "xpboost", 3600); msg = "✨ Boost XP actif 1h."
    elif key == "casinox2":
        add_buff(uid, "casinox2", 3600); msg = "🎰 Double casino actif 1h."
    else:
        msg = "Objet utilisé."
    e = em_ok("Objet utilisé", msg)
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
@commands.cooldown(1, 43200, commands.BucketType.user)
async def gift(ctx, member: discord.Member):
    if member.bot or member.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    amount = random.randint(50, 500)
    add_bal(str(member.id), amount)
    e = em_gold("🎁  Cadeau",
        f"{ctx.author.mention} offre **{amount:,} pièces** à {member.mention} !")
    e.set_thumbnail(url=ASSETS["gift"])
    await ctx.send(embed=e)

# ── Gamble / Slots / Vol classique ─────────────────────
@bot.command()
@commands.guild_only()
@commands.cooldown(1, 10, commands.BucketType.user)
async def gamble(ctx, montant: int = 0):
    if montant < 10:
        return await ctx.send(embed=em_err("Mise invalide", "Min: 10"))
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    grant_achievement(uid, "gambler")
    win = random.random() < 0.5
    if win:
        gain = montant
        if get_buff(uid, "casinox2"):
            gain *= 2
        add_bal(uid, gain)
        progress_quest(uid, "wins")
        check_balance_achievements(uid)
        e = em_ok("Gagné !", f"+**{gain:,}** pièces 🎉")
    else:
        add_bal(uid, -montant)
        e = em_err("Perdu", f"-**{montant:,}** pièces 💸")
    e.add_field(name="Solde", value=f"`{get_bal(uid):,}`")
    e.set_thumbnail(url=ASSETS["gamble"])
    await ctx.send(embed=e)

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
SLOT_MULT    = {"🍒": 1.5, "🍋": 2.0, "🍊": 2.5, "⭐": 3.0, "💎": 5.0, "7️⃣": 10.0}

@bot.command(aliases=["machine"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def slots(ctx, montant: int = 0):
    if montant < 10:
        return await ctx.send(embed=em_err("Mise invalide", "Mise minimum : `10`."))
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -montant)
    rouleaux = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    grant_achievement(uid, "gambler")
    if rouleaux[0] == rouleaux[1] == rouleaux[2]:
        gain = int(montant * SLOT_MULT[rouleaux[0]])
        if get_buff(uid, "casinox2"): gain *= 2
        add_bal(uid, gain); check_balance_achievements(uid)
        progress_quest(uid, "wins")
        resultat = f"JACKPOT ✨  +**{gain:,}**"; color = C_GOLD
    elif rouleaux[0] == rouleaux[1] or rouleaux[1] == rouleaux[2] or rouleaux[0] == rouleaux[2]:
        gain = int(montant * 1.2)
        if get_buff(uid, "casinox2"): gain *= 2
        add_bal(uid, gain)
        progress_quest(uid, "wins")
        resultat = f"Paire !  +**{gain:,}**"; color = C_GREEN
    else:
        resultat = f"Perdu.  -**{montant:,}**"; color = C_RED
    e = discord.Embed(
        title="🎰  Machine à sous",
        description=(f"```\n| {rouleaux[0]}  {rouleaux[1]}  {rouleaux[2]} |\n```\n"
                     f"{resultat}\n\n> Solde : `{get_bal(uid):,}`"),
        color=color, timestamp=datetime.utcnow())
    e.set_thumbnail(url=ASSETS["slots_thumb"])
    e.set_image(url=ASSETS["slots"])
    e.set_footer(text=random.choice(FOOTERS_ECO) + f"  •  {BOT_SIGNATURE}")
    await ctx.send(embed=e)

# ── Vol ────────────────────────────────────────────────
@bot.command(aliases=["steal"])
@commands.guild_only()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def vol(ctx, cible: discord.Member = None):
    if cible is None or cible.bot or cible.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    uid_v, uid_c = str(ctx.author.id), str(cible.id)
    bal_c = get_bal(uid_c)
    if bal_c < 50:
        return await ctx.send(embed=em_info("Trop pauvre",
            f"{cible.mention} n'a que `{bal_c}` pièces."))
    # Bouclier ?
    if get_buff(uid_c, "shield_active"):
        buffs[uid_c]["shield_active"] = 0; save("buffs", buffs)
        return await ctx.send(embed=em_warn("🛡 Bouclier !",
            f"{cible.mention} avait un bouclier qui a bloqué ton vol."))
    chance = 0.40
    if get_buff(uid_c, "alarm_active"): chance = 0.20
    if random.random() < chance:
        amt = max(1, int(bal_c * random.uniform(0.10, 0.30)))
        add_bal(uid_v, amt); add_bal(uid_c, -amt)
        grant_achievement(uid_v, "thief_ok")
        progress_quest(uid_v, "thefts")
        check_balance_achievements(uid_v)
        e = _em("🦹 Vol réussi",
            f"{ctx.author.mention} a volé **{amt:,}** à {cible.mention}.", C_GREEN)
        e.set_thumbnail(url=ASSETS["vol"])
        await ctx.send(embed=e)
    else:
        amende = max(1, int(get_bal(uid_v) * random.uniform(0.10, 0.20)))
        add_bal(uid_v, -amende)
        grant_achievement(uid_v, "thief_fail")
        e = _em("😅 Vol échoué",
            f"{ctx.author.mention} s'est fait prendre. Amende : **{amende:,}**.", C_RED)
        e.set_thumbnail(url=ASSETS["vol"])
        await ctx.send(embed=e)

# ── Braquage (gros risque, gros gain) ──────────────────
@bot.command(aliases=["heist"])
@commands.guild_only()
@commands.cooldown(1, 10800, commands.BucketType.user)
async def braquage(ctx, cible: discord.Member = None):
    if cible is None or cible.bot or cible.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    uid_v, uid_c = str(ctx.author.id), str(cible.id)
    bal_c = get_bal(uid_c)
    if bal_c < 500:
        return await ctx.send(embed=em_info("Pas assez à braquer",
            f"{cible.mention} doit avoir au moins `500` pièces."))
    if get_buff(uid_c, "shield_active"):
        buffs[uid_c]["shield_active"] = 0; save("buffs", buffs)
        return await ctx.send(embed=em_warn("🛡 Bouclier !",
            f"{cible.mention} était protégé(e). Braquage annulé."))
    intro = em_dark("💣  Braquage en cours…", "🚓 Préparation du braquage...")
    intro.set_image(url=ASSETS["braquage"])
    msg = await ctx.send(embed=intro)
    await asyncio.sleep(1.5)
    step = em_dark("💣  Braquage en cours…", "🔫 Tu entres dans la banque...")
    step.set_image(url=ASSETS["braquage"])
    await msg.edit(embed=step)
    await asyncio.sleep(1.5)
    chance = 0.25
    if get_buff(uid_c, "alarm_active"): chance = 0.10
    if random.random() < chance:
        amt = max(100, int(bal_c * random.uniform(0.30, 0.55)))
        add_bal(uid_v, amt); add_bal(uid_c, -amt)
        grant_achievement(uid_v, "robber")
        progress_quest(uid_v, "thefts")
        check_balance_achievements(uid_v)
        e = _em("💰 BRAQUAGE RÉUSSI",
            f"{ctx.author.mention} braque {cible.mention} pour **{amt:,} pièces** !\n"
            f"> Solde : `{get_bal(uid_v):,}`", C_GOLD)
        e.set_image(url=ASSETS["braquage"])
    else:
        amende = max(100, int(get_bal(uid_v) * random.uniform(0.30, 0.50)))
        add_bal(uid_v, -amende)
        e = _em("🚔 BRAQUAGE RATÉ",
            f"La police t'a coffré ! Amende : **{amende:,} pièces**.\n"
            f"> Solde : `{get_bal(uid_v):,}`", C_RED)
        e.set_image(url=ASSETS["braquage"])
    await msg.edit(embed=e)

# ── Roulette ───────────────────────────────────────────
@bot.command()
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def roulette(ctx, montant: int, choix: str):
    """!roulette <montant> rouge|noir|pair|impair|<0-36>"""
    uid = str(ctx.author.id)
    if montant < 10:
        return await ctx.send(embed=em_err("Mise minimum 10"))
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -montant)
    grant_achievement(uid, "gambler")
    spin1 = em_dark("🎡 Roulette", "La roue tourne...\n```\n🔴 ⚫ 🔴 ⚫ 🔴 ⚫\n```")
    spin1.set_image(url=ASSETS["roulette"])
    msg = await ctx.send(embed=spin1)
    await asyncio.sleep(1.0)
    spin2 = em_dark("🎡 Roulette", "Toujours en mouvement...\n```\n⚫ 🔴 ⚫ 🔴 ⚫ 🔴\n```")
    spin2.set_image(url=ASSETS["roulette"])
    await msg.edit(embed=spin2)
    await asyncio.sleep(1.0)
    res = random.randint(0, 36)
    couleur = "vert" if res == 0 else ("rouge" if res % 2 else "noir")
    emoji_c = "🟢" if couleur == "vert" else ("🔴" if couleur == "rouge" else "⚫")
    c = choix.lower()
    gagne = False; mult = 0
    if c.isdigit() and int(c) == res:
        gagne, mult = True, 14
    elif c == couleur and couleur != "vert":
        gagne, mult = True, 2
    elif c == "pair" and res != 0 and res % 2 == 0:
        gagne, mult = True, 2
    elif c == "impair" and res != 0 and res % 2 == 1:
        gagne, mult = True, 2
    if gagne:
        gain = montant * mult
        if get_buff(uid, "casinox2"): gain *= 2
        add_bal(uid, gain)
        progress_quest(uid, "wins")
        check_balance_achievements(uid)
        e = _em(f"🎡 Roulette — {emoji_c} {res}",
            f"GAGNÉ ! +**{gain:,}** pièces (x{mult})\n> Solde : `{get_bal(uid):,}`", C_GOLD)
    else:
        e = _em(f"🎡 Roulette — {emoji_c} {res}",
            f"Perdu. -**{montant:,}** pièces\n> Solde : `{get_bal(uid):,}`", C_RED)
    e.set_thumbnail(url=ASSETS["roulette_thumb"])
    e.set_image(url=ASSETS["roulette"])
    await msg.edit(embed=e)

# ══════════════════════════════════════════════════════
#  BLACKJACK
# ══════════════════════════════════════════════════════
def _bj_deck():
    vals = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
    random.shuffle(vals)
    return vals

def _bj_total(hand):
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
            result = "Tu as dépassé 21. Perdu !"; color = C_RED
        elif dtot > 21 or ptot > dtot:
            gain = self.mise * 2
            if get_buff(self.uid, "casinox2"): gain *= 2
            add_bal(self.uid, gain)
            result = f"Victoire ! +**{gain:,}** pièces"; color = C_GOLD
            check_balance_achievements(self.uid); progress_quest(self.uid, "wins")
        elif ptot == dtot:
            add_bal(self.uid, self.mise)
            result = "Égalité. Mise remboursée."; color = C_BLUE
        else:
            result = f"Croupier gagne. -**{self.mise:,}** pièces"; color = C_RED
        for child in self.children:
            child.disabled = True
        e = self._embed("🃏  Blackjack — Fin", self._status(reveal=True) + f"\n\n{result}", color)
        await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Tirer", emoji="🃏", style=discord.ButtonStyle.primary)
    async def tirer(self, interaction, button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Pas ta partie.", ephemeral=True)
        self.player.append(self.deck.pop())
        if _bj_total(self.player) > 21:
            return await self.end_game(interaction)
        e = self._embed("🃏  Blackjack", self._status(), C_DARK)
        await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Rester", emoji="🛑", style=discord.ButtonStyle.danger)
    async def rester(self, interaction, button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Pas ta partie.", ephemeral=True)
        await self.end_game(interaction)

@bot.command(aliases=["bj"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def blackjack(ctx, montant: int = 0):
    if montant < 10:
        return await ctx.send(embed=em_err("Mise minimum 10"))
    uid = str(ctx.author.id)
    if get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -montant)
    grant_achievement(uid, "gambler")
    deck   = _bj_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    view = BlackjackView(ctx, deck, player, dealer, montant, uid)
    if _bj_total(player) == 21:
        gain = int(montant * 2.5)
        add_bal(uid, gain); check_balance_achievements(uid)
        progress_quest(uid, "wins")
        return await ctx.send(embed=_em("🃏 Blackjack naturel !",
            f"21 dès le départ ! +**{gain:,}** pièces 🎉", C_GOLD))
    e = discord.Embed(title="🃏  Blackjack",
        description=(f"**Croupier :** `{dealer[0]}` + `?`\n"
                     f"**Toi :** {' + '.join(f'`{c}`' for c in player)} = **{_bj_total(player)}**\n\n"
                     f"Mise : `{montant:,}`"),
        color=C_DARK, timestamp=datetime.utcnow())
    e.set_thumbnail(url=ASSETS["blackjack_thumb"])
    e.set_image(url=ASSETS["blackjack"])
    e.set_footer(text=random.choice(FOOTERS_FUN) + f"  •  {BOT_SIGNATURE}")
    await ctx.send(embed=e, view=view)

# ══════════════════════════════════════════════════════
#  SOCIAL — RÉPUTATION / DUEL / RPS / QUIZ / SHIP
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
async def rep(ctx, member: discord.Member):
    if member.bot or member.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    uid = str(ctx.author.id)
    last = rep_cooldowns.get(uid, 0)
    now = datetime.utcnow().timestamp()
    if now - last < 86400:
        h = int((86400 - (now - last)) // 3600)
        return await ctx.send(embed=em_warn("Cooldown",
            f"Tu pourras redonner une réputation dans **{h}h**."))
    rep_cooldowns[uid] = now
    save("rep_cooldowns", rep_cooldowns)
    target = str(member.id)
    reputation[target] = reputation.get(target, 0) + 1
    save("reputation", reputation)
    if reputation[target] >= 10:
        grant_achievement(target, "popular")
    progress_quest(uid, "reps")
    e = em_ok("Réputation +1",
        f"{ctx.author.mention} a donné un point à {member.mention} !\n"
        f"> Total : **{reputation[target]} 💖**")
    await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def reps(ctx, member: discord.Member = None):
    target = member or ctx.author
    n = reputation.get(str(target.id), 0)
    e = em_info(f"Réputation — {target.display_name}", f"💖 **{n}** points")
    e.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=e)

class DuelView(discord.ui.View):
    def __init__(self, challenger, opponent, mise):
        super().__init__(timeout=30)
        self.challenger = challenger; self.opponent = opponent; self.mise = mise
        self.accepted = False

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept(self, interaction, button):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("Ce duel ne te vise pas.", ephemeral=True)
        if get_bal(str(self.opponent.id)) < self.mise:
            return await interaction.response.send_message("Tu n'as pas assez de pièces.", ephemeral=True)
        self.accepted = True
        winner = random.choice([self.challenger, self.opponent])
        loser  = self.opponent if winner == self.challenger else self.challenger
        add_bal(str(winner.id), self.mise)
        add_bal(str(loser.id), -self.mise)
        grant_achievement(str(winner.id), "duelist")
        for c in self.children: c.disabled = True
        e = _em("⚔️ Duel terminé",
            f"**Vainqueur :** {winner.mention}\n"
            f"**Mise :** `{self.mise:,}` pièces", C_GOLD)
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction, button):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("Pas pour toi.", ephemeral=True)
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=em_err("Duel refusé"), view=self)
        self.stop()

@bot.command()
@commands.guild_only()
async def duel(ctx, opponent: discord.Member, mise: int):
    if opponent.bot or opponent.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    if mise < 10: return await ctx.send(embed=em_err("Mise min 10"))
    if get_bal(str(ctx.author.id)) < mise:
        return await ctx.send(embed=em_err("Fonds insuffisants"))
    view = DuelView(ctx.author, opponent, mise)
    e = _em("⚔️ Duel proposé",
        f"{ctx.author.mention} défie {opponent.mention} pour **{mise:,} pièces** !\n"
        f"{opponent.mention}, tu acceptes ?", C_VIOLET)
    e.set_image(url=ASSETS["duel"])
    await ctx.send(content=opponent.mention, embed=e, view=view)

class RPSView(discord.ui.View):
    def __init__(self, ctx, opponent):
        super().__init__(timeout=30)
        self.ctx = ctx; self.opponent = opponent
        self.choices = {}

    async def _resolve(self, interaction):
        a = self.choices.get(self.ctx.author.id)
        b = self.choices.get(self.opponent.id)
        if not (a and b): return
        order = ["pierre","feuille","ciseaux"]
        if a == b: result = "Égalité !"; color = C_BLUE; winner = None
        elif (order.index(a) - order.index(b)) % 3 == 1:
            winner = self.ctx.author; result = f"{winner.mention} gagne ({a} bat {b}) !"; color = C_GOLD
        else:
            winner = self.opponent; result = f"{winner.mention} gagne ({b} bat {a}) !"; color = C_GOLD
        for c in self.children: c.disabled = True
        e = _em("✊✋✌️ Pierre/Feuille/Ciseaux", result, color)
        await interaction.message.edit(embed=e, view=self)
        self.stop()

    def _make(self, label, emoji):
        async def cb(interaction):
            if interaction.user.id not in (self.ctx.author.id, self.opponent.id):
                return await interaction.response.send_message("Pas pour toi.", ephemeral=True)
            if interaction.user.id in self.choices:
                return await interaction.response.send_message("Tu as déjà choisi.", ephemeral=True)
            self.choices[interaction.user.id] = label
            await interaction.response.send_message(f"Tu as choisi {emoji}", ephemeral=True)
            if len(self.choices) == 2:
                await self._resolve(interaction)
        return cb

    def build(self):
        for label, emoji in [("pierre","✊"),("feuille","✋"),("ciseaux","✌️")]:
            b = discord.ui.Button(label=label.capitalize(), emoji=emoji, style=discord.ButtonStyle.secondary)
            b.callback = self._make(label, emoji)
            self.add_item(b)
        return self

@bot.command()
@commands.guild_only()
async def rps(ctx, opponent: discord.Member):
    if opponent.bot or opponent.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    view = RPSView(ctx, opponent).build()
    e = em_info("✊✋✌️ Pierre/Feuille/Ciseaux",
        f"{ctx.author.mention} vs {opponent.mention}\nChoisissez chacun !")
    e.set_thumbnail(url=ASSETS["rps"])
    await ctx.send(content=opponent.mention, embed=e, view=view)

QUIZ_QUESTIONS = [
    ("Quelle est la capitale du Japon ?", "tokyo"),
    ("Combien font 7 × 8 ?", "56"),
    ("Quel élément a pour symbole 'Au' ?", "or"),
    ("En quelle année est tombé le mur de Berlin ?", "1989"),
    ("Quelle planète est la plus proche du soleil ?", "mercure"),
    ("Auteur de 'Les Misérables' ?", "hugo"),
    ("Combien de continents y a-t-il ?", "7"),
    ("Quelle est la plus grande île du monde ?", "groenland"),
]

@bot.command()
@commands.guild_only()
@commands.cooldown(1, 30, commands.BucketType.user)
async def quiz(ctx):
    q, a = random.choice(QUIZ_QUESTIONS)
    e = em_info("🧠 Quiz", f"**{q}**\nTu as 20 secondes.")
    e.set_thumbnail(url=ASSETS["quiz"])
    await ctx.send(embed=e)
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        m = await bot.wait_for("message", check=check, timeout=20)
        if a in m.content.lower():
            gain = random.randint(50, 200)
            add_bal(str(ctx.author.id), gain)
            await ctx.send(embed=em_ok("Bonne réponse !", f"+**{gain:,}** pièces"))
        else:
            await ctx.send(embed=em_err("Mauvaise réponse", f"C'était : `{a}`"))
    except asyncio.TimeoutError:
        await ctx.send(embed=em_err("Trop tard !", f"C'était : `{a}`"))

@bot.command()
async def conseil(ctx):
    conseils = [
        "Bois de l'eau régulièrement.", "Fais une pause toutes les 50 min.",
        "Sourire améliore l'humeur.", "Lis 10 minutes par jour.",
        "Marche un peu chaque jour.", "Évite ton téléphone avant de dormir.",
        "Note 3 choses positives chaque soir.", "Apprends quelque chose de nouveau ce mois-ci.",
        "Ne compare pas tes coulisses au feu d'artifice des autres.",
    ]
    await ctx.send(embed=em_info("💡 Conseil", random.choice(conseils)))

@bot.command()
async def ship(ctx, a: discord.Member, b: discord.Member):
    score = (hash(f"{min(a.id,b.id)}-{max(a.id,b.id)}") % 101)
    bar = "❤️" * (score // 10) + "🖤" * (10 - score // 10)
    e = _em(f"💘 {a.display_name} ❤️ {b.display_name}",
        f"```\n{bar}  {score}%\n```", C_VIOLET)
    e.set_thumbnail(url=ASSETS["ship"])
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  CLANS
# ══════════════════════════════════════════════════════
clan_invites: dict = {}  # uid -> clan_name (mémoire)

def find_user_clan(uid: str):
    for name, c in clans.items():
        if uid in c.get("members", []):
            return name, c
    return None, None

@bot.group(invoke_without_command=True)
@commands.guild_only()
async def clan(ctx):
    name, c = find_user_clan(str(ctx.author.id))
    if not name:
        return await ctx.send(embed=em_info("Clan",
            "Tu n'es dans aucun clan. `!clan create <nom>`"))
    return await clan_info(ctx, name=name)

@clan.command(name="create")
async def clan_create(ctx, *, nom: str):
    uid = str(ctx.author.id)
    if find_user_clan(uid)[0]:
        return await ctx.send(embed=em_err("Tu es déjà dans un clan"))
    if nom in clans:
        return await ctx.send(embed=em_err("Nom déjà pris"))
    if len(nom) > 24:
        return await ctx.send(embed=em_err("Nom trop long (24 max)"))
    cost = 1000
    if get_bal(uid) < cost:
        return await ctx.send(embed=em_err("Coût 1000 pièces"))
    add_bal(uid, -cost)
    clans[nom] = {"owner": uid, "members": [uid], "bank": 0,
                  "level": 1, "xp": 0, "guild": str(ctx.guild.id), "desc": ""}
    save("clans", clans)
    grant_achievement(uid, "clan_member")
    await ctx.send(embed=em_ok("Clan créé", f"🏰 **{nom}** fondé par {ctx.author.mention} !"))

@clan.command(name="info")
async def clan_info(ctx, *, name: str = None):
    if not name:
        n, _ = find_user_clan(str(ctx.author.id))
        if not n: return await ctx.send(embed=em_info("Aucun clan"))
        name = n
    c = clans.get(name)
    if not c: return await ctx.send(embed=em_err("Clan inconnu"))
    owner = ctx.guild.get_member(int(c["owner"]))
    e = _em(f"🏰  Clan — {name}",
        f"> **Chef :** {owner.mention if owner else c['owner']}\n"
        f"> **Niveau :** `{c.get('level',1)}`  •  **XP :** `{c.get('xp',0):,}`\n"
        f"> **Banque :** `{c.get('bank',0):,}` pièces\n"
        f"> **Membres :** `{len(c['members'])}`", C_BLUE)
    e.add_field(name="Membres", value=", ".join(
        (ctx.guild.get_member(int(m)).mention if ctx.guild.get_member(int(m)) else f"`{m}`")
        for m in c["members"][:15]) or "—", inline=False)
    e.set_thumbnail(url=ASSETS["clan"])
    await ctx.send(embed=e)

@clan.command(name="invite")
async def clan_invite(ctx, member: discord.Member):
    uid = str(ctx.author.id)
    name, c = find_user_clan(uid)
    if not name or c["owner"] != uid:
        return await ctx.send(embed=em_err("Tu dois être chef de clan"))
    if str(member.id) in c["members"]:
        return await ctx.send(embed=em_err("Déjà dans le clan"))
    clan_invites[str(member.id)] = name
    await ctx.send(embed=em_ok("Invitation envoyée",
        f"{member.mention} peut faire `!clan join {name}` pour rejoindre **{name}**."))

@clan.command(name="join")
async def clan_join(ctx, *, name: str):
    uid = str(ctx.author.id)
    if find_user_clan(uid)[0]:
        return await ctx.send(embed=em_err("Tu es déjà dans un clan"))
    if clan_invites.get(uid) != name:
        return await ctx.send(embed=em_err("Pas d'invitation pour ce clan"))
    if name not in clans:
        return await ctx.send(embed=em_err("Clan inconnu"))
    clans[name]["members"].append(uid)
    save("clans", clans)
    clan_invites.pop(uid, None)
    grant_achievement(uid, "clan_member")
    await ctx.send(embed=em_ok("Bienvenue !", f"Tu as rejoint **{name}** 🏰"))

@clan.command(name="leave")
async def clan_leave(ctx):
    uid = str(ctx.author.id)
    name, c = find_user_clan(uid)
    if not name: return await ctx.send(embed=em_err("Pas dans un clan"))
    if c["owner"] == uid:
        # Dissoudre si seul
        if len(c["members"]) == 1:
            del clans[name]; save("clans", clans)
            return await ctx.send(embed=em_ok("Clan dissous", f"**{name}** dissous."))
        return await ctx.send(embed=em_err("Tu es le chef",
            "Transfère le clan ou supprime des membres avant de partir."))
    c["members"].remove(uid); save("clans", clans)
    await ctx.send(embed=em_ok("Tu as quitté le clan", name))

@clan.command(name="deposit")
async def clan_deposit(ctx, montant: int):
    uid = str(ctx.author.id)
    name, c = find_user_clan(uid)
    if not name: return await ctx.send(embed=em_err("Pas dans un clan"))
    if montant <= 0 or get_bal(uid) < montant:
        return await ctx.send(embed=em_err("Montant invalide"))
    add_bal(uid, -montant)
    c["bank"] = c.get("bank",0) + montant
    c["xp"]   = c.get("xp",0) + montant // 10
    new_lvl = 1 + int(math.sqrt(c["xp"] / 500))
    c["level"] = max(c.get("level",1), new_lvl)
    save("clans", clans)
    await ctx.send(embed=em_ok("Dépôt effectué",
        f"+**{montant:,}** dans **{name}** • Niveau clan `{c['level']}`"))

@clan.command(name="top")
async def clan_top(ctx):
    rows = sorted(clans.items(), key=lambda kv: kv[1].get("bank",0), reverse=True)[:10]
    if not rows: return await ctx.send(embed=em_info("Aucun clan"))
    medals = ["🥇","🥈","🥉"] + ["🏰"]*7
    lines = [f"{medals[i]} **{n}** — Niv `{c.get('level',1)}` • `{c.get('bank',0):,}` 💰 • `{len(c['members'])}` membres"
             for i,(n,c) in enumerate(rows)]
    await ctx.send(embed=_em("🏰 Classement clans","\n".join(lines), C_BLUE))

# ══════════════════════════════════════════════════════
#  QUÊTES
# ══════════════════════════════════════════════════════
@bot.command(aliases=["quests", "missions"])
@commands.guild_only()
async def quetes(ctx):
    uid = str(ctx.author.id)
    q = get_quests(uid)
    lines = []
    for i, it in enumerate(q["active"]):
        status = "✅" if it["done"] else f"`{it['progress']}/{it['target']}`"
        claimed = " *(récupéré)*" if it.get("claimed") else ""
        lines.append(f"`#{i+1}` **{it['desc']}** — {status} • +{it['reward']} 💰{claimed}")
    e = _em("🗺️ Quêtes du jour", "\n".join(lines) +
        "\n\nUtilise `!claim_quest <#>` pour récupérer une quête terminée.", C_GREEN)
    e.set_thumbnail(url=ASSETS["quest"])
    await ctx.send(embed=e)

@bot.command(name="claim_quest")
@commands.guild_only()
async def claim_quest(ctx, idx: int):
    uid = str(ctx.author.id)
    q = get_quests(uid)
    if idx < 1 or idx > len(q["active"]):
        return await ctx.send(embed=em_err("Index invalide"))
    it = q["active"][idx - 1]
    if not it["done"]:
        return await ctx.send(embed=em_err("Quête non terminée"))
    if it.get("claimed"):
        return await ctx.send(embed=em_err("Déjà réclamée"))
    it["claimed"] = True
    add_bal(uid, it["reward"])
    grant_achievement(uid, "quest_done")
    save("quests", quests)
    await ctx.send(embed=em_ok("Quête réclamée",
        f"+**{it['reward']:,}** pièces 🎉"))

# ══════════════════════════════════════════════════════
#  FUN — ROLL / OUTILS
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
@commands.cooldown(1, 30, commands.BucketType.user)
async def roll(ctx):
    perso = random.choice(CHARACTERS)
    nom, etoiles, emoji = perso
    uid = str(ctx.author.id)
    cards.setdefault(uid, [])
    cards[uid].append(nom)
    save("cards", cards)
    if len(cards[uid]) >= 10:
        grant_achievement(uid, "collector")
    e = _em(f"{emoji}  {nom}",
        f"Rareté : {etoiles}\nAjouté à ton inventaire ({len(cards[uid])} cartes)", C_VIOLET)
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid = str(target.id)
    inv = cards.get(uid, [])
    if not inv:
        return await ctx.send(embed=em_info("Inventaire vide"))
    counts = {}
    for c in inv: counts[c] = counts.get(c, 0) + 1
    lines = [f"`{n}` × **{name}**" for name, n in sorted(counts.items(), key=lambda x:-x[1])]
    await ctx.send(embed=_em(f"📚 Cartes — {target.display_name}",
        "\n".join(lines[:20]), C_VIOLET))

@bot.command(name="8ball")
async def eight_ball(ctx, *, question: str):
    reps = ["Oui.", "Non.", "Peut-être.", "Sans aucun doute.", "Probablement pas.",
            "Demande plus tard.", "C'est certain.", "Mes sources disent non.",
            "Très probable.", "N'y compte pas."]
    await ctx.send(embed=em_dark("🔮 Oracle", f"> {question}\n**{random.choice(reps)}**"))

@bot.command()
async def de(ctx, faces: int = 6):
    faces = max(2, min(faces, 1000))
    await ctx.send(embed=em_info("🎲 Dé", f"Résultat : **{random.randint(1, faces)}** / {faces}"))

@bot.command()
async def coinflip(ctx):
    await ctx.send(embed=em_info("🪙 Pile ou Face", random.choice(["**Pile** 🪙", "**Face** 🪙"])))

@bot.command()
@commands.guild_only()
async def snipe(ctx):
    s = snipe_cache.get(ctx.channel.id)
    if not s: return await ctx.send(embed=em_info("Rien à sniper"))
    e = _em(f"Snipe — {s['author']}", f"```\n{s['content'] or '(vide)'}\n```", C_DARK)
    e.set_thumbnail(url=s["avatar"])
    e.set_footer(text=f"Supprimé à {s['time']} • {BOT_SIGNATURE}")
    await ctx.send(embed=e)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    e = _em(f"Avatar — {target.display_name}", color=C_VIOLET)
    e.set_image(url=target.display_avatar.url)
    await ctx.send(embed=e)

EMOJI_PATTERN = re.compile(r"<(a?):([A-Za-z0-9_]+):(\d+)>")

@bot.command(name="emojis", aliases=["voleremoji", "stealemoji"])
@commands.guild_only()
async def emojis(ctx, *, args: str = ""):
    """Vole un ou plusieurs emojis personnalisés et les ajoute à ce serveur.
    Usage : `!emojis <:nom:id> <:autre:id> ...`  (ou réponds à un message contenant les emojis)
    """
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    if not ctx.guild.me.guild_permissions.manage_emojis_and_stickers:
        return await ctx.send(embed=em_err("Permission bot manquante",
            "J'ai besoin de la permission **Gérer les emojis et stickers**."))

    # Source : message en réponse OU args
    source_text = args
    if ctx.message.reference and not source_text:
        try:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            source_text = ref.content
        except Exception:
            pass

    matches = EMOJI_PATTERN.findall(source_text or "")
    if not matches:
        return await ctx.send(embed=em_err("Aucun emoji trouvé",
            "Donne au moins un emoji custom : `!emojis <:nom:id>` ou réponds à un message qui en contient."))

    # Dédoublonnage par ID, max 10 par appel
    seen = set(); items = []
    for animated, name, eid in matches:
        if eid in seen: continue
        seen.add(eid)
        items.append((bool(animated), name, eid))
        if len(items) >= 10: break

    progress = em_info("🪄 Vol d'emojis en cours…",
        f"Tentative d'import de **{len(items)}** emoji(s)…")
    msg = await ctx.send(embed=progress)

    import aiohttp
    added, failed = [], []
    async with aiohttp.ClientSession() as session:
        for animated, name, eid in items:
            ext = "gif" if animated else "png"
            url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}?size=128&quality=lossless"
            try:
                async with session.get(url) as r:
                    if r.status != 200:
                        failed.append(f"`{name}` (HTTP {r.status})"); continue
                    data = await r.read()
                new_emoji = await ctx.guild.create_custom_emoji(
                    name=name[:32] or "vole",
                    image=data,
                    reason=f"Vol d'emoji par {ctx.author}"
                )
                added.append(str(new_emoji))
            except discord.HTTPException as exc:
                failed.append(f"`{name}` ({exc.text or exc.status})")
            except Exception as exc:
                failed.append(f"`{name}` ({type(exc).__name__})")

    color = C_GOLD if added and not failed else (C_GREEN if added else C_RED)
    e = _em("🪄 Vol d'emojis", None, color)
    if added:
        e.add_field(name=f"✦ Ajoutés ({len(added)})",
                    value=" ".join(added), inline=False)
    if failed:
        e.add_field(name=f"✗ Échecs ({len(failed)})",
                    value="\n".join(failed), inline=False)
    e.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Mask_thief.png/240px-Mask_thief.png")
    await msg.edit(embed=e)

@bot.command(name="stickers", aliases=["stealsticker", "volersticker"])
@commands.guild_only()
async def stickers(ctx, *, name_override: str = None):
    """Vole les stickers d'un message en réponse et les ajoute à ce serveur.
    Usage : réponds à un message contenant un/des sticker(s) avec `!stickers [nom]`
    """
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    if not ctx.guild.me.guild_permissions.manage_emojis_and_stickers:
        return await ctx.send(embed=em_err("Permission bot manquante",
            "J'ai besoin de la permission **Gérer les emojis et stickers**."))
    if not ctx.message.reference:
        return await ctx.send(embed=em_err("Aucune source",
            "Réponds à un message contenant un ou plusieurs stickers avec `!stickers`."))
    try:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except Exception:
        return await ctx.send(embed=em_err("Message introuvable"))
    if not ref.stickers:
        return await ctx.send(embed=em_err("Aucun sticker",
            "Le message ciblé ne contient pas de sticker."))

    items = ref.stickers[:5]
    progress = em_info("🪄 Vol de stickers en cours…",
        f"Tentative d'import de **{len(items)}** sticker(s)…")
    msg = await ctx.send(embed=progress)

    import aiohttp
    added, failed = [], []
    async with aiohttp.ClientSession() as session:
        for st in items:
            sticker_name = (name_override or st.name)[:30] or "vole"
            try:
                async with session.get(str(st.url)) as r:
                    if r.status != 200:
                        failed.append(f"`{st.name}` (HTTP {r.status})"); continue
                    data = await r.read()
                    ctype = r.headers.get("Content-Type", "")
                ext = "png"
                if "json" in ctype or str(st.url).endswith(".json"):
                    failed.append(f"`{st.name}` (Lottie non supporté)"); continue
                if "gif" in ctype: ext = "gif"
                elif "apng" in ctype: ext = "png"
                file = discord.File(fp=__import__("io").BytesIO(data), filename=f"{sticker_name}.{ext}")
                new_st = await ctx.guild.create_sticker(
                    name=sticker_name,
                    description=f"Volé par {ctx.author}",
                    emoji="⭐",
                    file=file,
                    reason=f"Vol de sticker par {ctx.author}"
                )
                added.append(f"`{new_st.name}`")
            except discord.HTTPException as exc:
                failed.append(f"`{st.name}` ({exc.text or exc.status})")
            except Exception as exc:
                failed.append(f"`{st.name}` ({type(exc).__name__})")

    color = C_GOLD if added and not failed else (C_GREEN if added else C_RED)
    e = _em("🪄 Vol de stickers", None, color)
    if added:
        e.add_field(name=f"✦ Ajoutés ({len(added)})",
                    value=" ".join(added), inline=False)
    if failed:
        e.add_field(name=f"✗ Échecs ({len(failed)})",
                    value="\n".join(failed), inline=False)
    e.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Mask_thief.png/240px-Mask_thief.png")
    await msg.edit(embed=e)

@bot.command()
@commands.guild_only()
async def serverinfo(ctx):
    g = ctx.guild
    e = _em(f"🏛 {g.name}",
        f"> **Membres :** `{g.member_count}`\n"
        f"> **Salons :** `{len(g.channels)}`\n"
        f"> **Rôles :** `{len(g.roles)}`\n"
        f"> **Créé le :** <t:{int(g.created_at.timestamp())}:D>",
        C_VIOLET)
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    target = member or ctx.author
    e = _em(f"👤 {target.display_name}", color=C_VIOLET)
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="ID",          value=f"`{target.id}`",                               inline=True)
    e.add_field(name="Rejoint le",  value=f"<t:{int(target.joined_at.timestamp())}:D>",   inline=True)
    e.add_field(name="Compte créé", value=f"<t:{int(target.created_at.timestamp())}:D>",  inline=True)
    top = target.top_role.mention if target.top_role != ctx.guild.default_role else "Aucun"
    e.add_field(name="Rôle principal", value=top, inline=True)
    e.add_field(name="Réputation", value=f"💖 {reputation.get(str(target.id), 0)}", inline=True)
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  CONFIGURATION HÉRITÉE
# ══════════════════════════════════════════════════════
@bot.command()
@commands.guild_only()
async def setautorole(ctx, role: discord.Role):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))
    auto_roles[str(ctx.guild.id)] = role.id
    save("auto_roles", auto_roles)
    await ctx.send(embed=em_ok("Auto-rôle",
        f"{role.mention} sera attribué aux nouveaux."))

@bot.command()
@commands.guild_only()
async def addrr(ctx, message_id: int, emoji: str, role: discord.Role):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    ok, msg = role_is_safe_to_manage(ctx.guild, role, ctx.author)
    if not ok:
        return await ctx.send(embed=em_err("Refus de sécurité", msg))
    key = str(message_id)
    reaction_roles.setdefault(key, {})
    reaction_roles[key][emoji] = role.id
    save("reaction_roles", reaction_roles)
    await ctx.send(embed=em_ok("Reaction role", f"{emoji} → {role.mention}"))

@bot.command()
@commands.guild_only()
async def removerr(ctx, message_id: int, emoji: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    key = str(message_id)
    if key in reaction_roles and emoji in reaction_roles[key]:
        del reaction_roles[key][emoji]
        if not reaction_roles[key]: del reaction_roles[key]
        save("reaction_roles", reaction_roles)
        await ctx.send(embed=em_ok("Reaction role retiré"))
    else:
        await ctx.send(embed=em_err("Introuvable"))

class SelfRoleMenu(discord.ui.View):
    def __init__(self, guild, role_ids):
        super().__init__(timeout=None)
        for rid in role_ids[:25]:
            r = guild.get_role(int(rid))
            if not r: continue
            btn = discord.ui.Button(label=r.name, style=discord.ButtonStyle.primary, custom_id=f"selfrole_{rid}")
            btn.callback = self._make(rid)
            self.add_item(btn)

    def _make(self, rid):
        async def cb(interaction: discord.Interaction):
            role = interaction.guild.get_role(int(rid))
            if not role:
                return await interaction.response.send_message("Rôle introuvable.", ephemeral=True)
            try:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role, reason="selfrole menu")
                    return await interaction.response.send_message(f"Rôle **{role.name}** retiré.", ephemeral=True)
                else:
                    await interaction.user.add_roles(role, reason="selfrole menu")
                    return await interaction.response.send_message(f"Rôle **{role.name}** ajouté.", ephemeral=True)
            except discord.Forbidden:
                return await interaction.response.send_message("Le bot n'a pas la permission.", ephemeral=True)
        return cb

@bot.command()
@commands.guild_only()
async def rolemenu(ctx, *, titre: str = "Choisis tes rôles"):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    g = get_gconf(str(ctx.guild.id))
    sr = g.get("self_roles", [])
    if not sr:
        return await ctx.send(embed=em_err("Aucun self-role",
            "Ajoute des rôles avec `!selfrole add <@rôle>`."))
    view = SelfRoleMenu(ctx.guild, sr)
    e = _em(titre, "Clique sur un bouton pour ajouter ou retirer le rôle.", C_VIOLET)
    await ctx.send(embed=e, view=view)

@bot.command()
@commands.guild_only()
async def addresponse(ctx, trigger: str, *, response: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    gid = str(ctx.guild.id)
    auto_responses.setdefault(gid, {})
    auto_responses[gid][trigger.lower()] = response
    save("auto_responses", auto_responses)
    await ctx.send(embed=em_ok("Réponse ajoutée", f"`{trigger}`"))

@bot.command()
@commands.guild_only()
async def removeresponse(ctx, trigger: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    gid = str(ctx.guild.id)
    if gid in auto_responses and trigger.lower() in auto_responses[gid]:
        del auto_responses[gid][trigger.lower()]
        save("auto_responses", auto_responses)
        await ctx.send(embed=em_ok("Supprimée"))
    else:
        await ctx.send(embed=em_err("Introuvable"))

@bot.command()
@commands.guild_only()
async def addword(ctx, *, word: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    gid = str(ctx.guild.id)
    word_filter.setdefault(gid, [])
    if word.lower() not in word_filter[gid]:
        word_filter[gid].append(word.lower()); save("word_filter", word_filter)
    await ctx.send(embed=em_ok("Mot banni"))

@bot.command()
@commands.guild_only()
async def removeword(ctx, *, word: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    gid = str(ctx.guild.id)
    if gid in word_filter and word.lower() in word_filter[gid]:
        word_filter[gid].remove(word.lower()); save("word_filter", word_filter)
        await ctx.send(embed=em_ok("Mot retiré"))
    else:
        await ctx.send(embed=em_err("Introuvable"))

@bot.command()
@commands.guild_only()
async def linkfilter(ctx, state: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    gid = str(ctx.guild.id)
    enabled = state.lower() in ("on","1","true","oui")
    link_filter[gid] = enabled
    save("link_filter", link_filter)
    await ctx.send(embed=em_ok("Filtre liens", "activé" if enabled else "désactivé"))

@bot.command()
@commands.guild_only()
async def additem(ctx, price: int, *, item_name: str):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    shop_items[item_name] = {"price": price, "type": "role", "desc": "Article custom"}
    save("shop", shop_items)
    await ctx.send(embed=em_ok("Article ajouté", f"**{item_name}** = `{price:,}`"))

@bot.command()
@commands.guild_only()
async def removeitem(ctx, *, item_name: str):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    item = next((k for k in shop_items if k.lower() == item_name.lower()), None)
    if item:
        del shop_items[item]; save("shop", shop_items)
        await ctx.send(embed=em_ok("Supprimé", item))
    else:
        await ctx.send(embed=em_err("Introuvable"))

@bot.command()
@commands.guild_only()
async def addmoney(ctx, member: discord.Member, montant: int):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    add_bal(str(member.id), montant)
    await ctx.send(embed=em_ok("Pièces ajoutées", f"+{montant:,} → {member.mention}"))

@bot.command()
@commands.guild_only()
async def removemoney(ctx, member: discord.Member, montant: int):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    add_bal(str(member.id), -montant)
    await ctx.send(embed=em_ok("Pièces retirées", f"-{montant:,} → {member.mention}"))

@bot.command()
@commands.guild_only()
async def say(ctx, *, message: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    try: await ctx.message.delete()
    except discord.Forbidden: pass
    await ctx.send(message)

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
        return await ctx.send(embed=em_err("Format invalide",
            "Exemple : `!reminder 10m Mon message`"))
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
EMBED_COLORS = {"violet": C_VIOLET,"gold":C_GOLD,"rouge":C_RED,"vert":C_GREEN,
                "bleu":C_BLUE,"dark":C_DARK,"jaune":C_YELLOW}

@bot.command(name="embed")
@commands.guild_only()
async def custom_embed(ctx, couleur: str = "violet", *, contenu: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    try: await ctx.message.delete()
    except discord.Forbidden: pass
    color = EMBED_COLORS.get(couleur.lower(), C_VIOLET)
    if " | " in contenu:
        titre, desc = contenu.split(" | ", 1)
    else:
        titre, desc = contenu, None
    if desc: desc = desc.replace("\\n", "\n")
    e = discord.Embed(title=titre.strip(), description=desc, color=color)
    e.set_footer(text=BOT_SIGNATURE)
    await ctx.send(embed=e)

@bot.command(name="panel")
@commands.guild_only()
async def panel_embed(ctx, *, contenu: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    try: await ctx.message.delete()
    except discord.Forbidden: pass
    lignes = contenu.split("\n")
    titre = lignes[0].strip() if lignes else "Panel"
    reste = "\n".join(lignes[1:]).strip()
    sections = [s.strip() for s in reste.split("---") if s.strip()]
    e = discord.Embed(title=titre, color=C_VIOLET)
    if sections:
        for section in sections:
            ls = section.split("\n")
            nom = ls[0].strip() if ls else "◈"
            val = "\n".join(ls[1:]).strip() if len(ls) > 1 else "\u200b"
            e.add_field(name=nom, value=val, inline=False)
    else:
        e.description = reste
    e.set_footer(text=BOT_SIGNATURE)
    await ctx.send(embed=e)

@bot.command(name="embedraw")
@commands.guild_only()
async def embed_raw(ctx, salon: discord.TextChannel = None, couleur: str = "violet", *, contenu: str):
    if not is_mod(ctx.author): return await no_perm(ctx, "mod")
    try: await ctx.message.delete()
    except discord.Forbidden: pass
    destination = salon or ctx.channel
    color = EMBED_COLORS.get(couleur.lower(), C_VIOLET)
    if " | " in contenu:
        titre, desc = contenu.split(" | ", 1)
    else:
        titre, desc = contenu, None
    if desc: desc = desc.replace("\\n", "\n")
    e = discord.Embed(title=titre.strip(), description=desc, color=color)
    e.set_footer(text=BOT_SIGNATURE)
    try:
        await destination.send(embed=e)
        await ctx.send(embed=em_ok("Envoyé", f"→ {destination.mention}"), delete_after=4)
    except discord.Forbidden:
        await ctx.send(embed=em_err("Permission refusée"))

# ══════════════════════════════════════════════════════
#  NIVEAUX — COMMANDES
# ══════════════════════════════════════════════════════
@bot.command(aliases=["level", "rank", "xp"])
@commands.guild_only()
async def niveau(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid = str(target.id)
    info = get_xp_info(uid)
    lvl, xp = info["level"], info["xp"]
    needed = xp_for_next(lvl); curr = xp_for_level(lvl)
    bar = xp_bar(xp, lvl)
    pct = int(((xp - curr) / max(needed - curr, 1)) * 100)
    e = em_lvl(f"Niveau {lvl} — {target.display_name}",
        f"```\n{bar}  {pct}%\n```\n"
        f"> **XP :** `{xp:,}` / `{needed:,}`\n"
        f"> **Prochain niveau :** `{needed - xp:,}` XP")
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="Niveau", value=f"`{lvl}`", inline=True)
    e.add_field(name="XP",     value=f"`{xp:,}`", inline=True)
    _foot(e, ctx.author); await ctx.send(embed=e)

@bot.command(aliases=["classementxp"])
@commands.guild_only()
async def topxp(ctx):
    scores = []
    for m in ctx.guild.members:
        if m.bot: continue
        info = get_xp_info(str(m.id))
        if info["xp"] > 0:
            scores.append((m.display_name, info["xp"], info["level"]))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:10]
    if not top:
        return await ctx.send(embed=em_info("Classement XP", "Vide."))
    medals = ["🥇","🥈","🥉"] + ["◈"]*7
    lines = [f"{medals[i]}  **{n}** — Niv `{l}` • `{x:,}` XP"
             for i,(n,x,l) in enumerate(top)]
    await ctx.send(embed=em_lvl("Classement XP", "\n".join(lines)))

@bot.command(aliases=["profile", "card"])
@commands.guild_only()
async def profil(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid = str(target.id)
    info = get_xp_info(uid); lvl, xp = info["level"], info["xp"]
    bal = get_bal(uid); inv = cards.get(uid, [])
    achiev = achievements_d.get(uid, [])
    rep_n = reputation.get(uid, 0)
    cl_name, _ = find_user_clan(uid)
    bar = xp_bar(xp, lvl); needed = xp_for_next(lvl)
    pct = int(((xp - xp_for_level(lvl)) / max(needed - xp_for_level(lvl), 1)) * 100)
    badges = " ".join(ACHIEVEMENTS[k][1] for k in achiev if k in ACHIEVEMENTS) or "Aucun"
    e = discord.Embed(title=f"◈  Profil — {target.display_name}",
        color=C_VIOLET, timestamp=datetime.utcnow())
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_image(url=target.display_avatar.url)
    e.add_field(name="◈  Niveau & XP",
        value=f"**Niveau {lvl}**\n`{bar}` {pct}%\n`{xp:,}` / `{needed:,}` XP",
        inline=False)
    e.add_field(name="✦  Pièces", value=f"`{bal:,}`",        inline=True)
    e.add_field(name="📚  Cartes", value=f"`{len(inv)}`",     inline=True)
    e.add_field(name="🏆  Succès", value=f"`{len(achiev)}`",  inline=True)
    e.add_field(name="💖  Réput.",  value=f"`{rep_n}`",        inline=True)
    e.add_field(name="🏰  Clan",    value=cl_name or "—",      inline=True)
    e.add_field(name="🎖  Badges",  value=badges,             inline=False)
    e.set_footer(text=f"{BOT_SIGNATURE}  •  {target.display_name}",
                 icon_url=target.display_avatar.url)
    await ctx.send(embed=e)

@bot.command(aliases=["achievements", "badges", "trophees"])
@commands.guild_only()
async def succes(ctx, membre: discord.Member = None):
    target = membre or ctx.author
    uid = str(target.id)
    unlocked = achievements_d.get(uid, [])
    lines = []
    for key, (name, emoji, desc) in ACHIEVEMENTS.items():
        if key in unlocked:
            lines.append(f"{emoji}  **{name}** — {desc}")
        else:
            lines.append(f"🔒  ~~{name}~~ — {desc}")
    e = discord.Embed(title=f"🏆  Succès — {target.display_name}",
        description="\n".join(lines), color=C_GOLD, timestamp=datetime.utcnow())
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_footer(text=f"{len(unlocked)}/{len(ACHIEVEMENTS)} débloqués  •  {BOT_SIGNATURE}")
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  EXTRAS — BANNER, POLL, AFK, WORK/CRIME/FISH, BANK,
#  MARIAGE, CODES PROMO
# ══════════════════════════════════════════════════════

# ── Banner d'utilisateur ──────────────────────────────
@bot.command()
async def banner(ctx, member: discord.Member = None):
    """Affiche la bannière de profil d'un membre."""
    target = member or ctx.author
    try:
        user = await bot.fetch_user(target.id)
    except discord.HTTPException:
        return await ctx.send(embed=em_err("Utilisateur introuvable"))
    if not user.banner:
        return await ctx.send(embed=em_info("Aucune bannière",
            f"{target.display_name} n'a pas de bannière de profil."))
    e = _em(f"Bannière — {target.display_name}", color=C_VIOLET)
    e.set_image(url=user.banner.url)
    await ctx.send(embed=e)

# ── Sondage ───────────────────────────────────────────
POLL_EMOJIS = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯"]

@bot.command()
@commands.guild_only()
async def poll(ctx, *, args: str):
    """Sondage : `!poll Question ? | option1 | option2 | ...` (jusqu'à 10 options)."""
    parts = [p.strip() for p in args.split("|") if p.strip()]
    if len(parts) < 3:
        return await ctx.send(embed=em_err("Format invalide",
            "Utilisation : `!poll Question ? | option1 | option2 | ...` (min 2 options)."))
    question, options = parts[0], parts[1:11]
    desc = "\n".join(f"{POLL_EMOJIS[i]}  {opt}" for i, opt in enumerate(options))
    e = _em(f"📊 {question}", desc, C_VIOLET)
    e.set_footer(text=f"Sondage par {ctx.author.display_name}  •  {BOT_SIGNATURE}")
    msg = await ctx.send(embed=e)
    for i in range(len(options)):
        try: await msg.add_reaction(POLL_EMOJIS[i])
        except discord.HTTPException: pass

# ── AFK ───────────────────────────────────────────────
@bot.command()
@commands.guild_only()
async def afk(ctx, *, raison: str = "Pas de raison"):
    uid = str(ctx.author.id)
    afk_data[uid] = {
        "reason": raison[:200],
        "since":  int(datetime.utcnow().timestamp()),
        "guild":  str(ctx.guild.id),
    }
    save("afk", afk_data)
    e = em_info(f"💤 {ctx.author.display_name} est AFK",
        f"> **Raison :** {raison[:200]}\n> Tape n'importe quel message pour revenir.")
    await ctx.send(embed=e)

# ── Travail (job honnête) ─────────────────────────────
WORK_LINES = [
    "Tu as livré des pizzas en scooter 🛵",
    "Tu as codé une fonctionnalité critique 💻",
    "Tu as servi des cafés tout l'après-midi ☕",
    "Tu as réparé une vieille horloge ⏰",
    "Tu as donné un cours de musique 🎵",
    "Tu as gardé des animaux 🐶",
    "Tu as repeint un appartement 🎨",
    "Tu as fait une mission de freelance 📑",
]

@bot.command()
@commands.guild_only()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def work(ctx):
    uid = str(ctx.author.id)
    gain = random.randint(120, 420)
    if get_buff(uid, "casinox2"): gain *= 2
    add_bal(uid, gain); check_balance_achievements(uid)
    progress_quest(uid, "wins")
    e = em_gold("💼 Travail terminé",
        f"{random.choice(WORK_LINES)}\n+**{gain:,}** pièces\n> Solde : `{get_bal(uid):,}`")
    await ctx.send(embed=e)

# ── Crime risqué ──────────────────────────────────────
CRIME_OK = [
    "Tu as cambriolé une bijouterie en silence 💎",
    "Tu as piraté un distributeur 🏧",
    "Tu as revendu des pièces volées au marché noir 🕶️",
    "Tu as fait gagner un cheval truqué 🐎",
]
CRIME_BAD = [
    "La police t'a coffré en pleine action 🚓",
    "Ton complice t'a balancé… 🐀",
    "Une caméra cachée a tout filmé 📹",
    "Tu t'es trompé d'adresse, c'était chez un flic 👮",
]

@bot.command()
@commands.guild_only()
@commands.cooldown(1, 7200, commands.BucketType.user)
async def crime(ctx):
    uid = str(ctx.author.id)
    if random.random() < 0.55:
        gain = random.randint(300, 900)
        if get_buff(uid, "casinox2"): gain *= 2
        add_bal(uid, gain); check_balance_achievements(uid)
        e = em_gold("🦹 Crime réussi",
            f"{random.choice(CRIME_OK)}\n+**{gain:,}** pièces\n> Solde : `{get_bal(uid):,}`")
    else:
        amende = random.randint(150, 600)
        add_bal(uid, -amende)
        e = _em("🚔 Crime raté",
            f"{random.choice(CRIME_BAD)}\n-**{amende:,}** pièces d'amende\n> Solde : `{get_bal(uid):,}`",
            C_RED)
    await ctx.send(embed=e)

# ── Pêche ─────────────────────────────────────────────
FISH_TABLE = [
    ("🐟  une sardine",        20,  60),
    ("🐠  un poisson tropical", 60, 150),
    ("🐡  un poisson-globe",   100, 220),
    ("🦑  un calamar géant",   180, 400),
    ("🦈  un requin",          400, 800),
    ("🐉  un dragon des mers (LÉGENDAIRE)", 1500, 3000),
    ("🥾  une vieille botte",   0,   0),
    ("🗑️  un sac plastique",    0,   0),
]
FISH_WEIGHTS = [30, 22, 16, 12, 6, 1, 7, 6]

@bot.command(aliases=["peche"])
@commands.guild_only()
@commands.cooldown(1, 300, commands.BucketType.user)
async def fish(ctx):
    uid = str(ctx.author.id)
    label, lo, hi = random.choices(FISH_TABLE, weights=FISH_WEIGHTS, k=1)[0]
    if hi == 0:
        e = em_info("🎣 Tu as pêché…", f"{label}\nDommage, rien à vendre.")
    else:
        gain = random.randint(lo, hi)
        if get_buff(uid, "casinox2"): gain *= 2
        add_bal(uid, gain); check_balance_achievements(uid)
        progress_quest(uid, "wins")
        e = em_gold("🎣 Belle prise !",
            f"Tu as pêché {label} et tu l'as revendu(e) **{gain:,}** pièces !\n"
            f"> Solde : `{get_bal(uid):,}`")
    await ctx.send(embed=e)

# ── Banque (protégée du vol) ──────────────────────────
def get_bank(uid: str) -> int:
    return int(bank_data.get(uid, 0))

def add_bank(uid: str, amt: int):
    bank_data[uid] = max(0, get_bank(uid) + amt)
    save("bank", bank_data)

@bot.group(invoke_without_command=True)
@commands.guild_only()
async def bank(ctx):
    uid = str(ctx.author.id)
    e = em_gold(f"🏦 Banque — {ctx.author.display_name}",
        f"> **Solde banque :** `{get_bank(uid):,}` pièces *(à l'abri des vols)*\n"
        f"> **Solde poche :** `{get_bal(uid):,}` pièces\n\n"
        f"Utilise `!bank deposit <montant>` ou `!bank withdraw <montant>`.")
    e.set_thumbnail(url=ASSETS.get("daily"))
    await ctx.send(embed=e)

@bank.command(name="deposit", aliases=["dep"])
async def bank_deposit(ctx, montant):
    uid = str(ctx.author.id)
    bal = get_bal(uid)
    if isinstance(montant, str) and montant.lower() in ("all", "max", "tout"):
        amt = bal
    else:
        try: amt = int(montant)
        except (ValueError, TypeError):
            return await ctx.send(embed=em_err("Montant invalide"))
    if amt <= 0:    return await ctx.send(embed=em_err("Montant invalide"))
    if amt > bal:   return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bal(uid, -amt); add_bank(uid, amt)
    await ctx.send(embed=em_ok("Dépôt effectué",
        f"+**{amt:,}** dans la banque.\n> Banque : `{get_bank(uid):,}`  •  Poche : `{get_bal(uid):,}`"))

@bank.command(name="withdraw", aliases=["wd", "retirer"])
async def bank_withdraw(ctx, montant):
    uid = str(ctx.author.id)
    b = get_bank(uid)
    if isinstance(montant, str) and montant.lower() in ("all", "max", "tout"):
        amt = b
    else:
        try: amt = int(montant)
        except (ValueError, TypeError):
            return await ctx.send(embed=em_err("Montant invalide"))
    if amt <= 0:   return await ctx.send(embed=em_err("Montant invalide"))
    if amt > b:    return await ctx.send(embed=em_err("Fonds insuffisants"))
    add_bank(uid, -amt); add_bal(uid, amt)
    await ctx.send(embed=em_ok("Retrait effectué",
        f"-**{amt:,}** de la banque.\n> Banque : `{get_bank(uid):,}`  •  Poche : `{get_bal(uid):,}`"))

@bank.command(name="balance", aliases=["bal"])
async def bank_balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid = str(target.id)
    e = em_gold(f"🏦 Banque — {target.display_name}",
        f"> Banque : `{get_bank(uid):,}`\n> Poche : `{get_bal(uid):,}`")
    await ctx.send(embed=e)

# ── Mariage / divorce ─────────────────────────────────
marriage_requests: dict = {}  # target_uid -> proposer_uid (mémoire)

@bot.command()
@commands.guild_only()
async def marry(ctx, member: discord.Member):
    if member.bot or member.id == ctx.author.id:
        return await ctx.send(embed=em_err("Cible invalide"))
    uid_a, uid_b = str(ctx.author.id), str(member.id)
    if uid_a in marriages:
        return await ctx.send(embed=em_err("Déjà marié(e)",
            f"Tu es déjà marié(e). Utilise `!divorce` d'abord."))
    if uid_b in marriages:
        return await ctx.send(embed=em_err("Cible déjà mariée"))
    if marriage_requests.get(uid_b) == uid_a:
        return await ctx.send(embed=em_warn("Demande déjà envoyée",
            f"{member.mention} doit faire `!marry {ctx.author.mention}` pour accepter."))
    if marriage_requests.get(uid_a) == uid_b:
        # Réciprocité : on marie
        marriage_requests.pop(uid_a, None)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        marriages[uid_a] = {"spouse": uid_b, "since": date_str}
        marriages[uid_b] = {"spouse": uid_a, "since": date_str}
        save("marriages", marriages)
        e = em_gold("💍 Mariage célébré !",
            f"{ctx.author.mention} et {member.mention} sont maintenant unis 💞")
        e.set_thumbnail(url=ASSETS.get("ship"))
        return await ctx.send(embed=e)
    marriage_requests[uid_b] = uid_a
    e = em_info("💌 Demande en mariage",
        f"{member.mention}, {ctx.author.mention} te propose de l'épouser !\n"
        f"Réponds par `!marry {ctx.author.mention}` pour accepter.")
    e.set_thumbnail(url=ASSETS.get("ship"))
    await ctx.send(embed=e)

@bot.command()
@commands.guild_only()
async def divorce(ctx):
    uid = str(ctx.author.id)
    if uid not in marriages:
        return await ctx.send(embed=em_err("Tu n'es pas marié(e)"))
    spouse = marriages.pop(uid).get("spouse")
    if spouse and spouse in marriages:
        marriages.pop(spouse, None)
    save("marriages", marriages)
    spouse_obj = ctx.guild.get_member(int(spouse)) if spouse else None
    mention = spouse_obj.mention if spouse_obj else f"`{spouse}`"
    await ctx.send(embed=em_warn("💔 Divorce",
        f"{ctx.author.mention} et {mention} ne sont plus mariés."))

@bot.command(aliases=["mariage"])
@commands.guild_only()
async def couple(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid = str(target.id)
    info = marriages.get(uid)
    if not info:
        return await ctx.send(embed=em_info("Célibataire",
            f"{target.display_name} n'est pas marié(e)."))
    spouse = ctx.guild.get_member(int(info["spouse"]))
    mention = spouse.mention if spouse else f"`{info['spouse']}`"
    e = _em(f"💞 Couple — {target.display_name}",
        f"> **Marié(e) à :** {mention}\n> **Depuis :** `{info.get('since','?')}`",
        C_VIOLET)
    e.set_thumbnail(url=ASSETS.get("ship"))
    await ctx.send(embed=e)

# ── Codes promo ───────────────────────────────────────
@bot.command(name="createcode", aliases=["addcode"])
@commands.guild_only()
async def create_code(ctx, code: str, montant: int, max_uses: int = 1):
    """Crée un code promo (réservé owner/admin)."""
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    if montant <= 0 or max_uses <= 0:
        return await ctx.send(embed=em_err("Valeurs invalides"))
    code_k = code.upper()
    if code_k in promo_codes:
        return await ctx.send(embed=em_err("Code déjà existant"))
    promo_codes[code_k] = {"amount": montant, "max_uses": max_uses, "used_by": []}
    save("promo_codes", promo_codes)
    e = em_ok("Code promo créé",
        f"`{code_k}` — **{montant:,}** pièces — utilisable **{max_uses}** fois\n"
        f"Les utilisateurs peuvent faire `!redeem {code_k}`.")
    await ctx.send(embed=e)

@bot.command(name="deletecode", aliases=["removecode"])
@commands.guild_only()
async def delete_code(ctx, code: str):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    code_k = code.upper()
    if code_k not in promo_codes:
        return await ctx.send(embed=em_err("Code inconnu"))
    promo_codes.pop(code_k); save("promo_codes", promo_codes)
    await ctx.send(embed=em_ok("Code supprimé", f"`{code_k}` supprimé."))

@bot.command(name="codes")
@commands.guild_only()
async def list_codes(ctx):
    if not is_owner(ctx.author) and not has_perm(ctx.author, "admin"):
        return await no_perm(ctx, "admin")
    if not promo_codes:
        return await ctx.send(embed=em_info("Aucun code"))
    lines = [f"`{k}` — **{d['amount']:,}** • {len(d['used_by'])}/{d['max_uses']} utilisé(s)"
             for k, d in promo_codes.items()]
    await ctx.send(embed=em_gold("Codes promo", "\n".join(lines)))

@bot.command()
@commands.guild_only()
async def redeem(ctx, code: str):
    code_k = code.upper()
    data = promo_codes.get(code_k)
    if not data:
        return await ctx.send(embed=em_err("Code invalide"))
    uid = str(ctx.author.id)
    if uid in data["used_by"]:
        return await ctx.send(embed=em_warn("Déjà utilisé",
            "Tu as déjà réclamé ce code."))
    if len(data["used_by"]) >= data["max_uses"]:
        return await ctx.send(embed=em_err("Code épuisé"))
    data["used_by"].append(uid); save("promo_codes", promo_codes)
    add_bal(uid, data["amount"]); check_balance_achievements(uid)
    e = em_gold("🎟️  Code utilisé",
        f"+**{data['amount']:,}** pièces !\n> Solde : `{get_bal(uid):,}`")
    await ctx.send(embed=e)

# ══════════════════════════════════════════════════════
#  DÉMARRAGE
# ══════════════════════════════════════════════════════
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
