#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python 3.x

__version__ = '1.7'

'''
布卡漫画转换工具
支持 .buka, .bup.view, .jpg.view

漫画目录 存放在 /sdcard/ibuka/down
'''

import sys
import os
import shutil
import time
import json
import struct
import subprocess
import sqlite3
from collections import deque

helpm = '''提取布卡漫画下载的漫画文件

用法: python3 %s 输入文件(夹) [输出文件夹]

必需参数:
 输入文件(夹)  .buka文件或包含下载文件的文件夹
             通常位于 (安卓SD卡) /sdcard/ibuka/down

可选参数:
 输出文件夹    指定输出文件夹
             默认为原目录下 output 文件夹
''' % sys.argv[0]


class BadBukaFile(Exception):
    pass

class BukaFile:
	def __init__(self, filename):
		'''Reads the buka file.'''
		self.filename = filename
		f = self.fp = open(filename, 'rb')
		buff = f.read(128)
		if buff[0:4] != b'buka':
			raise BadBukaFile('not a buka file')
		self.comicid = struct.unpack('<I', buff[12:16])[0]
		self.chapid = struct.unpack('<I', buff[16:20])[0]
		pos = buff.find(b'\x00', 20)
		self.comicname = buff[20:pos].decode(encoding='utf-8', errors='ignore')
		pos += 1
		endhead = pos + struct.unpack('<I', buff[pos:pos + 4])[0] - 1
		pos += 4
		f.seek(pos)
		buff = f.read(endhead-pos+1)
		self.files = {}
		pos = 0
		while pos+8 < len(buff):
			pointer, size = struct.unpack('<II', buff[pos:pos + 8])
			pos += 8
			end = buff.find(b'\x00', pos)
			name = buff[pos:end].decode(encoding='utf-8', errors='ignore')
			pos = end + 1
			self.files[name] = (pointer, size)
	
	def extract(self, member, path):
		with open(path, 'wb') as w:
			index = self.files[member]
			self.fp.seek(index[0])
			w.write(self.fp.read(index[1]))
	
	def extractall(self, path):
		if not os.path.exists(path):
			os.makedirs(path)
		for key in self.files:
			self.extract(key, os.path.join(path, key))
	
	def __repr__(self):
		return "<BukaFile comicid=%r chapid=%r comicname=%r>" % \
			(self.comicid, self.chapid, self.comicname)
	
	def close(self):
		self.fp.close()
	
	def __del__(self):
		self.fp.close()

class ComicInfo:
	def __init__(self, chaporder):
		self.chaporder = chaporder
		self.comicname = chaporder['name']
		self.chap = {}
		for d in chaporder['links']:
			self.chap[d['cid']] = d
		try:
			self.comicid = int(chaporder['logo'].split('/')[-1].split('-')[0])
		except:
			self.comicid = -1
	
	def renamef(self, cid):
		if cid in self.chap:
			if self.chap[cid]['title']:
				return self.chap[cid]['title']
			else:
				if self.chap[cid]['type'] == '0':
					return '第' + self.chap[cid]['idx'].zfill(2) + '卷'
				elif self.chap[cid]['type'] == '1':
					return '第' + self.chap[cid]['idx'].zfill(3) + '话'
				elif self.chap[cid]['type'] == '2':
					return '番外' + self.chap[cid]['idx'].zfill(2)
				else:
					return self.chap[cid]['idx'].zfill(3)
		else:
			return cid

	def __repr__(self):
		return "<ComicInfo comicid=%r comicname=%r>" % (self.comicid, self.comicname)

def buildfromdb(dbname):
	db = sqlite3.connect(dbname)
	c = db.cursor()
	initd = {'author': '', #mangainfo/author
			 'discount': '0', 'favor': 0,
			 'finish': '0', #ismangaend/isend
			 'intro': '',
			 'lastup': '', #mangainfo/recentupdatename
			 'lastupcid': '', #Trim and lookup chapterinfo/fulltitle
			 'lastuptime': '', #mangainfo/recentupdatetime
			 'lastuptimeex': '', #mangainfo/recentupdatetime + ' 00:00:00'
			 'links': [], #From chapterinfo
			 'links': [{'cid': '0', #chapterinfo/cid
						'idx': '0', #chapterinfo/idx
						'ressupport': '7',
						'size': '0',
						'title': '', #chapterinfo/title if not chapterinfo/fulltitle else ''
						'type': '0' #'卷' in chapterinfo/fulltitle : 0; '话':1; not chapterinfo/fulltitle: 2
						}],
			 'logo': 'http://c-pic3.weikan.cn/logo/logo/1906-b.jpg',
			 'logos': 'http://c-pic3.weikan.cn/logo/logo/1906-s.jpg',
			 'name': '有你的小镇',
			 'popular': 9999999,
			 'populars': '10000000+',
			 'rate': '20',
			 'readmode': 50331648,
			 'readmode2': '0',
			 'recomctrlparam': '101696',
			 'recomctrltype': '1',
			 'recomdelay': '2000',
			 'recomenter': '应聘>>>',
			 'recomwords': '我想找几个小伙伴一起玩~',
			 'res': [{'cid': '65651', 'csize': '4942', 'restype': '1'},
					 {'cid': '65651', 'csize': '8566', 'restype': '2'},
					 {'cid': '65651', 'csize': '7245', 'restype': '4'}],
			 'resupno': '1384827572',
			 'ret': 0,
			 'upno': '1418'}

	

