import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from threading import Thread
from flask import Flask
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
def has_charm(user_id):
    records = sheet.get_all_records()
    for row in records:
        if str(row["user_id"]) == str(user_id):
            return str(row.get("charm", "")).upper() == "TRUE"
    return False

def set_charm(user_id, has):
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["user_id"]) == str(user_id):
            sheet.update_cell(i + 2, 3, "TRUE" if has else "FALSE")
            return
    # ユーザーがまだ登録されてない場合
    sheet.append_row([str(user_id), STARTING_COINS, "TRUE" if has else "FALSE"])
from datetime import datetime

def has_received_bonus_today(user_id):
    records = sheet.get_all_records()
    today = datetime.now().strftime("%Y-%m-%d")
    for row in records:
        if str(row["user_id"]) == str(user_id):
            return str(row.get("last_bonus", "")) == today
    return False

def set_bonus_date(user_id):
    records = sheet.get_all_records()
    today = datetime.now().strftime("%Y-%m-%d")
    for i, row in enumerate(records):
        if str(row["user_id"]) == str(user_id):
            sheet.update_cell(i + 2, 3, today)  # 3列目が last_bonus の列
            return




# Flaskでダミーサーバー（Render対策）
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Google Sheets に接続
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("nosuke_data").sheet1  # スプレッドシート名に合わせてね

# 初期コイン数
STARTING_COINS = 100
def get_coins(user_id):
    records = sheet.get_all_records()
    for row in records:
        if str(row["user_id"]) == str(user_id):
            return int(row["coins"])
    return STARTING_COINS

def set_coins(user_id, coins):
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["user_id"]) == str(user_id):
            sheet.update_cell(i + 2, 2, coins)
            return
    sheet.append_row([str(user_id), coins])


# ファイル名
COIN_FILE = "user_coins.json"
CHARM_FILE = "charms.json"
SUPER_CHARM_FILE = "super_charms.json"
SUPER_CHARM_ACTIVE_FILE = "super_charm_active.json"
BANK_FILE = "bank.json"
LAST_INTEREST_WEEK_FILE = "last_interest_week.json"
DAILY_FILE = "daily_bonus.json"
RANK_FILE = "rank_bonus.json"

# 初期設定
STARTING_COINS = 100
SLOTS = ["🍒", "🍋", "🍊", "🍇", "🍉", "⭐", "🔔"]
DAILY_BONUSES = {0: 100, 1: 150, 2: 200, 3: 250, 4: 300, 5: 400, 6: 700}
RANK_BONUSES = [1000, 700, 500, 300, 200]

# JSON読み書き
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

# データ読み込み
user_coins = load_json(COIN_FILE)
user_charms = load_json(CHARM_FILE)
user_super_charms = load_json(SUPER_CHARM_FILE)
user_super_charm_active = load_json(SUPER_CHARM_ACTIVE_FILE)
user_bank = load_json(BANK_FILE)
last_interest_week = load_json(LAST_INTEREST_WEEK_FILE)
daily_claims = load_json(DAILY_FILE)
rank_claims = load_json(RANK_FILE)

# 週番号取得
def get_current_week():
    return datetime.utcnow().isocalendar().week

# 銀行利子の自動加算（週1回）
def apply_weekly_interest():
    current_week = get_current_week()
    if last_interest_week.get("week") == current_week:
        return
    for user_id, balance in user_bank.items():
        if balance > 0:
            interest = max(1, int(balance * 0.01))
            user_bank[user_id] += interest
    last_interest_week["week"] = current_week
    save_json(BANK_FILE, user_bank)
    save_json(LAST_INTEREST_WEEK_FILE, last_interest_week)

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"スラッシュコマンドを同期しました: {len(synced)}個")
    except Exception as e:
        print(f"同期エラー: {e}")
# 🎰 スロットコマンド
import random
import discord
from discord import app_commands

SLOTS = ["🍒", "🍋", "🍇", "🍊", "🍉"]

