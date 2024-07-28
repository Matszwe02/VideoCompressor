import sys
import subprocess
from pathlib import Path
from tqdm import tqdm
import os
import shutil
import psutil
import time
import atexit
import shlex
import uuid
import colors
from tkinter import filedialog


# codec - h264 or libx265
codec = 'h264'

# Constant Rate Factor - how much it's compressed - default 24
crf = 24

extension = 'mp4'

command = f'-vcodec {codec} -acodec aac -crf {crf}'



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


def compress_file(video_file):
    
    num_frames = get_num_frames(video_file)
    
    vid_name = './' + uuid.uuid4().hex + '.'  + extension

    final_filename = '.'.join(video_file.split('.')[:-1]) + '.' + extension
    cmd = shlex.split(f'ffmpeg -y -i "{video_file}" {command} {vid_name}')
    
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
            shutil.move(vid_name, final_filename)
            break
        except PermissionError:
            print(colors.red('warning! PermissionError. Retrying in 5s...'))
            time.sleep(5)


def find_videos(directory):
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.split('.')[-1] in ['mp4', 'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'mov', 'webm']:
                videos.append(os.path.join(root, file))
    return videos

if __name__ == "__main__":

    args = sys.argv[1:]
    if len(args) == 0:
        file_paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mpg *.mpeg *.wmv *.mov *.webm"), ("All files", "*")])
        for file in file_paths:
            args.append(file)

    print(f"using default params: {colors.green(command)}")
    print(colors.cyan("(Ctrl + C to set custom)"))
    try:
        time.sleep(5)
        customparams = 'N'
    except KeyboardInterrupt:
        customparams = 'y'


    if customparams.lower() == 'y':
        print(f"Type {colors.green('0-51')} to set {colors.cyan('CRF')}. Type {colors.green('h')} to set {colors.cyan('h264')}. Type {colors.green('l')} to set {colors.cyan('libx265')}. Type {colors.green('c')} to set custom command")
        x = input(colors.green('> '))
        
        if x == 'h': codec = 'h264'
        elif x == 'l': codec = 'libx265'
        elif x == 'c': pass
        else:
            crf = int(x)
            
        command = f'-vcodec {codec} -acodec aac -crf {crf}'
        
        if x == 'c':
            print(f'default extension: {colors.green(extension)}')
            new_extension = input("Video final extension: ")
            if new_extension.__len__() > 1: extension = new_extension
            print(f'default command: {colors.green(command)}')
            new_command = input("command: ")
            if new_command.__len__() > 1: command = new_command
        
        print('New command: ' + colors.green(command))

    print('\n\n')
    
    time.sleep(0.2)   
    videos = []


    for arg in args:
        if os.path.isdir(arg):
            videos.extend(find_videos(arg))
        elif os.path.isfile(arg) and arg.split('.')[-1] in ['mp4', 'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'mov', 'webm']:
            videos.append(arg)


    for i, vid in enumerate(videos):
        print(f'Compressing {colors.green(i+1)} of {colors.green(videos.__len__())}')
        video_file = Path(vid)
        compress_file(video_file.absolute().__str__())
            