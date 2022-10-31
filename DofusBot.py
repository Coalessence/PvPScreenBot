from ast import Str
from re import A
from tkinter import FIRST
from turtle import Screen, title
import discord
from discord import app_commands, emoji
import os
from dotenv import load_dotenv
import json
from extractScreen import DofusScreenExtractor,WINNERS, LOSERS
import asyncio

load_dotenv()
TOKEN=os.getenv("DISCORDTOKEN")
serverList=json.loads(os.getenv("SERVERS"))

path_to_tesseract = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
conf= "--psm 6 -l eng+ita+fra+rus"

dse=DofusScreenExtractor(path_to_tesseract, conf)

class DofusBot(discord.Client):
    def __init__(self, guildList):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.guildList=guildList
    
    async def on_ready(self):
        await self.wait_until_ready()
        print(f'logged on as {self.user}! in {self.guilds[0].name}')
    
    async def setup_hook(self):
        for guildItem in self.guildList:
            self.tree.copy_global_to(guild=discord.Object(id=guildItem))
            await self.tree.sync(guild=discord.Object(id=guildItem))
    
    def run(self):
        super().run(TOKEN)


client=DofusBot(serverList)
        
@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""#
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')
    
@client.tree.command( description="Upload your fight screen and get its data recorder")
@app_commands.describe(attachment="The screen you want to record in the system, please make it as focused as possible", 
                       type="What is your screen about? A perce aggro or defence, a fight in AvA or a kolo PvP")
@app_commands.choices(type=[
    app_commands.Choice(name="Perce", value="perce"),
    app_commands.Choice(name="Kolo", value="kolo"),
    app_commands.Choice(name="Ava", value="ava"),
    ])
async def screen(interaction: discord.Interaction, attachment: discord.Attachment, type: app_commands.Choice[str]):

    await interaction.response.defer()
    res=await dse.extractMain(await attachment.read())
    #res=await dse.extractMain( attachment.url)
    
    for i in range(len(res)):
        if res[i] in WINNERS:
            res[i]="Winners"
        elif res[i] in LOSERS:
            res[i]="Losers"
    
    perceFlag=True
    perceIndex=0
    losersIndex=res.index("Losers")
    positionFlag=0
    
    try:
        perceIndex=res.index("Perce")
        if(perceIndex>losersIndex):
            positionFlag=2
        else:
            positionFlag=1
            losersIndex-=1
        del res[perceIndex] 
    except ValueError:
        perceFlag=False
      
   
    
    winnersList=res[1:losersIndex]
    losersList=res[losersIndex+1:]
    
    
    embed=discord.Embed(title="Battle report", color=discord.Color.gold())
    
    winnersValue=""
    losersValue=""
    
    for winner in winnersList:
        winnersValue=winnersValue+winner+"\n"
    
    for loser in losersList:
        losersValue=losersValue+loser+"\n"
    
    match(type.value):
        case "perce":
            if perceFlag:
                if(positionFlag==1):
                    embed.add_field(name="\N{trophy}**Winners**", value="\N{shield}**Defenders** \n"+winnersValue)
                    embed.add_field(name="\N{headstone}**Losers**", value="\N{crossed swords}**Attackers** \n"+losersValue, inline=True)
                else:
                    embed.add_field(name="\N{trophy}**Winners**", value="\N{crossed swords}**Attackers** \n"+winnersValue)
                    embed.add_field(name="\N{headstone}**Losers**", value="\N{shield}**Defenders** \n"+losersValue, inline=True)
            else:
                embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot technician")
        case "kolo":
            if not perceFlag:
                embed.add_field(name="\N{trophy}**Winners**", value=winnersValue)
                embed.add_field(name="\N{headstone}**Losers**", value=losersValue, inline=True)
            else:
                embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot technician")

        case "ava":
            if not perceFlag:
                embed.add_field(name="\N{trophy}**Winners**", value=winnersValue)
                embed.add_field(name="\N{headstone}**Losers**", value=losersValue, inline=True)
            else:
                embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot technician")
    
    print(res)
    
    
    await interaction.followup.send(embed=embed)
