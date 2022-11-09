import os
import argparse

from pathlib import Path

parser = argparse.ArgumentParser(description='Re-encode Program Using FFMPEG')
parser.add_argument('--video-dir', type=str, required=True)
parser.add_argument('--output-dir', type=str, default="./")

args = parser.parse_args()

video_dir = args.video_dir
video_dir = video_dir.replace('"', '')
video_dir = video_dir.replace("'", '')

output_dir = args.output_dir
output_dir = output_dir.replace('"', '')
output_dir = output_dir.replace("'", '')

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

videos = [os.path.join(video_dir, video_file) for video_file in os.listdir(video_dir)]

for video in videos:
    
    if not video.lower().endswith((".avi", ".mp4", ".mkv")):
        continue
    
    video_name = Path(video).resolve().stem
    video_name = video_name.replace(" ", "_") + ".mp4"
    
    output = os.path.join(output_dir, video_name)
    
    cmd = "ffmpeg" + " "
    cmd += "-i" + " " + '"' + video + '"' + " "
    cmd += "-c:v" + " " + "copy" + " "
    cmd += "-y" + " "
    cmd += '"' + output + '"'
    
    print(cmd)
    os.system(cmd)
