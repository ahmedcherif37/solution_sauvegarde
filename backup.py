#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021 [CHERIF-Ahmed]

#from datetime import datetime
import os, subprocess, tarfile,logging , time, datetime
from ftplib import FTP

# retourne la date de système
def retour_date_systeme():
 #d= datetime.now()
 d= datetime.date.today()
 return d

# retourne la date sytème en chaine de caractère
def conversion_chaine(d):
 d= str(d)
 a= d[0:4]
 m= d[5:7]
 j= d[8:10]
 dc= j+ "_"+ m +"_"+ a
 return dc

# Compression des du fichier bfile et enregistrement dans le dossier dir
# dir : path dossier de destination
# bfile : string nom du fichier a compresser
def mysql_compress(dir, bfile):
 global ERREUR
 logging.info(' ------------------------------- Backup_compress %s ------------------------------- ', bfile)
 cmd = ['tar','zcvf',dir + '/' + bfile + '.tar.gz',dir + '/' + bfile]
 p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()
 if p.returncode != 0:
  logging.error(" Backup_compressError : L erreur %s est survenue pendant la compression du fichier %s : %s",p.returncode, dir + '/' + bfile, stderr)
  write_errormessage("Mysql_compress","Compression de la base",bfile, stderr)
  ERREUR=True
 else:
  logging.info(' Compression de la base %s OK', bfile)
 
 try:
  os.remove(os.path.join(dir,bfile))
 except Exception as e:
  logging.error(" Backup_compressError : L erreur %s est survenue pendant la suppression du fichier %s : %s",getattr(e, 'message', str(e)), dir + '/' + bfile, getattr(e, 'message', str(e)))
  write_errormessage("Mysql_compress","Suppression du fichier sql",bfile, getattr(e, 'message', str(e)))
  ERREUR=True
 else:
  logging.info(' Suppression du fichier SQL %s OK', dir + '/' + bfile)



# fonction permet de créer un backup de la base de données
def mysql_backup(d1, chemin):
 d2= conversion_chaine(d1)

 if  os.path.exists(chemin):
  bfile = "backup_base"+ d2+ ".sql"
  dumpfile = open(os.path.join(chemin, bfile), 'w')
  p = subprocess.Popen(['mysqldump', '-u','root','-pdevops','--all-databases'], stdout=dumpfile)
  retcode = p.wait()
  dumpfile.close()
  if retcode > 0:
   logging.error(" Mysql_backupError : L erreur %s est survenue pendant le dump de la base",retcode)
   ERREUR=True
  else:
   logging.info(" Dump de la base %s OK")
   mysql_compress(chemin,bfile)
 else:
  print("chemin n existe pas, il sera recréer , rexecuter le script")
  os.mkdir(chemin)
 
 return bfile


# fonction de transfert vers le serveur de sauvegarde
def put_backup(chemin,bfile): 
  
 source= chemin + '/'+bfile+'.tar.gz'
 cmd= ['ncftpput', '-u','cherif','-pdevops', '192.168.1.52','/home/cherif/ftp/', source]
 p= subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()
 if p.returncode != 0:
  logging.error(" Backup_putError : L erreur %s est survenue pendant le put du fichier %s : %s",p.returncode, chemin + '/' + bfile, stderr)
 else:
  logging.info(' Le sauvegarde a ete bien mis dans le serveur des backups')


# compresser tous les fichiers de site et les transmettres vers le serveur de sauvegarde

def put_file_backup(d1,chemin):
 global ERREUR

 d2= conversion_chaine(d1)
 site='/var/www/html/wordpress'
 namefile='site'+d2+ '.tar.gz'
 logging.info(' Backup_compress de site  ')
 cmd = ['tar','zcvf','/root/backup/'+namefile,site]
 p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()
 if p.returncode != 0:
  logging.error(" Backup_compressError : L'erreur est survenue pendant la compression du site ", p.returncode, stderr)
  ERREUR=True
 else:
  logging.info(' Compression de site OK')
 
 source= chemin + '/' + namefile 
 cmd= ['ncftpput', '-u','cherif','-pdevops', '192.168.1.52','/home/cherif/ftp/', source]
 p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
 stdout, stderr = p.communicate()
 if p.returncode != 0:
  logging.error(" Backup_compressError : L'erreur est survenue pendant l envoie du site vers le serveur de sauvegarde ", p.returncode)
  ERREUR=True
 else:
  logging.info(' Envoi de site OK')


# calcul la difference entre 2 dates en nombre de jours
def calcul_nombre_jour(d1,d2):
 
 d1= str(d1)
 d2= str(d2)
 d11= datetime.date(int(d1[0:4]), int(d1[5:7]), int(d1[8:10]))
 d21= datetime.date(int(d2[6:10]), int(d2[3:5]), int(d2[0:2]))
 nbj= d11 - d21
 return nbj.days


#supprimer  tous les backups locaux qui ont dépasser 15 jours
def delete_file(d1,chemin):
 
 for root, dirs, files in os.walk(chemin):
  for name in files:
   filename=chemin+"/"+name
   d2= time.strftime('%d/%m/%Y', time.localtime(os.path.getmtime(filename)))
   nbj= calcul_nombre_jour(d1,d2)
   #print ( name , ' ', nbj) 
   if  nbj >= 15 :
    os.remove(filename)

#supprimer tous les backups  du serveurs de sauvegarde qui ont dépasser  les 15 jours

def delete_backups_remote_server(d1):
 from datetime import datetime

 ftp = FTP('192.168.1.52')
 ftp.login('cherif', 'devops')
 path=  '/home/cherif/ftp/'
 ftp.cwd(path)
# files = ftp.retrlines('LIST')
 files=ftp.nlst()
 now = time.time()
 
 for f in files:
  modtime = ftp.sendcmd("MDTM "+ f)  
  d2= datetime.strptime(modtime[4:], "%Y%m%d%H%M%S").strftime('%d/%m/%Y')
  nbj= calcul_nombre_jour(d1,d2)
 # print(f, ' ', nbj)
  if  nbj >= 15 :
   ftp.delete(f)
# for f in os.listdir(path):
#  if os.stat(f).st_mtime < now - 7 * 86400:
   #if os.path.isfile(f):
       # os.remove(os.path.join(path, f))
    # print(f)   
 ftp.close()
 

#permettant de sauvegarder ces données et de les copier sur un serveur FTP externe. 
#Le script assurera une rotation des sauvegardes afin d’éviter une accumulation de ces fichiers.

def main():
 logging.basicConfig(filename='myapp.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p' )
 logging.info('Started')
 d1= retour_date_systeme()
 chemin= "/root/backup"
 bfile= mysql_backup(d1,chemin)
 put_backup(chemin,bfile)
 put_file_backup(d1, chemin)
 delete_file(d1,chemin)
 delete_backups_remote_server(d1)
 logging.info('Finished')





if __name__ == '__main__':
  main() 
