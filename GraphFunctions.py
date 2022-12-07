from py2neo import Graph, Node, Relationship
from py2neo.bulk import create_relationships, merge_nodes
import os

class DatabaseManager():
    
    def __init__(self, dbName):
        self.URI=os.getenv("NEO4J_URI")
        self.PASSWORD=os.getenv("NEO4J_PASSWORD")
        self.name=dbName

    def openConnection(self):
        
        try:
            self.g=Graph("bolt://localhost:7687", auth=("neo4j",self.PASSWORD))
            return True
        except:
            print("Can't connect to the database")
            return False
    
    async def getCharacterStats(self, chara: str):
        
        res=self.g.run('Match (:Character {name: $chara})-[r:HAS_PARTECIPATE_IN]->(n:Fight) '+
                    'WITH ' 
                    'CASE WHEN (r.result="won" And n.type="ava") THEN 1 ELSE 0 END as avaWon, '+
                    'CASE WHEN (r.result="lost" And n.type="ava") THEN 1 ELSE 0 END as avaLost, '+
                    'CASE WHEN (r.result="won" And n.type="kolo") THEN 1 ELSE 0 END as koloWon, '+
                    'CASE WHEN (r.result="lost" And n.type="kolo") THEN 1 ELSE 0 END as koloLost, '+
                    'CASE WHEN (r.result="won" And n.type="perce" and r.side="defender") THEN 1 ELSE 0 END as perceDefWon, '+
                    'CASE WHEN (r.result="lost" And n.type="perce" and r.side="defender") THEN 1 ELSE 0 END as perceDefLost, '+
                    'CASE WHEN (r.result="won" And n.type="perce" and r.side="attacker") THEN 1 ELSE 0 END as perceAttackWon, '+
                    'CASE WHEN (r.result="lost" And n.type="perce" and r.side="attacker") THEN 1 ELSE 0 END as perceAttackLost '+
                    'RETURN sum(avaWon) as aw, sum(avaLost) as al, sum(koloWon) as kw, sum(koloLost) as kl, sum(perceDefWon) as pdw, sum(perceDefLost) as pdl, sum(perceAttackWon) as paw, sum(perceAttackLost) as pal',
                    chara=chara).data()[0]
        if(res):
            return res
        else:
            return False
    
    def getUserStats(self, user: str):
        res=self.g.run('Match (:User {name: $user})-[:HAS_CHARACTER]->(:Character)-[r:HAS_PARTECIPATE_IN]->(n:Fight) '+
                    'WITH ' 
                    'CASE WHEN (r.result="won" And n.type="ava") THEN 1 ELSE 0 END as avaWon, '+
                    'CASE WHEN (r.result="lost" And n.type="ava") THEN 1 ELSE 0 END as avaLost, '+
                    'CASE WHEN (r.result="won" And n.type="kolo") THEN 1 ELSE 0 END as koloWon, '+
                    'CASE WHEN (r.result="lost" And n.type="kolo") THEN 1 ELSE 0 END as koloLost, '+
                    'CASE WHEN (r.result="won" And n.type="perce" and r.side="defender") THEN 1 ELSE 0 END as perceDefWon, '+
                    'CASE WHEN (r.result="lost" And n.type="perce" and r.side="defender") THEN 1 ELSE 0 END as perceDefLost, '+
                    'CASE WHEN (r.result="won" And n.type="perce" and r.side="attacker") THEN 1 ELSE 0 END as perceAttackWon, '+
                    'CASE WHEN (r.result="lost" And n.type="perce" and r.side="attacker") THEN 1 ELSE 0 END as perceAttackLost '+
                    'RETURN sum(avaWon) as aw, sum(avaLost) as al, sum(koloWon) as kw, sum(koloLost) as kl, sum(perceDefWon) as pdw, sum(perceDefLost) as pdl, sum(perceAttackWon) as paw, sum(perceAttackLost) as pal').data()[0]
        if(res):
            return res
        else:
            return False
    
    def addCharacter(self, user: str, chara: str):
        
        characterNode=self.g.run("Match (c:Character{name: $character}) "+
            "With c "+
            "CALL { "+
                "MATCH (:User {name: $user})-[r:HAS_CHARACTER]->(c) "+
                "Detach delete r} "+
            "Return c "+
            "Limit 1", character=chara, user=user).data()[0]["c"]
        
        if(characterNode):
        
            userNode=Node("User", name=user)
            userNode.__primarykey__ = "name"
            userNode.__primarylabel__ = "User"
            
            characterNode=Node("Character", name=chara)
            characterNode.__primarykey__ = "name"
            characterNode.__primarylabel__ = "Character"
            
            rel=Relationship(userNode, "HAS_CHARACTER", characterNode)
            
            a=self.g.merge(rel)
        
            return True
        else:
            return False
        
            
    def mergeNames(self, characterList):
        
        characterList=list(map(lambda el:[el.lower()], characterList))
        
        merge_nodes(self.g.auto(), characterList, ("Character", "name") , keys=["name"])

        
    def createRelationship(self, winnerList, loserList, fightNode, flag=0):
        
        finalList=list()
        
        if(not flag):
            for user in winnerList:
                finalList.append((((user.lower())), {"result": "won"}, fightNode))
                
            for user in loserList:
                finalList.append((((user.lower())), {"result": "lost"}, fightNode))
        elif(flag==1):
            for user in winnerList:
                finalList.append((((user.lower())), {"result": "won", "side": "defender"}, fightNode))
                
            for user in loserList:
                finalList.append((((user.lower())), {"result": "lost", "side": "attacker"}, fightNode))
                
        elif(flag==2):
            for user in winnerList:
                finalList.append((((user.lower())), {"result": "won", "side": "attacker"}, fightNode))
                
            for user in loserList:
                finalList.append((((user.lower())), {"result": "lost", "side": "defender"}, fightNode))
        else:
            print("you shouldn't be there")
        
        create_relationships(self.g.auto(), finalList, "HAS_PARTECIPATE_IN", start_node_key=("Character", "name"))
        
        return True
            
        
    def createFight(self, type):
        res=self.g.run("CREATE (x:Fight {type: $type, date: date()}) RETURN id(x) as id", type=type).data()
        return res[0]["id"]