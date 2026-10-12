"""Forty individually composed original designs. Coordinates use 1000-unit width."""

NAVY = "14243B"
CREAM = "F8F3E9"
GOLD = "DEAE5B"
GREEN = "0C5244"
WHITE = "FFFFFF"
RED = "E44B45"
BLUE = "3769EE"
PINK = "EBAEBB"


def rgba(value):
    if not isinstance(value, str): return list(value)
    value = value.lstrip("#")
    return [int(value[i:i+2], 16) for i in (0, 2, 4)] + [255]


class Design:
    def __init__(self, key, name, category, width=1080, height=1080, dpi=72):
        self.key, self.name, self.category = key, name, category
        self.width, self.height, self.dpi = width, height, dpi
        self.s = width/1000
        self.layers = []

    def box(self, x, y, w, h):
        return {"x": round(x*self.s), "y": round(y*self.s), "w": round(w*self.s), "h": round(h*self.s)}

    def bg(self, first, second=None, angle=90):
        self.layers.append({"gradient": {"angle": angle, "stops": [[0, rgba(first)], [1, rgba(second)]]}}
                           if second else {"bg": rgba(first)})
        return self

    def shape(self, kind, x, y, w, h, color, stroke=None, sw=0, rotation=0, name=None):
        self.layers.append({"shape": kind, **self.box(x,y,w,h), "fill": rgba(color) if color else None,
                            "stroke": rgba(stroke) if stroke else None, "sw": round(sw*self.s),
                            "rotation": rotation, "name": name or kind.capitalize()})
        return self

    def text(self, text, x, y, w, h, size, color, bold=False, align="left", shadow=0):
        self.layers.append({"text": text, **self.box(x,y,w,h), "size": round(size*self.s),
                           "color": rgba(color), "bold": bold, "align": align,
                           "shadow_offset": round(shadow*self.s), "name": text.split("\n")[0]})
        return self

    def image(self, kind, x, y, w, h, fg, bg, label):
        background = rgba(bg)
        background[3] = 0
        self.layers.append({"art": kind, **self.box(x,y,w,h), "foreground": rgba(fg),
                           "background": background, "name": "Photo · " + label})
        return self

    def rule(self, x, y, w, color):
        return self.shape("rectangle", x,y,w,3,color)


