import os, sys, platform, pytz, time, traceback, unicodedata, re, requests, random
from bs4 import BeautifulSoup as Soup, element
from datetime import date, datetime, timedelta
from threading import Thread
from ipywidgets import Output


def transstring(name): 
    if not name:
        logger.error('String is empty.')
        raise Exception('String is empty.')
    table = name.maketrans("",""," ,.;:!?'&#$%`!@^*_-/\\|'\"<>())[]{}")
    return name.translate(table).lower()

def transtitle(name, show = False): 
    if not name:
        logger.error('Name is empty.')
        raise Exception('Trans title,name is empty.')
    name = name.replace("&","and")
    dgts = year_pt.findall(name)
    year = ""
    if dgts: 
        if len(dgts) == 1 :
            name = name.split(dgts[0])[0]
            year = dgts[0]
        else:
            name.split(dgts[-1])[0]
            year = dgts[-1]
    table = name.maketrans("",""," '(#$%-,.;:!?)")
    return name.translate(table).lower() + year         # if not show else name.translate(table).lower()

def get_year(name): 
    dgts = year_pt.findall(name.split('1080')[0])
    if dgts: 
        return dgts[-1]
    else:
        return thisyear

def get_season(name, allow_year = True):
    logger.info(f'Retrieving season from: {name}')
    lookup = mf_pt.search(name)
    if lookup:
        sn = lookup.group()
        sn = 'S' + sn if len(sn) != 1 else 'S0' + sn
        logger.info(f'Found season: {sn}')
        return sn

    lookup = featurettes_pt.search(name)
    if lookup:
        ft = lookup.group()
        logger.info(f'Extra folder: {ft}')
        return "Extras"

    if allow_year:
        sn = get_year(name)  
        logger.info(f'Season retrieved as a year: {sn}')
        return sn
    else:
        logger.info(f'No season was retrieved.')
        return ''

def name_movie(name, quality = "1080"): 
    if quality in name:
        name = name.split(quality)[0]
    elif '720p' in name:
        name = name.split('720p')[0]
    table = name.maketrans({".": " ","(": None, ")": None})
    trans = name.translate(table)
    dgts = year_pt.findall(trans)
    if dgts and len(dgts) >= 1:
         res = f"{trans.split(dgts[-1])[0].strip()} {dgts[-1]}"
    else:
        res = trans.strip()
    return title(res)

def name_show(name, quality = "1080"): 
    if quality in name:
        name = name.split(quality)[0]
    elif "720p" in name:
        name = name.split("720p")[0]    
    table = name.maketrans({".": " ","(": None, ")": None, "'": None})
    trans = name.translate(table)
    search = year_pt.search(trans)
    if search: 
        year = search.group()
        res = f"{trans.split(year)[0].strip()} {year}"
    else:
        search = season_pt1.search(trans)
        if search: 
            res = trans.split(search.group())[0].strip()
        else: 
            res = trans.strip()
    return title(res)

def name_episode(name, quality = "1080"):
    if quality in name:
        name = name.split(quality)[0]
    elif "720p" in name:
        name = name.split("720p")[0]
    table = name.maketrans({".": " ","(": None, ")": None})
    name = name.translate(table)
    if name[-1] == ".":
        name = name[:-1]
    return title(name)

def movie_exists(name):
    if not name.strip():
        logger.error('Movie name is empty')
        return           
    logger.info(f"Checking if the movie {name} is downloaded.")
    try:
        movies_raw = filter_checks(next(os.walk(config.movies_path))[1])
    except:
        return False
    name_s = transtitle(name)
    result = {'type': 'movie', "foundname": "", "foundpath": "", "foundshow": "", 'foundfile': "", "founddir": ""}
    for i in range(len(movies_raw)):
        targetname = movies_raw[i]
        targetpath = path_movie(movies_raw[i])
        if name_s == transtitle(movies_raw[i]):
            foundfile =  get_movie_file_path(targetpath, targetname)
            if foundfile:
                logger.info(f"Found {name} as {targetname}")
                result["foundname"] = targetname
                result["foundpath"] = targetpath
                result["foundshow"] = ""
                result["foundfile"] = foundfile
                result["founddir"] = config.movies_path
                break
    if not result["foundpath"]:
        logger.info(f"{name} is not found")
    return result

def show_exists(searchshow: str):
    if not searchshow.strip():
        logger.error('Show name is empty')
        return
    logger.info(f"Checking if the show {searchshow} is downloaded")
    try:
        shows_raw = filter_checks(next(os.walk(config.tv_path))[1])
    except:
        return False
    name_trans = transtitle(searchshow, True)
    result = {'type': 'TV show', "foundname": "", "foundpath": "", "foundshow": "", 'foundfile': "", "founddir": ""}
    for i in range(len(shows_raw)):
        targetpath = path_tvshow(shows_raw[i])
        targetname = shows_raw[i]
        trans1 = transtitle(shows_raw[i], True)
        if startswith(trans1, name_trans) and not is_empty(targetpath):
            logger.info(f"{searchshow} is downloaded as {targetname}")
            result["foundname"] = targetname
            result["foundpath"] = targetpath
            result["foundshow"] = targetname
            result["foundfile"] = ''
            result["founddir"] = config.tv_path
            break
    if not result["foundpath"]:
        logger.info(f"{searchshow} is not found.")
    return result

