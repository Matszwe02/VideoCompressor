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


formats = ["mp4", "avi", "mkv", "mpg", "mpeg", "wmv", "mov", "webm"]


class VideoSettings():
    def __init__(self):
        self.codec = 'h264'
        self.crf = 24
        self.extension = 'mp4'
        self.new_video_append = ''
        self.scale = ''
        self.hwaccel = ''
        self.hwaccel_str = ''
        self.vid_filter_str = ''
        self.audio_filter_str = ''
        self.command = f'-vcodec {self.codec} -acodec aac -crf {self.crf}'


    def generate(self, video_file: str):
        """
        retrns:
            tuple[vid_name, final_filename, cmd]
        """
        vid_name = './' + uuid.uuid4().hex + '.'  + self.extension
        final_filename = '.'.join(video_file.split('.')[:-1]) + self.new_video_append + '.' + self.extension
        cmd = shlex.split(f'ffmpeg{self.hwaccel_str} -y -i "{video_file}" {self.command} {vid_name}')
        return (vid_name, final_filename, cmd)


    def gen_command(self):
        self.crf = min(self.crf, 63)
        if self.codec != 'libaom-av1': self.crf = min(self.crf, 51)
        crf_str = f'-crf {self.crf}'
        scale_str = 'scale'
        if self.hwaccel:
            self.hwaccel_str = " -hwaccel cuda -hwaccel_output_format cuda"
            crf_str = f'-cq:v {self.crf}'
            scale_str = 'scale_cuda'
            cuda_codecs = {'libx265' : "hevc_nvenc", 'libaom-av1': "av1_nvenc"}
            self.codec = cuda_codecs.get(self.codec, 'h264_nvenc')
        
        vid_format = ''
        if self.scale:
            vid_format = scale_str + self.scale
        
        command = f'-vcodec {self.codec} -acodec aac {crf_str}'
        if vid_format: command += ' -vf ' + vid_format
        if self.vid_filter_str: command += ' -filter:v' + self.vid_filter_str
        if self.audio_filter_str: command += ' -filter:a' + self.audio_filter_str
        
        self.command = command




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


def compress_file(video_file: str, video_settings: VideoSettings):
    
    num_frames = get_num_frames(video_file)
    vid_name, final_filename, cmd = video_settings.generate(video_file)
    
    print(colors.cyan(shlex.join(cmd)))
        
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
            if video_settings.new_video_append == '':
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
            if file.split('.')[-1] in formats:
                videos.append(os.path.join(root, file))
    return videos



def decode_params(params: str, vs: VideoSettings):
    
    if 'HE' in params: vs.codec = 'libx265'
    if 'AV' in params: vs.codec = 'libaom-av1'
    if 'f' in params: vs.vid_filter_str += ' fps=30'
    if 'a' in params: vs.audio_filter_str += ' loudnorm'
    
    vs.crf = int(''.join(filter(str.isdigit, params))) or vs.crf
    
    if 'h' in params: vs.hwaccel = 'cuda'
    
    if 'FHD' in params: vs.scale = '=-1:1080'
    elif 'HD' in params: vs.scale = '=-1:720'
    elif 'SD' in params: vs.scale = '=-1:480'
    
    if 'n' in params: vs.new_video_append = '_copy'
    
    if 'c' in params:
        print(f'default extension: {colors.green(vs.extension)}')
        new_extension = input("Video final extension: ")
        if new_extension.__len__() > 1: vs.extension = new_extension
        print(f'default command: {colors.green(vs.command)}')
        new_command = input("command: ")
        if new_command.__len__() > 1: vs.command = new_command
    else:
        vs.gen_command()



def main(videos: list[str], new_params: str):
    vs = VideoSettings()
    
    if new_params:
        decode_params(new_params, vs)
        print('Command: ' + colors.green(f'ffmpeg {vs.hwaccel} -y {vs.command}\n\n'))
        for i, vid in enumerate(videos):
            print(f'Compressing {colors.green(i+1)} of {colors.green(videos.__len__())}')
            compress_file(str(Path(vid).absolute()), vs)
            return
    
    print(f"using default params: {colors.green(vs.command)}")
    print(colors.cyan("(Ctrl + C to set custom)\n\n"))
    try:
        time.sleep(5)
        
    except KeyboardInterrupt:
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
        
        decode_params(input(colors.green('> ')), vs)
        
        if vs.codec == 'libaom-av1':
            print(colors.bg_yellow("WARNING: libaom-av1 SUCKS, use hwaccel, don't use AV1 or install non-lightweight ffmpeg with a better av1 codec installed."))
        
        print('New command: ' + colors.green(f'{vs.hwaccel} -y {vs.command}\n\n'))
    
    for i, vid in enumerate(videos):
        print(f'Compressing {colors.green(i+1)} of {colors.green(videos.__len__())}')
        compress_file(str(Path(vid).absolute()), vs)



if __name__ == "__main__":
    args = sys.argv[1:]
    
    new_params = ''
    
    if '--sendto' in args:
        os.system('explorer %USERPROFILE%\\AppData\\Roaming\\Microsoft\\Windows\\SendTo')
        exit()
    
    if args and args[0].startswith('-'):
        new_params = args.pop(0).lstrip('-')
    
    if len(args) == 0:
        file_paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*." + " *.".join(formats)), ("All files", "*")])
        for file in file_paths:
            args.append(file)
    videos = []
    for arg in args:
        if os.path.isdir(arg):
            videos.extend(find_videos(arg))
        elif os.path.isfile(arg) and arg.split('.')[-1] in formats:
            videos.append(arg)
    
    main(videos, new_params)