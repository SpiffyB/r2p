#!/usr/bin/python
import os
import sys
import csv
import m3u8
import argparse
import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(prog="Rekordbox to Playlist",
                                     description="Convert playlists in rekordbox library .XML to .m3u8 playlists.")
    parser.add_argument("xml", type=str, help="Path to the Library XML file.")
    parser.add_argument("-o", "--output_folder", type=str, help="Path to create the files at.", default=os.path.curdir)
    parser.add_argument("-p", "--playlists", type=str, help="List of playlists to convert. (CSV)")
    args = parser.parse_args()

    if args.output_folder:
        args.output_folder = Path(args.output_folder)
        if args.output_folder.is_dir() == False:
            print(f"Error: The path {args.output_folder} is not a folder")
            sys.exit(1)

    if args.playlists:
        f = StringIO(args.playlists)
        args.playlists = list(csv.reader(f , delimiter=','))[0]
    return args

def create_track_dict(xml_tree_root: str):
    track_dict={}
    for track in xml_tree_root.find('COLLECTION'):
        track_dict[track.attrib['TrackID']] = track.attrib
    return track_dict


def convert_playlist(playlist_node,  track_dict: dict, name_prefix: str = "", output_folder:str=None) -> str:
    playlist_name = playlist_node.attrib['Name']

    track_strings = []
    for track in playlist_node:
        title = track_dict[track.attrib['Key']]['Name']
        artist = track_dict[track.attrib['Key']]['Artist']
        total_time = track_dict[track.attrib['Key']]['TotalTime']
        location = track_dict[track.attrib['Key']]['Location']
        
        entry = f"#EXTINF:{total_time},{artist} - {title}\n{location}"
        track_strings.append(entry)

    if len(track_strings) <= 0:
        return False

    track_strings[0] = "\n".join(["#EXTM3U", track_strings[0]])
    m3u8_string = "\n".join(track_strings)
    m3u8_playlist = m3u8.loads(m3u8_string)

    if name_prefix != "":
        out_path = Path(name_prefix.replace('/', '&') + ' - ' + playlist_name.replace('/', '-') + '.m3u8')
    else:
        out_path = Path(playlist_name.replace('/', '-') + '.m3u8')

    if output_folder:
        out_path = Path(output_folder) / out_path
    m3u8_playlist.dump(out_path)

def traverse_playlist_tree(playlist_iter, track_dict, name_prefix:str = "", output_folder=None):
    for playlist in playlist_iter:
        if playlist.attrib['Name'] == 'Imported Playlists':
            continue
        if playlist.attrib['Type'] == "0":
            if name_prefix != "":
                name_prefix = name_prefix + ' - ' + playlist.attrib['Name']
            else:
                name_prefix = playlist.attrib['Name']
            traverse_playlist_tree(playlist, track_dict, name_prefix=name_prefix, output_folder=output_folder)
            name_prefix = ""
            continue
        
        convert_playlist(playlist, track_dict, name_prefix=name_prefix, output_folder=output_folder)


def convert(xml: str, output_folder:str=None, playlists=None):
    xml_tree = ET.parse(xml)
    xml_tree_root = xml_tree.getroot()
    track_dict = create_track_dict(xml_tree_root)
    all_playlists = xml_tree_root.find('PLAYLISTS/NODE')

    traverse_playlist_tree(all_playlists, track_dict, output_folder=output_folder)

if __name__ == '__main__':
    args = parse_args()
    convert(**vars(args))