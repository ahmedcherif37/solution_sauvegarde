#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021 [CHERIF-Ahmed]

import os, subprocess, tarfile,logging , time, datetime
from ftplib import FTP


def install_php_apache():
 
 cmd =  "apt install apache2 php7.3 libapache2-mod-php7.3 php7.3-common php7.3-mbstring php7.3-xmlrpc php7.3-soap php7.3-gd php7.3-xml php7.3-intl php7.3-mysql php7.3-cli php7.3-ldap php7.3-zip php7.3-curl -y"
 os.system(cmd)
 
def install_mysql():
 
 cmd = "apt install default-mysql-server -y"
 os.system(cmd)
 

def mysql_secure():

 p = subprocess.Popen(['./mysql_secure.sh'], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()

# Initialisation de la base de données et creation d'une base wordpress
def create_database():
 os.system('apt install python3-pip -y')
 os.system('pip3 install setuptools')
 os.system('pip3 install mysql-connector')
 import mysql.connector

 mydb = mysql.connector.connect(host="localhost", user="root" , password="devops")
 mycursor = mydb.cursor()
 mycursor.execute("CREATE DATABASE wordpress")
 mycursor.execute("GRANT ALL PRIVILEGES on wordpress.* TO 'wordpress_user'@'localhost' IDENTIFIED BY 'password'")
 mycursor.execute("FLUSH PRIVILEGES")

# Installation de wordpress et configuration
def install_wordpress():
 os.system('apt-get install wget -y')
 os.system('cd /tmp/')
 os.system('wget -c https://wordpress.org/latest.tar.gz')
 os.system('tar -xvzf latest.tar.gz')
 os.system('mv wordpress/ /var/www/html/')
 os.system('chown -R www-data:www-data /var/www/html/wordpress/')
 os.system('chmod 755 -R /var/www/html/wordpress/')
 os.system ('cp wordpress.conf  /etc/apache2/sites-available/')
 os.system ('a2ensite wordpress.conf')
 

# chercher les derniers backups du serveur de sauvegarde et telecharger vers le serveur de recupération
def get_backup():
 from datetime import datetime

 ftp = FTP('192.168.1.52')
 ftp.login('cherif', 'devops')
 path=  '/home/cherif/ftp/'
 ftp.cwd(path)
 names = ftp.nlst()
 latest_time = None
 for f in names:
  #renvoie la date de la dernier modification du fichier
  modtime = ftp.sendcmd("MDTM "+ f)  
  d= datetime.strptime(modtime[4:], "%Y%m%d%H%M%S").strftime('%d/%m/%Y')
  if (latest_time is None) or (d > latest_time):
    latest_time = d
 for f in names:
  modtime = ftp.sendcmd("MDTM "+ f)  
  d= datetime.strptime(modtime[4:], "%Y%m%d%H%M%S").strftime('%d/%m/%Y')
  if d == latest_time:
   # telecharger du serveur de sauvegarde
   ftp.retrbinary("RETR " + f ,open(f, 'wb').write) 

def decompresser_backup():
 
 # récupérer le chemin du répertoire courant
 path = os.getcwd()
 for f in os.listdir(path):
  file= path+"/"+f
  if f[0:4]== "site":
   p = subprocess.Popen(['tar', 'xzvf',file,'-C',path], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
   stdout, stderr = p.communicate()
  if f[0:4]== "back":
   p = subprocess.Popen(['tar', 'xzvf',file,'-C',path], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
   stdout, stderr = p.communicate()

#deplacer le dossier wordpress et restorer la base de donnée
def restore_backup():
 
 path = os.getcwd()
 repo= path+"/var/www/html/wordpress"
 print(repo)
 p = subprocess.Popen(['cp','-r' ,repo ,'/var/www/html'], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()
 print ( stderr) 
 path1= path+"/root/backup/"
 for f in os.listdir(path1):
  file1= path1 + f
 print(file1)
 
 cmd= "mysql -u root -pdevops < " +file1
 os.system(cmd)
 os.system('a2enmod rewrite')
 os.system('systemctl restart apache2')

def main():
 install_php_apache()
 install_mysql()
 mysql_secure()
 create_database()
 install_wordpress()
 get_backup()
 decompresser_backup()
 restore_backup()

if __name__ == '__main__':
  main() 
