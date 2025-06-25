







tutor local start -d



Version:1.0 StartHTML:0000000105 EndHTML:-9223372036854775704 StartFragment:-9223372036854775704 EndFragment:-9223372036854775704
curl https://acme-staging-v02.api.letsencrypt.org/directory



Version:1.0 StartHTML:0000000105 EndHTML:-9223372036854775704 StartFragment:-9223372036854775704 EndFragment:-9223372036854775704
echo "test-content" > acme-challenges/test-token



/home/h287zhu/.local/share/tutor/env/apps/caddy


/home/h287zhu/.local/share/tutor/env/local
/home/h287zhu/.local/share/tutor/env/apps/openedx/settings/cms



Version:1.0 StartHTML:0000000105 EndHTML:-9223372036854775704 StartFragment:-9223372036854775704 EndFragment:-9223372036854775704
@acme-challenge {
    path /.well-known/acme-challenge/*
}






    respond /.well-known/acme-challenge/* 200 {
        # 处理 Let's Encrypt 验证
    }




sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin




sudo usermod -aG docker $USER