def detectfile(filename):
	"""Tests file format."""
	if filename == 'index2.dat':
		return 'index2'
	elif filename == 'chaporder.dat':
		return 'chaporder'
	ext = os.path.splitext(filename)[1]
	if ext == 'buka':
		return 'buka'
	elif ext == 'bup':
		return 'bup'
	elif ext == 'view':
		ext2 = os.path.splitext(os.path.splitext(filename)[0])[1]
		if ext2 == 'jpg':
			return 'jpg'
		elif ext2 == 'bup':
			return 'bup'
		elif ext2 == 'png':
			return 'png'
	with open(filename, 'rb'):
		h = f.read(32)
	if h[6:10] in (b'JFIF', b'Exif'):
		return 'jpg'
	elif h.startswith(b'\211PNG\r\n\032\n'):
		return 'png'
	elif h[:4] == b"buka":
		return 'buka'
	elif h[:4] == b"AKUB":
		return 'index2'
	elif h[:4] == b"bup\x00":
		return 'bup'
	elif h.startswith(b'SQLite format 3'):
		return 'sqlite3'
	elif h[:4] == b"RIFF" and h[8:16] == b"WEBPVP8 ":
		return 'webp'
	else:
		return False

def extractbuka(bkname, target):
	if not os.path.isfile(bkname):
		print('没有此文件: ' + bkname)
		return ''
	if not os.path.exists(target):
		os.mkdir(target)
	toc = []
	comicname = ''
	with open(bkname, 'rb') as f:
		buff = f.read(16384)
		chapid = struct.unpack('<I', buff[16:20])[0]
		pos = buff.find(b'\x00', 20)
		comicname = buff[20:pos].decode(errors='ignore')
		pos += 1
		endhead = pos + struct.unpack('<I', buff[pos:pos + 4])[0] - 1
		pos += 4
		while pos < endhead:
			pointer, size = struct.unpack('<II', buff[pos:pos + 8])
			pos += 8
			end = buff.find(b'\x00', pos)
			name = buff[pos:end].decode(errors='ignore')
			pos = end + 1
			toc.append((pointer, size, name))
		for index in toc:
			img = open(os.path.join(target, index[2]), 'wb')
			f.seek(index[0])
			img.write(f.read(index[1]))
			img.close()









