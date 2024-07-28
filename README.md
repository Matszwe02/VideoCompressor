# Video Compressor


### Description

This is a video compressor that converts the video into a smaller size. It uses the ffmpeg library to do so.

### How to use

Drag and drop a directory or single / multiple video files into `compressor.bat`. The compressed videos will be saved in the same folder as the originals with the extension `.mp4` or your selected one.
You can also link `compressor.bat` into `C:\Users\$USER\AppData\Roaming\Microsoft\Windows\SendTo` to link it to right click `Send To`.
If you open the program directly, there will be a video selection dialog.

Defaults to mp4 with CRF 24.

Warning! It overwrites the original video files, so ensure your compressions settings are right!