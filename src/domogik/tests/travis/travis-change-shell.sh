# change the travis shell to /bin/bash to avoid some errors 
cat /etc/passwd
echo "====="
sudo usermod -s /bin/bash travis
echo "====="
ls -l /bin/bash
echo "====="
cat /etc/passwd
