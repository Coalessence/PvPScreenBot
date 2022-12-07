import discord
from discord import app_commands, emoji
import os
from dotenv import load_dotenv
import json
from extractScreen import DofusScreenExtractor,WINNERS, LOSERS
import asyncio
from GraphFunctions import DatabaseManager


load_dotenv()
TOKEN=os.getenv("DISCORDTOKEN")
serverList=json.loads(os.getenv("SERVERS"))

path_to_tesseract = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
conf= "--psm 6 -l eng+ita+fra+rus"
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

####################  INIT #######################################

dse=DofusScreenExtractor(path_to_tesseract, conf)
graphManager=DatabaseManager("")
if(graphManager.openConnection()):
    client=DofusBot(serverList)
else:
    print("error in the database connection")

#################### END INIT #####################################
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        
    @discord.ui.button(label="✅Confirm the results", style=discord.ButtonStyle.grey)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️Submitting⚙️", ephemeral=True)
        self.value = 1
        self.stop()

    @discord.ui.button(label="🆘There is an error in the result", style=discord.ButtonStyle.grey)
    async def manageError(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 2
        self.stop()
    
    @discord.ui.button(label="❌Cancel the results", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 3
        self.stop()
        
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

class addNameModal(discord.ui.Modal):
    
    text=discord.ui.TextInput(label="Insert the name of the character", required=True, min_length=3)
    
    def __init__(self, title):
        super().__init__(title=title)
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.value=self.text.value
        self.stop()
        
class ChooseErrorView(discord.ui.View):
    @discord.ui.select( 
        placeholder = "Tell me what kind of error happened",
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options=[discord.SelectOption(label="One of the names is spelled wrong", value="errorName"), 
            discord.SelectOption(label="One of the names shouldn't be there", value="errorDelete"),
            discord.SelectOption(label="One of the names that should be there is missing", value="errorAdd")]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select): 
        await interaction.response.defer()
        self.value=select.values[0]
        self.stop()
        
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

class ChooseSideAddView(discord.ui.View):
    @discord.ui.select( 
        placeholder = "Which of the two teams is missing a Character",
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options=[discord.SelectOption(label="Winners Team", value="win"), 
            discord.SelectOption(label="Losers Team", value="lose")]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select): 
        
        nameModal=addNameModal("Add Player")
        await interaction.response.send_modal(nameModal)
        await nameModal.wait()
        self.value={"side" :select.values[0], "name": nameModal.value}
        self.stop()
        
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

class ErrorNameOptions(discord.ui.Select):
    def __init__(self, userList):
        options=list()  
        for user in userList:
            options.append(discord.SelectOption(label=user, value=user))
        super().__init__(placeholder="Which is the name that you want to change?", min_values=1, max_values=1, options=options)
        
class ErrorDeleteOptions(discord.ui.Select):
    def __init__(self, userList):
        options=list()
        for user in userList:
            options.append(discord.SelectOption(label=user, value=user))
        super().__init__(placeholder="Which is the name that you want to delete?", min_values=1, max_values=1, options=options)

class ErrorView(discord.ui.View):
    def __init__(self, typeError, userList):
        super().__init__()
        self.value=None
        self.options=None
        self.typeError=typeError
        match(typeError):
            case "errorName":
                self.options=ErrorNameOptions(userList)
                self.options.callback=self.select_callback
                self.add_item(self.options)
            case "errorDelete":
                self.options=ErrorDeleteOptions(userList)
                self.options.callback=self.select_callback
                self.add_item(self.options)
                
    async def select_callback(self, interaction: discord.Interaction): 
        if(self.typeError=="errorDelete"):
            await interaction.response.defer()
            self.value=self.options.values[0]
            self.stop()
        else:
            nameModal=addNameModal("Add Player")
            await interaction.response.send_modal(nameModal)
            await nameModal.wait()
            self.value={"oldName" :self.options.values[0], "newName": nameModal.value}
            self.stop()
            
@client.tree.command(
    description="See the stats of a character"
)
@app_commands.describe(character="The name of the character you want to see the stats")
async def stats(interaction: discord.Interaction, character: str):
    res=await graphManager.getCharacterStats(character.lower())
    
    if(res):
        embed=discord.Embed(title=character+" Scores", color=discord.Color.gold())
        
        embed.add_field(name="Type", value="Kolo\nAva\nPerce Attack     \nPerce Defence     ", inline=True)
        embed.add_field(name="Won", value=""+str(res["kw"])+"\n"+str(res["aw"])+"\n"+str(res["paw"])+"\n"+str(res["pdw"]))
        embed.add_field(name="Lost", value=""+str(res["kl"])+"\n"+str(res["al"])+"\n"+str(res["pal"])+"\n"+str(res["pdl"]))
        
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("There was an error, please contact the bot administrator", ephemeral=True)
        
@client.tree.command()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")
  
@client.tree.command(
    description="Link your character to your discord user, don't use it on characters that aren't yours please"
)
@app_commands.describe(character="The name of the character you want to link to your username")
async def addcharacter(interaction: discord.Interaction, character: str):
    user=interaction.user.name
    res=await graphManager.addCharacter(user, character.lower())
    
    if(res):
        await interaction.response.send_message("Correctly linked user: "+user+" with character: "+character)
    else:
        await interaction.response.send_message("There was an error, please contact the bot administrator", ephemeral=True)
    
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
    
    for i in range(len(res)):
        if res[i] in WINNERS:
            res[i]="Winners"
        elif res[i] in LOSERS:
            res[i]="Losers"
    
    perceFlag=True
    perceIndex=0
    losersIndex=res.index("Losers")
    positionFlag=0
    sendFlag=False
    
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
    
    if(len(res)>losersIndex+1):
        losersList=res[losersIndex+1:]
    else:
        losersList=list()
   
    while(True):
        
        embed=discord.Embed(title="Battle report", color=discord.Color.gold())
        
        winnersValue=""
        losersValue=""
        
        if len(winnersList)==0:
            winnersList.append("🏳️")
            
        if len(losersList)==0:
            losersList.append("🏳️")
            
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
                    embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot administrator")
            case "kolo":
                if not perceFlag:
                    embed.add_field(name="\N{trophy}**Winners**", value=winnersValue)
                    embed.add_field(name="\N{headstone}**Losers**", value=losersValue, inline=True)
                else:
                    embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot administrator")

            case "ava":
                if not perceFlag:
                    embed.add_field(name="\N{trophy}**Winners**", value=winnersValue)
                    embed.add_field(name="\N{headstone}**Losers**", value=losersValue, inline=True)
                else:
                    embed.add_field(name="Error", value="Something went wrong, if you are sure you selected the right category contact your bot administrator")
        
        confirmView=Confirm()
        
        msg=await interaction.followup.send(embed=embed, view=confirmView, wait=True)
                                    
        await confirmView.wait()
        
        await msg.edit(view=None)
        
        if confirmView.value is None:
            await msg.delete()
            interaction.followup.send(content="The confirmation timed out, your screen will not be registered", ephemeral=True)
            break
        elif confirmView.value==1:
            sendFlag=True
            break
        elif confirmView.value==2:
                
            errorChooseView=ChooseErrorView()
            
            msg= await interaction.followup.send(view=errorChooseView, ephemeral=True, wait=True)
            
            await errorChooseView.wait()
            
            await msg.delete()
            
            match(errorChooseView.value):
                case "errorName":
                    
                    errorView=ErrorView(errorChooseView.value, winnersList+losersList)
                    
                    msg= await interaction.followup.send(view=errorView, ephemeral=True, wait=True)
                    await errorView.wait()
                    await msg.delete()
                    
                    oldName=errorView.value["oldName"]
                    newName=errorView.value["newName"]
                    
                    if(oldName in winnersList):
                        winnersList = list(map(lambda x: x.replace(oldName, newName), winnersList))
                    else:
                        losersList = list(map(lambda x: x.replace(oldName, newName), losersList))
                    
                case "errorDelete":
                    errorView=ErrorView(errorChooseView.value, winnersList+losersList)
                    
                    msg= await interaction.followup.send(view=errorView, ephemeral=True, wait=True)
                    await errorView.wait()
                    await msg.delete()
                    
                    if(errorView.value in winnersList):
                        winnersList.remove(errorView.value)
                    else:
                        losersList.remove(errorView.value)
                        
                case "errorAdd":
                    sideAddView=ChooseSideAddView()
            
                    msg= await interaction.followup.send(view=sideAddView, ephemeral=True, wait=True)
                    
                    await sideAddView.wait()
                    
                    await msg.delete()
                    
                    name=sideAddView.value["name"]
                    
                    print(sideAddView.value)
                    
                    #could be more robust, for now it's fine
                    if(" " in name):
                        sideAddView.value=""
                    
                    match(sideAddView.value["side"]):
                        case "win":
                            winnersList.append(name)
                        case "lose":
                            losersList.append(name)
                        case _:
                            await interaction.followup.send(content="Error in name or interaction timed out", ephemeral=True)
                case _:
                    await interaction.followup.send(content="Interaction timed out", ephemeral=True)
                            
        else:
            await msg.delete()
            await interaction.followup.send(content="Your screen won't be registered", ephemeral=True)
            break
    if(sendFlag):
        
        if "🏳️" in winnersList:    
            winnersList.remove("🏳️")
            
        if "🏳️" in losersList:    
            losersList.remove("🏳️")

        graphManager.mergeNames(winnersList+losersList)
        
        match(type.value):
            case "perce":
                if(graphManager.createRelationship(winnersList, losersList, graphManager.createFight(type.value), positionFlag)):
                    await interaction.followup.send("Screen registered correctly")
                else:
                    await interaction.followup.send("There was an error, please contact the bot administrator", ephemeral=True)
            case "ava":
                if(graphManager.createRelationship(winnersList, losersList, graphManager.createFight(type.value))):
                    await interaction.followup.send("Screen registered correctly")
                else:
                    await interaction.followup.send("There was an error, please contact the bot administrator", ephemeral=True)
            case "kolo":
                if(graphManager.createRelationship(winnersList, losersList, graphManager.createFight(type.value))):
                    await interaction.followup.send("Screen registered correctly")
                else:
                    await interaction.followup.send("There was an error, please contact the bot administrator", ephemeral=True) 