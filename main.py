# FFMPEG version = 7.1 essentials build from https://www.gyan.dev/ffmpeg/builds/


import sys
import subprocess
from pathlib import Path
from tqdm import tqdm
import os
import shutil
import time
import shlex
import uuid
import colors
from tkinter import filedialog


codec = 'h264'
"codec - h264 or libx265"

crf = 24
"Constant Rate Factor - how much it's compressed - default 24"

extension = 'mp4'

new_video_append = ''

command = f'-vcodec {codec} -acodec aac -crf {crf}'

vid_format = ''
"Pixel format of video, for example 'scale=1080:-1'"

hwaccel = ''
"HW-accel config"

vid_filter_str = ''
"FFMPEG filters"
audio_filter_str = ''
"FFMPEG filters"



def check_file_name(name: str):
    base, ext = os.path.splitext(name)
    new_name = f"{base}{ext}"
    
    i = 1
    
    while os.path.exists(new_name):
        new_name = f"{base}{i}{ext}"
        i += 1
    return new_name


def get_num_frames(video_file):
    
    try:
        frame_command = ["ffmpeg", "-i", video_file, "-map", "0:v:0", "-c", "copy", "-f", "null", "-y", "/dev/null"]
        result = subprocess.run(frame_command, capture_output=True, text=True)
        
        lines = result.stdout + result.stderr
        if 'frame=' in lines:
            num_frames = lines.split('frame=')[1].split('fps')[0]
            return int(num_frames)
        
    except Exception:
        pass
    
    return 0


def compress_file(video_file):
    
    num_frames = get_num_frames(video_file)
    
    vid_name = './' + uuid.uuid4().hex + '.'  + extension

    final_filename = '.'.join(video_file.split('.')[:-1]) + new_video_append + '.' + extension
    cmd = shlex.split(f'ffmpeg{hwaccel} -y -i "{video_file}" {command} {vid_name}')
    
    print(colors.cyan(' '.join(cmd)))
        
    lines = ''
        
    ffmpeg = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    try:
        with tqdm(total=num_frames, unit='frames') as pbar:
            xint = 0
            for line in iter(ffmpeg.stdout.readline, ''):
                lines += line
                x = line[6:]
                x = x[:x.find('fps=')]
                try: xint = int(x.strip())
                except ValueError: continue
                pbar.n = min(xint, num_frames)
                pbar.update(0)
        
        returncode = ffmpeg.wait()
        ffmpeg.communicate()
        pbar.n = num_frames
        pbar.update(0)
        ffmpeg.terminate()
        
        if returncode > 0:
            print(colors.red(f'FFMPEG ERROR with {video_file} :\n'))
            time.sleep(1)
            print(colors.bg_red(lines))
            time.sleep(1)
            os.remove(vid_name)
            return
    
    except BaseException as e:
        
        ffmpeg.wait()
        ffmpeg.communicate()
        ffmpeg.terminate()
        
        os.remove(vid_name)
        raise e
    
    while True:
        try:
            if new_video_append == '':
                os.remove(video_file)
            else:
                final_filename = check_file_name(final_filename)
                print('File saved under name "' + colors.green(final_filename) + '"')
            
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
    print(colors.cyan("(Ctrl + C to set custom)\n"))
    try:
        time.sleep(5)
        customparams = 'N'
    except KeyboardInterrupt:
        customparams = 'y'


    if customparams.lower() == 'y':
        print(
            f"Type {colors.green('0-51')} to set {colors.cyan('CRF')}, \n" \
            f"{colors.green('HE')} to set {colors.cyan('HEVC/h265')} (default {colors.cyan('h264')}), \n" \
            f"{colors.green('AV')} to set {colors.cyan('AV1')}, \n" \
            f"{colors.green('SD')}, {colors.green('HD')}, {colors.green('FHD')} to rescale ({colors.cyan('480p, 720p, 1080p')}),\n" \
            f"{colors.green('f')} to set framerate to {colors.cyan('30fps')},\n" \
            f"{colors.green('a')} to normalize audio,\n" \
            f"{colors.green('h')} for {colors.cyan('Hardware Acceleration (CUDA)')},\n" \
            f"{colors.green('n')} to create a new file (without overriding current one).\n" \
            f"\n" \
            f"You can combine them, for example {colors.green('HEhn24HD')}\n" \
            f"{colors.cyan('24')} is good HD quality and {colors.cyan('42')} is acceptable SD quality for {colors.cyan('h264')} and {colors.cyan('HEVC')}\n" \
            f"\n" \
            f"Type {colors.green('c')} to set custom command\n"
        )
        
        x = input(colors.green('> '))
        
        scale_str = 'scale'
        
        if 'HE' in x: codec = 'libx265'
        if 'AV' in x: codec = 'libaom-av1'
        
        if 'f' in x: vid_filter_str += ' fps=30'
        
        if 'a' in x: audio_filter_str += ' loudnorm'
        
        max_crf = 51
        if codec == 'libaom-av1': max_crf = 63
        
        digits = ''.join(filter(str.isdigit, x))
        if digits and int(digits) in range(0, max_crf):
            crf = int(digits)
        
        crf_str = f'-crf {crf}'
        
        if 'h' in x:
            hwaccel = " -hwaccel cuda -hwaccel_output_format cuda"
            if codec == 'libx265': codec = "hevc_nvenc"
            elif codec == 'libaom-av1': codec = "av1_nvenc"
            else: codec = 'h264_nvenc'
            
            scale_str = 'scale_cuda'
            crf_str = f'-cq:v {crf}'
        
        
        if 'FHD' in x: vid_format = scale_str + '=-1:1080'
        elif 'HD' in x: vid_format = scale_str + '=-1:720'
        elif 'SD' in x: vid_format = scale_str + '=-1:480'
        
        if 'n' in x: new_video_append = '_copy'
        
        
        command = f'-vcodec {codec} -acodec aac {crf_str}'
        
        if vid_format != '':
            command += ' -vf ' + vid_format
        
        if vid_filter_str != '':
            command += ' -filter:v' + vid_filter_str
            
        if audio_filter_str != '':
            command += ' -filter:a' + audio_filter_str
        
        if 'c' in x:
            print(f'default extension: {colors.green(extension)}')
            new_extension = input("Video final extension: ")
            if new_extension.__len__() > 1: extension = new_extension
            print(f'default command: {colors.green(command)}')
            new_command = input("command: ")
            if new_command.__len__() > 1: command = new_command
        
        if codec == 'libaom-av1':
            print(colors.bg_yellow("WARNING: libaom-av1 SUCKS, use hwaccel, don't use AV1 or install non-lightweight ffmpeg with a better av1 codec installed."))
        
        print('New command: ' + colors.green(f'{hwaccel} -y {command}'))

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
            