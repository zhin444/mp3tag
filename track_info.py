import os,re,psycopg2,json,sys,eyed3, datetime
from operator import itemgetter

##gets release date and
def album_info(conn,artist_name,album_name,release_id=0):
    cur = conn.cursor()
    
    cache_list = []
    for f0 in os.listdir():
        if len(re.compile(r'.album_[0-9]{12}\.txt').findall(f0)):
            cache_list.append(f0)
    
    cache_list.sort()

    ans='n'
    if len(cache_list) > 0 and release_id==0:
        ls_date = cache_list[-1].replace('.album_','').replace('.txt','')
        ans = input(f'Would you like to use the cached album info from {ls_date[0:2]}/{ls_date[2:4]}/{ls_date[4:6]} ? Y/N\n')
    if ans =='' or ans[0].lower() == 'y':
        print('reading album info from cache...')
        cache_list.sort()
        
        fs = open(cache_list[-1],'r')
        album_list = fs.read()
        album_list = json.loads(album_list)
        print( f'num. of albums found: {len(album_list)}' )
        for index,album in enumerate(album_list):
            print(f'**{index+1}.-\r\n\t release name:{album['release_group_name']};\r\n\t total tracks:{album['track_count']};\r\n\t format:{album['format']}')

        album_index = input("Pick an album\n")
        if len(re.compile(r'[0-9]{1,10}').findall(album_index)) > 0:
            track_list = track_info(conn,artist_name,album_list[int(album_index)-1])
        else:
            track_list = []
        # print(json.dumps(track_list,indent=4))
        cur.close()
        return album_list, track_list
    elif release_id!= 0:
        print('album info..')
        cur.execute(f'''
        SELECT
            r.id as release_id,
            rg.id as release_group_id,
            r.name as release_name,
            rg.name as release_group_name,
            m.id as medium_id,
            rgm.first_release_date_day || '/' || rgm.first_release_date_month || '/' || rgm.first_release_date_year as release_date,
            m.track_count as track_count,
            r.comment as release_comment,
            rg.comment as release_group_comment,
            mf.name
        FROM
            release as r,
            release_group as rg,
            release_group_meta as rgm,
            medium as m,
            medium_format as mf
        WHERE
            rg.artist_credit IN (SELECT id FROM artist_credit WHERE lower(name) LIKE '%{artist_name.lower()}%') AND
            r.id = {str(release_id)} AND
            rg.id = r.release_group AND
            rgm.id=rg.id AND
            m.release= r.id AND 
            mf.id = m.format
        ''')

        json_query = []
        for query_result in cur.fetchall():
            json_query.append({
                'release_id':query_result[0],
                'release_group_id':query_result[1],
                'release_name':query_result[2],
                'release_group_name':query_result[3],
                'medium.id':query_result[4],
                'release_date':query_result[5],
                'track_count':query_result[6],
                'release_comment':query_result[7],
                'release_group_comment':query_result[8],
                'format':query_result[9]
        })

        if len(json_query) > 0:
            track_list = track_info(conn,artist_name,json_query[0])
            print(f'\r\ntracks for {json_query[0]['release_id']} - {json_query[0]['release_name']}')
        else:
            track_list = []
            print(f'No album for id:{release_id}')
        cur.close()
        return json_query , track_list
    else:
        print('album info..')
        cache_file = f'{ datetime.datetime.strftime(datetime.datetime.now(),'%d%m%y%H%M%S') }'
        cache_file = '.album_' + cache_file + '.txt'
        
        cur.execute(f'''
        SELECT
            r.id as release_id,
            rg.id as release_group_id,
            r.name as release_name,
            rg.name as release_group_name,
            m.id as medium_id,
            rgm.first_release_date_day || '/' || rgm.first_release_date_month || '/' || rgm.first_release_date_year as release_date,
            m.track_count as track_count,
            r.comment as release_comment,
            rg.comment as release_group_comment,
            mf.name
        FROM
            release as r,
            release_group as rg,
            release_group_meta as rgm,
            medium as m,
            medium_format as mf
        WHERE
            rg.artist_credit IN (SELECT id FROM artist_credit WHERE lower(name) LIKE '%{artist_name.lower()}%') AND
            lower(rg.name) LIKE '%{album_name.lower()}%' AND
            rgm.id=rg.id AND
            r.release_group=rg.id AND
            m.release= r.id AND
            mf.id = m.format
        ''')
        

        json_query = []
        for query_result in cur.fetchall():
            json_query.append({
                'release_id':query_result[0],
                'release_group_id':query_result[1],
                'release_name':query_result[2],
                'release_group_name':query_result[3],
                'medium.id':query_result[4],
                'release_date':query_result[5],
                'track_count':query_result[6],
                'release_comment':query_result[7],
                'release_group_comment':query_result[8],
                'format':query_result[9]
            })

        fs = open(cache_file,'x')
        fs.write(   json.dumps(json_query,indent=4)    )
        fs.close()

        if len(cache_list) >0:
            for ff in cache_list: os.remove(ff)

        print( f'num. of albums found: {len(json_query)}' )
        for index,album in enumerate(json_query):
            print(f'**{index+1}.-\r\n\t release name:{album['release_group_name']};\r\n\t total tracks:{album['track_count']};\r\n\t format:{album['format']}')

        album_index = input('Pick an album\n')      
        if len(re.compile(r'[0-9]{1,10}').findall(album_index)) > 0:
            track_list = track_info(conn,artist_name,json_query[int(album_index)-1])
        else:
            track_list = []

        # print(json.dumps(track_list,indent=4))
        cur.close()
        return json_query , track_list
    


