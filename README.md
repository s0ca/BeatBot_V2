# BeatBot - audio streaming Discord bot

## Introduction
Beatbot is a self-hostable, single-server, home-made audio streaming bot that can
take input from YouTube, SoundCloud and virtually every platform `youtube-dl` supports.

Some CTF tools are also include

## Getting started
### Docker
```shell
git clone https://github.com/ZanyMonk/docker-beatbot beatbot
cd beatbot
docker-compose up
```

### Boomer
```shell
git clone https://github.com/s0ca/BeatBot_V2 beatbot
cd beatbot
pip install -r requirement.txt
./beatbot.py
```

### For Windows users (for real ?) 
```whell
.env files are buggy, you might need to hardcode the content of your .env file in beatbot.py 
```

## @TODO
- [ ] Fix vocal channel management
  - [ ] Quit all vocal channels when exiting
  - [ ] Auto-select a vocal channel when instigator isn't connected to any
  - [ ] Stabilize hard-reboot
- [ ] Rebase Docker image on `python:3.7-alpine`
- [ ] Finish reaction-based control
  - [ ] Implement button-like reactions
  - [ ] Improve embed filter for initial reaction (slash-command ?)
- [ ] Implement slash-command controls
