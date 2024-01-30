import sys
import subprocess
from pathlib import Path
from moviepy.editor import VideoFileClip
from tqdm import tqdm
import os
import shutil
import psutil
import time
import atexit

# codec - h264 or libx265
codec = 'h264'

# Constant Rate Factor - how much it's compressed - default 24
crf = 24

def exitprogram():
    os.remove('./LOCK')

atexit.register(exitprogram)

def get_num_frames(video_file):
    try:
        command = ["ffmpeg", "-i", video_file, "-map", "0:v:0", "-c", "copy", "-f", "null", "-y", "/dev/null"]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        lines = output.decode().split('\n')
        for line in lines:
            if 'frame=' in line:
                num_frames = line.split('frame=')[1].split('fps=')[0]
                return int(num_frames.strip())
    except Exception:
        return 0

# num_frames = get_num_frames('your_video_file.mp4')
# print(f'Number of frames: {num_frames}')


def compress_file(video_file):
    # print(video_file)
    # clip = VideoFileClip(video_file)
    # num_frames = clip.reader.nframes
    num_frames = get_num_frames(video_file)
    # clip.close()

    final_filename = '.'.join(video_file.split('.')[:-1]) + '.mp4'

    cmd = ['ffmpeg', '-y', '-i', video_file, '-vcodec', codec, '-acodec','aac', '-crf', str(crf), './temp.mp4']
    
    ffmpeg = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    xint = 0
    
    with tqdm(total=num_frames, unit='frames') as pbar:
        for line in iter(ffmpeg.stdout.readline, ''):
            x = line[6:]
            x = x[:x.find('fps=')]
            try: xint = int(x.strip())
            except ValueError: continue
            pbar.n = min(xint, num_frames)
            pbar.update(0)
    
    ffmpeg.wait()
    ffmpeg.communicate()
    pbar.n = num_frames
    pbar.update(0)
    ffmpeg.terminate()
    
    while True:
        try:
            os.remove(video_file)
            shutil.move('./temp.mp4', final_filename)
            break
        except PermissionError:
            print('warning! PermissionError. Retrying in 5s...')
            time.sleep(5)

time.sleep(0.2)

args = sys.argv[1:]

while os.path.exists('./LOCK'):
    print('Waiting for other instances to close...')
    time.sleep(10)

open('./LOCK','w').close()

for i, arg in enumerate(args):
    print(f'Compressing {i+1} of {args.__len__()}')
    video_file = Path(arg)
    compress_file(video_file.absolute().__str__())
        