def new_templates(Template):
    out = []
    def new(key, name, category, width=1080, height=1080, dpi=72):
        d = Design("pro_"+key, name, category, width,height,dpi)
        out.append(d)
        return d
    sports = "Football & Sports"
    business = "Business & Marketing"
    islamic = "Ramadan & Islamic Holidays"
    wedding = "Weddings & Celebrations"
    education = "Education & Books"
    civic = "Announcements & Civic Information"
    digital = "Digital Content"

    # Sports: editorial split, scoreboard, pitch diagram, transfer card, fixture, portrait.
    d = new("match_day", "Match Day", sports,1080,1350).bg(NAVY,"102F4F",35)
    d.shape("rectangle",610,0,390,1250,"CDF75C").text("CITY FOOTBALL CLUB",55,40,520,50,23,WHITE,True)
    d.text("MATCH\nDAY",55,160,570,265,110,WHITE,True,shadow=2).image("ball",660,220,290,390,NAVY,"CDF75C","Football artwork")
    d.rule(55,470,520,"CDF75C").text("MOGADISHU\nvs. KISMAYO",55,520,530,180,54,WHITE,True)
    d.text("SATURDAY · 18:00\nCITY STADIUM",55,790,520,110,34,WHITE).text("TOGETHER\nWE PLAY.",655,750,300,180,50,NAVY,True)
    d.text("Tickets & details: 061-XXXXXXX",55,1120,850,55,26,WHITE)

    d = new("match_results", "Match Results", sports).bg("F0EFE9")
    d.shape("rectangle",0,0,1000,240,NAVY).text("FULL TIME",70,65,860,100,76,WHITE,True,align="center")
    d.image("crest",80,350,200,240,BLUE,"F0EFE9","Home team crest").image("crest",720,350,200,240,RED,"F0EFE9","Away team crest")
    d.text("3 : 1",295,340,410,160,125,NAVY,True,align="center").text("MOGADISHU",50,610,330,65,32,NAVY,True,align="center")
    d.text("KISMAYO",650,610,300,65,32,NAVY,True,align="center").rule(80,720,840,GOLD)
    d.text("A night to remember.",80,770,840,80,43,NAVY,True,align="center").text("CITY LEAGUE  /  MATCH 08",80,900,840,45,25,NAVY,align="center")

    d = new("starting_lineup", "Starting Lineup", sports,1080,1350).bg("124E41","082A25")
    d.text("THE STARTING XI",60,35,880,90,65,WHITE,True).text("CITY FC  /  4–3–3",60,135,880,50,30,"ACD9B4")
    d.shape("rectangle",65,240,870,870,None,"6DAB88",3).rule(65,675,870,"6DAB88").shape("ellipse",370,535,260,260,None,"6DAB88",3)
    for x,y,n in [(185,320,"07"),(455,320,"09"),(725,320,"11"),(185,520,"08"),(455,520,"06"),(725,520,"10"),(90,800,"03"),(330,800,"04"),(570,800,"05"),(810,800,"02"),(455,990,"01")]:
        d.shape("ellipse",x,y,85,85,CREAM).text(n,x,y,85,85,36,GREEN,True,align="center")
    d.image("crest",825,25,110,140,GOLD,"124E41","Team crest").text("Coach: Your name  ·  Kick-off: 18:00",65,1155,870,50,27,WHITE)

    d = new("player_transfer", "Player Transfer", sports,1080,1350).bg("EDE9DE")
    d.shape("rectangle",0,0,450,1250,NAVY).image("portrait",40,255,390,715,GOLD,NAVY,"Player portrait")
    d.text("WELCOME",480,110,460,80,63,NAVY,True).text("TO THE\nCITY",480,250,470,190,75,NAVY,True)
    d.rule(575,525,365,RED).text("PLAYER\nNAME",560,585,380,160,58,NAVY,True)
    d.shape("rounded",560,845,375,110,RED).text("SIGNED 2026",580,870,330,60,36,WHITE,True,align="center")
    d.text("A NEW CHAPTER BEGINS",55,1120,360,65,24,GOLD,True)

    d = new("tournament", "Tournament Announcement", sports,1080,1350).bg("201B3F","533684",45)
    d.image("ball",640,60,300,310,GOLD,"302454","Tournament photo").text("THE CITY\nCUP",60,100,600,245,92,WHITE,True)
    d.text("FOOTBALL TOURNAMENT",60,390,880,60,37,GOLD,True).rule(60,495,880,GOLD)
    for y,num,title in [(550,"16","TEAMS"),(735,"04","WEEKS"),(920,"01","CHAMPION")]:
        d.text(num,70,y,190,120,86,GOLD,True).text(title,310,y+20,580,90,45,WHITE,True)
    d.text("Register your team · 061-XXXXXXX",65,1145,870,50,29,WHITE)

    d = new("player_match", "Player of the Match", sports).bg("EFE5D0")
    d.shape("ellipse",220,140,580,580,GOLD).image("portrait",285,180,430,550,NAVY,"EFE5D0","Player portrait")
    d.text("PLAYER OF THE MATCH",65,35,870,65,45,NAVY,True,align="center")
    d.shape("rectangle",50,690,900,240,NAVY).text("PLAYER NAME",85,725,830,70,59,WHITE,True,align="center")
    d.text("02 GOALS   /   01 ASSIST",85,825,830,55,31,GOLD,True,align="center")

    # Business: seven unrelated compositions with distinct product/photo slots.
    d = new("smartphone", "Smartphone Shop Advertisement", business).bg("091326","183B65",40)
    d.text("SMART STORE",60,40,880,55,30,"93D8E8",True).text("Upgrade\nyour everyday.",60,165,580,205,68,WHITE,True)
    d.image("phone",650,170,290,480,"5CC4D6","143050","Smartphone photo")
    d.text("Fast. Clear. Connected.",60,455,550,70,31,WHITE).shape("rounded",60,585,530,150,"5CC4D6")
    d.text("FROM $199",85,610,475,95,64,NAVY,True).text("Visit us in Mogadishu\n061-XXXXXXX",60,820,850,105,33,WHITE)

    d = new("supermarket", "Supermarket Promotion", business,1080,1350).bg("FFF6DC")
    d.shape("rectangle",0,0,1000,170,"1F744F").text("YOUR LOCAL MARKET",60,45,880,70,42,WHITE,True)
    d.text("FRESH FINDS.\nSMALL PRICES.",60,225,880,180,70,GREEN,True).image("basket",500,440,440,390,"F1B734","FFF6DC","Featured products")
    d.shape("ellipse",60,475,340,340,"F1B734").text("SAVE\n30%",75,535,310,210,82,GREEN,True,align="center")
    d.rule(60,900,880,GREEN).text("WEEKEND SPECIALS",60,935,880,65,44,GREEN,True).text("Fruit · Rice · Everyday essentials\nVisit our shop · 061-XXXXXXX",60,1040,880,125,32,GREEN)

    d = new("restaurant_offer", "Restaurant Special Offer", business).bg("311D19")
    d.text("THE CITY KITCHEN",60,30,880,50,27,"EABD85",True,align="center").image("food",190,100,620,550,"D99448","311D19","Dish photo")
    d.shape("rectangle",0,620,1000,380,"F3E7D5").text("LUNCH, MADE SPECIAL.",60,665,880,75,51,"311D19",True,align="center")
    d.text("TODAY'S COMBO  ·  $8",60,765,880,65,41,"AF4630",True,align="center").text("Dine in or take away  /  061-XXXXXXX",60,895,880,50,27,"311D19",align="center")

    d = new("fashion", "Fashion Sale", business,1080,1350).bg("E8E0DA")
    d.shape("rectangle",40,40,535,1100,"D1BFB0").image("fashion",40,40,535,1100,"95715E","D1BFB0","Fashion collection")
    d.text("THE\nNEW\nEDIT",605,140,340,310,88,"30241F",True).rule(605,520,335,"30241F")
    d.text("Modern looks.\nEveryday confidence.",605,600,335,125,31,"30241F").text("40%\nOFF",605,790,335,210,89,"9B4235",True)
    d.text("YOUR BOUTIQUE  /  MOGADISHU",60,1170,880,45,25,"30241F",True)

    d = new("real_estate", "Real Estate Advertisement", business,1080,1350).bg("F2F1EC")
    d.shape("rectangle",40,40,920,550,"DDE5DE").image("house",40,40,920,550,"6C927D","DDE5DE","Property photo").shape("rectangle",40,575,230,65,NAVY)
    d.text("FOR SALE",55,582,200,48,29,WHITE,True,align="center").text("Find your\nnext home.",60,690,610,190,74,NAVY,True)
    d.text("3 BEDS\n2 BATHS",730,705,215,160,35,NAVY,True).rule(60,955,880,"A7B6AA")
    d.text("Wadajir, Mogadishu\nArrange a viewing: 061-XXXXXXX",60,1000,880,120,34,NAVY)

    d = new("internet", "Internet Service Advertisement", business).bg("092E45","085F73",35)
    d.text("STAY\nCONNECTED.",60,70,860,210,90,WHITE,True).image("router",520,325,410,400,"50D7C7","0A5267","Router or service photo")
    d.text("100\nMbps",60,345,430,200,91,"50D7C7",True).text("HOME INTERNET",60,610,450,70,34,WHITE,True)
    d.rule(60,785,880,"50D7C7").text("Simple plans. Local support.\nCall 061-XXXXXXX to connect.",60,820,880,120,32,WHITE)

    d = new("beauty_salon", "Beauty Salon Promotion", business,1080,1350).bg("F7ECE9")
    d.shape("ellipse",500,60,480,480,"E6C6BD").image("beauty",520,95,430,560,"956B5B","E6C6BD","Salon portrait")
    d.text("BLOOM\nBEAUTY",60,185,445,200,73,"573F38",True).text("Your moment\nto shine.",60,460,420,150,45,"573F38")
    d.rule(60,735,880,"BA8C76").text("CARE · STYLE · CONFIDENCE",60,780,880,60,37,"573F38",True)
    d.shape("rounded",60,930,880,140,"573F38").text("BOOK YOUR APPOINTMENT",85,960,830,65,41,WHITE,True,align="center")
    d.text("Mogadishu  /  061-XXXXXXX",60,1145,880,50,28,"573F38",align="center")

    # Holidays: ornamental but restrained, different silhouette and text hierarchy.
    d = new("ramadan", "Ramadan Kareem", islamic,1080,1350).bg("103F38","062C2C")
    d.shape("rounded",55,55,890,1140,None,GOLD,3).image("moon",250,110,500,420,GOLD,"103F38","Crescent artwork")
    d.text("RAMADAN",80,590,840,120,94,GOLD,True,align="center").text("KAREEM",80,730,840,100,75,CREAM,align="center")
    d.rule(275,910,450,GOLD).text("May this month bring peace,\nkindness and togetherness.",125,965,750,125,35,CREAM,align="center")

    d = new("eid_fitr", "Eid al-Fitr", islamic).bg("F5EDDB")
    d.shape("ellipse",-80,-90,520,520,"E5D4A8").image("lantern",570,35,340,445,"AB813D","F5EDDB","Eid lantern artwork")
    d.text("EID\nAL-FITR",65,275,540,240,92,GREEN,True).rule(65,605,870,GOLD)
    d.text("Ciid wanaagsan",65,660,870,95,65,GREEN,True).text("Celebrate gratitude. Share joy.\nFrom our family to yours.",65,810,870,115,33,GREEN)

    d = new("eid_adha", "Eid al-Adha", islamic,1080,1350).bg("2D345B")
    d.shape("rectangle",0,0,1000,270,"D8BB7B").text("EID AL-ADHA",60,75,880,105,74,"2D345B",True,align="center")
    d.image("moon",180,340,640,500,"D8BB7B","2D345B","Crescent or family photo")
    d.text("A time for\ngenerosity.",80,875,840,170,60,CREAM,align="center").text("Wishing you a blessed Eid",80,1135,840,50,29,"D8BB7B",align="center")

    d = new("iftar", "Iftar Invitation", islamic,1080,1350).bg("EEDCC2")
    d.text("YOU ARE INVITED",70,60,860,55,30,"704D35",align="center").text("Iftar\nTogether",80,190,840,255,100,"704D35",align="center")
    d.image("food",270,485,460,360,"AC7844","EEDCC2","Iftar meal photo").rule(90,880,820,"704D35")
    d.text("SATURDAY · SUNSET",80,930,840,65,41,"704D35",True,align="center").text("Your venue, Mogadishu\nRSVP: 061-XXXXXXX",80,1045,840,120,32,"704D35",align="center")

    d = new("friday", "Friday Mubarak", islamic).bg("E7EFE9")
    d.shape("rectangle",50,50,900,900,None,"9EB8A2",3).image("moon",355,90,290,280,GREEN,"E7EFE9","Friday greeting artwork")
    d.text("FRIDAY",80,400,840,125,104,GREEN,True,align="center").text("MUBARAK",80,550,840,100,70,GREEN,align="center")
    d.text("Pause. Reflect. Be kind.",100,740,800,70,39,"58765E",align="center").text("JIMCO WANAAGSAN",100,870,800,45,27,GREEN,True,align="center")

    # Invitations & celebrations: floral, interlocked, editorial, playful, stationery.
    d = new("wedding", "Wedding Invitation", wedding,1080,1350).bg("FCF7EE")
    d.shape("rectangle",50,50,900,1150,None,"AC9271",2).image("bouquet",325,75,350,320,"B19777","FCF7EE","Floral or couple photo")
    d.text("TOGETHER WITH OUR FAMILIES",90,420,820,45,23,"7E6A55",align="center").text("Amina\n& Ahmed",90,505,820,220,83,"4C443B",align="center")
    d.rule(350,805,300,"AC9271").text("SATURDAY, 24 OCTOBER\nAT SIX IN THE EVENING",90,875,820,100,30,"7E6A55",align="center")
    d.text("Your venue · Mogadishu\nRSVP: 061-XXXXXXX",90,1035,820,105,29,"7E6A55",align="center")

    d = new("engagement", "Engagement Announcement", wedding).bg("753E4E")
    d.image("ring",80,70,350,360,"EDC9A1","753E4E","Engagement photo").text("WE'RE\nENGAGED",470,135,460,185,63,"FCEDE6",True)
    d.rule(70,500,860,"C99195").text("Amina + Ahmed",70,560,860,110,68,"FCEDE6",align="center")
    d.text("The beginning of our forever.",70,730,860,70,36,"EDC9A1",align="center").text("SAVE THE DATE  /  24 OCTOBER",70,885,860,50,27,"FCEDE6",align="center")

    d = new("graduation", "Graduation Congratulations", wedding,1080,1350).bg("F1EADD")
    d.shape("rectangle",0,0,330,1250,"253950").image("graduate",60,250,430,670,GOLD,"253950","Graduate portrait")
    d.text("CLASS\nOF 2026",500,130,445,180,74,"253950",True).text("CONGRATS,\nGRADUATE!",500,410,445,165,56,"253950",True)
    d.rule(530,660,400,GOLD).text("Your Name",530,730,400,90,49,"253950",True)
    d.text("Your future\nstarts here.",530,885,400,145,39,"253950").text("PROUD OF EVERY STEP",35,1145,260,50,20,GOLD,True)

    d = new("birthday", "Birthday Greeting", wedding).bg("F6C95D")
    for x,y,r,c in [(15,15,100,PINK),(835,65,130,BLUE),(800,740,150,RED),(80,780,70,BLUE)]: d.shape("ellipse",x,y,r,r,c)
    d.text("HAPPY",90,110,820,95,84,"4B2E63",True,align="center").text("BIRTHDAY!",60,235,880,110,94,"4B2E63",True,align="center")
    d.image("cake",315,395,370,370,"D76289","F6C95D","Birthday photo").text("YOUR NAME",120,800,760,70,53,"4B2E63",True,align="center")
    d.text("Here’s to a wonderful year.",100,910,800,50,29,"4B2E63",align="center")

    d = new("thank_you", "Thank You Card", wedding,1500,1000).bg("E6EEE9")
    d.shape("rectangle",30,30,940,607,None,"709887",2).image("bouquet",60,115,240,350,"709887","E6EEE9","Thank-you photo")
    d.text("Thank\nyou.",355,90,575,235,100,"234B3C",align="left").text("Your kindness made\nall the difference.",355,380,575,105,33,"234B3C")
    d.rule(355,540,220,"709887").text("WITH GRATITUDE · YOUR NAME",355,570,575,40,21,"234B3C",True)

    # Education: cover, academic event, registration, course cards, formal certificate.
    d = new("book", "Professional Book Cover", education,1600,2400,300).bg("172C44")
    d.shape("rectangle",680,0,320,1500,"D8AF70").image("book",420,525,520,630,"F7EEDD","172C44","Cover artwork")
    d.text("A NEW\nWAY TO\nTHINK",70,100,800,340,108,WHITE,True).rule(70,1180,360,"D8AF70")
    d.text("Ideas for a better tomorrow",70,1240,850,70,40,CREAM).text("AUTHOR NAME",70,1380,850,60,34,"D8AF70",True)

    d = new("university", "University Event Poster", education,1080,1350).bg("EEECE4")
    d.shape("rectangle",0,0,1000,200,"304C63").text("YOUR UNIVERSITY",60,55,880,80,52,WHITE,True)
    d.text("IDEAS\nIN MOTION",60,285,880,215,91,"304C63",True).image("community",610,590,320,355,"E59252","EEECE4","Campus event photo")
    d.text("STUDENT\nINNOVATION\nFORUM",65,625,535,200,48,"304C63",True).rule(65,975,865,"E59252")
    d.text("24 OCTOBER  /  10:00 AM\nMain hall · Open to all students",65,1030,870,125,33,"304C63")

    d = new("school", "School Registration", education,1080,1350).bg("F8EFD9")
    d.shape("rectangle",0,0,1000,80,"3D7260").text("OPEN THE DOOR\nTO LEARNING",60,150,880,175,71,"244B3D",True)
    d.image("book",565,405,360,450,"E2AD48","F8EFD9","School photo").text("ENROLMENT\nIS OPEN",60,435,470,150,49,"244B3D",True)
    d.text("Small classes\nCaring teachers\nBright futures",60,650,470,150,33,"244B3D")
    d.shape("rounded",60,965,880,130,"3D7260").text("REGISTER TODAY",85,995,830,65,47,WHITE,True,align="center")
    d.text("Your school · 061-XXXXXXX",60,1160,880,45,29,"244B3D",align="center")

    d = new("course", "Course Advertisement", education).bg("212542")
    d.text("LEARN SOMETHING NEW",60,50,880,50,31,"A9B8FA",True).text("DESIGN\nYOUR FUTURE",60,170,880,195,86,WHITE,True)
    d.image("course",605,440,330,330,"F1B96B","212542","Course or instructor photo")
    d.text("6 WEEKS\nPRACTICAL SKILLS\nLOCAL MENTORS",60,445,535,185,38,WHITE,True).shape("rounded",60,725,495,90,"F1B96B")
    d.text("ENROL NOW",80,735,450,65,39,"212542",True,align="center").text("Starts 24 October · 061-XXXXXXX",60,890,880,55,29,"A9B8FA")

    d = new("certificate", "Certificate Design", education,1754,1240,150).bg("FFFCF6")
    d.shape("rectangle",25,25,950,657,None,"314F61",5).shape("rectangle",45,45,910,617,None,GOLD,2)
    d.image("badge",810,90,100,120,GOLD,"FFFCF6","School seal or logo")
    d.text("CERTIFICATE",100,90,690,75,64,"314F61",True,align="center").text("OF ACHIEVEMENT",100,185,690,40,26,"314F61",align="center")
    d.text("PRESENTED TO",100,285,800,40,22,"6E7F85",align="center").text("Recipient Name",100,345,800,85,60,"314F61",align="center")
    d.text("For successfully completing your course",100,450,800,55,28,"314F61",align="center")
    d.rule(130,590,250,GOLD).rule(620,590,250,GOLD).text("DATE",130,600,250,35,19,"314F61",align="center").text("SIGNATURE",620,600,250,35,19,"314F61",align="center")

    # Neutral civic information. Dates, venue and organizer details are editable examples.
    d = new("job", "Job Vacancy", civic,1080,1350).bg("F4F0E9")
    d.shape("rectangle",0,0,300,1250,"315C55").image("community",35,80,225,290,"CDB582","315C55","Employer logo")
    d.text("WE'RE\nHIRING.",355,95,585,200,88,"315C55",True).text("GRAPHIC DESIGNER",355,360,580,65,42,"315C55",True)
    d.rule(355,495,570,"CDB582").text("CREATIVE THINKING\nATTENTION TO DETAIL\nTEAM SPIRIT",355,550,570,210,36,"315C55")
    d.text("APPLY BY 24 OCTOBER",355,895,570,60,35,"315C55",True).text("Send your portfolio to:\njobs@example.com",355,1000,570,110,31,"315C55")

    d = new("public_meeting", "Public Meeting", civic).bg("EDF0F6")
    d.shape("rectangle",0,0,1000,115,"38598C").text("YOUR COMMUNITY COUNCIL",60,30,880,50,30,WHITE,True)
    d.text("LET'S\nTALK.",60,190,550,235,110,"233C63",True).image("community",620,250,310,310,"38598C","EDF0F6","Meeting photo")
    d.text("PUBLIC MEETING",60,535,880,75,54,"233C63",True).rule(60,675,880,"B7C6DF")
    d.text("24 OCTOBER  /  16:00\nCommunity hall, Mogadishu",60,720,880,110,34,"233C63").text("Everyone is welcome to listen and share.",60,895,880,55,27,"38598C")

    d = new("community_event", "Community Event", civic,1080,1350).bg("F6EEDB")
    d.text("BETTER\nTOGETHER",60,70,880,195,83,"435E41",True).image("community",165,355,670,490,"E5AA5E","F6EEDB","Community event photo")
    d.shape("rounded",60,890,880,240,"435E41").text("COMMUNITY DAY",95,925,810,65,51,WHITE,True,align="center")
    d.text("24 OCTOBER · 10:00\nYour venue · Bring a friend",95,1010,810,85,29,WHITE,align="center").text("Details: 061-XXXXXXX",60,1175,880,45,26,"435E41",align="center")

    d = new("election_info", "Election Information", civic,1080,1350).bg("F5F4F0")
    d.shape("rectangle",0,0,1000,190,"2E5064").text("ELECTION INFORMATION",55,60,890,75,48,WHITE,True)
    d.image("community",725,240,200,200,"2E5064","F5F4F0","Official information logo")
    for y,n,title,body in [(275,"01","CHECK THE DATE","Add the verified election date."),(535,"02","CONFIRM YOUR LOCATION","Add the official polling information."),(795,"03","READ OFFICIAL GUIDANCE","Add the authority's contact details.")]:
        d.text(n,60,y,140,80,66,"A98444",True).text(title,225,y,705,60,34,"2E5064",True).text(body,225,y+85,705,65,28,"52656B")
    d.rule(60,1085,880,"BCC8CB").text("Replace examples with verified official information.\nOrganizer: Your public information office",60,1130,880,80,25,"52656B")

    d = new("public_debate", "Public Debate Announcement", civic,1080,1350).bg("273441")
    d.text("LISTEN.\nQUESTION.\nUNDERSTAND.",60,70,880,260,77,WHITE,True).image("microphone",630,415,310,430,"E1BC78","273441","Speaker or microphone photo")
    d.text("PUBLIC\nDEBATE",60,475,550,170,69,"E1BC78",True).rule(60,905,880,"E1BC78")
    d.text("24 OCTOBER  /  18:00\nYour venue, Mogadishu",60,955,880,110,36,WHITE).text("Open discussion · Neutral moderation",60,1145,880,50,29,"B7C4CD")

    # Digital: aspect-specific layouts, no recycling of the square poster grid.
    d = new("youtube", "YouTube Thumbnail", digital,1280,720).bg("112036")
    d.shape("rectangle",635,0,365,563,"F3BA51").image("portrait",650,45,330,480,"34506F","F3BA51","Video host photo")
    d.text("MAKE\nIT HAPPEN",40,85,590,210,92,WHITE,True,shadow=2).shape("rounded",40,365,535,95,"F3BA51")
    d.text("5 SIMPLE STEPS",65,375,485,65,43,NAVY,True,align="center").text("YOUR CHANNEL",40,505,590,35,23,WHITE,True)

    d = new("podcast", "Podcast Cover", digital).bg("C8D1BC")
    d.text("THE LOCAL",60,40,880,70,49,"25382C",True).text("VOICE",45,140,910,160,148,"25382C",True)
    d.image("podcast",310,360,380,380,"50684B","C8D1BC","Podcast host or artwork")
    d.rule(60,820,880,"25382C").text("IDEAS. PEOPLE. STORIES.",60,865,880,55,34,"25382C",True)

    d = new("instagram", "Instagram Advertisement", digital).bg("F6E4DD")
    d.image("phone",545,90,355,490,"C37459","F6E4DD","Product photo").text("LESS\nSCROLL.\nMORE STYLE.",60,140,515,255,71,"5F382C",True)
    d.rule(60,635,880,"C37459").text("YOUR BRAND",60,695,880,65,43,"5F382C",True)
    d.shape("rounded",60,815,880,110,"5F382C").text("SHOP THE COLLECTION",85,835,830,65,41,WHITE,True,align="center")

    d = new("facebook", "Facebook Promotion", digital,1200,630).bg("144B61")
    d.image("house",610,30,345,450,"8FCDB6","144B61","Promotion photo")
    d.text("LOCAL BUSINESS.\nBIG POSSIBILITIES.",50,90,540,150,54,WHITE,True).text("Meet your next favourite service.",50,290,540,55,25,"AFE0CF")
    d.shape("rounded",50,390,455,80,"AFE0CF").text("DISCOVER MORE",65,397,425,60,31,"144B61",True,align="center")

    d = new("tiktok", "TikTok Cover", digital,1080,1920).bg("161829")
    d.text("CREATE\nYOUR\nMOMENT",60,130,880,345,116,WHITE,True,shadow=3).rule(60,555,880,"D4F264")
    d.image("portrait",150,650,700,750,"B996D1","161829","Creator portrait")
    d.shape("rectangle",60,1470,880,170,"D4F264").text("NEW VIDEO",90,1515,820,75,61,"161829",True,align="center")
    d.text("@yourname  /  EPISODE 01",60,1690,880,45,28,WHITE,align="center")

    d = new("whatsapp", "WhatsApp Status", digital,1080,1920).bg("E6EDDF")
    d.text("A LITTLE\nGOOD NEWS.",60,135,880,230,96,"345343",True).text("Your new collection is here.",60,450,880,65,37,"345343")
    d.image("basket",110,665,780,720,"79935A","E6EDDF","Status product photo")
    d.rule(60,1480,880,"79935A").text("MESSAGE US TO ORDER",60,1535,880,75,45,"345343",True,align="center")
    d.text("061-XXXXXXX",60,1665,880,60,38,"345343",align="center")

    d = new("livestream", "Livestream Announcement", digital,1280,720).bg("372B56","171B34",35)
    d.shape("rounded",50,40,165,55,RED).text("LIVE",65,45,135,40,28,WHITE,True,align="center")
    d.text("LET'S BUILD\nSOMETHING.",50,145,620,190,73,WHITE,True).image("play",735,120,220,280,"AD8ECD","2B2548","Presenter photo")
    d.rule(50,410,900,"AD8ECD").text("24 OCTOBER · 19:00  /  YOUR CHANNEL",50,455,900,65,31,"DCD4EB",True)

    assert len(out) == 40
    return [Template(d.key,d.name,d.category,d.width,d.height,d.layers,d.dpi) for d in out]
