## Deployment Notes

Fresh Ubuntu server (18.04 LTS) in `~/` where `~`=`/home/ubuntu` on AWS EC2:

### Installing Docker
```
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker ubuntu
exit
```

### Installing and Deploying Zoom-Coordinator
(logs back in to `~/` as `ubuntu`)
```
git clone https://github.com/ChoateProgrammingUnion/zoom-coordinator
cd zoom-coordinator/
bash deploy
```
