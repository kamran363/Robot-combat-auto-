#!/bin/bash
# Segment normalization: 720x1280 24fps clips -> 1080x1920 30fps yuv420p segments, then concat
set -e
VID=/home/hatch/workspace/robot-combat-auto/staging/2026-10-05/vid
cd "$VID"

norm() { # norm <in> <ss> <t> <speed:1|half|fast> <out>
  local VF="scale=1080:1920"
  case "$4" in
    half) VF="$VF,setpts=2.0*PTS" ;;
    fast) VF="$VF,setpts=0.75*PTS" ;;
  esac
  VF="$VF,fps=30,format=yuv420p"
  /usr/bin/ffmpeg -hide_banner -loglevel error -y -ss "$2" -t "$3" -i "$1" \
    -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$5"
}

# ---------- V1: spinner vs hammer ----------
A="$VID/media-generation-rc-2026-10-05-v1a-0-a4e4751b-6e14-43bf-825a-2cdd69baa33b.mp4"
B="$VID/media-generation-rc-2026-10-05-v1b-0-78815fca-6430-485d-8f06-2b2fcd07ac97.mp4"
C="$VID/media-generation-rc-2026-10-05-v1c-0-31c84e6d-d0a0-40d7-a4a1-dfa35ce3d81a.mp4"
norm "$A" 0 6 normal v1_seg1.mp4
norm "$B" 1 6 normal v1_seg2.mp4
norm "$B" 4 3 half   v1_seg3.mp4
norm "$C" 1 6 normal v1_seg4.mp4
printf "file 'v1_seg1.mp4'\nfile 'v1_seg2.mp4'\nfile 'v1_seg3.mp4'\nfile 'v1_seg4.mp4'\n" > v1_list.txt
/usr/bin/ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i v1_list.txt -c copy v1_video_only.mp4

# ---------- V2: drum vs flipper ----------
A="$VID/media-generation-rc-2026-10-05-v2a-0-561addb1-0ad1-4385-92cb-956c94cb5121.mp4"
B="$VID/media-generation-rc-2026-10-05-v2c-0-73c8d46c-1dc1-436c-b862-92f932cda5b7.mp4"
C="$VID/media-generation-rc-2026-10-05-v2d-0-42f6e196-dc43-4b62-bf9e-f79cb3c24ae5.mp4"
norm "$A" 0 6 normal v2_seg1.mp4
norm "$B" 1 6 normal v2_seg2.mp4
norm "$C" 2 6 normal v2_seg3.mp4
norm "$A" 4 4.5 fast  v2_seg4.mp4
printf "file 'v2_seg1.mp4'\nfile 'v2_seg2.mp4'\nfile 'v2_seg3.mp4'\nfile 'v2_seg4.mp4'\n" > v2_list.txt
/usr/bin/ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i v2_list.txt -c copy v2_video_only.mp4

# ---------- V3: lifter vs wedge ----------
A="$VID/media-generation-rc-2026-10-05-v3a-0-64a1e37c-9d13-47fa-8601-6950e5beea9e.mp4"
B="$VID/media-generation-rc-2026-10-05-v3b-0-496d1481-1885-448a-b206-f512a1514991.mp4"
C="$VID/media-generation-rc-2026-10-05-v3c-0-81cda2ca-878c-4987-b8ef-59aad0b7962e.mp4"
norm "$A" 0 6 normal v3_seg1.mp4
norm "$B" 1 6 normal v3_seg2.mp4
norm "$B" 4 3 half   v3_seg3.mp4
norm "$C" 1 6 normal v3_seg4.mp4
printf "file 'v3_seg1.mp4'\nfile 'v3_seg2.mp4'\nfile 'v3_seg3.mp4'\nfile 'v3_seg4.mp4'\n" > v3_list.txt
/usr/bin/ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i v3_list.txt -c copy v3_video_only.mp4

for f in v1_video_only.mp4 v2_video_only.mp4 v3_video_only.mp4; do
  echo "== $f =="
  /usr/bin/ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -of default=noprint_wrappers=1 "$f" | tr '\n' ' '; echo
  /usr/bin/ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:format=duration "$f"
done
echo SEGMENTS_DONE