def track_info(conn,artist_name,album_result:dict):
    cur = conn.cursor()
    cached_list = []
    for fs1 in os.listdir():
        name, ext = os.path.splitext(fs1)
        if ext == '.txt':
            if len( re.compile(r'.songs_' + str(album_result['release_id']) + r'_[0-9]{12}').findall(name) ) >0:
                cached_list.append(fs1)
        

    ans='n'
    cached_list.__len__
    if len(cached_list) >0:
        cached_list.sort()
        ls_date = cached_list[-1].replace('.songs_','').replace('.txt','').replace(f'{str(album_result['release_id'])}_','')
        ans = input(f'Would you like to use the cached tracks from {ls_date[0:2]}/{ls_date[2:4]}/{ls_date[4:6]} ? Y/N\n')


    if ans=='' or ans[0].lower() =='y':
        print('reading songs from text file..')
        
        fs = open(cached_list[-1],'rt')
        track_list=fs.read()
        track_list = json.loads(track_list)
        cur.close()
        return track_list
    else:
        print('listing songs..')
        track_list=[]
        cache_file= f'{datetime.datetime.strftime(datetime.datetime.now(),'%d%m%y%H%M%S')}'
        cache_file = '.songs_' + str(album_result['release_id']) + '_' + cache_file + '.txt'

        cur.execute(f'''
        SELECT
            track.id,
            track.recording,
            track.name,
            track.position,
            track.medium,
            release.name,
            medium_format.name,
            medium.track_count
        FROM
            track,release,medium, medium_format
        WHERE
            release.id={album_result['release_id']} AND
            medium.release = release.id AND
            track.medium = medium.id AND
            medium_format.id = medium.format
        ''')

        qresult = cur.fetchall()

        for recording in qresult:
            track_list.append({
                'release_id': album_result['release_id'],
                'track_id': recording[0],
                'recording_id': recording[1],
                'track_name': recording[2],
                'track_position': recording[3],
                'medium_id': recording[4],
                'release': recording[5],
                'format': recording[6],
                'track_count': recording[7]
            })
        
        fs = open(cache_file,'x')
        fs.writelines( json.dumps(track_list,indent=4) )
        for ff in cached_list: os.remove(ff)
        fs.close()
        cur.close()
        return track_list
    

def tag2(file0,track,artist_name):
    try:
        mp3 = eyed3.load(file0)
        tag = mp3.initTag()
        tag:eyed3.id3.Tag
        tag.artist = artist_name
        tag.track_num = track['track_position']
        tag.title = track['track_name']
        tag.album = track['release']
        tag.save()
        print(f'{file0} tagged!')
    except Exception as e:
        print(e)
        print(f'Exception while tagging!')

