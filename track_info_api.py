import requests
import json
import sys
import os
import re
import eyed3
import tinytag

def select_album(artist_name:str ,album_name:str ):
    url:str = f"https://musicbrainz.org/ws/2/release/?query=artist:{artist_name} AND release:{album_name}"
    params:dict[str,str] = {
        'fmt': 'json'
    }
    headers: dict[str,str] = {
            "User-Agent": "track_info_api/1.0 (test@example.com)"
    }

    response:requests.Response = requests.get(url, params = params, headers = headers)
    data = response.json()
    for index,release in enumerate(data['releases']):
        print(f'''({index+1}) {release['title']} - {release['artist-credit'][0]['name']} - {release['media'][0]['format']} - track count:{release['media'][0]['track-count']}''')
    selected_album = input("select an album number..")
    selected_album = data['releases'][int(selected_album)-1]
    # print(f'selected->{json.dumps(selected_album,indent=4)}')
    print(f'selected-> {selected_album['title']} - {selected_album['artist-credit'][0]['name']} - {selected_album['media'][0]['format']} - {selected_album['media'][0]['track-count']}')
    return selected_album['id'], selected_album['release-group']['id']

def get_songs(artist_name:str, album_name:str, release_id:str,release_group_id:str):
    url:str = f"https://musicbrainz.org/ws/2/release/{release_id}?inc=recordings"
    params:dict[str,str] = {
        'fmt': 'json'
    }
    headers: dict[str,str] = {
            "User-Agent": "track_info_api/1.0 (test@example.com)"
    }
    response = requests.get(url, params = params,  headers = headers)
    data = response.json()
    track_list:list[str] = []

    for media in data['media']:
        for track in media['tracks']:
            # print(json.dumps(track,indent=4))
            track_list.append(track)
    return track_list

def get_album_cover(release_id):
    url=f'https://coverartarchive.org/release/{release_id}'
    # url = "http://coverartarchive.org/release/943aa9da-7dc7-4a4a-a95e-2ffa707b6858/26256624132.jpg"
    response = requests.get(url)
    data = response.json()
    try:
        url = data['images'][0]['image']
    except Exception as e:
        print(e.args)
        print(e)

    content_type = response.headers.get("Content-Type", "image/jpeg")
    response = requests.get(url)
    image_data = response.content
    return image_data, content_type
    
def tag(artist_name:str, album_name:str):
    selected_album = select_album(artist_name=artist_name, album_name=album_name)
    print(selected_album)
    release_id,release_group_id  = selected_album
    track_list = get_songs(artist_name,album_name,release_id, release_group_id)
    print('track list length->{}'.format(len(track_list)))

    for mp3 in os.listdir():
        mp3_name, mp3_ext = os.path.splitext(mp3)
        if mp3_ext != ".mp3": continue
        print(f"***** {mp3} *****")
        words_filename = re.compile(r'[A-Za-z0-9]{1,1111}').findall(mp3_name)

        for track in track_list:
            match = 0
            # print('track->{}'.format(track['title']))s
            words_track = re.compile(r'[A-Za-z0-9]{1,1111}').findall(track['recording']['title'])
            for word_track in words_track:
                for word_filename in words_filename:
                    if word_filename == word_track:
                        match += 1
            if match /len(words_track)>0.5:
                print(f"\tmatch->{track['title']} - {mp3_name}")
                res = input("tag? Y/N.. Y")
                if res =="" or res.lower()=='y':
                    track_title = track['recording']['title']
                    track_position = track['position']
                    mp3_tag = eyed3.load(mp3)
                    mp3_tag.tag.artist = track_title
                    mp3_tag.tag.album = album_name
                    mp3_tag.tag.track_num = track_position
                    image_data, content_type = get_album_cover(release_id)
                    
                    mp3_tag.tag.images.set(3, image_data, content_type, u"Cover")
                    mp3_tag.tag.save()

                    print("tagged!!")


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
    tag(artist_name=artist_name, album_name=album_name)



if __name__ == '__main__':
    if sys.argv.__len__() == 1:
        print('COMMAND USE:\n\r\t--tag-songs ARTIST_NAME ALBUM_NAME: tags songs based on artist and album name,\r\n\t');
    elif sys.argv[1]=='--tag-songs':
        main()