def season_exists(foundshow, searchseason):
    if not searchseason.strip():
        logger.error('Season name is empty')
        return
    if not foundshow.strip():
        logger.error('Show name is empty')
        return
    logger.info(f"Checking if the season {searchseason} of {foundshow} is downloaded")
    showsearch = show_exists(foundshow)
    targetpath = ""
    result = {'type': 'TV season', "foundname": "", "foundpath": "", "foundshow": "", 'foundfile': "", "founddir": ""}
    if showsearch['foundpath']:
        foundshow = showsearch['foundname']
        result["foundshow"] = foundshow
        showpath = path_tvshow(foundshow)
        targetpath = path_season(foundshow, searchseason)
        if os.path.exists(targetpath) and not is_empty(targetpath):
            logger.info(f"Season {searchseason} of {foundshow} is downloaded")
            result["foundname"] = searchseason
            result["foundpath"] = targetpath
            result["foundfile"] = targetpath
            result["founddir"] = showpath
        else:
            logger.info(f"Season {searchseason} of {foundshow} is not downloaded")
    return result

def episode_exists(foundshow, season, searchepisode): 
    logger.info(f"Checking if the episode: {searchepisode} is downloaded")
    showsearch = show_exists(foundshow)
    targetepisode = ""
    targetpath= ""
    result = {'type': 'TV episode', "foundname": "", "foundpath": "", "foundshow": "", 'foundfile': "", "founddir": ""}
    if showsearch['foundpath']:
        foundshow = showsearch['foundname']
        result["foundshow"] = foundshow
        seasonpath = path_season(foundshow, season)
        if os.path.exists(seasonpath) and not is_empty(seasonpath):
            check = eps_pt.search(searchepisode) #rerite search algorithm
            eps = check.group() if check else searchepisode
            epses = next(os.walk(seasonpath))[2]
            for targetepisode in epses:
                splt = os.path.splitext(targetepisode)
                if splt[1] == ".mp4" or splt[1] == ".mkv": 
                    if contains(splt[0], eps):
                        targetpath = path_episode(foundshow, season, targetepisode)
                        logger.info(f"Episode: {searchepisode} is downloaded as {targetpath}")
                        result["foundname"] = targetepisode
                        result["foundpath"] = targetpath
                        result["foundfile"] = targetpath
                        result["founddir"] = seasonpath
                        break
    if not result["foundpath"]:
        logger.info(f"Episode: {searchepisode} is not downloaded.")
    return result

def check_download(type_, name):
    if type_ == MOVIE:
        name = name_movie(name)
        return movie_exists(name)
    if type_ == SHOW:
        name = name_show(name)
        return show_exists(name)

def get_movie_file_path(path, name):
    if path and os.path.exists(path):
        files = next(os.walk(path))[2]
        for file in files:
            splt = os.path.splitext(file)
            ext = splt[1]
            title: str = splt[0].lower()
            if (ext == ".mp4" or ext == ".mkv" or ext == ".av" or ext == ".ts") and name.lower().startswith(title):
                return path + "/" + file
    return ""

def rename_title(newname):
    inp = input().lower()
    if inp:
        words = inp.split()
    else:
        words: list[str] = newname.split()
    check1 = " ".join(words[:2])
    check2 = len(words[0]) > 3
    movies = filter_checks(next(os.walk(config.movies_path))[1])
    res = []

    for mv in movies:
        if mv.startswith(check1) or (check2 and mv.startswith(words[0])) or any(not check3.isdigit() and len(check3) > 3 and contains(mv, check3) for check3  in words):
            res.append(mv)
    if len(res) == 1:
        title = res[0]
    elif res:
        res.sort()
        i = 0
        for mv in res:
            i += 1
            print(f"{i} {mv}")       
        c = input()
        if c == "" or c == " " or c == "q" or c == "s":
            return
        else:
            try:
                title = res[int(c)-1]
            except Exception as e:
                print(e)
                return
    else:
        return
    if input() != "n":
        p0 = config.movies_path + "/" + title
        p1 = config.movies_path + "/" + newname
        !mv "$p0" "$p1"

        for p3 in config.moviesbackups:
            p0 = joinpath(p3, title)
            if os.path.exists(p0):
                p1 = joinpath(p3, newname) 
                !mv "$p0" "$p1"

def replace_download(path):
    if path and os.path.exists(path):
        parent = os.path.dirname(path)
        rp = parent + "/" + ".replace"
        os.makedirs(rp, exist_ok=True)
        !mv "$path" "$rp"

def get_tv_type(attrs: DownloadAttrs):
    search = eps_pt.search(attrs.name)
    if search:
        return EPISODE
    search = check_sn_pt.search(attrs.name)
    if search:
        return SEASON  
    
def music_title(name: str):
    search = split_musictitle_pt.search(name)
    if search:
        name = name.split(search.group())[0]
    splt = name.split("-")
    if splt:
        artist = splt[0].strip() 
        name = splt[1].strip()
        title = f"{artist} - {name}"
    else:
        artist = ""
        name = title = name.strip()
    return (artist, name, title)