def match_files(artist_name, track_list:list):
    file_found = []
    not_found = []

    for file0 in os.listdir():
        filename, ext = os.path.splitext(file0)
        if ext != '.mp3': continue
        words_filename = re.compile(r'[A-Za-z0-9]{1,1111}').findall(filename)
        found = False
        ######################################################
        # lleva una cuenta del numero de cadenas de caracteres 
        # que se encuentran en el nombre del archivo y 
        # el nombre de la pista
        ######################################################
        for track in track_list:
            words_track = re.compile(r'[A-Za-z0-9]{1,1111}').findall(track['track_name'])
            matches = 0
            ######################################################
            # lleva un conteo del numero de cadenas de caracteres 
            # que se encuentran en el nombre del archivo y 
            # el nombre de la pista
            ######################################################
            for track_word in words_track:
                for filename_word in words_filename:
                    if track_word == filename_word:
                        matches+=1
            #########################################################
            # Si mas de la mitad del contenido de las listas es igual
            # pide confirmacion para agregar los atributos 
            # del registro encontrado al archivo
            #########################################################
            if matches/len(words_track) > 0.5:
                try:
                    ans = input(f'\nfile:\t\"{file0}\"\r\ntrack:\t{track['track_name']}\t{track['track_position']}/{len(track_list)} ****  Yes/No ? **** Y' )
                    if ans.upper() == 'Y' or ans=='':   
                        print('tagging2...')         
                        tag2(file0,track,artist_name)
                        file_found.append((file0,{
                            'release_id': track['release_id'],
                            'release': track['release']
                        }))
                        found = True
                except Exception as e:
                    print(e)
                    print(e.args)
        if not found: not_found.append(file0)

    return file_found, not_found
    

def tag(artist_name, track_list:list, tag_not_found=True, tag_songs=True):
    ##################################################################
    # Relaciona el archivo encontrado con algun registro de track_list
    ##################################################################
    not_found = []
    mp3_found = []
    for file0 in os.listdir():
        filename, ext = os.path.splitext(file0)
        if ext != '.mp3': continue
        words_filename = re.compile(r'[A-Za-z0-9]{1,1111}').findall(filename)
        found = False
        ######################################################
        # lleva una cuenta del numero de cadenas de caracteres 
        # que se encuentran en el nombre del archivo y 
        # el nombre de la pista
        ######################################################
        for track in track_list:
            words_track = re.compile(r'[A-Za-z0-9]{1,1111}').findall(track['track_name'])
            matches = 0
            ######################################################
            # lleva un conteo del numero de cadenas de caracteres 
            # que se encuentran en el nombre del archivo y 
            # el nombre de la pista
            ######################################################
            for track_word in words_track:
                for filename_word in words_filename:
                    if track_word == filename_word:
                        matches+=1
            #########################################################
            # Si mas de la mitad del contenido de las listas es igual
            # pide confirmacion para agregar los atributos 
            # del registro encontrado al archivo
            #########################################################
            if matches/len(words_track) > 0.5:
                try:
                    if tag_songs: 
                        ans = input(f'\nfile:\t\"{file0}\"\r\ntrack:\t{track['track_name']}\t{track['track_position']}/{len(track_list)} ****  Yes/No ? **** Y' )
                        if ans.upper() == 'Y' or ans=='':
                            print('tagging..')
                            tag2(file0,track,artist_name)
                            found = True
                            track0 = f'{track['release_id']} - {track['release']}'
                            tup0 = file0, track0
                            mp3_found.append(tup0)
                            # print(f'{json.dumps(mp3_found,indent=4)}')
                    else:
                        found = True
                        track0 = f'{track['release_id']} - {track['release']}'
                        tup0 = file0, track0
                        mp3_found.append(tup0)

                except Exception as e:
                    print('Exception while tagging..')
                    print(e)
                    print(e.args)
        if not found: not_found.append(file0)
    
    # mp3_found, not_found = match_files(artist_name,track_list)
    no_tag = []

    if tag_not_found and tag_songs:
        for notfound in not_found:
            ans = input(f'\n{notfound} not found.. \r\nwould you like to manually choose a song from the album tracklist Y/N ? Y')
            sorted_tracks = sorted(track_list,key=itemgetter('track_name'))
            if ans=='' or ans[0].upper() == 'Y':
                for index,track in enumerate(sorted_tracks):
                    print(f'**{index+1}.- \t{track['track_name']}')
                ans = input(f'choose a song: ')
                try:
                    if tag_songs: tag2(notfound, sorted_tracks[int(ans)-1], artist_name)
                    mp3_found.append(  (notfound, sorted_tracks[int(ans)-1])  )
                except:
                    no_tag.append(notfound)
            else:
                no_tag.append(notfound)
        
        return mp3_found, no_tag
    else:
        # print(f'*** FOUND ***\n{json.dumps(mp3_found,indent=4)}')
        return mp3_found , not_found


