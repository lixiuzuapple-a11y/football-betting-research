"""TASK0037 manually reviewed 2026-10 multi-competition cross-provider event identity.

Sources (explicit evidence, no odds or score selection):
- Sporttery official all-name Chinese team labels and immutable team IDs from
  verified original gz raw-response SHA / SQLite snapshot.
- ESPN league-specific public fixture team ID, English displayName, event ID,
  ISO UTC kickoff. Exact match required to approve.
Manual match-level alias record is deliberately explicit: no fuzzy auto-joins.
"""
APPROVED = {
  "2041921": {
    "event_id": "401912628",
    "official_chinese": [
      "迪拜连接",
      "吉达国民"
    ],
    "espn_display": [
      "Al Wasl",
      "Al Ahli"
    ]
  },
  "2041951": {
    "event_id": "401912626",
    "official_chinese": [
      "上海海港",
      "大田市民"
    ],
    "espn_display": [
      "Shanghai Port",
      "Daejeon Hana Citizen"
    ]
  },
  "2041952": {
    "event_id": "401912647",
    "official_chinese": [
      "布里兰",
      "北京国安"
    ],
    "espn_display": [
      "Buriram United",
      "Beijing Guoan"
    ]
  },
  "2041953": {
    "event_id": "401915418",
    "official_chinese": [
      "朗斯",
      "里斯本竞技"
    ],
    "espn_display": [
      "Lens",
      "Sporting CP"
    ]
  },
  "2041954": {
    "event_id": "401915413",
    "official_chinese": [
      "国际米兰",
      "布鲁日"
    ],
    "espn_display": [
      "Internazionale",
      "Club Brugge"
    ]
  },
  "2041955": {
    "event_id": "401915417",
    "official_chinese": [
      "阿森纳",
      "里尔"
    ],
    "espn_display": [
      "Arsenal",
      "Lille"
    ]
  },
  "2041956": {
    "event_id": "401915410",
    "official_chinese": [
      "比利亚雷亚尔",
      "那不勒斯"
    ],
    "espn_display": [
      "Villarreal",
      "Napoli"
    ]
  },
  "2041957": {
    "event_id": "401915411",
    "official_chinese": [
      "维京",
      "拜仁慕尼黑"
    ],
    "espn_display": [
      "Viking FK",
      "Bayern Munich"
    ]
  },
  "2041958": {
    "event_id": "401915434",
    "official_chinese": [
      "莱比锡红牛",
      "PSV埃因霍温"
    ],
    "espn_display": [
      "RB Leipzig",
      "PSV Eindhoven"
    ]
  },
  "2041959": {
    "event_id": "401915435",
    "official_chinese": [
      "加拉塔萨雷",
      "巴塞罗那"
    ],
    "espn_display": [
      "Galatasaray",
      "Barcelona"
    ]
  },
  "2041960": {
    "event_id": "401915412",
    "official_chinese": [
      "马德里竞技",
      "曼彻斯特联"
    ],
    "espn_display": [
      "Atlético Madrid",
      "Manchester United"
    ]
  },
  "2041962": {
    "event_id": "401912645",
    "official_chinese": [
      "神户胜利船",
      "全北现代"
    ],
    "espn_display": [
      "Vissel Kobe",
      "Jeonbuk Hyundai Motors"
    ]
  },
  "2041963": {
    "event_id": "401912623",
    "official_chinese": [
      "柏太阳神",
      "曼谷港务"
    ],
    "espn_display": [
      "Kashiwa Reysol",
      "Port FC"
    ]
  },
  "2041965": {
    "event_id": "401915416",
    "official_chinese": [
      "费耶诺德",
      "科莫"
    ],
    "espn_display": [
      "Feyenoord Rotterdam",
      "Como"
    ]
  },
  "2041966": {
    "event_id": "401915415",
    "official_chinese": [
      "LASK林茨",
      "利物浦"
    ],
    "espn_display": [
      "LASK Linz",
      "Liverpool"
    ]
  },
  "2041968": {
    "event_id": "401915414",
    "official_chinese": [
      "罗马",
      "皇家马德里"
    ],
    "espn_display": [
      "AS Roma",
      "Real Madrid"
    ]
  },
  "2041969": {
    "event_id": "401915393",
    "official_chinese": [
      "博德闪耀",
      "多特蒙德"
    ],
    "espn_display": [
      "Bodo/Glimt",
      "Borussia Dortmund"
    ]
  },
  "2041970": {
    "event_id": "401915408",
    "official_chinese": [
      "皇家贝蒂斯",
      "波尔图"
    ],
    "espn_display": [
      "Real Betis",
      "FC Porto"
    ]
  },
  "2041971": {
    "event_id": "401915407",
    "official_chinese": [
      "曼彻斯特城",
      "巴黎圣日尔曼"
    ],
    "espn_display": [
      "Manchester City",
      "Paris Saint-Germain"
    ]
  },
  "2041972": {
    "event_id": "401915409",
    "official_chinese": [
      "阿斯顿维拉",
      "费内巴切"
    ],
    "espn_display": [
      "Aston Villa",
      "Fenerbahce"
    ]
  },
  "2041973": {
    "event_id": "401912522",
    "official_chinese": [
      "弗鲁米嫩塞",
      "帕尔梅拉斯"
    ],
    "espn_display": [
      "Fluminense",
      "Palmeiras"
    ]
  },
  "2041975": {
    "event_id": "401915566",
    "official_chinese": [
      "里昂",
      "水晶宫"
    ],
    "espn_display": [
      "Lyon",
      "Crystal Palace"
    ]
  },
  "2041976": {
    "event_id": "401915575",
    "official_chinese": [
      "托林斯",
      "桑德兰"
    ],
    "espn_display": [
      "Torreense",
      "Sunderland"
    ]
  },
  "2041977": {
    "event_id": "401915576",
    "official_chinese": [
      "波兹南莱赫",
      "勒沃库森"
    ],
    "espn_display": [
      "Lech Poznan",
      "Bayer Leverkusen"
    ]
  },
  "2041978": {
    "event_id": "401915574",
    "official_chinese": [
      "圣吉尔联合",
      "皇家社会"
    ],
    "espn_display": [
      "Union St.-Gilloise",
      "Real Sociedad"
    ]
  },
  "2041979": {
    "event_id": "401915568",
    "official_chinese": [
      "萨尔茨堡",
      "AC米兰"
    ],
    "espn_display": [
      "RB Salzburg",
      "AC Milan"
    ]
  },
  "2041981": {
    "event_id": "401915560",
    "official_chinese": [
      "维戈塞尔塔",
      "尤文图斯"
    ],
    "espn_display": [
      "Celta Vigo",
      "Juventus"
    ]
  },
  "2041982": {
    "event_id": "401915563",
    "official_chinese": [
      "霍芬海姆",
      "贝西克塔斯"
    ],
    "espn_display": [
      "TSG Hoffenheim",
      "Besiktas"
    ]
  },
  "2041983": {
    "event_id": "401915550",
    "official_chinese": [
      "马赛",
      "奥林匹亚科斯"
    ],
    "espn_display": [
      "Marseille",
      "Olympiacos"
    ]
  },
  "2041984": {
    "event_id": "401915571",
    "official_chinese": [
      "伯恩茅斯",
      "格拉茨风暴"
    ],
    "espn_display": [
      "AFC Bournemouth",
      "SK Sturm Graz"
    ]
  },
  "2041985": {
    "event_id": "401915562",
    "official_chinese": [
      "本菲卡",
      "凯尔特人"
    ],
    "espn_display": [
      "Benfica",
      "Celtic"
    ]
  },
  "2041986": {
    "event_id": "401915852",
    "official_chinese": [
      "哥本哈根",
      "布拉加"
    ],
    "espn_display": [
      "F.C. København",
      "Braga"
    ]
  },
  "2041987": {
    "event_id": "401912523",
    "official_chinese": [
      "拉普拉塔大学生",
      "弗拉门戈"
    ],
    "espn_display": [
      "Estudiantes de La Plata",
      "Flamengo"
    ]
  },
  "2041988": {
    "event_id": "401912650",
    "official_chinese": [
      "纽卡斯尔喷气机",
      "大阪钢巴"
    ],
    "espn_display": [
      "Newcastle Jets",
      "Gamba Osaka"
    ]
  },
  "2041989": {
    "event_id": "401915854",
    "official_chinese": [
      "克拉约瓦大学",
      "赫塔费"
    ],
    "espn_display": [
      "CSU Craiova",
      "Getafe"
    ]
  }
}
