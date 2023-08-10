from m_functions import *
from m_vars import *

load_dotenv()
MANGALIST = os.getenv('MANGALIST')

async def manga_timer(args):
	# On check for manga updates
	global mangaTime
	global m_timer
	chan = args["chan"]
	mangaIDs = []
	# Get list of manga from mangadex custom list
	try:
		response = requests.get("https://api.mangadex.org/list/" + MANGALIST)
		temp = response.json().get("data").get("relationships")
	except:
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})
		return
	for i in temp:
		if response.json().get("result") == "ok":
			mangaIDs.append(i.get("id"))
	# Compare newest manga to database
	for i in mangaIDs:
		info = await getMangaInfo(i)
		if not info.get("errFlag"):
			result = await findManga(i)
			info.update(await getNewestChapter(i))
			if result == -1:
				# If manga is not in database
				if not info.get("errFlag"):
					await addManga(i, info.get("newChap"))
			elif not result == "err":
				if not info.get("errFlag"):
					newChap = info.get("newChap")
					if float(newChap) > float(result) and newChap != None:
						# If manga in database has been updated
						msgText = await constructMessage(TextEnum.Manga)
						title = info.get("title") + " Chapter " + info.get("newChap")
						embed = discord.Embed(title=title, description=info.get("link"))
						embed.set_image(url=info.get("cover"))
						await chan.send(msgText.replace("***", info.get("title")).replace("###", newChap), embed=embed)
						await editManga(i, newChap)
	m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

async def addManga(mangaID, chapterNUM):
	global con
	con.execute("INSERT INTO MANGA VALUES (?, ?)", (mangaID, chapterNUM))
	con.commit()

async def removeManga(mangaID):
	global con
	con.execute("DELETE FROM MANGA WHERE mangaID=?", (mangaID,))
	con.commit()

async def findManga(mangaID):
	global con
	out = -1
	cursor = con.execute("SELECT chapterNUM FROM MANGA WHERE mangaID=?", (mangaID,))
	for manga in cursor.fetchall():
		out = manga[0]
	if out is None:
		return "err"
	return out

async def editManga(mangaID, chapterNUM):
	global con
	cursor = con.execute("UPDATE MANGA SET chapterNUM=? WHERE mangaID=?", (chapterNUM, mangaID))
	con.commit()

async def getManga():
	global con
	cursor = con.execute("SELECT mangaID FROM MANGA")
	out = []
	for manga in cursor.fetchall():
		out.append(manga[0])
	return out

async def getNewestChapter(mangaID):
	try:
		request = "https://api.mangadex.org/manga/" + mangaID + "/aggregate"
		response = requests.get(request, params={"translatedLanguage[]":"en"})
		respo = response.json().get("volumes")
		vols = list(respo)
	except:
		return {"errFlag": True}
		print("ERROR in m_functions.py:getNewestChapter():try:1")
	try:
		chaps = list(respo.get("none").get("chapters").keys())
		chapID = respo.get("none").get("chapters").get(chaps[0]).get("id")
	except:
		chaps = list(respo.get(vols[0]).get("chapters").keys())
		chapID = respo.get(vols[0]).get("chapters").get(chaps[0]).get("id")
		#print("ERROR in m_functions.py:getNewestChapter():try:2")
		#print("^^^ planned error: chapID = " + str(chapID))
	try:
		request = "https://api.mangadex.org/chapter/" + chapID
		response = requests.get(request)
		link = response.json().get("data").get("attributes").get("externalUrl")
	except:
		return {"errFlag": True}
		print("ERROR in m_functions.py:getNewestChapter():try:3")
	if link is None:
		link = "https://mangadex.org/chapter/" + chapID
	return {"newChap": chaps[0], "link": link}

async def getMangaInfo(mangaID):
	try:
		resp = requests.get("https://api.mangadex.org/manga/" + mangaID)
		if resp.json().get("result") != "ok":
			return {"errFlag": True}
	except:
		return {"errFlag": True}
	title = list(resp.json().get("data").get("attributes").get("title").values())[0]
	respo = resp.json().get("data").get("relationships")
	cover = "https://uploads.mangadex.org/covers/" + mangaID
	errFlag = True
	for i in respo:
		if i.get("type") == "cover_art":
			try:
				response = requests.get("https://api.mangadex.org/cover/" + i.get("id"))
				if resp.json().get("result") != "ok":
					return { "errFlag": errFlag}
			except:
				return { "errFlag": errFlag}
			cover += "/" + response.json().get("data").get("attributes").get("fileName")
			errFlag = False
			break
	return {"title": title, "cover": cover, "errFlag": errFlag}