def get_all_tracks(conn,artist_name):
    cur = conn.cursor()
    if not os.path.exists('.songs.txt'):
        print('listing songs..')
        track_list=[]
        cur.execute(f'''
        SELECT
            track.id,
            track.recording,
            track.name,
            track.position,
            track.medium,
            release.name,
            medium_format.name,
            medium.track_count,
            release.id
        FROM
            track, artist_credit, release, medium, medium_format
        WHERE
            lower(artist_credit.name) LIKE '%{artist_name.lower()}%' AND
            track.artist_credit = artist_credit.id AND
            medium.id = track.medium AND
            release.id = medium.release AND
            medium_format.id = medium.format
        ''')

        qresult = cur.fetchall()

        for recording in qresult:
            track_list.append({
                'track_id': recording[0],
                'recording_id': recording[1],
                'track_name': recording[2],
                'track_position': recording[3],
                'medium_id': recording[4],
                'release': recording[5],
                'format': recording[6],
                'track_count': recording[7],
                'release_id': recording[8]
            })
        
        fs = open('.songs.txt','x')
        fs.writelines( json.dumps(track_list,indent=4) )
        fs.close()
        cur.close()
        return track_list
    else:
        print('reading songs from text file..')
        fs = open('.songs.txt','rt')
        track_list=fs.read()
        track_list = json.loads(track_list)
        cur.close()
        return track_list