@bot.tree.command(name="slot", description="スロットマシンを回してコインを賭けよう！")
async def slot(interaction: discord.Interaction, bet: int):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    coins = get_coins(user_id)

    if bet <= 0 or bet > coins:
        await interaction.followup.send("⚠️ 賭け金が無効か、コインが足りないよ！")
        return

    roll = [random.choice(SLOTS) for _ in range(3)]

    if roll[0] == roll[1] == roll[2]:
        winnings = bet * 3
        coins += winnings
        result_text = f"🎉 ジャックポット！{winnings}コイン獲得！"
    elif roll[0] == roll[1] or roll[1] == roll[2] or roll[0] == roll[2]:
        coins -= bet  # まず全額引く
        refund = int(bet * 0.5)
        coins += refund  # その後、半分だけ返す
        result_text = f"🔁 2つ一致！{refund}コイン返ってきたよ！"


    else:
        coins -= bet
        result_text = f"😢 はずれ！{bet}コイン失ったよ…"

    set_coins(user_id, coins)

    await interaction.followup.send(
        f"{' | '.join(roll)}\n{result_text}\n💰 現在のコイン残高: {coins}"
    )



# 🧧 ラッキーチャーム購入
@bot.tree.command(name="buy_charm", description="ラッキーチャームを購入するよ")
async def buy_charm(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    coins = get_coins(user_id)

    if has_charm(user_id):
        await interaction.followup.send("🧧 すでにお守りを持ってるよ！")
        return

    if coins < 300:
        await interaction.followup.send("💸 コインが足りないよ！")
        return

    coins -= 300
    set_coins(user_id, coins)
    set_charm(user_id, True)

    await interaction.followup.send("🧧 ラッキーチャームを購入したよ！")

# 🌟 スーパーラッキーチャーム使用
@bot.tree.command(name="use_scharm", description="スーパーラッキーチャームを使うよ")
async def use_scharm(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if not user_super_charms.get(user_id, False):
        await interaction.response.send_message("🧧 スーパーラッキーチャームを持ってないよ！", ephemeral=True)
        return
    if user_super_charm_active.get(user_id, False):
        await interaction.response.send_message("⚠️ すでに使用中だよ！", ephemeral=True)
        return
    user_super_charms[user_id] = False
    user_super_charm_active[user_id] = True
    save_json(SUPER_CHARM_FILE, user_super_charms)
    save_json(SUPER_CHARM_ACTIVE_FILE, user_super_charm_active)
    await interaction.response.send_message("🌟 スーパーラッキーチャームを使ったよ！次のスロットでジャックポット確定！")

# 🎁 ミステリーボックス購入
@bot.tree.command(name="buy_box", description="ミステリーボックスを購入して開けるよ！")
async def buy_box(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    coins = get_coins(user_id)

    if coins < 400:
        await interaction.followup.send("💸 コインが足りないよ！")
        return

    coins -= 400
    result = random.randint(-500, 1000)
    got_super_charm = random.random() < 0.05
    msg = ""

    # スーパーお守りの処理（Google Sheetsで管理するなら別関数が必要）
    if got_super_charm and not has_super_charm(user_id):
        set_super_charm(user_id, True)
        msg += "🌟 スーパーラッキーチャームを引き当てた！\n"
    elif got_super_charm:
        result += 300
        msg += "🎁 レアお守りが出たけど、すでに持ってたから代わりに+300コイン！\n"

    coins += result
    set_coins(user_id, coins)

    if result > 0:
        msg += f"🎉 +{result}コインゲット！"
    elif result < 0:
        msg += f"😱 {result}コイン失った…"
    else:
        msg += "😐 中身は空っぽだった！±0コイン！"

    msg += f"\n💰 現在のコイン残高: {coins}"
    await interaction.followup.send(msg)

# 📅 デイリーボーナス
@bot.tree.command(name="daily", description="1日1回のデイリーボーナスを受け取ろう！")
async def daily(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)

    if has_received_bonus_today(user_id):
        await interaction.followup.send("🕒 今日はもうデイリーボーナスを受け取ったよ！また明日ね！")
        return

    bonus = random.randint(100, 300)
    coins = get_coins(user_id)
    coins += bonus
    set_coins(user_id, coins)
    set_bonus_date(user_id)

    await interaction.followup.send(f"🎁 デイリーボーナス！{bonus}コインゲット！\n💰 現在のコイン残高: {coins}")


# 🏦 銀行：預け入れ
@bot.tree.command(name="deposit", description="銀行にコインを預けるよ")
async def deposit(interaction: discord.Interaction, amount: int):
    apply_weekly_interest()
    user_id = str(interaction.user.id)
    if amount <= 0 or user_coins.get(user_id, STARTING_COINS) < amount:
        await interaction.response.send_message("⚠️ 金額が無効か、コインが足りないよ！", ephemeral=True)
        return
    user_coins[user_id] -= amount
    user_bank[user_id] = user_bank.get(user_id, 0) + amount
    save_json(COIN_FILE, user_coins)
    save_json(BANK_FILE, user_bank)
    await interaction.response.send_message(f"🏦 {amount}コインを銀行に預けたよ！")

# 🏦 銀行：引き出し
@bot.tree.command(name="withdraw", description="銀行からコインを引き出すよ")
async def withdraw(interaction: discord.Interaction, amount: int):
    apply_weekly_interest()
    user_id = str(interaction.user.id)
    if amount <= 0 or user_bank.get(user_id, 0) < amount:
        await interaction.response.send_message("⚠️ 金額が無効か、預金が足りないよ！", ephemeral=True)
        return
    user_bank[user_id] -= amount
    user_coins[user_id] = user_coins.get(user_id, STARTING_COINS) + amount
    save_json(COIN_FILE, user_coins)
    save_json(BANK_FILE, user_bank)
    await interaction.response.send_message(f"💸 {amount}コインを銀行から引き出したよ！")

# 🏦 銀行：残高確認
@bot.tree.command(name="bank", description="銀行の預金残高を確認するよ")
async def bank(interaction: discord.Interaction):
    apply_weekly_interest()
    user_id = str(interaction.user.id)
    balance = user_bank.get(user_id, 0)
    await interaction.response.send_message(f"🏦 あなたの銀行預金残高は **{balance}コイン** だよ！")

# 🏆 ランキングボーナス受け取り
@bot.tree.command(name="rank_bonus", description="2週に1回のランキングボーナスを受け取るよ！")
async def rank_bonus(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    current_week = get_current_week()
    weekday = datetime.utcnow().weekday()

    if current_week % 2 != 0 or weekday != 0:
        await interaction.response.send_message("📅 このボーナスは**偶数週の月曜日**だけ受け取れるよ！", ephemeral=True)
        return

    if rank_claims.get(user_id) == current_week:
        await interaction.response.send_message("🎁 今週のランキングボーナスはもう受け取ったよ！", ephemeral=True)
        return

    sorted_users = sorted(user_coins.items(), key=lambda x: x[1], reverse=True)
    top_users = [uid for uid, _ in sorted_users[:len(RANK_BONUSES)]]

    if user_id in top_users:
        rank = top_users.index(user_id)
        bonus = RANK_BONUSES[rank]
        user_coins[user_id] += bonus
        rank_claims[user_id] = current_week
        save_json(COIN_FILE, user_coins)
        save_json(RANK_FILE, rank_claims)
        await interaction.response.send_message(
            f"🏆 ランキング{rank+1}位！{bonus}コインのボーナスをゲット！\n💰 現在のコイン残高: {user_coins[user_id]}"
        )
    else:
        await interaction.response.send_message("😢 今回はランキングに入れなかったみたい…また次回がんばろう！", ephemeral=True)

# 💰 残高確認
@bot.tree.command(name="balance", description="自分のコイン残高を確認するよ")
async def balance(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    user_id = str(interaction.user.id)
    coins = get_coins(user_id)
    await interaction.followup.send(f"💰 あなたのコイン残高は {coins} コインだよ！")


# 🔑 トークンで起動
TOKEN = os.getenv("YOUR_BOT_TOKEN")
bot.run(TOKEN)
