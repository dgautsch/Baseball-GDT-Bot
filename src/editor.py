# does all the post generating and editing

import player

import xml.etree.ElementTree as ET
import urllib2
import simplejson as json
from datetime import datetime, timedelta
import time

class Editor:

    def __init__(self,time_info,settings):
        (self.time_zone,self.time_change) = time_info
        self.SETTINGS = settings

    def generate_title(self,dir,thread,dh=False,dhnum=0):
        if thread == "pre": title = self.SETTINGS.get('PRE_THREAD_SETTINGS').get('PRE_THREAD_TAG') + " "
        elif thread == "game": title = self.SETTINGS.get('THREAD_SETTINGS').get('THREAD_TAG') + " "
        elif thread == "post":
            if self.SETTINGS.get('WINLOSS_POST_THREAD_TAGS'):
                myteamwon = ""
                myteamwon = self.didmyteamwin(dir)
                if myteamwon == "0":
                    title = self.SETTINGS.get('POST_THREAD_SETTINGS').get('POST_THREAD_LOSS_TAG') + " "
                elif myteamwon == "1":
                    title = self.SETTINGS.get('POST_THREAD_SETTINGS').get('POST_THREAD_WIN_TAG') + " "
                else:
                    title = self.SETTINGS.get('POST_THREAD_SETTINGS').get('POST_THREAD_TAG') + " "
            else: title = self.SETTINGS.get('POST_THREAD_SETTINGS').get('POST_THREAD_TAG') + " "
        while True:
            try:
                response = urllib2.urlopen(dir + "linescore.json")
                break
            except:
                if self.SETTINGS.get('LOG_LEVEL')>0: print "Couldn't find linescore.json for title, trying again in 20 seconds..."
                time.sleep(20)
        filething = json.load(response)
        game = filething.get('data').get('game')
        timestring = game.get('time_date') + " " + game.get('ampm')
        date_object = datetime.strptime(timestring, "%Y/%m/%d %I:%M %p")
        title = title + game.get('away_team_name') + " (" + game.get('away_win') + "-" + game.get('away_loss') + ")"
        title = title + " @ "
        title = title + game.get('home_team_name') + " (" + game.get('home_win') + "-" + game.get('home_loss') + ")"
        title = title + " - "
        title = title + date_object.strftime("%B %d, %Y")
        if dh:
            if thread == "pre" and self.SETTINGS.get('CONSOLIDATE_PRE'):
                title = title + " - DOUBLEHEADER"
            else:
                title = title + " - GAME " + dhnum
        if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning",thread,"title..."
        return title

    def generate_pre_code(self,games,gameid,othergameid=None):
        code = ""

        if othergameid and int(games[othergameid].get('gamenum')) < int(games[gameid].get('gamenum')):
            tempgameid = othergameid
            othergameid = gameid
            gameid = tempgameid
        
        if othergameid:
            code = code + "#Game " + games[gameid].get('gamenum') + "\n"

        temp_dirs = []
        temp_dirs.append(games[gameid].get('url') + "linescore.json")
        temp_dirs.append(games[gameid].get('url') + "gamecenter.xml")
        files = self.download_pre_files(temp_dirs)
        if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('BLURB'):
            code = code + self.generate_blurb(files, self.get_homeaway(self.SETTINGS.get('TEAM_CODE'),games[gameid].get('url')))
        if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('PROBABLES'): code = code + self.generate_pre_probables(files)
        if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('FIRST_PITCH'): code = code + self.generate_pre_first_pitch(files)
        if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('DESCRIPTION'): code = code + self.generate_pre_description(files)
        code = code + "\n\n"

        if othergameid:
            code = code + "---\n#Game " + games[othergameid].get('gamenum') + "\n"
            temp_dirs = []
            temp_dirs.append(games[othergameid].get('url') + "linescore.json")
            temp_dirs.append(games[othergameid].get('url') + "gamecenter.xml")
            files = self.download_pre_files(temp_dirs)
            if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('BLURB'):
                code = code + self.generate_blurb(files, self.get_homeaway(self.SETTINGS.get('TEAM_CODE'),games[othergameid].get('url')))
            if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('PROBABLES'): code = code + self.generate_pre_probables(files)
            if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('FIRST_PITCH'): code = code + self.generate_pre_first_pitch(files)
            if self.SETTINGS.get('PRE_THREAD_SETTINGS').get('CONTENT').get('DESCRIPTION'): code = code + self.generate_pre_description(files)
            code = code + "\n\n"

        if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning all pre code..."
        return code

    def download_pre_files(self,dirs):
        files = dict()
        response = urllib2.urlopen(dirs[0])
        files["linescore"] = json.load(response)
        response = urllib2.urlopen(dirs[1])
        files["gamecenter"] = ET.parse(response)
        return files

    def generate_pre_probables(self,files):
        probables = ""
        try:
            game = files["linescore"].get('data').get('game')
            subs = self.get_subreddits(game.get('home_team_name'), game.get('away_team_name'))

            root = files["gamecenter"].getroot()
            broadcast = root.find('broadcast')

            if not isinstance(broadcast[0][0].text, type(None)):
                home_tv_broadcast = broadcast[0][0].text
            if not isinstance(broadcast[1][0].text, type(None)):
                away_tv_broadcast = broadcast[1][0].text
            if not isinstance(broadcast[0][1].text, type(None)):
                home_radio_broadcast = broadcast[0][1].text
            if not isinstance(broadcast[1][1].text, type(None)):
                away_radio_broadcast = broadcast[1][1].text

            away_pitcher_obj = game.get('away_probable_pitcher')
            home_pitcher_obj = game.get('home_probable_pitcher')

            away_pitcher = away_pitcher_obj.get('first_name') + " " + away_pitcher_obj.get('last_name')
            away_pitcher = "[" + away_pitcher + "](" + "http://mlb.mlb.com/team/player.jsp?player_id=" + away_pitcher_obj.get('id') + ")"
            away_pitcher += " (" + away_pitcher_obj.get('wins') + "-" + away_pitcher_obj.get('losses') + ", " + away_pitcher_obj.get('era') + ")"
            home_pitcher = home_pitcher_obj.get('first_name') + " " + home_pitcher_obj.get('last_name')
            home_pitcher = "[" + home_pitcher + "](" + "http://mlb.mlb.com/team/player.jsp?player_id=" + home_pitcher_obj.get('id') + ")"
            home_pitcher += " (" + home_pitcher_obj.get('wins') + "-" + home_pitcher_obj.get('losses') + ", " + home_pitcher_obj.get('era') + ")"

            away_preview = "[Link](http://mlb.com" + game.get('away_preview_link') + ")"
            home_preview = "[Link](http://mlb.com" + game.get('home_preview_link') + ")"

            probables  = " |Pitcher|TV|Radio|Preview\n"
            probables += "-|-|-|-|-\n"
            probables += "[" + game.get('away_team_name') + "](" + subs[1] + ")|" + away_pitcher + "|" + away_tv_broadcast + "|" + away_radio_broadcast + "|" + away_preview + "\n"
            probables += "[" + game.get('home_team_name') + "](" + subs[0] + ")|" + home_pitcher + "|" + home_tv_broadcast + "|" + home_radio_broadcast + "|" + home_preview + "\n"

            probables += "\n"
            
            return probables
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for probables, returning empty string..."
            return probables

    def generate_pre_first_pitch(self,files):
        first_pitch = ""
        try:
            game = files["linescore"].get('data').get('game')

            timestring = game.get('time_date') + " " + game.get('ampm')
            date_object = datetime.strptime(timestring, "%Y/%m/%d %I:%M %p")
            t = timedelta(hours=self.time_change)
            timezone = self.time_zone
            date_object = date_object - t
            first_pitch = "**First Pitch:** " + date_object.strftime("%I:%M %p ") + timezone + "\n\n"

            return first_pitch
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for first_pitch, returning empty string..."
            return first_pitch

    def generate_pre_description(self,files):
        first_pitch = ""
        try:
            game = files["linescore"].get('data').get('game')
            if game.get('description',False):
                return "**Game Note:** " + game.get('description') + "\n\n"
            else:
                if self.SETTINGS.get('LOG_LEVEL')>2: print "No game description found, returning empty string..."
                return ""
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for first_pitch, returning empty string..."
            return ""

    def generate_blurb(self,files,homeaway='mlb'):
        blurb = ""
        if homeaway not in ['home','away']:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Home or away not specified for blurb, using 'mlb'..."
            homeaway = 'mlb'
        try:
            root = files["gamecenter"].getroot()
            preview = root.find('previews').find(homeaway)
            headline = preview.find('headline').text
            blurbtext = preview.find('blurb').text

            blurb = "**" + headline + "**\n\n" + blurbtext + "\n\n"
            return blurb
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for blurb, returning empty string..."
            return blurb

    def get_homeaway(self, team_code, url):
        try:
            response = urllib2.urlopen(url+"linescore.json")
            linescore = json.load(response)
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Error downloading linescore, returning empty string for whether team is home or away..."
            return None
        game = linescore.get('data').get('game')

        if game.get('home_code') == team_code:
            return "home"
        elif game.get('away_code') == team_code:
            return "away"
        else:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Cannot determine if team is home or away, returning empty string..."
            return None
        return None

    def generate_code(self,dir,thread):
        code = ""
        dirs = []
        dirs.append(dir + "linescore.json")
        dirs.append(dir + "gamecenter.xml")
        dirs.append(dir + "boxscore.json")
        dirs.append(dir + "plays.json")
        dirs.append(dir + "inning/inning_Scores.xml")
        dirs.append(dir + "media/mobile.xml")
        files = self.download_files(dirs)
        if thread == "game":
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('HEADER'): code = code + self.generate_header(files)
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('BOX_SCORE'): code = code + self.generate_boxscore(files)
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('LINE_SCORE'): code = code + self.generate_linescore(files)
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('SCORING_PLAYS'): code = code + self.generate_scoring_plays(files)
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('HIGHLIGHTS'): code = code + self.generate_highlights(files,self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('THEATER_LINK'))
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('FOOTER'): code = code + self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('FOOTER') + "\n\n"
        elif thread == "post":
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('HEADER'): code = code + self.generate_header(files)
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('BOX_SCORE'): code = code + self.generate_boxscore(files)
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('LINE_SCORE'): code = code + self.generate_linescore(files)
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('SCORING_PLAYS'): code = code + self.generate_scoring_plays(files)
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('HIGHLIGHTS'): code = code + self.generate_highlights(files,self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('THEATER_LINK'))
            if self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('FOOTER'): code = code + self.SETTINGS.get('POST_THREAD_SETTINGS').get('CONTENT').get('FOOTER') + "\n\n"
        code = code + self.generate_status(files)
        if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning all",thread,"code..."
        return code

    def download_files(self,dirs):
        files = dict()
        try:
            response = urllib2.urlopen(dirs[0])
            files["linescore"] = json.load(response)
            response = urllib2.urlopen(dirs[1])
            files["gamecenter"] = ET.parse(response)
            response = urllib2.urlopen(dirs[2])
            files["boxscore"] = json.load(response)
            response = urllib2.urlopen(dirs[3])
            files["plays"] = json.load(response)
            response = urllib2.urlopen(dirs[4])
            files["scores"] = ET.parse(response)
            response = urllib2.urlopen(dirs[5])
            files["highlights"] = ET.parse(response)
        except Exception as e:
            if self.SETTINGS.get('LOG_LEVEL')>1: print e

        return files

    def generate_header(self,files):
        header = ""
        try:
            game = files["linescore"].get('data').get('game')
            timestring = game.get('time_date') + " " + game.get('ampm')
            date_object = datetime.strptime(timestring, "%Y/%m/%d %I:%M %p")
            t = timedelta(hours=self.time_change)
            timezone = self.time_zone
            date_object = date_object - t
            myteamis = ""
            if game.get('home_code') == self.SETTINGS.get('TEAM_CODE'):
                myteamis = "home"
            elif game.get('away_code') == self.SETTINGS.get('TEAM_CODE'):
                myteamis = "away"
            if self.SETTINGS.get('THREAD_SETTINGS').get('CONTENT').get('PREVIEW_BLURB'): header = self.generate_blurb(files,myteamis)
            header = header + "**First Pitch:** " + date_object.strftime("%I:%M %p ") + timezone + "\n\n"
            if game.get('description',False): header = header + "**Game Note:** " + game.get('description') + "\n\n"
            header = header + "[Preview](http://mlb.mlb.com/mlb/gameday/index.jsp?gid=" + game.get('gameday_link') + ")\n\n"
            weather = files["plays"].get('data').get('game').get('weather')
            root = files["gamecenter"].getroot()
            broadcast = root.find('broadcast')
            notes = self.get_notes(game.get('home_team_name'), game.get('away_team_name'))
            header = "|Game Info|Links|\n"
            header = header + "|:--|:--|\n"
            header = header + "|**First Pitch:** " + date_object.strftime("%I:%M %p ") + timezone + " @ " + game.get(
                'venue') + "|[Gameday](http://mlb.mlb.com/mlb/gameday/index.jsp?gid=" + game.get(
                'gameday_link') + ")|\n"
            header = header + "|**Weather:** " + weather.get('condition') + ", " + weather.get(
                'temp') + " F, " + "Wind " + weather.get('wind')
            if "Y" in game.get('double_header_sw') or "S" in game.get('double_header_sw'):
                header = header + "|[Game Graph](http://www.fangraphs.com/livewins.aspx?date=" + date_object.strftime(
                    "%Y-%m-%d") + "&team=" + game.get('home_team_name') + "&dh=" + game.get(
                    'game_nbr') + "&season=" + date_object.strftime("%Y") + ")|\n"
            else:
                header = header + "|[Game Graph](http://www.fangraphs.com/livewins.aspx?date=" + date_object.strftime(
                    "%Y-%m-%d") + "&team=" + game.get('home_team_name') + "&dh=0&season=" + date_object.strftime(
                    "%Y") + ")|\n"
            header = header + "|**TV:** "
            if not isinstance(broadcast[0][0].text, type(None)):
                header = header + broadcast[0][0].text
            if not isinstance(broadcast[1][0].text, type(None)):
                header = header + ", " + broadcast[1][0].text
            header = header + "|[Strikezone Map](http://www.brooksbaseball.net/pfxVB/zoneTrack.php?month=" + date_object.strftime(
                "%m") + "&day=" + date_object.strftime("%d") + "&year=" + date_object.strftime(
                "%Y") + "&game=gid_" + game.get('gameday_link') + "%2F)|\n"
            header = header + "|**Radio:** "
            if not isinstance(broadcast[0][1].text, type(None)):
                header = header + broadcast[0][1].text
            if not isinstance(broadcast[1][1].text, type(None)):
                header = header + ", " + broadcast[1][1].text
            header = header + "|**Notes:** [Away](http://mlb.mlb.com/mlb/presspass/gamenotes.jsp?c_id=" + notes[
                1] + "), [Home](http://mlb.mlb.com/mlb/presspass/gamenotes.jsp?c_id=" + notes[0] + ")|\n"
            if game.get('description',False): header = header + "|**Game Note:** " + game.get('description') + "||\n"
            header = header + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning header..."
            return header
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for header, returning partial header or empty string..."
            return header

    def generate_boxscore(self,files):
        boxscore = ""
        try:
            homebatters = []
            awaybatters = []
            homepitchers = []
            awaypitchers = []
            game = files["boxscore"].get('data').get('boxscore')
            team = files["linescore"].get('data').get('game')
            batting = game.get('batting')
            for i in range(0, len(batting)):
                players = batting[i].get('batter')
                for b in range(0, len(players)):
                    if players[b].get('bo') != None:
                        if batting[i].get('team_flag') == "home":
                            homebatters.append(
                                player.batter(players[b].get('name'), players[b].get('pos'), players[b].get('ab'),
                                              players[b].get('r'), players[b].get('h'), players[b].get('rbi'),
                                              players[b].get('bb'), players[b].get('so'), players[b].get('avg'),
                                              players[b].get('id')))
                        else:
                            awaybatters.append(
                                player.batter(players[b].get('name'), players[b].get('pos'), players[b].get('ab'),
                                              players[b].get('r'), players[b].get('h'), players[b].get('rbi'),
                                              players[b].get('bb'), players[b].get('so'), players[b].get('avg'),
                                              players[b].get('id')))
            pitching = game.get('pitching')
            for i in range(0, len(pitching)):
                players = pitching[i].get('pitcher')
                if type(players) is list:
                    for p in range(0, len(players)):
                        if pitching[i].get('team_flag') == "home":
                            homepitchers.append(
                                player.pitcher(players[p].get('name'), players[p].get('out'), players[p].get('h'),
                                               players[p].get('r'), players[p].get('er'), players[p].get('bb'),
                                               players[p].get('so'), players[p].get('np'), players[p].get('s'),
                                               players[p].get('era'), players[p].get('id')))
                        else:
                            awaypitchers.append(
                                player.pitcher(players[p].get('name'), players[p].get('out'), players[p].get('h'),
                                               players[p].get('r'), players[p].get('er'), players[p].get('bb'),
                                               players[p].get('so'), players[p].get('np'), players[p].get('s'),
                                               players[p].get('era'), players[p].get('id')))
                elif type(players) is dict:
                    if pitching[i].get('team_flag') == "home":
                        homepitchers.append(
                            player.pitcher(players.get('name'), players.get('out'), players.get('h'), players.get('r'),
                                           players.get('er'), players.get('bb'), players.get('so'), players.get('np'),
                                           players.get('s'), players.get('era'), players.get('id')))
                    else:
                        awaypitchers.append(
                            player.pitcher(players.get('name'), players.get('out'), players.get('h'), players.get('r'),
                                           players.get('er'), players.get('bb'), players.get('so'), players.get('np'),
                                           players.get('s'), players.get('era'), players.get('id')))
            while len(homebatters) < len(awaybatters):
                homebatters.append(player.batter())
            while len(awaybatters) < len(homebatters):
                awaybatters.append(player.batter())
            while len(homepitchers) < len(awaypitchers):
                homepitchers.append(player.pitcher())
            while len(awaypitchers) < len(homepitchers):
                awaypitchers.append(player.pitcher())
            boxscore = boxscore + team.get('away_team_name') + "|Pos|AB|R|H|RBI|BB|SO|BA|"
            boxscore = boxscore + team.get('home_team_name') + "|Pos|AB|R|H|RBI|BB|SO|BA|"
            boxscore = boxscore + "\n"
            boxscore = boxscore + ":--|:--|:--|:--|:--|:--|:--|:--|:--|"
            boxscore = boxscore + ":--|:--|:--|:--|:--|:--|:--|:--|:--|"
            boxscore = boxscore + "\n"
            for i in range(0, len(homebatters)):
                boxscore = boxscore + str(awaybatters[i]) + "|" + str(homebatters[i]) + "\n"
            boxscore = boxscore + "\n"
            boxscore = boxscore + team.get('away_team_name') + "|IP|H|R|ER|BB|SO|P-S|ERA|"
            boxscore = boxscore + team.get('home_team_name') + "|IP|H|R|ER|BB|SO|P-S|ERA|"
            boxscore = boxscore + "\n"
            boxscore = boxscore + ":--|:--|:--|:--|:--|:--|:--|:--|:--|"
            boxscore = boxscore + ":--|:--|:--|:--|:--|:--|:--|:--|:--|"
            boxscore = boxscore + "\n"
            for i in range(0, len(homepitchers)):
                boxscore = boxscore + str(awaypitchers[i]) + "|" + str(homepitchers[i]) + "\n"
            boxscore = boxscore + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning boxscore..."
            return boxscore
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for boxscore, returning empty string..."
            return boxscore

    def generate_linescore(self,files):
        linescore = ""
        try:
            game = files["linescore"].get('data').get('game')
            subreddits = self.get_subreddits(game.get('home_team_name'), game.get('away_team_name'))
            lineinfo = game.get('linescore')
            innings = len(lineinfo) if len(lineinfo) > 9 else 9
            linescore = linescore + "Linescore|"
            for i in range(1, innings + 1):
                linescore = linescore + str(i) + "|"
            linescore = linescore + "R|H|E\n"
            for i in range(0, innings + 4):
                linescore = linescore + ":--|"
            linescore = linescore + "\n" + "[" + game.get('away_team_name') + "](" + subreddits[1] + ")" + "|"
            x = 1
            if type(lineinfo) is list:
                for v in lineinfo:
                    linescore = linescore + v.get('away_inning_runs') + "|"
                    x = x + 1
            elif type(lineinfo) is dict:
                linescore = linescore + lineinfo.get('away_inning_runs') + "|"
                x = x + 1
            for i in range(x, innings + 1):
                linescore = linescore + "|"
            linescore = linescore + game.get('away_team_runs') + "|" + game.get('away_team_hits') + "|" + game.get(
                'away_team_errors')
            linescore = linescore + "\n" + "[" + game.get('home_team_name') + "](" + subreddits[0] + ")" "|"
            x = 1
            if type(lineinfo) is list:
                for v in lineinfo:
                    linescore = linescore + v.get('home_inning_runs') + "|"
                    x = x + 1
            elif type(lineinfo) is dict:
                linescore = linescore + lineinfo.get('home_inning_runs') + "|"
                x = x + 1
            for j in range(x, innings + 1):
                linescore = linescore + "|"
            linescore = linescore + game.get('home_team_runs') + "|" + game.get('home_team_hits') + "|" + game.get(
                'home_team_errors')
            linescore = linescore + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning linescore..."
            return linescore
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for linescore, returning empty string..."
            return linescore

    def generate_scoring_plays(self,files):
        scoringplays = ""
        try:
            root = files["scores"].getroot()
            scores = root.findall("score")
            currinning = ""
            hometeam_abbrev = self.lookup_team_info(field="name_abbrev", lookupfield="team_code", lookupval=root.get("home_team"))
            awayteam_abbrev = self.lookup_team_info(field="name_abbrev", lookupfield="team_code", lookupval=root.get("away_team"))
            scoringplays = scoringplays + "Inning|Scoring Play Description|Score\n"
            scoringplays = scoringplays + ":--|:--|:--\n"
            for s in scores:
                if s.get("top_inning") == "Y":
                    inningcheck = "Top "
                else:
                    inningcheck = "Bottom "
                inningcheck = inningcheck + s.get("inn") + "|"
                if inningcheck != currinning:
                    currinning = inningcheck
                    scoringplays = scoringplays + currinning
                else:
                    scoringplays = scoringplays + " |"

                actions = s.findall("action")
                try:
                    if s.find('atbat').get('score') == "T":
                        scoringplays = scoringplays + s.find('atbat').get('des')
                    elif s.find('action').get("score") == "T":
                        scoringplays = scoringplays + s.find('action').get('des')
                    else:
                        scoringplays = scoringplays + s.get('pbp')
                except:
                    scoringplays = scoringplays + "Scoring play description currently unavailable."

                scoringplays = scoringplays + "|"
                if int(s.get("home")) < int(s.get("away")):
                    scoringplays = scoringplays + s.get("away") + "-" + s.get("home") + " " + awayteam_abbrev.upper()
                elif int(s.get("home")) > int(s.get("away")):
                    scoringplays = scoringplays + s.get("home") + "-" + s.get("away") + " " + hometeam_abbrev.upper()
                else:
                    scoringplays = scoringplays + s.get("home") + "-" + s.get("away")
                scoringplays = scoringplays + "\n"
            scoringplays = scoringplays + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning scoringplays..."
            return scoringplays
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for scoringplays, returning empty string..."
            return scoringplays

    def generate_highlights(self,files,theater_link=False):
        highlight = ""
        try:
            root = files["highlights"].getroot()
            video = root.findall("media")
            highlight = highlight + "|Team|Highlight|\n"
            highlight = highlight + "|:--|:--|\n"
            for v in video:
                if v.get('type') == "video" and v.get('media-type') == "T":              
                    try:
                        team = self.get_team(v.get('team_id'))
                        highlight = highlight + "|" + team[0] + "|[" + v.find("headline").text + "](" + v.find("url").text + ")|\n"                   
                    except:
                        highlight = highlight + "|[](/MLB)|[" + v.find("headline").text + "](" + v.find("url").text + ")|\n"                     
            if theater_link:
                game = files["linescore"].get('data').get('game')
                gamedate = game.get("time_date").split(" ",1)[0].replace("/","")
                game_pk = game.get("game_pk")
                highlight = highlight + "||See all highlights at [Baseball.Theater](http://baseball.theater/game/" + gamedate + "/" + game_pk + ")|\n"
            highlight = highlight + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning highlight..."
            return highlight
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for highlight, returning empty string..."
            return highlight

    def generate_decisions(self,files):
        decisions = ""
        try:
            homepitchers = []
            awaypitchers = []
            game = files["boxscore"].get('data').get('boxscore')
            team = files["linescore"].get('data').get('game')
            subreddits = self.get_subreddits(team.get('home_team_name'), team.get('away_team_name'))
            pitching = game.get('pitching')
            for i in range(0, len(pitching)):
                players = pitching[i].get('pitcher')
                if type(players) is list:
                    for p in range(0, len(players)):
                        if pitching[i].get('team_flag') == "home":
                            homepitchers.append(
                                player.decision(players[p].get('name'), players[p].get('note'), players[p].get('id')))
                        else:
                            awaypitchers.append(
                                player.decision(players[p].get('name'), players[p].get('note'), players[p].get('id')))
                elif type(players) is dict:
                    if pitching[i].get('team_flag') == "home":
                        homepitchers.append(
                            player.decision(players.get('name'), players.get('note'), players.get('id')))
                    else:
                        awaypitchers.append(
                            player.decision(players.get('name'), players.get('note'), players.get('id')))
            decisions = decisions + "|Decisions||" + "\n"
            decisions = decisions + "|:--|:--|" + "\n"
            decisions = decisions + "|" + "[" + team.get('away_team_name') + "](" + subreddits[1] + ")|"
            for i in range(0, len(awaypitchers)):
                decisions = decisions + str(awaypitchers[i]) + " "
            decisions = decisions + "\n" + "|" + "[" + team.get('home_team_name') + "](" + subreddits[0] + ")|"
            for i in range(0, len(homepitchers)):
                decisions = decisions + str(homepitchers[i])
            decisions = decisions + "\n\n"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning decisions..."
            return decisions
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for decisions, returning empty string..."
            return decisions

    def get_status(self,url):
        try:
            response = urllib2.urlopen(url+"linescore.json")
            linescore = json.load(response)
            return linescore.get('data').get('game').get('status')
        except:
            return None
        return None

    def generate_status(self,files):
        status = ""
        try:
            game = files["linescore"].get('data').get('game')
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Status:",game.get('status')
            if game.get('status') == "Game Over" or game.get('status') == "Final":
                s = files["linescore"].get('data').get('game')
                status = status + "##FINAL: "
                if int(s.get("home_team_runs")) < int(s.get("away_team_runs")):
                    status = status + s.get("away_team_runs") + "-" + s.get("home_team_runs") + " " + s.get(
                        "away_team_name") + "\n"
                    status = status + self.generate_decisions(files)
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
                elif int(s.get("home_team_runs")) > int(s.get("away_team_runs")):
                    status = status + s.get("home_team_runs") + "-" + s.get("away_team_runs") + " " + s.get(
                        "home_team_name") + "\n"
                    status = status + self.generate_decisions(files)
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
                elif int(s.get("home_team_runs")) == int(s.get("away_team_runs")):
                    status = status + "TIE"
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
            elif game.get('status') == "Completed Early":
                status = status + "##COMPLETED EARLY: "
                if int(s.get("home_team_runs")) < int(s.get("away_team_runs")):
                    status = status + s.get("away_team_runs") + "-" + s.get("home_team_runs") + " " + s.get(
                        "away_team_name") + "\n"
                    status = status + self.generate_decisions(files)
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
                elif int(s.get("home_team_runs")) > int(s.get("away_team_runs")):
                    status = status + s.get("home_team_runs") + "-" + s.get("away_team_runs") + " " + s.get(
                        "home_team_name") + "\n"
                    status = status + self.generate_decisions(files)
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
                elif int(s.get("home_team_runs")) == int(s.get("away_team_runs")):
                    status = status + "TIE"
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                    return status
            elif game.get('status') == "Postponed":
                status = status + "##POSTPONED\n\n"
                if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                return status
            elif game.get('status') == "Suspended":
                status = status + "##SUSPENDED\n\n"
                if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                return status
            elif game.get('status') == "Cancelled":
                status = status + "##CANCELLED\n\n"
                if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning status..."
                return status
            else:
                if self.SETTINGS.get('LOG_LEVEL')>2: print "Status not final or postponed, returning empty string..."
                return status
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Missing data for status, returning empty string..."
            return status

    def didmyteamwin(self, url):
    #returns 0 for loss, 1 for win, 2 for tie, 3 for postponed/suspended/canceled, blank for exception
        myteamwon = ""
        myteamis = ""
        try:
            response = urllib2.urlopen(url+"linescore.json")
            linescore = json.load(response)
        except:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Error downloading linescore, returning empty string for whether my team won..."
            return myteamwon
        game = linescore.get('data').get('game')

        if game.get('home_code') == self.SETTINGS.get('TEAM_CODE'):
            myteamis = "home"
        elif game.get('away_code') == self.SETTINGS.get('TEAM_CODE'):
            myteamis = "away"
        else:
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Cannot determine if my team is home or away, returning empty string for whether my team won..."
            return myteamwon
        if game.get('status') == "Game Over" or game.get('status') == "Final" or game.get('status') == "Completed Early":
            hometeamruns = int(game.get("home_team_runs"))
            awayteamruns = int(game.get("away_team_runs"))
            if int(hometeamruns == awayteamruns):
                myteamwon = "2"
                if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning whether my team won (TIE)..."
                return myteamwon
            else:
                if hometeamruns < awayteamruns:
                    if myteamis == "home":
                        myteamwon = "0"
                    elif myteamis == "away":
                        myteamwon = "1"
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning whether my team won..."
                    return myteamwon
                elif hometeamruns > awayteamruns:
                    if myteamis == "home":
                        myteamwon = "1"
                    elif myteamis == "away":
                        myteamwon = "0"
                    if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning whether my team won..."
                    return myteamwon
        elif game.get('status') == "Postponed" or game.get('status') == "Suspended" or game.get('status') == "Cancelled":
            myteamwon = "3"
            if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning whether my team won (postponed, suspended, or canceled)..."
            return myteamwon
        if self.SETTINGS.get('LOG_LEVEL')>2: print "Returning whether my team won (exception)..." + myteamwon
        return myteamwon

    def get_subreddits(self, homename, awayname):
        subreddits = []
        options = {
            "Twins": "/r/minnesotatwins",
            "White Sox": "/r/WhiteSox",
            "Tigers": "/r/MotorCityKitties",
            "Royals": "/r/KCRoyals",
            "Indians": "/r/WahoosTipi",
            "Rangers": "/r/TexasRangers",
            "Astros": "/r/Astros",
            "Athletics": "/r/OaklandAthletics",
            "Angels": "/r/AngelsBaseball",
            "Mariners": "/r/Mariners",
            "Red Sox": "/r/RedSox",
            "Yankees": "/r/NYYankees",
            "Blue Jays": "/r/TorontoBlueJays",
            "Rays": "/r/TampaBayRays",
            "Orioles": "/r/Orioles",
            "Cardinals": "/r/Cardinals",
            "Reds": "/r/Reds",
            "Pirates": "/r/Buccos",
            "Cubs": "/r/CHICubs",
            "Brewers": "/r/Brewers",
            "Giants": "/r/SFGiants",
            "Diamondbacks": "/r/azdiamondbacks",
            "D-backs": "/r/azdiamondbacks",
            "Rockies": "/r/ColoradoRockies",
            "Dodgers": "/r/Dodgers",
            "Padres": "/r/Padres",
            "Phillies": "/r/Phillies",
            "Mets": "/r/NewYorkMets",
            "Marlins": "/r/letsgofish",
            "Nationals": "/r/Nationals",
            "Braves": "/r/Braves"
        }
        subreddits.append(options[homename])
        subreddits.append(options[awayname])
        return subreddits

    def get_notes(self, homename, awayname):
        notes = []
        options = {
            "Twins": "min",
            "White Sox": "cws",
            "Tigers": "det",
            "Royals": "kc",
            "Indians": "cle",
            "Rangers": "tex",
            "Astros": "hou",
            "Athletics": "oak",
            "Angels": "ana",
            "Mariners": "sea",
            "Red Sox": "bos",
            "Yankees": "nyy",
            "Blue Jays": "tor",
            "Rays": "tb",
            "Orioles": "bal",
            "Cardinals": "stl",
            "Reds": "cin",
            "Pirates": "pit",
            "Cubs": "chc",
            "Brewers": "mil",
            "Giants": "sf",
            "Diamondbacks": "ari",
            "D-backs": "ari",
            "Rockies": "col",
            "Dodgers": "la",
            "Padres": "sd",
            "Phillies": "phi",
            "Mets": "nym",
            "Marlins": "mia",
            "Nationals": "was",
            "Braves": "atl"
        }
        notes.append(options[homename])
        notes.append(options[awayname])
        return notes

    def lookup_team_info(self, field="name_abbrev", lookupfield="team_code", lookupval=None):
        try:
            response = urllib2.urlopen("http://mlb.com/lookup/json/named.team_all.bam?sport_code=%27mlb%27&active_sw=%27Y%27&all_star_sw=%27N%27")
            teaminfo = json.load(response)
        except Exception as e:
            if self.SETTINGS.get('LOG_LEVEL')>1: print e
            return None

        teamlist = teaminfo.get('team_all').get('queryResults').get('row')
        for team in teamlist:
            if team.get(lookupfield,None).lower() == lookupval.lower(): return team.get(field)

        if self.SETTINGS.get('LOG_LEVEL')>1: print "Couldn't look up",field,"from",lookupfield,"=",lookupval
        return None

    def get_team(self, team_id):
        team = []
        options = {
            "142": "[MIN](/r/minnesotatwins)",
            "145": "[CWS](/r/WhiteSox)",
            "116": "[DET](/r/MotorCityKitties)",
            "118": "[KCR](/r/KCRoyals)",
            "114": "[CLE](/r/WahoosTipi)",
            "140": "[TEX](/r/TexasRangers)",
            "117": "[HOU](/r/Astros)",
            "133": "[OAK](/r/OaklandAthletics)",
            "108": "[LAA](/r/AngelsBaseball)",
            "136": "[SEA](/r/Mariners)",
            "111": "[BOS](/r/RedSox)",
            "147": "[NYY](/r/NYYankees)",
            "141": "[TOR](/r/TorontoBlueJays)",
            "139": "[TBR](/r/TampaBayRays)",
            "110": "[BAL](/r/Orioles)",
            "138": "[STL](/r/Cardinals)",
            "113": "[CIN](/r/Reds)",
            "134": "[PIT](/r/Buccos)",
            "112": "[CHC](/r/CHICubs)",
            "158": "[MIL](/r/Brewers)",
            "137": "[SFG](/r/SFGiants)",
            "109": "[ARI](/r/azdiamondbacks)",
            "115": "[COL](/r/ColoradoRockies)",
            "119": "[LAD](/r/Dodgers)",
            "135": "[SDP](/r/Padres)",
            "143": "[PHI](/r/Phillies)",
            "121": "[NYM](/r/NewYorkMets)",
            "146": "[MIA](/r/letsgofish)",
            "120": "[WSH](/r/Nationals)",
            "144": "[ATL](/r/Braves)"
        }
        team.append(options[team_id])
        return team        