def album_match_songs(autotag = True):
    conn = psycopg2.connect( 'host=localhost user=musicbrainz dbname=musicbrainz password=passgres' )
    if len(sys.argv) >2:
        artist_name= sys.argv[2]
    else:
        # artist_name = os.getcwd().split(os.path.sep)[-1].split(' - ')[0]
        print('specify an artist name please..')
        return
    
    track_list = get_all_tracks(conn=conn,artist_name=artist_name)
    ##################################################################
    # Relaciona el archivo encontrado con algun registro de track_list
    ##################################################################
    tracks_found = []
    for file0 in os.listdir():
        filename,ext = os.path.splitext(file0)
        if ext != '.mp3': continue
        words_filename = re.compile(r'[A-Za-z0-9]{1,1111}').findall(filename)
        found = False
        ######################################################
        # lleva una cuenta del numero de cadenas de caracteres 
        # que se encuentran en el nombre del archivo y 
        # el nombre de la pista
        ######################################################
        for track in track_list:
            words_track = re.compile(r'[A-Za-z0-9]{1,1111}').findall(track['track_name'])
            matches = 0
            ######################################################
            # lleva un conteo del numero de cadenas de caracteres 
            # que se encuentran en el nombre del archivo y 
            # el nombre de la pista
            ######################################################
            for track_word in words_track:
                for filename_word in words_filename:
                    if track_word == filename_word:
                        matches+=1
            #########################################################
            # Si mas de la mitad del contenido de las listas es igual
            # pide confirmacion para agregar los atributos 
            # del registro encontrado al archivo
            #########################################################
            if matches/len(words_filename) > 0.4:
                # print(f'{filename} <-> {track['track_name']}')
                tracks_found.append(track)
    
    # print(json.dumps(tracks_found,indent=4))
    sorted_tracks_release = sorted(tracks_found,key=itemgetter('release'))
    sorted_tracks = sorted(tracks_found, key=itemgetter('track_name'))
    unique_albums = []
    unique_tracks = []

    current = ''
    count0 = 0
    bundle_tracks = []

    for index, tr in enumerate(sorted_tracks_release):
        if tr['release'] != current or index == len(sorted_tracks_release) - 1:
            if count0 != 0:
                # bundle_tracks.sort()
                bundle_tracks = sorted(bundle_tracks,key=itemgetter('release_name'))
                # print(f'{count0}\n{json.dumps(bundle_tracks,indent=4)}')
                unique_albums.append({
                    'release_id': bundle_tracks[0]['release_id'],
                    'release_name': bundle_tracks[0]['release_name'],
                    'tracks' : {json.dumps(bundle_tracks)},
                    'track_count': bundle_tracks[0]['track_count'],
                    'matches': len(bundle_tracks),
                    'percent': len(bundle_tracks) / int(bundle_tracks[0]['track_count'])
                })

                count0 = 0
                bundle_tracks.clear()
            # if index != len(sorted_tracks_release) - 1:
            #     print(      f'\n\nrelease: {tr['release']}\ntrack count:{tr['track_count']}\nformat:{tr['format']}'    )


        count0 +=1
        current = tr['release']

        bundle_tracks.append({
            'release_id': tr['release_id'],
            'track_name': tr['track_name'],
            'release_name': tr['release'],
            'track_count': tr['track_count']
            })
    
    for tr in sorted_tracks:
        if tr['track_name'] != current:
            # print(f'{tr['track_name']}')
            unique_tracks.append(tr)
        current = tr['track_name']

    print(f'******************************************\n\nThe following matches have been found..')
    for al in unique_albums:
        # print(f'{al['release_name']} -> {al['matches']} / {al['track_count']}')
        if al['percent'] >= 0.9:
            print(f'{al['release_name']}\t\t\t\t<->\t{al['matches']}/{al['track_count']}')
    print(f'******************************************\n')

    reallyfound = []
    
    for al in unique_albums:
        if al['percent'] >= 0.9:
            conn = psycopg2.connect( 'host=localhost user=musicbrainz dbname=musicbrainz password=passgres' )
            print(f'{al['release_id']} , {al['release_name']}')
            found, notfound = tag(  artist_name, album_info(conn,artist_name, al['release_name'], al['release_id'])[1],False ,autotag  )
            reallyfound.append(found)
    
    if len(reallyfound) > 0:
        # found.index('s')
        for index, rf in enumerate(reallyfound):
            print(f'{rf[0][1]}') ## album name
            lst = ''
            for rff in rf: ## song name
                if rff[0] != lst: print(f'\t{rff[0]}')
                lst = rff[0]
        all_mp3 = []

        for ff in os.listdir():  
            if os.path.splitext(ff)[1] == '.mp3':
                total=0
                albums = ''
                for rf in reallyfound:
                    try:

                        if rf.index( (ff,rf[0][1]) ) != -1: 
                            total+=1
                            albums += rf[0][1][0:7] + '\t'
                    except:
                        pass
                # all_mp3.append( (ff,total) )
                # print(f'{ff}\t{total}\t{albums}')
                all_mp3.append(f'{total}\t{albums}\t{ff}')
        all_mp3.sort()
        for mp in all_mp3: print(mp)
    
    else:
        print('nothing found')


def main():
    if len(sys.argv) >2:
        artist_name= sys.argv[2]
        album_name= sys.argv[3]
    else:
        try:
            artist_name = os.getcwd().split(os.path.sep)[-1].split(' - ')[0]
            album_name = os.getcwd().split(os.path.sep)[-1].split(' - ')[1]
        except IndexError as e:
            print(e)
            print('make sure the directory name has the format: "artist_name - album_name" \nor insted pass in the arguments artist_name album_name')
            return
    
    print(f'*********{artist_name} - {album_name}*********')
    conn = psycopg2.connect( 'host=localhost user=musicbrainz dbname=musicbrainz password=passgres' )
    tag(    artist_name, album_info(conn,artist_name,album_name)[1]  )
    conn.close()

if __name__ == '__main__':
    if sys.argv.__len__() == 1:
        print('COMMAND USE:\n\r\t--tag-songs ARTIST_NAME ALBUM_NAME: tags songs based on artist and album name,\r\n\t\
            --match-songs ARTIST_NAME: gets albums from specific artist that best match the songs in the current directory')
    elif sys.argv[1]=='--tag-songs':
        main()
    elif sys.argv[1]=='--match-songs':
        ans = input('tag songs? Y/N')
        if ans=='' or ans.lower()=='y':
            album_match_songs(True)
        else:
            album_match_songs(False)