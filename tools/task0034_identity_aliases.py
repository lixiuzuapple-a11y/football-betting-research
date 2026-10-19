"""Human-reviewed name and abbreviation crosswalk used only for identity.

Source evidence: official Sporttery fixture abbreviations/team ids and ESPN
scoreboard team abbreviations and display names; Football-Data 26/27 league
team names; no final scores or odds in mapping inputs. An alias alone does
NOT establish match identity; league, kickoff and BOTH teams must also agree.
"""
OFFICIAL_TO_ESPN={
 "英超":{"ASV":"AVL","BRN":"BRE","MNU":"MAN","NOT":"NFO"},
 "英冠":{"STO":"STK","NOH":"NOR","WLV":"WOL","LIN":"LCN"},
 "德甲":{"FRT":"SGE","COL":"KOE","MGB":"BMG","FRE":"SCF","SCH":"S04",
         "AUG":"FCA","WBR":"SVW","PAD":"SCP","MAZ":"M05",
         "STU":"VFB","UBL":"FCU","BMN":"MUN","LEV":"B04","HOF":"TSG"},
 "西甲":{"ALS":"ALA","RMD":"RMA","CFE":"ELC","CVO":"CEL","RBT":"BET",
          "RAS":"RAC","LVT":"LEV","VCA":"VAL","BIL":"ATH","VNO":"RAY","MAL":"MCF"},
 "意甲":{"INM":"INT","NPL":"NAP","FSN":"FRO","CMO":"COMO","ROM":"ROMA",
          "MOZ":"MON","LCC":"LEC","BOG":"BOL","SSL":"SAS","ACM":"MIL",
          "VEZ":"VEN","ACT":"TOR","GNA":"GEN"},
 "法甲":{"LIL":"LILL","LEH":"HAC","NIC":"NICE","STB":"STR",
          "MAS":"OLM","TRO":"TRY","SOA":"ANG","LYO":"LYON","LEM":"MNS"},
}
# Only exact ESPN display names to independently documented Football-Data team
# names. No substring/fuzzy matching and each mapping is league scoped.
ESPN_TO_FD={
 "英超":{
  "Leeds United":"Leeds","AFC Bournemouth":"Bournemouth","Ipswich Town":"Ipswich",
  "Brighton & Hove Albion":"Brighton","Manchester United":"Man United",
  "Tottenham Hotspur":"Tottenham","Nottingham Forest":"Nott'm Forest",
  "Hull City":"Hull","Manchester City":"Man City","Newcastle United":"Newcastle"},
 "英冠":{
  "Norwich City":"Norwich","Queens Park Rangers":"QPR","Derby County":"Derby",
  "Lincoln City":"Lincoln","West Ham United":"West Ham","Cardiff City":"Cardiff",
  "Charlton Athletic":"Charlton","Birmingham City":"Birmingham","Stoke City":"Stoke",
  "Bolton Wanderers":"Bolton","Swansea City":"Swansea",
  "West Bromwich Albion":"West Brom","Blackburn Rovers":"Blackburn","Preston North End":"Preston",
  "Sheffield United":"Sheffield United","Wolverhampton Wanderers":"Wolves"},
 "德甲":{
  "FC Cologne":"FC Koln","Borussia Mönchengladbach":"M'gladbach","SC Freiburg":"Freiburg",
  "1. FC Union Berlin":"Union Berlin","Borussia Dortmund":"Dortmund",
  "Hamburg SV":"Hamburg","VfB Stuttgart":"Stuttgart","SV Elversberg":"Elversberg",
  "FC Augsburg":"Augsburg","SC Paderborn 07":"Paderborn","Bayer Leverkusen":"Leverkusen",
  "TSG Hoffenheim":"Hoffenheim","Eintracht Frankfurt":"Ein Frankfurt",
  "Werder Bremen":"Werder Bremen","Bayern Munich":"Bayern Munich"},
 "西甲":{
  "Rayo Vallecano":"Vallecano","Athletic Club":"Ath Bilbao","Atlético Madrid":"Ath Madrid",
  "Celta Vigo":"Celta","Real Sociedad":"Sociedad","Deportivo":"La Coruna",
  "Real Betis":"Betis","Racing Santander":"Santander","Espanyol":"Espanol",
  "Elche":"Elche","Real Madrid":"Real Madrid","Málaga":"Malaga"},
 "意甲":{"AS Roma":"Roma","AC Milan":"Milan","Internazionale":"Inter",
          "SSC Napoli":"Napoli","Bologna":"Bologna","Frosinone":"Frosinone",
          "Como":"Como","Torino":"Torino"},
 "法甲":{"Le Havre AC":"Le Havre","AS Monaco":"Monaco",
         "Paris Saint-Germain":"Paris SG","Stade Rennais":"Rennes",
         "AJ Auxerre":"Auxerre","Olympique de Marseille":"Marseille",
         "Nice":"Nice","Lille":"Lille","Strasbourg":"Strasbourg"}
}
def sporttery_to_espn(league,code):
    return OFFICIAL_TO_ESPN.get(league,{}).get(code,code)
def espn_to_fd(league,team_name,fd_club_names):
    proposed=ESPN_TO_FD.get(league,{}).get(team_name,team_name)
    if proposed not in fd_club_names:return None
    return proposed