def copytree(src, dst, symlinks=False, ignore=None):
	if not os.path.exists(dst):
		os.makedirs(dst)
	for item in os.listdir(src):
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if os.path.isfile(s) and (os.path.splitext(s)[1] not in [".view", ".buka"]) and item != 'chaporder.dat':
			continue
		if os.path.isdir(s):
			copytree(s, d, symlinks, ignore)
		else:
			if os.path.isfile(os.path.join(dst, os.path.splitext(item)[0])):
				continue
			elif not os.path.isfile(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
				shutil.copy2(s, d)

def build_dict(seq, key):
	rd = {}
	for d in seq:
		rd[d[key]] = d
	return rd


class dwebpManager:
	def __init__(self, dwebp):
		self.dwebp = dwebp
		self.queue = deque()
		self.proc = deque()
		self.maxlen = 5
	
	def decode(self, webp):
		self.proc.append(subprocess.Popen([dwebp, basepath + ".webp", "-o", os.path.splitext(basepath)[0] + ".png"], cwd=os.getcwd()))

def main():
	if sys.version_info[0] < 3:
		print('要求 Python 3.')
		if os.name == 'nt':
			time.sleep(3)
		sys.exit()

	if len(sys.argv) == 2:
		if sys.argv[1] in ("-h", "--help"):
			print(helpm)
			if os.name == 'nt':
				time.sleep(3)
			sys.exit()
		else:
			target = os.path.join(os.path.dirname(sys.argv[1]), "output")
			if not os.path.exists(target):
				os.mkdir(target)
	elif len(sys.argv) == 3:
		target = sys.argv[2]
	else:
		print(helpm)
		if os.name == 'nt':
			time.sleep(3)
		sys.exit()

	fn_buka = sys.argv[1]
	programdir = os.path.dirname(os.path.abspath(sys.argv[0]))

	if os.name == 'nt':
		dwebp = os.path.join(programdir, 'dwebp.exe')
	else:
		dwebp = os.path.join(programdir, 'dwebp')

	print("检查环境...")
	try:
		with open(os.devnull, 'w') as nul:
			p = subprocess.Popen(dwebp, stdout=nul, stderr=nul).wait()
		supportwebp = True
	except Exception as ex:
		if os.name == 'posix':
			try:
				with open(os.devnull, 'w') as nul:
					p = subprocess.Popen('dwebp', stdout=nul, stderr=nul).wait()
				supportwebp = True
			except Exception as ex:
				print(_("dwebp 不可用，仅支持普通文件格式。\n") + repr(ex))
				supportwebp = False
		else:
			print(_("dwebp 不可用，仅支持普通文件格式。\n") + repr(ex))
			supportwebp = False

	if os.path.isdir(target):
		if os.path.splitext(fn_buka)[1] == ".buka":
			if not os.path.isfile(fn_buka):
				print('没有此文件: ' + fn_buka)
				if not os.listdir(target):
					os.rmdir(target)
				if os.name == 'nt':
					time.sleep(3)
				sys.exit()
			print('正在提取 ' + fn_buka)
			extractbuka(fn_buka, target)
			if os.path.isfile(os.path.join(target, "chaporder.dat")):
				dat = json.loads(open(os.path.join(target, "chaporder.dat"), 'r').read())
				os.remove(os.path.join(target, "chaporder.dat"))
				chap = build_dict(dat['links'], 'cid')
				newtarget = os.path.join(os.path.dirname(target), dat['name'] + '-' + renamef(chap, os.path.basename(os.path.splitext(fn_buka)[0])))
				shutil.move(target, newtarget)
				target = newtarget
		elif os.path.isdir(fn_buka):
			print('正在复制...')
			copytree(fn_buka, target)
		else:
			print("输入必须为 .buka 文件或一个文件夹。")
		allfile = []
		dwebps = []
		for root, subFolders, files in os.walk(target):
			for name in files:
				fpath = os.path.join(root, name)
				if os.path.splitext(fpath)[1] == ".buka":
					print('正在提取 ' + fpath)
					extractbuka(fpath, os.path.splitext(fpath)[0])
					chaporder = os.path.join(os.path.splitext(fpath)[0], "chaporder.dat")
					if os.path.isfile(chaporder):
						dat = json.loads(open(chaporder, 'r').read())
						os.remove(chaporder)
						chap = build_dict(dat['links'], 'cid')
						shutil.move(os.path.splitext(fpath)[0], os.path.join(os.path.dirname(fpath), renamef(chap, os.path.basename(os.path.splitext(fpath)[0]))))
					os.remove(fpath)
		for root, subFolders, files in os.walk(target):
			for name in files:
				allfile.append(os.path.join(root, name))
		for fpath in allfile:
			print('正在提取 ' + fpath)
			if os.path.splitext(fpath)[1] in (".view", ".bup"):
				if os.path.splitext(fpath)[1] == ".view":
					bupname = os.path.splitext(fpath)[0]
				else:
					bupname = fpath
				basepath = os.path.splitext(bupname)[0]
				if os.path.splitext(bupname)[1] == ".bup":
					if supportwebp:
						with open(fpath, "rb") as bup, open(basepath + ".webp", "wb") as webp:
							bup.read(64)  # and eat it
							shutil.copyfileobj(bup, webp)
						os.remove(fpath)
						p = subprocess.Popen([dwebp, basepath + ".webp", "-o", os.path.splitext(basepath)[0] + ".png"], cwd=os.getcwd())  # .wait()  faster
						time.sleep(0.2)  # prevent creating too many dwebp's
						if not p.poll():
							dwebps.append(p)
					else:
						os.remove(fpath)
				else:
					shutil.move(fpath, bupname)
			# else:	pass
		if dwebps:
			print("等待所有 dwebp 转换进程...")
			for p in dwebps:
				p.wait()
		print("完成转换。")
		print("正在重命名...")
		alldir = []
		for root, subFolders, files in os.walk(target):
			for name in files:
				if os.path.splitext(name)[1] == ".webp":
					os.remove(os.path.join(root, name))
			for name in subFolders:
				alldir.append((root, name))
		alldir.append(os.path.split(target))
		for dirname in alldir:
			fpath = os.path.join(dirname[0], dirname[1])
			if os.path.isfile(os.path.join(fpath, "chaporder.dat")):
				dat = json.loads(open(os.path.join(fpath, "chaporder.dat"), 'r').read())
				os.remove(os.path.join(fpath, "chaporder.dat"))
				chap = build_dict(dat['links'], 'cid')
				for item in os.listdir(fpath):
					if os.path.isdir(os.path.join(fpath, item)):
						shutil.move(os.path.join(fpath, item), os.path.join(fpath, renamef(chap, item)))
				shutil.move(fpath, os.path.join(dirname[0], dat['name']))
		if not supportwebp:
			print('警告: .bup 格式文件无法提取。')
		print('完成。')
	else:
		print("错误: 输出文件夹路径为一个文件。")
