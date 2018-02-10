# Given an mp4 video assigns the timing of the video frames
# based on an external file
#
# Alters:
# - stss
# - mvhd duration
# - mdhd duration
#
# Reference:
# https://wiki.multimedia.cx/index.php/QuickTime_container#stco
#
# by Emanuele Ruffaldi 2017

import sys
import os
import struct
from mp4file import Mp4File
from atom import Atom
import numpy as np

def copyfileobj(fsrc, fdst, size,length=16*1024):
    """copy data from file-like object fsrc to file-like object fdst"""
    while size > 0:
        buf = fsrc.read(length if length > size else size)
        if not buf:
            break
        size -= len(buf)
        fdst.write(buf)

"""
  ftyp,
  free,
  mdat,
  moov: [
    mvhd,
    trak: [
      tkhd,
      edts: [elst],
      mdia: [
        mdhd,
        hdlr,
        minf: [
          vmhd,
          dinf: [dref],
          stbl: [
            stsd: [mp4v],
            stts,
            stsc,
            stsz,
            stco
          ]
        ]
      ]
    ],
    udta: [meta: [hdlr, ilst: [xtoo: [data]]]]
  ],


Copy exactly up to moov (exact bytes to be fast)
Put all the metadata atoms in memory altering the content of:
    mvhd e mdhd due to the duration change
    stts with the new durations
"""

def cloneatom(a):
    oa = Atom(type=a.type)
    if not a.is_normal_container():
        # content followed by table
        oa.makestrstorage() # avoid using file
        a.seek(0,os.SEEK_SET)
        z = a.read()
        if len(z) != a.size():
            print "ERROR of size with atom",a.type
            raise Exception()
        oa.write(z)
        if a.is_special_container():
            print "special ",a.type,"has content",len(z),"and children",len(a)
    if a.is_container():
        for x in a:
            oa.append(cloneatom(x))        
    a.seek(0,os.SEEK_SET) #rewind
    return oa

class Mp4TimeSetter:
    def __init__(self,infile,output,durations,rate,duration,timeunit_hz,stream,verbose):
        self.infile = infile
        self.output = output # output filename
        self.durations = durations
        self.tstream = stream
        self.duration = duration # in seconds
        self.rate = rate
        self.timeunit_hz = timeunit_hz

        self.istream = 0
        self.found = False
        self.verbose = verbose
    def run(self):
        self.found = False
        """ Process the MP4 """
        moovseen = False
        self.infile.seek(0,os.SEEK_END)
        size = self.infile.tell()
        self.infile.seek(0,os.SEEK_SET)
        while self.infile.tell() < size:
            pre = self.infile.tell()
            root_atom = Atom( stream=self.infile, offset=pre )
            root_atom.seek( 0, os.SEEK_END )
            if root_atom.type == "moov":
                moovseen = True
                post = self.infile.tell()
                print "cloning all moov"
                c = cloneatom(root_atom)
                print "Cloned moov with",len(c),"children"

                self.infile.seek(0,os.SEEK_SET)
                print "Found moov at",pre,"copying for this size from input:",self.infile.tell(),"to output:",self.output.tell()
                copyfileobj(self.infile,self.output,pre)

                print "Patching moov"
                self.descendfix(c)
                print "Writing moov to output"
                # write out moov adjusting sizes
                c.save(self.output)
                print "Continuining after moov with input:",post,"output:",self.output.tell()
                self.infile.seek(post,os.SEEK_SET) 
            elif moovseen:
                print "unsupported after moov",root_atom.type
                self.found = False
        return self.found 
    def descendfix(self,c,sep=""):
        print "entering",sep,c.type
        if c.type == "mvhd" or c.type == "mdhd":
            c.seek(0, os.SEEK_SET)
            L = c.read(4)
            print "Patching",c.type,len(L),"with ",dict(duration=self.duration,timeunit_hz=self.timeunit_hz)
            v1 = struct.unpack(">L",L)[0]
            if v1 == 1:
                created_t,modified_t = struct.unpack(">QQ",c.read(16))
                tss = 8
            else:
                created_t,modified_t = struct.unpack(">LL",c.read(8))
                tss = 4
            c.write(struct.pack(">L",self.timeunit_hz))
            if v1 == 1:
                c.write(struct.pack(">Q",self.duration))
            else:
                c.write(struct.pack(">L",self.duration))
            c.write(struct.pack(">H",1)) # WHY we need to write it down
            #typically 1 c.write(struct.pack(">H",self.rate))
        elif c.type == "stts":        
            c.seek(0, os.SEEK_SET)
            v1 = struct.unpack(">L",c.read(4))[0]
            c.truncate()
            n = self.durations.shape[0]
            print "Patching stss with",n,"elements","version",v1
            c.write(struct.pack(">L",n))
            # now append all the stss
            c.write(np.reshape(self.durations.astype(np.dtype(">i4")),n*2).tostring())
            self.found = True
        if c.is_container():
            #print "descending",sep,c.type
            for child in c:
                self.descendfix(child,sep+"-")
def main():
    import argparse 

    parser = argparse.ArgumentParser(description='MP4 Time Setter')
    parser.add_argument("input")
    parser.add_argument("inputtime")
    parser.add_argument("--output",default="")
    parser.add_argument("--verbose",action="store_true")
    parser.add_argument("--stream",type=int,default=0)
    parser.add_argument("--scale",type=float,default=1)
    parser.add_argument("--timeunit",type=int,default=1000)

    args = parser.parse_args()

    if args.output == "":
        args.output = args.input + ".set.mp4"

    mp4file = Mp4File( args.input )
    durations = np.loadtxt(args.inputtime)
    if len(durations.shape) == 1:
        print "adding RLE1",durations.shape
        durations = np.reshape(durations,(durations.shape[0],1))
        durations = np.concatenate((
                np.ones((durations.shape[0],1),dtype=durations.dtype),durations),axis=1)
    durations[:,1] *= args.timeunit
    if args.scale != 1:
        durations[:,1] *= args.scale
    print durations
    total = np.sum(durations[:,1])
    print "total is",total/args.timeunit,"seconds with ",durations.shape[0],"frames"
    # TODO convert durations to RLE

    # rate duration timeunit_hz
    q = open(args.output+".tmp","wb")
    #self,infile,output,durations,rate,duration,timeunit_hzoutput,stream,verbose
    ee = Mp4TimeSetter(open(args.input,"rb"),q,  durations, 1, total, args.timeunit ,args.stream,args.verbose)
    if ee.run():
        print "done"
        q.close()
        os.rename(args.output+".tmp",args.output)
    else:
        print "error"
if __name__ == '__main__':
    main()