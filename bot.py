import discord
from discord.ext import commands
from cve_hunter import CVEHunter
import os
from dotenv import load_dotenv

# .envファイルを読み込む（これでおまじないのように設定が読み込まれる）
load_dotenv()

# ==========================================
# 環境変数からTOKENを取得
TOKEN = os.getenv("DISCORD_TOKEN")
# ==========================================

# Tokenがない場合のエラーチェック
if not TOKEN or TOKEN == "ここにDiscordのTokenを貼り付け":
    print("❌ エラー: .env ファイルに DISCORD_TOKEN が設定されていません！")
    exit(1)

# Botの設定 (メッセージの中身を読む権限をONにする)
intents = discord.Intents.default()
intents.message_content = True

# コマンドのプレフィックス
bot = commands.Bot(command_prefix='!', intents=intents)

# 分析エンジンを初期化
hunter = CVEHunter()

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="!cve CVE-xxxx で分析"))

@bot.command()
async def cve(ctx, cve_id: str):
    """
    コマンド: !cve CVE-2024-XXXX
    指定されたCVEを分析して返します。
    """
    cve_id = cve_id.upper().strip()

    if not cve_id.startswith("CVE-"):
        await ctx.send("❌ フォーマットエラー: `CVE-xxxx-xxxx` の形式で入力してください。")
        return

    await ctx.message.add_reaction("🔍")
    loading_msg = await ctx.send(f"🤖 **{cve_id}** を調査中... NVDへの問い合わせとAI分析を行っています。")

    try:
        # 重い処理を別スレッドで実行
        result = await bot.loop.run_in_executor(None, hunter.process_specific_cve, cve_id)

        if result['status'] == "error":
            await loading_msg.edit(content=f"❌ エラー: {result['msg']}")
            return

        data = result['data']
        summary = result['summary']
        
        # 色の決定
        color = 0x3498db
        if data['score'] >= 9.0: color = 0xff0000
        elif data['score'] >= 7.0: color = 0xe67e22
        
        # Embedを作成
        embed = discord.Embed(
            title=f"🛡️ {data['id']} Analysis Result",
            url=f"https://nvd.nist.gov/vuln/detail/{data['id']}",
            color=color
        )
        embed.add_field(name="CVSS Score", value=f"{data['score']} ({data['severity']})", inline=True)
        embed.add_field(name="Published", value=data['published'][:10], inline=True)
        
        # 説明文のトリミング
        embed.description = summary[:4000]
        
        embed.set_footer(text="✅ Obsidianにも保存しました / MySOC Bot")

        await ctx.send(embed=embed)
        await loading_msg.delete()
        await ctx.message.add_reaction("✅")

    except Exception as e:
        print(f"Error: {e}") # コンソールに詳細を出す
        await ctx.send(f"💥 致命的なエラーが発生しました: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)